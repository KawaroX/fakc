import os
import yaml
import re
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from config import Config

class EnhancedConceptManager:
    def __init__(self, vault_path: str):
        self.vault_path = vault_path
        self.concept_database = {}
        self.database_file = os.path.join(vault_path, "概念数据库.md")
        
    def scan_law_notes_only(self) -> None:
        """只扫描01-14法考科目文件夹中的笔记建立概念数据库"""
        print("🔍 扫描法考科目笔记...")
        
        total_notes = 0
        total_concepts = 0
        
        # 遍历01-14的科目文件夹
        for subject_name, folder_name in Config.SUBJECT_MAPPING.items():
            subject_path = os.path.join(self.vault_path, folder_name)
            
            if not os.path.exists(subject_path):
                continue
                
            print(f"  📂 扫描 {folder_name}...")
            subject_notes = 0
            
            # 遍历科目文件夹中的所有.md文件
            for root, dirs, files in os.walk(subject_path):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        if self._extract_concepts_from_file(file_path, subject_name):
                            subject_notes += 1
                            total_concepts += 1
            
            if subject_notes > 0:
                print(f"    ✅ {subject_notes} 个笔记")
                total_notes += subject_notes
        
        print(f"📚 总计扫描: {total_notes} 个笔记，{total_concepts} 个概念")
        
        # 保存概念数据库到文件
        self.save_database_to_file()
    
    def _extract_concepts_from_file(self, file_path: str, subject: str) -> bool:
        """从单个文件提取概念信息"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取YAML前置元数据
            yaml_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if yaml_match:
                try:
                    yaml_data = yaml.safe_load(yaml_match.group(1))
                    title = yaml_data.get('title', os.path.splitext(os.path.basename(file_path))[0])
                    aliases = yaml_data.get('aliases', [])
                    tags = yaml_data.get('tags', [])
                    
                    # 提取相关概念（所有[[]]链接）
                    related_concepts = re.findall(r'\\[\\[(.*?)\\]\\]', content)
                    related_concepts = [concept.strip() for concept in related_concepts if concept.strip()]
                    
                    # 存储概念信息
                    self.concept_database[title] = {
                        'file_path': os.path.relpath(file_path, self.vault_path),
                        'aliases': aliases,
                        'tags': tags,
                        'related_concepts': list(set(related_concepts)),
                        'subject': subject,
                        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    return True
                except yaml.YAMLError as e:
                    print(f"⚠️ YAML解析错误 {file_path}: {e}")
                    return False
            else:
                # 没有YAML前置元数据的文件，尝试从文件名获取标题
                title = os.path.splitext(os.path.basename(file_path))[0]
                related_concepts = re.findall(r'\\[\\[(.*?)\\]\\]', content)
                related_concepts = [concept.strip() for concept in related_concepts if concept.strip()]
                
                if related_concepts:  # 只有包含概念链接的文件才纳入数据库
                    self.concept_database[title] = {
                        'file_path': os.path.relpath(file_path, self.vault_path),
                        'aliases': [],
                        'tags': [subject],
                        'related_concepts': list(set(related_concepts)),
                        'subject': subject,
                        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    return True
                
        except Exception as e:
            print(f"⚠️ 读取文件失败 {file_path}: {e}")
            
        return False
    
    def save_database_to_file(self) -> None:
        """将概念数据库保存为markdown文件"""
        try:
            # 按科目分组
            subjects_data = {}
            for concept, data in self.concept_database.items():
                subject = data['subject']
                if subject not in subjects_data:
                    subjects_data[subject] = []
                subjects_data[subject].append((concept, data))
            
            # 生成markdown内容
            content = self._generate_database_markdown(subjects_data)
            
            # 写入文件
            with open(self.database_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            print(f"💾 概念数据库已保存: {os.path.basename(self.database_file)}")
            
        except Exception as e:
            print(f"❌ 保存概念数据库失败: {e}")
    
    def _generate_database_markdown(self, subjects_data: Dict) -> str:
        """生成概念数据库的markdown内容"""
        content = f"""---
title: "法考概念数据库"
aliases: ["概念数据库", "法考概念库"]
tags: ["法考", "概念", "数据库", "索引", "hide-from-graph"]
created: "{datetime.now().astimezone().isoformat()}"
last_updated: "{datetime.now().astimezone().isoformat()}"
total_concepts: {len(self.concept_database)}
---

# 法考概念数据库

> 自动生成的法考概念索引，包含所有科目的概念及其关联关系
> 
> 📊 **统计信息**
> - 总概念数量: {len(self.concept_database)}
> - 涵盖科目: {len(subjects_data)}
> - 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 概念索引

"""
        
        # 按科目组织内容
        for subject in sorted(subjects_data.keys()):
            concepts = subjects_data[subject]
            content += f"### {subject} ({len(concepts)}个概念)\n\n"
            
            for concept, data in sorted(concepts, key=lambda x: x[0]):
                content += f"#### [[{concept}]]\n"
                content += f"- **文件**: `{data['file_path']}`\n"
                
                if data['aliases']:
                    aliases_str = "、".join(data['aliases'])
                    content += f"- **别名**: {aliases_str}\n"
                
                if data['related_concepts']:
                    related_str = "、".join([f"[[{c}]]" for c in data['related_concepts'][:5]])
                    if len(data['related_concepts']) > 5:
                        related_str += f" 等{len(data['related_concepts'])}个"
                    content += f"- **相关概念**: {related_str}\n"
                
                content += f"- **最后更新**: {data['last_updated']}\n\n"
        
        # 添加JSON数据（用于程序读取）
        content += "## 数据备份\n\n"
        content += "```json\n"
        content += json.dumps(self.concept_database, ensure_ascii=False, indent=2)
        content += "\n```\n"
        
        return content
    
    def load_database_from_file(self) -> bool:
        """从文件加载概念数据库"""
        try:
            if not os.path.exists(self.database_file):
                return False
                
            with open(self.database_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取JSON数据
            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                json_data = json.loads(json_match.group(1))
                self.concept_database = json_data
                print(f"📖 已加载概念数据库: {len(self.concept_database)} 个概念")
                return True
                
        except Exception as e:
            print(f"⚠️ 加载概念数据库失败: {e}")
            
        return False
    
    def get_all_concepts_for_ai(self) -> Dict[str, Any]:
        """获取所有概念信息供AI参考"""
        return {
            'existing_concepts': list(self.concept_database.keys()),
            'concept_aliases': {k: v.get('aliases', []) for k, v in self.concept_database.items()},
            'concept_relationships': {k: v.get('related_concepts', []) for k, v in self.concept_database.items()},
            'concept_subjects': {k: v.get('subject', '') for k, v in self.concept_database.items()}
        }
    
    def update_database(self, new_notes: List[Dict]) -> None:
        """更新概念数据库"""
        for note in new_notes:
            yaml_data = note['yaml']
            title = yaml_data['title']
            
            # 提取相关概念
            related_concepts = re.findall(r'\\[\\[(.*?)\\]\\]', note['content'])
            related_concepts = [concept.strip() for concept in related_concepts if concept.strip()]
            
            self.concept_database[title] = {
                'file_path': f"{title}.md",
                'aliases': yaml_data.get('aliases', []),
                'tags': yaml_data.get('tags', []),
                'related_concepts': list(set(related_concepts)),
                'subject': yaml_data.get('subject', ''),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        # 保存更新后的数据库
        self.save_database_to_file()
    
    def get_concept_info(self, concept_name: str) -> Optional[Dict]:
        """获取特定概念的信息"""
        # 直接匹配
        if concept_name in self.concept_database:
            return self.concept_database[concept_name]
        
        # 通过别名匹配
        for concept, data in self.concept_database.items():
            if concept_name in data.get('aliases', []):
                return data
                
        return None
    
    def find_related_concepts(self, concept_name: str, max_depth: int = 2) -> List[str]:
        """查找与指定概念相关的概念（支持多层关联）"""
        related = set()
        to_check = [concept_name]
        checked = set()
        
        for depth in range(max_depth):
            current_level = []
            for concept in to_check:
                if concept in checked:
                    continue
                checked.add(concept)
                
                concept_data = self.get_concept_info(concept)
                if concept_data:
                    concept_related = concept_data.get('related_concepts', [])
                    related.update(concept_related)
                    current_level.extend(concept_related)
            
            to_check = current_level
            
        return list(related - {concept_name})
