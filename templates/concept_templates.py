"""
概念模板定义模块
定义各类法考概念的标准模板结构和内容要求
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class ImportanceLevel(Enum):
    """重要性级别枚举"""
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"

class ConceptType(Enum):
    """概念类型枚举"""
    DEFINITION = "定义性概念"
    ELEMENTS = "构成要件"
    PROCEDURE = "程序性知识"
    STANDARDS = "判断标准"
    REGULATIONS = "法条规定"
    PRACTICE = "实务经验"

@dataclass
class TemplateSection:
    """模板章节定义"""
    title: str                      # 章节标题
    required: bool                  # 是否必需
    order: int                      # 显示顺序
    description: str                # 章节描述
    extraction_prompt: str          # AI提取提示词
    default_content: Optional[str] = None  # 默认内容
    importance_levels: List[str] = None    # 适用的重要性级别

@dataclass
class ConceptTemplate:
    """概念模板完整定义"""
    type_name: str                  # 模板类型名称
    display_name: str               # 显示名称
    description: str                # 模板描述
    sections: List[TemplateSection] # 章节列表
    priority: int                   # 模板优先级（多类型时使用）
    compatible_types: List[str] = None  # 兼容的其他类型

class ConceptTemplates:
    """概念模板集合类"""
    
    @staticmethod
    def get_definition_template() -> ConceptTemplate:
        """定义性概念模板"""
        sections = [
            TemplateSection(
                title="核心定义",
                required=True,
                order=1,
                description="概念的基本定义和内涵",
                extraction_prompt="请提取这个概念的核心定义，包括法律条文定义、学理定义或权威解释。注意保留原文表述的准确性。",
                importance_levels=["高", "中", "低"]
            ),
            TemplateSection(
                title="关键要素",
                required=True,
                order=2,
                description="构成概念的核心要素",
                extraction_prompt="请提取构成这个概念的关键要素或特征，如果有明确的构成要件请逐一列出。",
                importance_levels=["高", "中"]
            ),
            TemplateSection(
                title="适用条件",
                required=False,
                order=3,
                description="概念适用的前提条件",
                extraction_prompt="请提取这个概念适用的前提条件、适用范围或限制条件。",
                importance_levels=["高", "中"]
            ),
            TemplateSection(
                title="典型案例",
                required=False,
                order=4,
                description="典型案例和实际应用",
                extraction_prompt="请提取老师提到的典型案例、实际例子或应用场景，保留具体细节。",
                importance_levels=["高", "中", "低"]
            ),
            TemplateSection(
                title="易混概念",
                required=False,
                order=5,
                description="容易混淆的相似概念",
                extraction_prompt="请提取与此概念容易混淆的其他概念，以及它们之间的区别要点。",
                importance_levels=["高", "中"]
            ),
            TemplateSection(
                title="记忆要点",
                required=True,
                order=6,
                description="关键记忆点和应用场景",
                extraction_prompt="请总结这个概念的关键记忆点、口诀、应用场景和重要提醒。",
                importance_levels=["高", "中", "低"]
            )
        ]
        
        return ConceptTemplate(
            type_name="定义性概念",
            display_name="定义性概念",
            description="适用于基本概念、法律术语、理论定义等",
            sections=sections,
            priority=1,
            compatible_types=["法条规定", "判断标准"]
        )
    
    @staticmethod
    def get_elements_template() -> ConceptTemplate:
        """构成要件模板"""
        sections = [
            TemplateSection(
                title="要件概述",
                required=True,
                order=1,
                description="构成要件的总体说明",
                extraction_prompt="请提取这个构成要件的总体概述，包括其在整个法律关系中的地位和作用。",
                importance_levels=["高", "中", "低"]
            ),
            TemplateSection(
                title="要件详解",
                required=True,
                order=2,
                description="各个具体要件的详细说明",
                extraction_prompt="请逐一提取各个具体要件的内容，包括主观要件、客观要件等，保持条理清晰。",
                importance_levels=["高", "中"]
            ),
            TemplateSection(
                title="举证责任",
                required=False,
                order=3,
                description="各要件的举证责任分配",
                extraction_prompt="请提取各个要件的举证责任分配，谁主张谁举证的具体要求。",
                importance_levels=["高", "中"]
            ),
            TemplateSection(
                title="实务要点",
                required=False,
                order=4,
                description="实务中的注意事项",
                extraction_prompt="请提取实务操作中的注意事项、常见问题和处理技巧。",
                importance_levels=["高", "中"]
            ),
            TemplateSection(
                title="典型争议",
                required=False,
                order=5,
                description="常见争议问题",
                extraction_prompt="请提取围绕这些要件的典型争议问题和解决方案。",
                importance_levels=["高", "中"]
            ),
            TemplateSection(
                title="记忆要点",
                required=True,
                order=6,
                description="关键记忆点和口诀",
                extraction_prompt="请总结要件记忆的关键点、口诀和实用技巧。",
                importance_levels=["高", "中", "低"]
            )
        ]
        
        return ConceptTemplate(
            type_name="构成要件",
            display_name="构成要件",
            description="适用于犯罪构成、合同要件、诉讼条件等",
            sections=sections,
            priority=2,
            compatible_types=["程序性知识", "判断标准"]
        )
    
    @staticmethod
    def get_procedure_template() -> ConceptTemplate:
        """程序性知识模板"""
        sections = [
            TemplateSection(
                title="程序概述",
                required=True,
                order=1,
                description="程序的整体框架和目的",
                extraction_prompt="请提取这个程序的整体框架、适用场景和主要目的。",
                importance_levels=["高", "中", "低"]
            ),
            TemplateSection(
                title="操作步骤",
                required=True,
                order=2,
                description="具体的操作流程和步骤",
                extraction_prompt="请按顺序提取具体的操作流程，包括每个步骤的具体要求和时间限制。",
                importance_levels=["高", "中"]
            ),
            TemplateSection(
                title="时间要求",
                required=False,
                order=3,
                description="各阶段的时间限制",
                extraction_prompt="请提取各个阶段的时间要求、期限规定和时效要求。",
                importance_levels=["高", "中"]
            ),
            TemplateSection(
                title="注意事项",
                required=False,
                order=4,
                description="操作中的注意事项",
                extraction_prompt="请提取操作过程中的注意事项、禁止性规定和风险提示。",
                importance_levels=["高", "中"]
            ),
            TemplateSection(
                title="常见错误",
                required=False,
                order=5,
                description="容易出现的错误",
                extraction_prompt="请提取实务中容易出现的错误、失误点和避免方法。",
                importance_levels=["高", "中"]
            ),
            TemplateSection(
                title="记忆要点",
                required=True,
                order=6,
                description="程序记忆的关键点",
                extraction_prompt="请总结程序记忆的关键点、操作技巧和实用提醒。",
                importance_levels=["高", "中", "低"]
            )
        ]
        
        return ConceptTemplate(
            type_name="程序性知识",
            display_name="程序性知识",
            description="适用于诉讼程序、执行程序、办案流程等",
            sections=sections,
            priority=3,
            compatible_types=["构成要件", "实务经验"]
        )
    
    @staticmethod
    def get_standards_template() -> ConceptTemplate:
        """判断标准模板"""
        sections = [
            TemplateSection(
                title="标准概述",
                required=True,
                order=1,
                description="判断标准的基本内容",
                extraction_prompt="请提取这个判断标准的基本内容、适用范围和判断目的。",
                importance_levels=["高", "中", "低"]
            ),
            TemplateSection(
                title="判断要素",
                required=True,
                order=2,
                description="具体的判断要素和标准",
                extraction_prompt="请提取具体的判断要素、判断标准和考量因素。",
                importance_levels=["高", "中"]
            ),
            TemplateSection(
                title="适用情形",
                required=False,
                order=3,
                description="标准的具体适用情形",
                extraction_prompt="请提取这个标准的具体适用情形、适用条件和适用范围。",
                importance_levels=["高", "中"]
            ),
            TemplateSection(
                title="例外情况",
                required=False,
                order=4,
                description="不适用的例外情况",
                extraction_prompt="请提取标准不适用的例外情况、特殊规定和限制条件。",
                importance_levels=["高", "中"]
            ),
            TemplateSection(
                title="实务案例",
                required=False,
                order=5,
                description="实际应用案例",
                extraction_prompt="请提取运用这个标准的实际案例、司法实践和具体应用。",
                importance_levels=["高", "中"]
            ),
            TemplateSection(
                title="记忆要点",
                required=True,
                order=6,
                description="判断要点和记忆技巧",
                extraction_prompt="请总结判断要点、记忆技巧和实用方法。",
                importance_levels=["高", "中", "低"]
            )
        ]
        
        return ConceptTemplate(
            type_name="判断标准",
            display_name="判断标准",
            description="适用于认定标准、区分标准、适用标准等",
            sections=sections,
            priority=4,
            compatible_types=["定义性概念", "构成要件"]
        )
    
    @staticmethod
    def get_regulations_template() -> ConceptTemplate:
        """法条规定模板"""
        sections = [
            TemplateSection(
                title="条文内容",
                required=True,
                order=1,
                description="法条的具体内容",
                extraction_prompt="请提取法条的具体内容、条文表述和法律规定。",
                importance_levels=["高", "中", "低"]
            ),
            TemplateSection(
                title="立法背景",
                required=False,
                order=2,
                description="法条的立法背景和目的",
                extraction_prompt="请提取这个法条的立法背景、立法目的和制定原因。",
                importance_levels=["高"]
            ),
            TemplateSection(
                title="适用情形",
                required=True,
                order=3,
                description="法条的适用情形",
                extraction_prompt="请提取法条的具体适用情形、适用条件和适用范围。",
                importance_levels=["高", "中"]
            ),
            TemplateSection(
                title="司法解释",
                required=False,
                order=4,
                description="相关司法解释",
                extraction_prompt="请提取相关的司法解释、最高法院的解释和实施细则。",
                importance_levels=["高", "中"]
            ),
            TemplateSection(
                title="实务争议",
                required=False,
                order=5,
                description="实务中的争议问题",
                extraction_prompt="请提取围绕这个法条的实务争议、理解分歧和解决方案。",
                importance_levels=["高", "中"]
            ),
            TemplateSection(
                title="记忆要点",
                required=True,
                order=6,
                description="法条记忆要点",
                extraction_prompt="请总结法条的记忆要点、关键词和应用技巧。",
                importance_levels=["高", "中", "低"]
            )
        ]
        
        return ConceptTemplate(
            type_name="法条规定",
            display_name="法条规定",
            description="适用于具体法条、法律条文、规范性文件等",
            sections=sections,
            priority=5,
            compatible_types=["定义性概念", "判断标准"]
        )
    
    @staticmethod
    def get_practice_template() -> ConceptTemplate:
        """实务经验模板"""
        sections = [
            TemplateSection(
                title="经验概述",
                required=True,
                order=1,
                description="实务经验的基本内容",
                extraction_prompt="请提取这个实务经验的基本内容、适用场景和实用价值。",
                importance_levels=["高", "中", "低"]
            ),
            TemplateSection(
                title="操作要点",
                required=True,
                order=2,
                description="具体操作要点",
                extraction_prompt="请提取具体的操作要点、实务技巧和处理方法。",
                importance_levels=["高", "中"]
            ),
            TemplateSection(
                title="注意事项",
                required=False,
                order=3,
                description="操作中的注意事项",
                extraction_prompt="请提取操作过程中的注意事项、风险提示和防范措施。",
                importance_levels=["高", "中"]
            ),
            TemplateSection(
                title="典型案例",
                required=False,
                order=4,
                description="典型案例和实际应用",
                extraction_prompt="请提取典型案例、成功经验和失败教训。",
                importance_levels=["高", "中"]
            ),
            TemplateSection(
                title="实用技巧",
                required=False,
                order=5,
                description="实用技巧和经验总结",
                extraction_prompt="请提取实用技巧、经验总结和提升方法。",
                importance_levels=["高", "中"]
            ),
            TemplateSection(
                title="记忆要点",
                required=True,
                order=6,
                description="经验记忆要点",
                extraction_prompt="请总结经验的记忆要点、实用技巧和应用提醒。",
                importance_levels=["高", "中", "低"]
            )
        ]
        
        return ConceptTemplate(
            type_name="实务经验",
            display_name="实务经验",
            description="适用于实务技巧、经验总结、操作方法等",
            sections=sections,
            priority=6,
            compatible_types=["程序性知识", "构成要件"]
        )

class TemplateRegistry:
    """模板注册表"""
    
    _templates: Dict[str, ConceptTemplate] = {}
    
    @classmethod
    def initialize(cls):
        """初始化模板注册表"""
        templates = ConceptTemplates()
        cls._templates = {
            "定义性概念": templates.get_definition_template(),
            "构成要件": templates.get_elements_template(),
            "程序性知识": templates.get_procedure_template(),
            "判断标准": templates.get_standards_template(),
            "法条规定": templates.get_regulations_template(),
            "实务经验": templates.get_practice_template()
        }
    
    @classmethod
    def get_template(cls, concept_type: str) -> Optional[ConceptTemplate]:
        """根据概念类型获取模板"""
        if not cls._templates:
            cls.initialize()
        return cls._templates.get(concept_type)
    
    @classmethod
    def get_all_templates(cls) -> Dict[str, ConceptTemplate]:
        """获取所有模板"""
        if not cls._templates:
            cls.initialize()
        return cls._templates.copy()
    
    @classmethod
    def get_template_types(cls) -> List[str]:
        """获取所有模板类型"""
        if not cls._templates:
            cls.initialize()
        return list(cls._templates.keys())
    
    @classmethod
    def get_default_template(cls) -> ConceptTemplate:
        """获取默认模板（定义性概念）"""
        if not cls._templates:
            cls.initialize()
        return cls._templates["定义性概念"]

# 初始化模板注册表
TemplateRegistry.initialize()
