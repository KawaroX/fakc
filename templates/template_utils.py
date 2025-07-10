"""
模板工具函数模块
提供模板选择、合并、过滤等辅助功能
"""

import re
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from .concept_templates import ConceptTemplate, TemplateSection, TemplateRegistry

@dataclass
class TemplateSelectionResult:
    """模板选择结果"""
    primary_template: ConceptTemplate           # 主要模板
    secondary_templates: List[ConceptTemplate] = field(default_factory=list)  # 次要模板
    merged_sections: List[TemplateSection] = field(default_factory=list)      # 合并后的章节
    selection_reason: str = ""                  # 选择原因
    confidence_score: float = 1.0               # 选择置信度

class TemplateUtils:
    """模板工具类"""
    
    # 概念类型的权重配置（用于多类型选择）
    TYPE_WEIGHTS = {
        "定义性概念": 1.0,
        "构成要件": 1.2,
        "程序性知识": 1.1,
        "判断标准": 1.15,
        "法条规定": 1.25,
        "实务经验": 0.9
    }
    
    # 重要性级别对应的章节数量
    IMPORTANCE_SECTION_LIMITS = {
        "高": None,      # 无限制，包含所有章节
        "中": 5,         # 限制为5个主要章节
        "低": 3          # 限制为3个核心章节
    }
    
    @staticmethod
    def select_template_for_concept(concept_types: Union[str, List[str]], 
                                  importance_level: str = "中") -> TemplateSelectionResult:
        """
        为概念选择最合适的模板
        
        Args:
            concept_types: 概念类型，可以是单个字符串或列表
            importance_level: 重要性级别
            
        Returns:
            TemplateSelectionResult: 模板选择结果
        """
        # 统一处理为列表格式
        if isinstance(concept_types, str):
            type_list = [concept_types.strip()]
        else:
            type_list = [t.strip() for t in concept_types if t.strip()]
        
        # 如果没有有效类型，使用默认模板
        if not type_list:
            default_template = TemplateRegistry.get_default_template()
            return TemplateSelectionResult(
                primary_template=default_template,
                merged_sections=TemplateUtils._filter_sections_by_importance(
                    default_template.sections, importance_level
                ),
                selection_reason="未识别概念类型，使用默认模板",
                confidence_score=0.5
            )
        
        # 单一类型的情况
        if len(type_list) == 1:
            return TemplateUtils._select_single_template(type_list[0], importance_level)
        
        # 多类型的情况
        return TemplateUtils._select_multiple_templates(type_list, importance_level)
    
    @staticmethod
    def _select_single_template(concept_type: str, importance_level: str) -> TemplateSelectionResult:
        """选择单一类型的模板"""
        template = TemplateRegistry.get_template(concept_type)
        
        if template is None:
            # 使用默认模板
            default_template = TemplateRegistry.get_default_template()
            return TemplateSelectionResult(
                primary_template=default_template,
                merged_sections=TemplateUtils._filter_sections_by_importance(
                    default_template.sections, importance_level
                ),
                selection_reason=f"未找到'{concept_type}'对应模板，使用默认模板",
                confidence_score=0.6
            )
        
        filtered_sections = TemplateUtils._filter_sections_by_importance(
            template.sections, importance_level
        )
        
        return TemplateSelectionResult(
            primary_template=template,
            merged_sections=filtered_sections,
            selection_reason=f"匹配概念类型'{concept_type}'",
            confidence_score=1.0
        )
    
    @staticmethod
    def _select_multiple_templates(type_list: List[str], importance_level: str) -> TemplateSelectionResult:
        """选择多类型的模板并合并"""
        # 获取所有有效的模板
        valid_templates = []
        for concept_type in type_list:
            template = TemplateRegistry.get_template(concept_type)
            if template:
                weight = TemplateUtils.TYPE_WEIGHTS.get(concept_type, 1.0)
                valid_templates.append((template, weight, concept_type))
        
        # 如果没有有效模板，使用默认模板
        if not valid_templates:
            default_template = TemplateRegistry.get_default_template()
            return TemplateSelectionResult(
                primary_template=default_template,
                merged_sections=TemplateUtils._filter_sections_by_importance(
                    default_template.sections, importance_level
                ),
                selection_reason=f"所有类型'{type_list}'都未找到对应模板，使用默认模板",
                confidence_score=0.4
            )
        
        # 按权重排序，选择主要模板
        valid_templates.sort(key=lambda x: x[1], reverse=True)
        primary_template, primary_weight, primary_type = valid_templates[0]
        secondary_templates = [t[0] for t in valid_templates[1:]]
        
        # 合并章节
        merged_sections = TemplateUtils._merge_template_sections(
            [t[0] for t in valid_templates], importance_level
        )
        
        types_str = ", ".join([t[2] for t in valid_templates])
        confidence = min(1.0, 0.8 + (primary_weight - 1.0) * 0.2)
        
        return TemplateSelectionResult(
            primary_template=primary_template,
            secondary_templates=secondary_templates,
            merged_sections=merged_sections,
            selection_reason=f"多类型概念({types_str})，主要类型为'{primary_type}'",
            confidence_score=confidence
        )
    
    @staticmethod
    def _merge_template_sections(templates: List[ConceptTemplate], 
                               importance_level: str) -> List[TemplateSection]:
        """合并多个模板的章节"""
        # 收集所有章节，按标题分组
        section_groups = {}
        
        for template in templates:
            for section in template.sections:
                title = section.title
                if title not in section_groups:
                    section_groups[title] = []
                section_groups[title].append(section)
        
        # 合并相同标题的章节
        merged_sections = []
        for title, sections in section_groups.items():
            # 选择最高优先级的章节作为基础
            base_section = min(sections, key=lambda s: s.order)
            
            # 合并提取提示词
            extraction_prompts = []
            for section in sections:
                if section.extraction_prompt and section.extraction_prompt not in extraction_prompts:
                    extraction_prompts.append(section.extraction_prompt)
            
            merged_prompt = " ".join(extraction_prompts) if extraction_prompts else base_section.extraction_prompt
            
            # 如果任一章节是必需的，则合并后也是必需的
            is_required = any(section.required for section in sections)
            
            # 合并重要性级别
            importance_levels = []
            for section in sections:
                if section.importance_levels:
                    importance_levels.extend(section.importance_levels)
            unique_levels = list(set(importance_levels)) if importance_levels else None
            
            merged_section = TemplateSection(
                title=title,
                required=is_required,
                order=base_section.order,
                description=base_section.description,
                extraction_prompt=merged_prompt,
                default_content=base_section.default_content,
                importance_levels=unique_levels
            )
            
            merged_sections.append(merged_section)
        
        # 按order排序
        merged_sections.sort(key=lambda s: s.order)
        
        # 根据重要性级别过滤
        return TemplateUtils._filter_sections_by_importance(merged_sections, importance_level)
    
    @staticmethod
    def _filter_sections_by_importance(sections: List[TemplateSection], 
                                     importance_level: str) -> List[TemplateSection]:
        """根据重要性级别过滤章节"""
        # 获取章节数量限制
        limit = TemplateUtils.IMPORTANCE_SECTION_LIMITS.get(importance_level)
        
        # 过滤适用于当前重要性级别的章节
        applicable_sections = []
        for section in sections:
            if (section.importance_levels is None or 
                importance_level in section.importance_levels):
                applicable_sections.append(section)
        
        # 确保必需章节始终包含
        required_sections = [s for s in applicable_sections if s.required]
        optional_sections = [s for s in applicable_sections if not s.required]
        
        # 如果没有数量限制，返回所有适用章节
        if limit is None:
            return applicable_sections
        
        # 如果必需章节已经达到或超过限制，只返回必需章节
        if len(required_sections) >= limit:
            return required_sections[:limit]
        
        # 否则按优先级选择可选章节
        remaining_slots = limit - len(required_sections)
        selected_optional = optional_sections[:remaining_slots]
        
        final_sections = required_sections + selected_optional
        final_sections.sort(key=lambda s: s.order)
        
        return final_sections
    
    @staticmethod
    def generate_extraction_prompt(template_result: TemplateSelectionResult, 
                                 knowledge_point: Dict[str, Any], 
                                 segment_text: str) -> str:
        """生成AI信息提取提示词"""
        concept_name = knowledge_point.get('concept_name', '未命名概念')
        concept_types = knowledge_point.get('concept_type', '定义性概念')
        
        # 构建基础提示词
        base_prompt = f"""
你是专业的法考笔记整理专家。请从以下字幕内容中提取关于"{concept_name}"的相关信息。

概念信息：
- 概念名称：{concept_name}
- 概念类型：{concept_types}
- 重要性级别：{knowledge_point.get('importance_level', '中')}

字幕内容：
{segment_text}

请按照以下结构提取信息：
"""
        
        # 添加各个章节的提取要求
        section_prompts = []
        for i, section in enumerate(template_result.merged_sections, 1):
            required_mark = "【必需】" if section.required else "【可选】"
            section_prompt = f"""
{i}. {section.title} {required_mark}
   描述：{section.description}
   提取要求：{section.extraction_prompt}
"""
            section_prompts.append(section_prompt)
        
        sections_text = "".join(section_prompts)
        
        # 构建完整提示词
        full_prompt = f"""{base_prompt}
{sections_text}

提取要求：
1. 严格基于字幕内容进行提取，不要添加字幕中没有的信息
2. 保持老师的原始表述和重要细节
3. 如果某个章节在字幕中没有相关内容，可以标注"字幕中未涉及"
4. 提取的信息要准确、简洁、条理清晰
5. 保持法考笔记的专业性和实用性

请按照上述结构，为每个章节提取对应的信息。"""

        return full_prompt
    
    @staticmethod
    def generate_template_filled_note(template_result: TemplateSelectionResult,
                                    knowledge_point: Dict[str, Any],
                                    extracted_content: Dict[str, str],
                                    metadata: Dict[str, Any]) -> str:
        """根据模板和提取内容生成标准化笔记"""
        concept_name = knowledge_point.get('concept_name', '未命名概念')
        concept_id = knowledge_point.get('id', '')
        concept_types = knowledge_point.get('concept_type', '定义性概念')
        importance_level = knowledge_point.get('importance_level', '中')
        time_range = knowledge_point.get('time_range', '')
        
        # 处理概念类型（可能是列表）
        if isinstance(concept_types, list):
            concept_type_str = ", ".join(concept_types)
            primary_type = concept_types[0] if concept_types else "定义性概念"
        else:
            concept_type_str = concept_types
            primary_type = concept_types
        
        # 生成YAML头部
        yaml_header = f"""---
title: "【{metadata.get('subject', '')}】{concept_name}"
aliases: ["{concept_name}"]
tags: ["{metadata.get('subject', '')}", "{primary_type}", "{importance_level}"]
source: "{metadata.get('source', '')}"
course_url: "{metadata.get('course_url', '')}"
time_range: "{time_range}"
subject: "{metadata.get('subject', '')}"
exam_importance: "{importance_level}"
concept_id: "{concept_id}"
concept_types: "{concept_type_str}"
template_used: "{template_result.primary_template.type_name}"
created: "{metadata.get('created', '')}"
---"""
        
        # 生成笔记标题
        note_title = f"# 【{metadata.get('subject', '')}】{concept_name}"
        
        # 生成各个章节内容
        section_contents = []
        for section in template_result.merged_sections:
            section_title = f"## {section.title}"
            
            # 获取对应的提取内容
            content_key = section.title.replace(" ", "_").lower()
            section_content = extracted_content.get(content_key, 
                                                  extracted_content.get(section.title, ""))
            
            # 如果没有内容且有默认内容，使用默认内容
            if not section_content and section.default_content:
                section_content = section.default_content
            
            # 如果仍然没有内容，添加占位符
            if not section_content:
                if section.required:
                    section_content = "*此部分内容需要补充*"
                else:
                    continue  # 跳过可选的空章节
            
            section_contents.append(f"{section_title}\n\n{section_content}")
        
        # 生成相关概念链接（如果有relationships信息）
        relationships = knowledge_point.get('relationships', [])
        if relationships:
            related_concepts = []
            for rel in relationships:
                if isinstance(rel, dict):
                    related_name = rel.get('related_concept', '')
                    relation_type = rel.get('relation_type', '')
                    if related_name:
                        related_concepts.append(f"- [[{related_name}]] ({relation_type})")
                elif isinstance(rel, str):
                    related_concepts.append(f"- [[{rel}]]")
            
            if related_concepts:
                related_section = "## 相关概念\n\n" + "\n".join(related_concepts)
                section_contents.append(related_section)
        
        # 添加时间戳信息
        if time_range:
            timestamp_info = f"\n---\n*视频时间段：{time_range}*"
        else:
            timestamp_info = ""
        
        # 组合完整笔记
        full_note = f"""{yaml_header}

{note_title}

{chr(10).join(section_contents)}{timestamp_info}"""
        
        return full_note
    
    @staticmethod
    def validate_template_content(content: str) -> Tuple[bool, List[str]]:
        """验证模板生成的内容是否符合要求"""
        errors = []
        
        # 检查YAML头部
        if not content.startswith('---'):
            errors.append("缺少YAML头部")
        
        # 检查YAML结构
        yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not yaml_match:
            errors.append("YAML头部格式错误")
        
        # 检查必需字段
        required_fields = ['title', 'tags', 'concept_id']
        for field in required_fields:
            if f'{field}:' not in content:
                errors.append(f"缺少必需字段：{field}")
        
        # 检查章节结构
        section_count = len(re.findall(r'^## ', content, re.MULTILINE))
        if section_count == 0:
            errors.append("没有找到章节内容")
        
        # 检查内容完整性
        if len(content.strip()) < 200:
            errors.append("内容过于简短")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def extract_concept_types_from_text(text: str) -> List[str]:
        """从文本中智能识别可能的概念类型"""
        type_indicators = {
            "定义性概念": ["定义", "概念", "含义", "是指", "所谓"],
            "构成要件": ["构成", "要件", "条件", "要素", "必须"],
            "程序性知识": ["程序", "步骤", "流程", "如何", "怎样"],
            "判断标准": ["标准", "判断", "区分", "认定", "界定"],
            "法条规定": ["法条", "条文", "规定", "法律", "条例"],
            "实务经验": ["实务", "经验", "技巧", "方法", "操作"]
        }
        
        detected_types = []
        text_lower = text.lower()
        
        for concept_type, indicators in type_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text_lower)
            if score > 0:
                detected_types.append((concept_type, score))
        
        # 按得分排序，返回类型列表
        detected_types.sort(key=lambda x: x[1], reverse=True)
        return [t[0] for t in detected_types[:3]]  # 最多返回3个类型
