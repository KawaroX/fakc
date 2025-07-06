import os
import json
import math
import requests
from typing import List, Dict, Any, Optional, Tuple
from concept_manager import ConceptManager
from ai_processor import AIProcessor

class SiliconFlowConceptEnhancer:
    """基于SiliconFlow BGE-M3和reranker的智能概念增强器"""
    
    def __init__(self, api_key: str, ai_processor: AIProcessor, concept_manager: ConceptManager):
        self.api_key = api_key
        self.ai_processor = ai_processor
        self.concept_manager = concept_manager
        
        # API配置
        self.embedding_url = "https://api.siliconflow.cn/v1/embeddings"
        self.rerank_url = "https://api.siliconflow.cn/v1/rerank"
        self.embedding_model = "BAAI/bge-m3"
        self.rerank_model = "BAAI/bge-reranker-v2-m3"
        
        # 缓存文件
        self.embeddings_cache_file = os.path.join(
            concept_manager.vault_path, 
            "概念嵌入缓存_BGE.json"
        )
        self.embeddings_cache = {}
        self.load_embeddings_cache()
    
    def load_embeddings_cache(self) -> None:
        """加载嵌入向量缓存"""
        try:
            if os.path.exists(self.embeddings_cache_file):
                with open(self.embeddings_cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.embeddings_cache = data.get('embeddings', {})
                print(f"📖 已加载 {len(self.embeddings_cache)} 个概念的BGE嵌入向量")
        except Exception as e:
            print(f"⚠️ 加载嵌入缓存失败: {e}")
            self.embeddings_cache = {}
    
    def save_embeddings_cache(self) -> None:
        """保存嵌入向量缓存"""
        try:
            cache_data = {
                'metadata': {
                    'total_embeddings': len(self.embeddings_cache),
                    'model': self.embedding_model,
                    'last_updated': self._get_current_timestamp()
                },
                'embeddings': self.embeddings_cache
            }
            
            with open(self.embeddings_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 已保存 {len(self.embeddings_cache)} 个BGE嵌入向量")
        except Exception as e:
            print(f"❌ 保存嵌入缓存失败: {e}")
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """获取文本的BGE嵌入向量"""
        # 检查缓存
        if text in self.embeddings_cache:
            return self.embeddings_cache[text]
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "model": self.embedding_model,
                "input": text,
                "encoding_format": "float"
            }
            
            response = requests.post(self.embedding_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            embedding = result['data'][0]['embedding']
            
            # 缓存结果
            self.embeddings_cache[text] = embedding
            return embedding
            
        except Exception as e:
            print(f"❌ 获取BGE嵌入向量失败: {e}")
            return None
    
    def batch_get_embeddings(self, texts: List[str]) -> Dict[str, List[float]]:
        """批量获取嵌入向量（更高效）"""
        results = {}
        texts_to_process = []
        
        # 检查缓存，收集需要处理的文本
        for text in texts:
            if text in self.embeddings_cache:
                results[text] = self.embeddings_cache[text]
            else:
                texts_to_process.append(text)
        
        if not texts_to_process:
            return results
        
        # 批量处理（BGE-M3支持批量输入）
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # 分批处理，避免单次请求过大
            batch_size = 10  # 每次处理10个
            
            for i in range(0, len(texts_to_process), batch_size):
                batch_texts = texts_to_process[i:i + batch_size]
                
                data = {
                    "model": self.embedding_model,
                    "input": batch_texts,
                    "encoding_format": "float"
                }
                
                response = requests.post(self.embedding_url, headers=headers, json=data)
                response.raise_for_status()
                
                result = response.json()
                
                # 处理批量结果
                for j, embedding_data in enumerate(result['data']):
                    text = batch_texts[j]
                    embedding = embedding_data['embedding']
                    
                    # 缓存和返回结果
                    self.embeddings_cache[text] = embedding
                    results[text] = embedding
                
                print(f"  📊 已处理 {min(i + batch_size, len(texts_to_process))}/{len(texts_to_process)} 个概念")
            
        except Exception as e:
            print(f"❌ 批量获取嵌入向量失败: {e}")
        
        return results
    
    def rerank_concepts(self, query: str, concept_docs: List[str], top_k: int = 20) -> List[Tuple[int, float]]:
        """使用BGE reranker对概念进行重排序"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "model": self.rerank_model,
                "query": query,
                "documents": concept_docs,
                "return_documents": False
            }
            
            response = requests.post(self.rerank_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            
            # 检查响应格式 - SiliconFlow使用'results'而不是'data'
            if 'results' not in result:
                print(f"    ❌ API响应中缺少'results'字段: {list(result.keys())}")
                return []
            
            # 提取排序结果
            ranked_results = []
            for item in result['results']:
                if 'index' not in item or 'relevance_score' not in item:
                    print(f"    ⚠️ 排序项缺少必要字段: {item}")
                    continue
                    
                index = item['index']
                score = item['relevance_score']  # SiliconFlow使用relevance_score
                
                # SiliconFlow的分数已经是0-1范围，不需要sigmoid转换
                ranked_results.append((index, score))
            
            # 按分数排序并返回top_k
            ranked_results.sort(key=lambda x: x[1], reverse=True)
            
            print(f"    📊 重排序得分分布: 最高{ranked_results[0][1]:.3f}, 最低{ranked_results[-1][1]:.3f}")
            
            return ranked_results[:top_k]
            
        except requests.exceptions.HTTPError as e:
            print(f"❌ BGE重排序HTTP错误: {e}")
            print(f"    响应状态码: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"    错误详情: {error_detail}")
            except:
                print(f"    响应内容: {response.text}")
            return []
        except requests.exceptions.RequestException as e:
            print(f"❌ BGE重排序请求失败: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ BGE重排序响应解析失败: {e}")
            print(f"    响应内容: {response.text}")
            return []
        except Exception as e:
            print(f"❌ BGE重排序未知错误: {e}")
            return []
    
    def build_concept_embeddings(self, force_rebuild: bool = False) -> None:
        """为所有概念构建BGE嵌入向量"""
        print("🔄 构建概念BGE嵌入向量...")
        
        if not self.concept_manager.concept_database:
            print("❌ 概念数据库为空，请先扫描笔记")
            return
        
        concepts_to_process = []
        
        for concept_name, concept_data in self.concept_manager.concept_database.items():
            if force_rebuild or concept_name not in self.embeddings_cache:
                concepts_to_process.append((concept_name, concept_data))
        
        if not concepts_to_process:
            print("✅ 所有概念的BGE嵌入向量已存在")
            return
        
        print(f"📝 需要处理 {len(concepts_to_process)} 个概念")
        
        # 准备批量文本
        concept_texts = []
        concept_names = []
        
        for concept_name, concept_data in concepts_to_process:
            concept_text = self._build_concept_description(concept_name, concept_data)
            concept_texts.append(concept_text)
            concept_names.append(concept_name)
        
        # 批量获取嵌入向量
        print("🚀 批量获取BGE嵌入向量...")
        embeddings = self.batch_get_embeddings(concept_texts)
        
        # 映射回概念名称
        for i, concept_name in enumerate(concept_names):
            concept_text = concept_texts[i]
            if concept_text in embeddings:
                self.embeddings_cache[concept_name] = embeddings[concept_text]
        
        # 保存缓存
        self.save_embeddings_cache()
        print("✅ 概念BGE嵌入向量构建完成")
    
    def _build_concept_description(self, concept_name: str, concept_data: Dict) -> str:
        """构建概念的描述文本用于嵌入"""
        parts = [concept_name]
        
        # 添加别名
        if concept_data.get('aliases'):
            parts.extend(concept_data['aliases'])
        
        # 添加科目信息
        if concept_data.get('subject'):
            parts.append(f"法考{concept_data['subject']}")
        
        # 添加标签
        if concept_data.get('tags'):
            parts.extend([tag for tag in concept_data['tags'] if tag])
        
        # 添加相关概念（有限数量）
        if concept_data.get('related_concepts'):
            parts.extend(concept_data['related_concepts'][:3])  # 只取前3个
        
        return ' '.join(parts)
    
    def find_related_concepts_hybrid(
        self, 
        note_content: str, 
        note_title: str,
        embedding_top_k: int = 100,
        rerank_top_k: int = 15,
        rerank_threshold: float = 0.98  # 调整默认阈值适应BGE特性
    ) -> List[Tuple[str, float]]:
        """
        混合检索：先用BGE embedding召回，再用reranker精排
        
        Args:
            note_content: 笔记内容
            note_title: 笔记标题
            embedding_top_k: embedding召回的数量
            rerank_top_k: reranker精排后返回的数量
            rerank_threshold: reranker分数阈值
            
        Returns:
            (概念名, reranker分数) 的列表
        """
        # 1. 构建查询文本
        query_text = f"{note_title} {note_content}"
        
        # 2. BGE embedding召回阶段
        print(f"🔍 BGE embedding召回 top-{embedding_top_k}...")
        
        query_embedding = self.get_embedding(query_text)
        if query_embedding is None:
            return []
        
        # 计算与所有概念的余弦相似度
        similarities = []
        for concept_name in self.concept_manager.concept_database.keys():
            if concept_name == note_title:  # 跳过自己
                continue
                
            if concept_name not in self.embeddings_cache:
                continue
            
            concept_embedding = self.embeddings_cache[concept_name]
            similarity = self._cosine_similarity(query_embedding, concept_embedding)
            similarities.append((concept_name, similarity))
        
        # 按相似度排序并取top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_concepts = similarities[:embedding_top_k]
        
        print(f"  📊 召回 {len(top_concepts)} 个候选概念")
        
        if not top_concepts:
            return []
        
        # 3. BGE reranker精排阶段
        print(f"🎯 BGE reranker精排 top-{rerank_top_k}...")
        
        # 准备reranker输入
        concept_names = [concept for concept, _ in top_concepts]
        concept_docs = []
        
        for concept_name in concept_names:
            concept_data = self.concept_manager.concept_database.get(concept_name, {})
            concept_doc = self._build_concept_description(concept_name, concept_data)
            concept_docs.append(concept_doc)
        
        # 调用reranker
        rerank_results = self.rerank_concepts(query_text, concept_docs, rerank_top_k)
        
        # 映射回概念名称并过滤
        final_results = []
        for doc_index, rerank_score in rerank_results:
            if rerank_score >= rerank_threshold:
                concept_name = concept_names[doc_index]
                final_results.append((concept_name, rerank_score))
        
        # 如果阈值过高导致结果太少，动态调整
        if len(final_results) < 3 and rerank_results:
            # 取前5个最高分的，不管阈值
            print(f"    🔄 阈值{rerank_threshold}过高，动态调整为前5个最高分概念")
            final_results = []
            for doc_index, rerank_score in rerank_results[:5]:
                concept_name = concept_names[doc_index]
                final_results.append((concept_name, rerank_score))
        
        print(f"  ✨ 精排后保留 {len(final_results)} 个高质量概念")
        
        # 显示top 5结果
        for i, (concept, score) in enumerate(final_results[:5]):
            print(f"    {i+1}. {concept}: {score:.4f}")  # 提高精度显示
        
        return final_results
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算两个向量的余弦相似度"""
        try:
            import numpy as np
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
        except Exception:
            return 0.0
    
    def enhance_note_with_hybrid_search(
        self, 
        note_content: str, 
        note_title: str,
        embedding_top_k: int = 100,
        rerank_top_k: int = 15,
        rerank_threshold: float = 0.98  # 调整默认阈值
    ) -> Optional[Dict]:
        """
        使用混合检索增强单个笔记的概念关系
        """
        print(f"🔍 混合检索查找相关概念...")
        
        # 1. 混合检索找到最相关的概念
        related_concepts = self.find_related_concepts_hybrid(
            note_content, note_title, embedding_top_k, rerank_top_k, rerank_threshold
        )
        
        if not related_concepts:
            print(f"  ⚠️ 未找到重排序分数高于 {rerank_threshold} 的相关概念")
            return {'modified': False}
        
        # 2. 构建精简的概念列表给AI
        filtered_concepts = {
            'existing_concepts': [concept for concept, _ in related_concepts],
            'concept_aliases': {},
            'concept_relationships': {},
            'rerank_scores': {concept: score for concept, score in related_concepts}
        }
        
        # 添加概念的详细信息
        for concept_name, _ in related_concepts:
            if concept_name in self.concept_manager.concept_database:
                data = self.concept_manager.concept_database[concept_name]
                filtered_concepts['concept_aliases'][concept_name] = data.get('aliases', [])
                filtered_concepts['concept_relationships'][concept_name] = data.get('related_concepts', [])
        
        # 3. 调用AI进行精确分析
        print(f"🤖 AI分析最相关的 {len(related_concepts)} 个概念...")
        
        enhanced_prompt = self._build_hybrid_enhanced_prompt(
            note_content, note_title, filtered_concepts
        )
        
        try:
            response = self.ai_processor.client.chat.completions.create(
                model=self.ai_processor.model,
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0,
            )
            
            result = self.ai_processor._parse_single_note_enhancement_response(
                response.choices[0].message.content, 
                note_content
            )
            
            if result and result.get('modified'):
                print(f"  ✅ AI建议修改")
            else:
                print(f"  ⚠️ AI认为无需修改")
            
            return result
            
        except Exception as e:
            print(f"❌ AI增强失败: {e}")
            return {'modified': False}
    
    def _build_hybrid_enhanced_prompt(
        self, 
        note_content: str, 
        note_title: str, 
        filtered_concepts: Dict
    ) -> str:
        """构建基于混合检索的增强提示词"""
        
        concepts_info = []
        for concept in filtered_concepts['existing_concepts']:
            aliases = filtered_concepts['concept_aliases'].get(concept, [])
            score = filtered_concepts['rerank_scores'].get(concept, 0.0)
            
            info = f"- {concept} (相关度: {score:.3f})"
            if aliases:
                info += f" [别名: {', '.join(aliases[:2])}]"
            concepts_info.append(info)
        
        concepts_list = '\n'.join(concepts_info)
        
        return f"""
(defun 法考概念链接专家 ()
  "基于概念库优化法考笔记概念关系"
  (身份 . 法考知识体系专家)
  (专长 . (概念关系分析 知识图谱构建 语义相关性判断))
  (工具箱 . (概念库匹配 双链语法规范 关联性分析))
  (质量标准 . (高度相关性 严格把控 概念库准确性))
  (链接格式 . "[[【科目】概念名|概念名/别名]]"))

(defun 概念关系分析器 (笔记标题 笔记内容 概念库)
  "分析笔记与概念库的关联性，优化概念链接"
  (let* ((内容解析 (语义分析 笔记内容))
         (现有链接检查 (验证现有链接 笔记内容 概念库))
         (遗漏概念识别 (发现相关概念 内容解析 概念库))
         (关系分类 (概念分类器 遗漏概念识别))
         (链接优化 (双链格式化 关系分类 现有链接检查)))
    (静默输出 链接优化)))

(defun 验证现有链接 (笔记内容 概念库)
  "检查笔记中现有的[[概念]]链接是否准确"
  (let ((现有链接 (提取现有链接 笔记内容)))
    (filter (lambda (链接)
              (概念库中存在? 链接 概念库))
            现有链接)))

(defun 发现相关概念 (笔记语义 概念库)
  "识别笔记中可能遗漏的重要概念关联"
  (filter (lambda (概念)
            (and (概念库中存在? 概念 概念库)
                 (or (直接提及? 概念 笔记语义)
                     (语义相关? 概念 笔记语义)
                     (上下级关系? 概念 笔记语义)
                     (并列关系? 概念 笔记语义))))
          概念库))

(defun 概念分类器 (相关概念)
  "按照关系类型对概念进行分类"
  (let ((分类结果 '()))
    (dolist (概念 相关概念)
      (cond ((核心相关? 概念) (push 概念 (getf 分类结果 :核心)))
            ((构成要件相关? 概念) (push 概念 (getf 分类结果 :要件)))
            ((承担方式相关? 概念) (push 概念 (getf 分类结果 :方式)))
            ((对比概念? 概念) (push 概念 (getf 分类结果 :对比)))))
    分类结果))

(defun 静默输出 (优化结果)
  "静默执行，仅输出标准格式结果，禁止任何代码块包裹"
  (cond ((需要修改? 优化结果)
         (format nil "MODIFIED: true~%ENHANCED_CONTENT:~%~a" 
                 (直接输出文字内容 优化结果)))
        (t "MODIFIED: false")))

(defun 直接输出文字内容 (优化结果)
  "直接输出纯文本内容，不使用任何markdown代码块包裹"
  (生成完整内容 优化结果))

(defun 静默执行模式 ()
  "设置静默执行约束"
  '((禁止解释 . t)
    (禁止分析过程输出 . t) 
    (禁止额外说明 . t)
    (仅输出结果 . t)
    (严格格式控制 . t)
    (禁止代码块包裹 . t)))

(defun 质量控制规则 ()
  "确保输出质量的规则集"
  '((概念库存在性 . "只添加确实存在于概念库中的概念链接")
    (高度相关性 . "确保新增的概念链接与笔记内容高度相关")
    (现有链接验证 . "检查笔记中现有的[[概念]]链接是否准确")
    (格式标准 . "严格使用双链显示别名格式")
    (移除无关 . "移除指向不存在概念的链接")))

(defun start ()
  "启动静默执行模式"
  (setq system-role 法考概念链接专家)
  (setq execution-mode (静默执行模式))
  (setq quality-rules (质量控制规则))
  (setq output-only t))

;; 执行约束
;; 1. 必须启动静默执行模式
;; 2. 禁止输出任何分析过程、解释或说明
;; 3. 禁止输出思考过程或中间结果
;; 4. 严格输出格式：仅 "MODIFIED: true/false" 和对应内容
;; 5. 任何非标准格式的输出都是错误的
;; 6. 不得添加引言、总结、解释或其他文字
;; 7. 禁止使用```代码块包裹输出内容

;; ========== Python脚本模板接口 ==========

请分析以下笔记，检查并优化其概念关系链接：

**笔记标题：**{note_title}

**笔记内容：**
{note_content}

**现有概念库：**
{concepts_list}

执行分析任务：(概念关系分析器 "{note_title}" 笔记内容 概念库)"""
    
    def batch_enhance_with_hybrid_search(
        self, 
        notes: List[Dict[str, Any]],
        rebuild_embeddings: bool = False,
        embedding_top_k: int = 100,
        rerank_top_k: int = 15,
        rerank_threshold: float = 0.98  # 调整默认阈值
    ) -> Dict[str, int]:
        """
        使用混合检索批量增强笔记
        """
        print("🚀 启动基于BGE混合检索的笔记增强...")
        
        # 1. 确保嵌入向量已构建
        self.build_concept_embeddings(force_rebuild=rebuild_embeddings)
        
        # 2. 批量处理笔记
        stats = {
            'total': len(notes),
            'enhanced': 0,
            'unchanged': 0,
            'failed': 0
        }
        
        for i, note_info in enumerate(notes, 1):
            print(f"\n🔄 处理 {i}/{len(notes)}: {note_info['title']}")
            
            try:
                result = self.enhance_note_with_hybrid_search(
                    note_info['content'], 
                    note_info['title'],
                    embedding_top_k,
                    rerank_top_k,
                    rerank_threshold
                )
                
                if result and result.get('modified'):
                    # 应用修改
                    if self._apply_enhancement(note_info, result):
                        stats['enhanced'] += 1
                        print(f"  ✅ 增强成功")
                    else:
                        stats['failed'] += 1
                        print(f"  ❌ 应用修改失败")
                else:
                    stats['unchanged'] += 1
                    print(f"  ⚠️ 无需修改")
                    
            except Exception as e:
                stats['failed'] += 1
                print(f"  ❌ 处理失败: {e}")
        
        # 输出统计结果
        print(f"\n🎉 基于BGE混合检索的批量增强完成！")
        print(f"  📊 总计: {stats['total']} 个笔记")
        print(f"  ✅ 成功增强: {stats['enhanced']} 个")
        print(f"  ⚠️ 无需修改: {stats['unchanged']} 个")
        print(f"  ❌ 处理失败: {stats['failed']} 个")
        
        return stats
    
    def _apply_enhancement(self, note_info: Dict[str, Any], result: Dict) -> bool:
        """应用增强结果到文件"""
        try:
            # 备份原文件
            backup_path = note_info['file_path'] + '.backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(note_info['content'])
            
            # 写入增强后的内容
            with open(note_info['file_path'], 'w', encoding='utf-8') as f:
                f.write(result['enhanced_content'])
            
            # 删除备份文件
            os.remove(backup_path)
            return True
            
        except Exception as e:
            print(f"❌ 应用增强失败: {e}")
            return False
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳字符串"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


# config.py 中需要添加SiliconFlow配置
class Config:
    # 现有配置...
    
    # SiliconFlow API配置
    SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "your_siliconflow_api_key")


# 主程序集成代码片段
def integrate_siliconflow_enhancer():
    """集成SiliconFlow增强器到主程序的示例代码"""
    
    # 在 main.py 的 LawExamNoteProcessor 类中修改：
    
    def __init__(self):
        # ... 现有初始化代码 ...
        
        # 添加SiliconFlow增强器
        self.siliconflow_enhancer = None  # 延迟初始化
    
    def _get_siliconflow_enhancer(self):
        """获取SiliconFlow增强器实例（延迟初始化）"""
        if self.siliconflow_enhancer is None:
            from siliconflow_concept_enhancer import SiliconFlowConceptEnhancer
            self.siliconflow_enhancer = SiliconFlowConceptEnhancer(
                Config.SILICONFLOW_API_KEY,
                self.ai_processor, 
                self.concept_manager
            )
        return self.siliconflow_enhancer
    
    def _enhance_with_hybrid_search(self):
        """使用BGE混合检索增强笔记"""
        print("\n🔖 BGE混合检索模式（embedding召回+reranker精排）")
        
        enhancer = self._get_siliconflow_enhancer()
        
        print("参数配置:")
        print("1. 使用默认参数（召回100个，精排15个，阈值0.3）")
        print("2. 自定义参数")
        print("3. 返回")
        
        config_choice = input("请选择 (1-3): ").strip()
        
        if config_choice == '2':
            try:
                embedding_top_k = int(input("embedding召回数量 (建议50-200): ") or "100")
                rerank_top_k = int(input("reranker精排数量 (建议10-20): ") or "15")
                rerank_threshold = float(input("reranker分数阈值 (建议0.2-0.5): ") or "0.3")
            except ValueError:
                print("❌ 参数格式错误，使用默认值")
                embedding_top_k, rerank_top_k, rerank_threshold = 100, 15, 0.3
        elif config_choice == '1':
            embedding_top_k, rerank_top_k, rerank_threshold = 100, 15, 0.3
        else:
            return
        
        print("1. 增强所有科目的笔记")
        print("2. 增强特定科目的笔记")
        print("3. 返回")
        
        choice = input("请选择操作 (1-3): ").strip()
        
        if choice == '1':
            notes = self._collect_all_law_notes()
            if notes:
                enhancer.batch_enhance_with_hybrid_search(
                    notes, False, embedding_top_k, rerank_top_k, rerank_threshold
                )
        elif choice == '2':
            subject = self._select_subject()
            if subject:
                notes = self._collect_subject_notes_by_name(subject)
                if notes:
                    enhancer.batch_enhance_with_hybrid_search(
                        notes, False, embedding_top_k, rerank_top_k, rerank_threshold
                    )
        
        # 重新扫描更新概念数据库
        if choice in ['1', '2']:
            print(f"\n📚 重新扫描更新概念数据库...")
            self.concept_manager.scan_existing_notes()