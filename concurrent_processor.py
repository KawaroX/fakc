import asyncio
import time
import math
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from openai import AsyncOpenAI
import logging

@dataclass
class ProcessingTask:
    """处理任务数据类"""
    task_id: str
    data: Any
    retry_count: int = 0
    error: Optional[Exception] = None
    result: Optional[Any] = None
    processing_time: Optional[float] = None

@dataclass
class ConcurrentConfig:
    """并发配置"""
    max_concurrent: int = 20  # 最大并发数（API限制）
    max_retries: int = 3  # 最大重试次数
    retry_delay: float = 1.0  # 重试延迟（秒）
    timeout: int = 60  # 单个任务超时时间（秒）
    rate_limit_delay: float = 60.0  # 达到限制后的等待时间（秒）
    min_batch_size: int = 1  # 最小批次大小
    
class ConcurrentKnowledgeProcessor:
    """并发知识点处理器"""
    
    def __init__(self, client, model: str, config: Optional[ConcurrentConfig] = None):
        """
        初始化并发处理器
        
        Args:
            client: OpenAI客户端实例
            model: 使用的模型名称
            config: 并发配置，如果为None则使用默认配置
        """
        # 如果传入的是同步客户端，创建异步客户端
        if hasattr(client, 'api_key'):
            self.async_client = AsyncOpenAI(
                api_key=client.api_key,
                base_url=getattr(client, 'base_url', None) or client._base_url
            )
        else:
            self.async_client = client
            
        self.model = model
        self.config = config or ConcurrentConfig()
        
        # 统计信息
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'total_retries': 0,
            'total_processing_time': 0.0,
            'batches_processed': 0
        }
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
    
    def calculate_optimal_batches(self, total_tasks: int, estimated_remaining_calls: int = None) -> List[int]:
        """
        计算最优的批次分配
        
        Args:
            total_tasks: 总任务数
            estimated_remaining_calls: 估计的剩余API调用次数
            
        Returns:
            每个批次的任务数量列表
        """
        if total_tasks <= 0:
            return []
        
        # 如果没有提供剩余调用次数，假设有足够的调用次数
        if estimated_remaining_calls is None:
            estimated_remaining_calls = self.config.max_concurrent
        
        # 实际可用的并发数（考虑剩余API调用次数）
        available_concurrent = min(self.config.max_concurrent, estimated_remaining_calls, total_tasks)
        
        if available_concurrent <= 0:
            # 如果没有可用的并发数，逐个处理
            return [1] * total_tasks
        
        if total_tasks <= available_concurrent:
            # 如果任务数不超过并发数，一次处理完
            return [total_tasks]
        
        # 计算最优的批次数量，尽量减少批次数
        num_batches = math.ceil(total_tasks / available_concurrent)
        batches = []
        
        remaining_tasks = total_tasks
        for i in range(num_batches):
            # 均匀分配任务，最后一批可能少一些
            tasks_in_batch = min(available_concurrent, remaining_tasks)
            batches.append(tasks_in_batch)
            remaining_tasks -= tasks_in_batch
            
            # 如果是多批次处理，第二批开始可以使用更多的并发数（假设已过了一分钟）
            if i == 0 and num_batches > 1:
                available_concurrent = min(self.config.max_concurrent, remaining_tasks)
        
        return batches
    
    async def process_single_task(self, task: ProcessingTask, prompt_builder: Callable) -> ProcessingTask:
        """
        处理单个任务
        
        Args:
            task: 处理任务
            prompt_builder: 提示词构建函数
            
        Returns:
            处理完成的任务
        """
        start_time = time.time()
        
        try:
            # 构建提示词
            prompt = prompt_builder(task.data)
            
            # 调用API
            response = await asyncio.wait_for(
                self.async_client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                ),
                timeout=self.config.timeout
            )
            
            # 提取结果
            task.result = response.choices[0].message.content.strip()
            task.processing_time = time.time() - start_time
            
            self.logger.info(f"Task {task.task_id} completed in {task.processing_time:.2f}s")
            
        except Exception as e:
            task.error = e
            task.processing_time = time.time() - start_time
            self.logger.error(f"Task {task.task_id} failed: {e}")
        
        return task
    
    async def process_batch(self, tasks: List[ProcessingTask], prompt_builder: Callable) -> List[ProcessingTask]:
        """
        处理一个批次的任务
        
        Args:
            tasks: 任务列表
            prompt_builder: 提示词构建函数
            
        Returns:
            处理完成的任务列表
        """
        self.logger.info(f"Processing batch of {len(tasks)} tasks")
        
        # 创建异步任务
        async_tasks = [
            self.process_single_task(task, prompt_builder) 
            for task in tasks
        ]
        
        # 并发执行
        completed_tasks = await asyncio.gather(*async_tasks, return_exceptions=True)
        
        # 处理返回的结果
        results = []
        for i, result in enumerate(completed_tasks):
            if isinstance(result, Exception):
                tasks[i].error = result
            else:
                results.append(result)
        
        return results if results else tasks
    
    async def process_with_retries(self, tasks: List[ProcessingTask], prompt_builder: Callable) -> List[ProcessingTask]:
        """
        处理任务并包含重试逻辑
        
        Args:
            tasks: 任务列表
            prompt_builder: 提示词构建函数
            
        Returns:
            处理完成的任务列表
        """
        completed_tasks = []
        retry_tasks = tasks.copy()
        
        while retry_tasks and any(task.retry_count <= self.config.max_retries for task in retry_tasks):
            # 筛选需要重试的任务
            current_batch = [
                task for task in retry_tasks 
                if task.retry_count <= self.config.max_retries and task.result is None
            ]
            
            if not current_batch:
                break
            
            # 处理当前批次
            batch_results = await self.process_batch(current_batch, prompt_builder)
            
            # 分类处理结果
            new_retry_tasks = []
            for task in batch_results:
                if task.result is not None:
                    # 成功完成
                    completed_tasks.append(task)
                    self.stats['completed_tasks'] += 1
                elif task.retry_count < self.config.max_retries:
                    # 需要重试
                    task.retry_count += 1
                    new_retry_tasks.append(task)
                    self.stats['total_retries'] += 1
                    
                    # 重试延迟
                    await asyncio.sleep(self.config.retry_delay * task.retry_count)
                else:
                    # 重试次数用尽，标记为失败
                    completed_tasks.append(task)
                    self.stats['failed_tasks'] += 1
            
            retry_tasks = new_retry_tasks
            
            # 如果还有需要重试的任务，等待一段时间再继续
            if retry_tasks:
                await asyncio.sleep(self.config.retry_delay)
        
        # 将剩余的失败任务也加入结果
        for task in retry_tasks:
            if task not in completed_tasks:
                completed_tasks.append(task)
                self.stats['failed_tasks'] += 1
        
        return completed_tasks
    
    async def process_knowledge_points_concurrent(
        self,
        knowledge_points_data: List[Tuple[str, Any]],  # (kp_id, kp_data)
        prompt_builder: Callable,
        progress_callback: Optional[Callable] = None,
        estimated_remaining_calls: int = None
    ) -> List[Tuple[str, Any, Optional[str], Optional[Exception]]]:
        """
        并发处理知识点
        
        Args:
            knowledge_points_data: 知识点数据列表，每个元素是(知识点ID, 知识点数据)
            prompt_builder: 提示词构建函数，接收知识点数据返回提示词
            progress_callback: 进度回调函数，接收(completed, total)
            estimated_remaining_calls: 估计的剩余API调用次数
            
        Returns:
            处理结果列表，每个元素是(知识点ID, 原始数据, 结果, 错误)
        """
        if not knowledge_points_data:
            return []
        
        # 重置统计信息
        self.stats = {
            'total_tasks': len(knowledge_points_data),
            'completed_tasks': 0,
            'failed_tasks': 0,
            'total_retries': 0,
            'total_processing_time': 0.0,
            'batches_processed': 0
        }
        
        self.logger.info(f"Starting concurrent processing of {len(knowledge_points_data)} knowledge points")
        
        # 创建任务
        tasks = [
            ProcessingTask(task_id=kp_id, data=kp_data)
            for kp_id, kp_data in knowledge_points_data
        ]
        
        # 计算最优批次
        batch_sizes = self.calculate_optimal_batches(
            len(tasks), estimated_remaining_calls
        )
        
        self.logger.info(f"Optimal batch strategy: {batch_sizes}")
        
        # 按批次处理
        all_results = []
        task_index = 0
        
        for batch_num, batch_size in enumerate(batch_sizes):
            batch_tasks = tasks[task_index:task_index + batch_size]
            task_index += batch_size
            
            self.logger.info(f"Processing batch {batch_num + 1}/{len(batch_sizes)} with {len(batch_tasks)} tasks")
            
            # 处理当前批次
            batch_start_time = time.time()
            batch_results = await self.process_with_retries(batch_tasks, prompt_builder)
            batch_time = time.time() - batch_start_time
            
            all_results.extend(batch_results)
            self.stats['batches_processed'] += 1
            self.stats['total_processing_time'] += batch_time
            
            # 调用进度回调
            if progress_callback:
                progress_callback(len(all_results), len(tasks))
            
            # 如果不是最后一个批次，等待一段时间避免速率限制
            if batch_num < len(batch_sizes) - 1:
                # 智能等待：如果批次处理很快，可能需要等待以避免速率限制
                if batch_time < 10:  # 如果批次在10秒内完成，等待一段时间
                    wait_time = max(0, 60 - batch_time)  # 确保每分钟不超过限制
                    if wait_time > 0:
                        self.logger.info(f"Waiting {wait_time:.1f}s before next batch to avoid rate limits")
                        await asyncio.sleep(wait_time)
        
        # 构建最终结果
        final_results = []
        for task in all_results:
            original_data = next(
                (data for kp_id, data in knowledge_points_data if kp_id == task.task_id),
                None
            )
            final_results.append((
                task.task_id,
                original_data,
                task.result,
                task.error
            ))
        
        # 记录统计信息
        self.logger.info(f"Processing completed. Stats: {self.stats}")
        
        return final_results
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        return self.stats.copy()

# 同步包装器函数
def run_concurrent_processing(
    knowledge_points_data: List[Tuple[str, Any]],
    prompt_builder: Callable,
    client,
    model: str,
    config: Optional[ConcurrentConfig] = None,
    progress_callback: Optional[Callable] = None,
    estimated_remaining_calls: int = None
) -> Tuple[List[Tuple[str, Any, Optional[str], Optional[Exception]]], Dict[str, Any]]:
    """
    并发处理的同步包装器函数
    
    Args:
        knowledge_points_data: 知识点数据列表
        prompt_builder: 提示词构建函数
        client: OpenAI客户端
        model: 模型名称
        config: 并发配置
        progress_callback: 进度回调
        estimated_remaining_calls: 估计的剩余API调用次数
        
    Returns:
        (处理结果列表, 统计信息字典)
    """
    processor = ConcurrentKnowledgeProcessor(client, model, config)
    
    # 运行异步处理
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        results = loop.run_until_complete(
            processor.process_knowledge_points_concurrent(
                knowledge_points_data,
                prompt_builder,
                progress_callback,
                estimated_remaining_calls
            )
        )
        stats = processor.get_processing_stats()
        return results, stats
    finally:
        loop.close()
