import os
from typing import Dict, Any

class Config:
    # API配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-5q5D1V9gxu0u1MfP8OCqo7c3wwwb36ztuYywin07wq5ADx5b")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://yunwu.ai/v1")
    # 字幕处理模型 (例如，更注重内容提取和结构化的模型)
    SUBTITLE_PROCESSING_MODEL = os.getenv("SUBTITLE_PROCESSING_MODEL", "gpt-4.1-mini-2025-04-14")
    # 概念增强模型 (例如，更注重关系推理和知识图谱的模型)
    CONCEPT_ENHANCEMENT_MODEL = os.getenv("CONCEPT_ENHANCEMENT_MODEL", "gpt-4.1-2025-04-14") # 可以设置为不同的模型

    # SiliconFlow API配置
    SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "sk-rdraiurfdxaaytyxluvwuhoaedfnwgpjvddtebmynzzvuhle")

    # 文件路径配置
    OBSIDIAN_VAULT_PATH = "/Users/kawarox/Library/Mobile Documents/iCloud~md~obsidian/Documents/Xiada"
    
    # 科目序号映射
    SUBJECT_MAPPING = {
        "民法": "01民法",
        "刑法": "02刑法", 
        "行政法": "03行政法",
        "民事诉讼法": "04民事诉讼法",
        "刑事诉讼法": "05刑事诉讼法",
        "行政诉讼法": "06行政诉讼法",
        "商法": "07商法",
        "经济法": "08经济法",
        "国际法": "09国际法",
        "国际私法": "10国际私法",
        "国际经济法": "11国际经济法",
        "环境资源法": "12环境资源法",
        "劳动社会保障法": "13劳动社会保障法",
        "司法制度和法律职业道德": "14司法制度和法律职业道德"
    }
    
    @classmethod
    def get_subject_folder_name(cls, subject: str) -> str:
        """根据科目名称获取带序号的文件夹名"""
        return cls.SUBJECT_MAPPING.get(subject, f"99{subject}")  # 未知科目用99前缀
    
    @classmethod
    def get_output_path(cls, subject: str) -> str:
        """获取特定科目的输出路径"""
        subject_folder = cls.get_subject_folder_name(subject)
        return os.path.join(cls.OBSIDIAN_VAULT_PATH, subject_folder)
    
    @classmethod
    def ensure_directories(cls, subject: str = None):
        """确保必要的目录存在"""
        os.makedirs(cls.OBSIDIAN_VAULT_PATH, exist_ok=True)
        if subject:
            subject_path = cls.get_output_path(subject)
            os.makedirs(subject_path, exist_ok=True)
            print(f"📁 创建/确认科目目录: {subject_path}")
    
    @classmethod
    def list_available_subjects(cls) -> list:
        """获取可用的科目列表"""
        return list(cls.SUBJECT_MAPPING.keys())
