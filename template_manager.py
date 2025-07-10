"""
模板管理核心类
统一管理概念模板的选择、填充和生成流程
"""

import json
import re
import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict

from templates.concept_templates import ConceptTemplate, TemplateRegistry
from templates.template_utils import TemplateUtils, TemplateSelectionResult

@dataclass
class TemplateProcessingResult:
    """模板处理结果"""
    success: bool                               # 是否成功
    generated_note: Optional[str] = None        # 生成的笔记内容
    template_used: Optional[str] = None         # 使用的模板类型
    extraction_prompt: Optional[str] = None     # 生成的提取提示词
    processing_info: Dict[str, Any] = None      # 处理信息
    errors: List[str] = None                    # 错误信息
    
    def __post_init__(self):
        if self.processing_info is None:
            self.processing_info = {}
        if self.errors is None:
            self.errors = []

class TemplateManager:
    """模板管理器"""
    
    def __init__(self):
        """初始化模板管理器"""
        self.registry = TemplateRegistry
        self.utils = TemplateUtils
        self._processing_stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "template_usage": {},
            "error_types": {}
        }
    
    def process_knowledge_point(self, 
                               knowledge_point: Dict[str, Any],
                               segment_text: str,
                               metadata: Dict[str, Any],
                               ai_extraction_function: Optional[callable] = None) -> TemplateProcessingResult:
        """
        处理单个知识点，选择模板并生成笔记
        
        Args:
            knowledge_point: 知识点信息
            segment_text: 分段的字幕文本
            metadata: 元数据信息（课程信息等）
            ai_extraction_function: AI提取函数（可选）
            
        Returns:
            TemplateProcessingResult: 处理结果
        """
        try:
            self._processing_stats["total_processed"] += 1
            
            # 第一步：解析概念类型
            concept_types = self._parse_concept_types(knowledge_point)
            importance_level = knowledge_point.get('importance_level', '中')
            
            # 第二步：选择合适的模板
            template_result = self.utils.select_template_for_concept(
                concept_types, importance_level
            )
            
            # 记录模板使用统计
            template_name = template_result.primary_template.type_name
            self._processing_stats["template_usage"][template_name] = \
                self._processing_stats["template_usage"].get(template_name, 0) + 1
            
            # 第三步：生成信息提取提示词
            extraction_prompt = self.utils.generate_extraction_prompt(
                template_result, knowledge_point, segment_text
            )
            
            # 第四步：AI信息提取（如果提供了AI函数）
            extracted_content = {}
            if ai_extraction_function:
                try:
                    ai_response = ai_extraction_function(extraction_prompt)
                    extracted_content = self._parse_ai_extraction_response(
                        ai_response, template_result
                    )
                except Exception as e:
                    print(f"⚠️ AI提取失败: {str(e)}")
                    # 使用fallback方式
                    extracted_content = self._create_fallback_content(
                        knowledge_point, segment_text, template_result
                    )
            else:
                # 如果没有AI函数，创建基础内容
                extracted_content = self._create_basic_content(
                    knowledge_point, segment_text, template_result
                )
            
            # 第五步：生成标准化笔记
            generated_note = self.utils.generate_template_filled_note(
                template_result, knowledge_point, extracted_content, metadata
            )
            
            # 第六步：验证生成的内容
            is_valid, validation_errors = self.utils.validate_template_content(generated_note)
            
            if not is_valid:
                print(f"⚠️ 内容验证失败: {validation_errors}")
                # 尝试修复常见问题
                generated_note = self._fix_common_issues(generated_note, validation_errors)
            
            # 记录成功
            self._processing_stats["successful"] += 1
            
            # 返回处理结果
            return TemplateProcessingResult(
                success=True,
                generated_note=generated_note,
                template_used=template_name,
                extraction_prompt=extraction_prompt,
                processing_info={
                    "concept_types": concept_types,
                    "importance_level": importance_level,
                    "template_confidence": template_result.confidence_score,
                    "selection_reason": template_result.selection_reason,
                    "sections_count": len(template_result.merged_sections),
                    "ai_extraction_used": ai_extraction_function is not None,
                    "content_validation": is_valid,
                    "processing_time": datetime.datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            # 记录失败
            self._processing_stats["failed"] += 1
            error_type = type(e).__name__
            self._processing_stats["error_types"][error_type] = \
                self._processing_stats["error_types"].get(error_type, 0) + 1
            
            return TemplateProcessingResult(
                success=False,
                errors=[f"模板处理失败: {str(e)}"],
                processing_info={
                    "error_type": error_type,
                    "knowledge_point_id": knowledge_point.get('id', 'unknown'),
                    "processing_time": datetime.datetime.now().isoformat()
                }
            )
    
    def _parse_concept_types(self, knowledge_point: Dict[str, Any]) -> Union[str, List[str]]:
        """解析概念类型"""
        concept_type = knowledge_point.get('concept_type')
        
        if not concept_type:
            return "定义性概念"  # 默认类型
        
        # 如果是字符串，检查是否包含多个类型
        if isinstance(concept_type, str):
            # 检查常见的分隔符
            separators = [',', '，', ';', '；', '/', '|', '&', '和']
            for sep in separators:
                if sep in concept_type:
                    types = [t.strip() for t in concept_type.split(sep) if t.strip()]
                    return types if len(types) > 1 else concept_type
            return concept_type
        
        # 如果已经是列表
        elif isinstance(concept_type, list):
            return [str(t).strip() for t in concept_type if str(t).strip()]
        
        return "定义性概念"
    
    def _parse_ai_extraction_response(self, 
                                    ai_response: str, 
                                    template_result: TemplateSelectionResult) -> Dict[str, str]:
        """解析AI提取响应"""
        extracted_content = {}
        
        # 尝试按章节解析响应
        for section in template_result.merged_sections:
            section_title = section.title
            
            # 查找章节内容的各种模式
            patterns = [
                rf"{re.escape(section_title)}[：:]\s*(.*?)(?=\n\d+\.|$)",
                rf"\d+\.\s*{re.escape(section_title)}[：:]\s*(.*?)(?=\n\d+\.|$)",
                rf"##\s*{re.escape(section_title)}\s*(.*?)(?=\n##|$)",
                rf"【{re.escape(section_title)}】\s*(.*?)(?=\n【|$)"
            ]
            
            content = ""
            for pattern in patterns:
                match = re.search(pattern, ai_response, re.DOTALL | re.IGNORECASE)
                if match:
                    content = match.group(1).strip()
                    break
            
            # 如果没有找到，尝试使用关键词搜索
            if not content:
                keywords = self._get_section_keywords(section_title)
                for keyword in keywords:
                    pattern = rf"{re.escape(keyword)}[：:]\s*(.*?)(?=\n|$)"
                    match = re.search(pattern, ai_response, re.IGNORECASE)
                    if match:
                        content = match.group(1).strip()
                        break
            
            # 清理内容
            if content:
                content = self._clean_extracted_content(content)
            
            extracted_content[section_title] = content
        
        return extracted_content
    
    def _get_section_keywords(self, section_title: str) -> List[str]:
        """获取章节的关键词"""
        keyword_map = {
            "核心定义": ["定义", "含义", "概念"],
            "关键要素": ["要素", "特征", "组成"],
            "要件概述": ["要件", "概述", "总体"],
            "要件详解": ["详解", "具体要件", "分析"],
            "程序概述": ["程序", "概述", "流程"],
            "操作步骤": ["步骤", "流程", "过程"],
            "标准概述": ["标准", "概述", "原则"],
            "判断要素": ["判断", "要素", "标准"],
            "条文内容": ["条文", "法条", "规定"],
            "适用情形": ["适用", "情形", "范围"],
            "经验概述": ["经验", "概述", "总结"],
            "操作要点": ["要点", "技巧", "方法"],
            "典型案例": ["案例", "例子", "实例"],
            "注意事项": ["注意", "事项", "提醒"],
            "记忆要点": ["记忆", "要点", "口诀"]
        }
        
        return keyword_map.get(section_title, [section_title])
    
    def _clean_extracted_content(self, content: str) -> str:
        """清理提取的内容"""
        if not content:
            return ""
        
        # 移除多余的空行
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        # 移除开头的序号或标记
        content = re.sub(r'^[\d\.\-\*\+】】\s]*', '', content)
        
        # 移除末尾的多余字符
        content = content.rstrip('。，、；')
        
        return content.strip()
    
    def _create_fallback_content(self, 
                               knowledge_point: Dict[str, Any],
                               segment_text: str,
                               template_result: TemplateSelectionResult) -> Dict[str, str]:
        """创建fallback内容"""
        content = {}
        concept_name = knowledge_point.get('concept_name', '未命名概念')
        
        # 为每个章节创建基础内容
        for section in template_result.merged_sections:
            section_title = section.title
            
            if section_title == "核心定义":
                content[section_title] = f"{concept_name}的定义需要从课程内容中补充。"
            elif section_title == "记忆要点":
                content[section_title] = f"🔮 重要概念 — {concept_name}\n📱 实际应用 — 需要结合具体情况\n💡 注意事项 — 注意与相关概念的区别"
            else:
                content[section_title] = f"关于{section_title}的内容需要从课程内容中补充。"
        
        return content
    
    def _create_basic_content(self, 
                            knowledge_point: Dict[str, Any],
                            segment_text: str,
                            template_result: TemplateSelectionResult) -> Dict[str, str]:
        """创建基础内容（不使用AI）"""
        content = {}
        concept_name = knowledge_point.get('concept_name', '未命名概念')
        core_definition = knowledge_point.get('core_definition', '')
        
        # 为每个章节创建内容
        for section in template_result.merged_sections:
            section_title = section.title
            
            if section_title == "核心定义" and core_definition:
                content[section_title] = core_definition
            elif section_title == "记忆要点":
                importance = knowledge_point.get('importance_level', '中')
                content[section_title] = f"🔮 {importance}重要概念 — {concept_name}\n📱 应用场景 — 根据具体情况确定\n💡 重要提醒 — 注意准确理解和应用"
            else:
                # 尝试从字幕文本中提取相关内容
                relevant_text = self._extract_relevant_text(segment_text, section_title, concept_name)
                content[section_title] = relevant_text if relevant_text else f"*{section_title}内容待补充*"
        
        return content
    
    def _extract_relevant_text(self, text: str, section_title: str, concept_name: str) -> str:
        """从文本中提取相关内容"""
        if not text:
            return ""
        
        # 简单的关键词匹配
        keywords = self._get_section_keywords(section_title)
        
        sentences = re.split(r'[。！？]', text)
        relevant_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 检查是否包含概念名称
            if concept_name in sentence:
                relevant_sentences.append(sentence)
                continue
            
            # 检查是否包含关键词
            for keyword in keywords:
                if keyword in sentence:
                    relevant_sentences.append(sentence)
                    break
        
        if relevant_sentences:
            return "。".join(relevant_sentences[:3]) + "。"  # 最多3句
        
        return ""
    
    def _fix_common_issues(self, content: str, errors: List[str]) -> str:
        """修复常见问题"""
        fixed_content = content
        
        # 修复YAML头部问题
        if "缺少YAML头部" in errors:
            if not fixed_content.startswith('---'):
                fixed_content = '---\n' + fixed_content
        
        # 修复YAML结构问题
        if "YAML头部格式错误" in errors:
            lines = fixed_content.split('\n')
            yaml_end_index = -1
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    yaml_end_index = i
                    break
            
            if yaml_end_index == -1:
                # 在第一个非YAML行前添加结束标记
                for i, line in enumerate(lines[1:], 1):
                    if not line.startswith((' ', 'title:', 'aliases:', 'tags:', 'source:')):
                        lines.insert(i, '---')
                        break
                fixed_content = '\n'.join(lines)
        
        # 修复必需字段问题
        for error in errors:
            if error.startswith("缺少必需字段："):
                field = error.split("：")[1]
                if field == 'concept_id':
                    fixed_content = fixed_content.replace(
                        '---\n', f'---\nconcept_id: "auto_generated_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}"\n'
                    )
        
        return fixed_content
    
    def get_available_templates(self) -> Dict[str, ConceptTemplate]:
        """获取所有可用模板"""
        return self.registry.get_all_templates()
    
    def get_template_info(self, template_type: str) -> Optional[Dict[str, Any]]:
        """获取模板信息"""
        template = self.registry.get_template(template_type)
        if not template:
            return None
        
        return {
            "type_name": template.type_name,
            "display_name": template.display_name,
            "description": template.description,
            "sections": [
                {
                    "title": section.title,
                    "required": section.required,
                    "description": section.description,
                    "importance_levels": section.importance_levels
                }
                for section in template.sections
            ],
            "priority": template.priority,
            "compatible_types": template.compatible_types
        }
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        stats = self._processing_stats.copy()
        if stats["total_processed"] > 0:
            stats["success_rate"] = stats["successful"] / stats["total_processed"]
        else:
            stats["success_rate"] = 0.0
        
        return stats
    
    def reset_stats(self):
        """重置统计信息"""
        self._processing_stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "template_usage": {},
            "error_types": {}
        }
    
    def batch_process_knowledge_points(self,
                                     knowledge_points: List[Dict[str, Any]],
                                     segments: List[Any],  # Segment对象列表
                                     metadata: Dict[str, Any],
                                     ai_extraction_function: Optional[callable] = None,
                                     progress_callback: Optional[callable] = None) -> List[TemplateProcessingResult]:
        """
        批量处理知识点
        
        Args:
            knowledge_points: 知识点列表
            segments: 分段列表
            metadata: 元数据信息
            ai_extraction_function: AI提取函数
            progress_callback: 进度回调函数
            
        Returns:
            List[TemplateProcessingResult]: 处理结果列表
        """
        results = []
        
        # 创建知识点ID到分段的映射
        kp_to_segment = {}
        for segment in segments:
            for kp_id in segment.knowledge_points:
                kp_to_segment[kp_id] = segment
        
        total_count = len(knowledge_points)
        
        for i, kp in enumerate(knowledge_points):
            kp_id = kp.get('id', f'kp_{i}')
            
            # 找到对应的分段
            segment = kp_to_segment.get(kp_id)
            segment_text = segment.text if segment else ""
            
            # 处理知识点
            result = self.process_knowledge_point(
                kp, segment_text, metadata, ai_extraction_function
            )
            results.append(result)
            
            # 调用进度回调
            if progress_callback:
                progress_callback(i + 1, total_count, result.success)
        
        return results
