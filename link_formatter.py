import re
from typing import Dict, List

class LinkFormatter:
    """处理双链格式的工具类"""
    
    @staticmethod
    def format_concept_links(content: str, concept_database: Dict) -> str:
        """
        格式化内容中的概念链接，使用显示别名格式
        
        Args:
            content: 笔记内容
            concept_database: 概念数据库
            
        Returns:
            格式化后的内容
        """
        # 找到所有 [[概念]] 格式的链接
        link_pattern = r'\[\[([^\]]+)\]\]'
        
        def replace_link(match):
            concept_name = match.group(1)
            
            # 如果概念名有【科目】前缀，转换为显示别名格式
            if concept_name.startswith('【') and '】' in concept_name:
                # 提取科目和概念名
                subject_end = concept_name.find('】')
                display_name = concept_name[subject_end + 1:]
                
                # 检查概念是否存在于数据库中
                if concept_name in concept_database:
                    return f"[[{concept_name}|{display_name}]]"
                else:
                    # 也检查别名
                    for existing_concept, data in concept_database.items():
                        if concept_name in data.get('aliases', []):
                            return f"[[{existing_concept}|{display_name}]]"
                    
                    # 如果都没找到，保持原样
                    return f"[[{concept_name}]]"
            else:
                # 没有科目前缀，检查是否需要添加科目前缀
                for existing_concept, data in concept_database.items():
                    if existing_concept.endswith(f'】{concept_name}'):
                        # 找到了对应的带科目前缀的概念
                        return f"[[{existing_concept}|{concept_name}]]"
                    elif concept_name in data.get('aliases', []):
                        # 通过别名找到了概念
                        if existing_concept.startswith('【') and '】' in existing_concept:
                            subject_end = existing_concept.find('】')
                            display_name = existing_concept[subject_end + 1:]
                            return f"[[{existing_concept}|{display_name}]]"
                        else:
                            return f"[[{existing_concept}]]"
                
                # 没找到对应概念，保持原样
                return f"[[{concept_name}]]"
        
        return re.sub(link_pattern, replace_link, content)
    
    @staticmethod
    def extract_display_name(concept_name: str) -> str:
        """
        从概念名中提取显示名称
        
        Args:
            concept_name: 概念名称，如 "【民法】善意取得"
            
        Returns:
            显示名称，如 "善意取得"
        """
        if concept_name.startswith('【') and '】' in concept_name:
            subject_end = concept_name.find('】')
            return concept_name[subject_end + 1:]
        return concept_name
    
    @staticmethod
    def find_matching_concept(target_name: str, concept_database: Dict) -> str:
        """
        在概念数据库中查找匹配的概念
        
        Args:
            target_name: 要查找的概念名
            concept_database: 概念数据库
            
        Returns:
            匹配的完整概念名，如果没找到则返回原名
        """
        # 直接匹配
        if target_name in concept_database:
            return target_name
        
        # 通过别名匹配
        for concept_name, data in concept_database.items():
            if target_name in data.get('aliases', []):
                return concept_name
        
        # 部分匹配（去掉科目前缀）
        for concept_name in concept_database.keys():
            if concept_name.endswith(f'】{target_name}'):
                return concept_name
        
        return target_name