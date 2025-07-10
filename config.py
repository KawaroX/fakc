import os
from typing import Dict
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 尝试加载.env文件，如果不存在则不报错
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logging.warning("python-dotenv 未安装，无法从.env文件加载环境变量。")
except Exception as e:
    logging.error(f"加载.env文件时发生错误: {e}")

class Config:
    # 定义所有必需的环境变量
    REQUIRED_ENV_VARS = [
        "SUBTITLE_PROCESSING_API_KEY",
        "SUBTITLE_PROCESSING_BASE_URL",
        "SUBTITLE_PROCESSING_MODEL",
        "CONCEPT_ENHANCEMENT_API_KEY",
        "CONCEPT_ENHANCEMENT_BASE_URL",
        "CONCEPT_ENHANCEMENT_MODEL",
        "SILICONFLOW_API_KEY",
        "OBSIDIAN_VAULT_PATH"
    ]

    # API配置
    SUBTITLE_PROCESSING_API_KEY = os.getenv("SUBTITLE_PROCESSING_API_KEY")
    SUBTITLE_PROCESSING_BASE_URL = os.getenv("SUBTITLE_PROCESSING_BASE_URL")
    SUBTITLE_PROCESSING_MODEL = os.getenv("SUBTITLE_PROCESSING_MODEL")

    CONCEPT_ENHANCEMENT_API_KEY = os.getenv("CONCEPT_ENHANCEMENT_API_KEY")
    CONCEPT_ENHANCEMENT_BASE_URL = os.getenv("CONCEPT_ENHANCEMENT_BASE_URL")
    CONCEPT_ENHANCEMENT_MODEL = os.getenv("CONCEPT_ENHANCEMENT_MODEL")

    SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")

    # 文件路径配置
    OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH")
    
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
            logging.info(f"📁 创建/确认科目目录: {subject_path}")
    
    @classmethod
    def list_available_subjects(cls) -> list:
        """获取可用的科目列表"""
        return list(cls.SUBJECT_MAPPING.keys())

    @classmethod
    def check_and_get_missing_env(cls) -> list:
        """
        检查所有必需的环境变量是否都已设置，并返回缺失的变量列表。
        对于API KEY，如果值为空或与预设的占位符值相同，则视为缺失。
        对于其他变量，如果值为空，则视为缺失。
        """
        missing_vars = []
        # 硬编码占位符值，包括API KEY和OBSIDIAN_VAULT_PATH
        placeholder_values = {
            "SUBTITLE_PROCESSING_API_KEY": "your_subtitle_processing_api_key",
            "CONCEPT_ENHANCEMENT_API_KEY": "your_concept_enhancement_api_key",
            "SILICONFLOW_API_KEY": "your_siliconflow_api_key",
            "OBSIDIAN_VAULT_PATH": "/Path/to/your/obsidian/vault"
        }

        for var_name in cls.REQUIRED_ENV_VARS:
            current_value = os.getenv(var_name)
            
            is_missing = False
            if var_name in placeholder_values:
                # 对于API KEY和OBSIDIAN_VAULT_PATH，检查是否为空或与占位符相同
                if current_value is None or current_value.strip() == "" or current_value == placeholder_values[var_name]:
                    is_missing = True
            else:
                # 对于其他变量（如BASE_URL, MODEL），只检查是否为空
                if current_value is None or current_value.strip() == "":
                    is_missing = True
            
            if is_missing:
                missing_vars.append(var_name)
        return missing_vars

    @classmethod
    def update_env_file(cls, updates: Dict[str, str]):
        """
        更新.env文件中的环境变量。
        如果.env文件不存在，则创建它。
        """
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        env_content = []

        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                env_content = f.readlines()

        updated_keys = set(updates.keys())
        new_content = []
        found_keys = set()

        for line in env_content:
            # 检查行是否包含我们要更新的变量
            matched = False
            for key in updated_keys:
                if line.strip().startswith(f"{key}="):
                    new_content.append(f"{key}={updates[key]}\n")
                    found_keys.add(key)
                    matched = True
                    break
            if not matched:
                new_content.append(line)
        
        # 添加新的或未找到的变量
        for key in updated_keys:
            if key not in found_keys:
                new_content.append(f"{key}={updates[key]}\n")

        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_content)
        logging.info(f"✅ .env 文件已更新: {', '.join(updates.keys())}")
