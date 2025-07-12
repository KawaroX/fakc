import os
import yaml
import re
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from config import Config

class ConceptManager:
    def __init__(self, vault_path: str):
        self.vault_path = vault_path
        self.concept_database = {}
        self.database_file = os.path.join(vault_path, "概念数据库.md")
        self.database_json_file = os.path.join(vault_path, "概念数据库.json")
    
    def scan_existing_notes(self) -> None:
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
        self.save_database_to_files()
    
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
                    related_concepts = re.findall(r'\[\[(.*?)\]\]', content)
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
                related_concepts = re.findall(r'\[\[(.*?)\]\]', content)
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
    
    def save_database_to_files(self) -> None:
        """将概念数据库分别保存为markdown文件和JSON文件"""
        try:
            # 1. 保存JSON文件（用于程序解析）
            self._save_json_database()
            
            # 2. 保存Markdown文件（用于人类查看）
            self._save_markdown_database()
            
            print(f"💾 概念数据库已保存:")
            print(f"  📄 {os.path.basename(self.database_file)} (查看用)")
            print(f"  📊 {os.path.basename(self.database_json_file)} (程序用)")
            
        except Exception as e:
            print(f"❌ 保存概念数据库失败: {e}")
    
    def _save_json_database(self) -> None:
        """保存JSON格式的概念数据库"""
        # 添加元数据
        database_with_meta = {
            'metadata': {
                'created': datetime.now().strftime('%Y-%m-%d'),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_concepts': len(self.concept_database),
                'version': '1.0'
            },
            'concepts': self.concept_database
        }
        
        with open(self.database_json_file, 'w', encoding='utf-8') as f:
            json.dump(database_with_meta, f, ensure_ascii=False, indent=2)
    
    def _save_markdown_database(self) -> None:
        """保存Markdown格式的概念数据库"""
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
    
    def _generate_database_markdown(self, subjects_data: Dict) -> str:
        """生成概念数据库的markdown内容（纯文档，不包含JSON）"""
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
> 
> 📁 **相关文件**
> - 程序数据: `概念数据库.json`

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
        
        # 添加使用说明
        content += f"""## 使用说明

### 如何使用这个数据库

1. **查看概念**: 点击任意 [[概念名]] 链接跳转到对应笔记
2. **搜索概念**: 使用 Obsidian 的搜索功能查找特定概念
3. **关系图谱**: 通过相关概念链接查看知识点之间的关联

### 文件说明

- `概念数据库.md`: 本文件，供人类查看的概念索引
- `概念数据库.json`: 程序使用的结构化数据，包含完整的概念信息

### 自动维护

此数据库由程序自动生成和维护：
- 处理新字幕文件时自动更新
- 增强笔记概念关系时自动更新
- 手动重新扫描时更新

---
*最后生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return content
    
    def load_database_from_file(self) -> bool:
        """从JSON文件加载概念数据库（优先），如果不存在则从markdown文件加载"""
        # 优先尝试从JSON文件加载
        if self._load_from_json():
            return True
        
        # 如果JSON文件不存在，尝试从旧的markdown文件加载
        if self._load_from_markdown():
            print("📄 从markdown文件加载成功，建议重新扫描生成JSON文件")
            return True
            
        return False
    
    def _load_from_json(self) -> bool:
        """从JSON文件加载概念数据库"""
        try:
            if not os.path.exists(self.database_json_file):
                return False
                
            with open(self.database_json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查数据格式
            if 'concepts' in data:
                self.concept_database = data['concepts']
                metadata = data.get('metadata', {})
                total_concepts = metadata.get('total_concepts', len(self.concept_database))
                print(f"📖 已从JSON加载概念数据库: {total_concepts} 个概念")
                return True
            else:
                # 兼容旧格式
                self.concept_database = data
                print(f"📖 已从JSON加载概念数据库: {len(self.concept_database)} 个概念")
                return True
                
        except Exception as e:
            print(f"⚠️ 从JSON加载概念数据库失败: {e}")
            return False
    
    def _load_from_markdown(self) -> bool:
        """从markdown文件加载概念数据库（向后兼容）"""
        try:
            if not os.path.exists(self.database_file):
                return False
                
            with open(self.database_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取JSON数据（如果存在）
            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                json_data = json.loads(json_match.group(1))
                self.concept_database = json_data
                print(f"📖 已从markdown文件加载概念数据库: {len(self.concept_database)} 个概念")
                return True
                
        except Exception as e:
            print(f"⚠️ 从markdown加载概念数据库失败: {e}")
            
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
            
            # 处理双链格式
            content = note['content']
            if hasattr(self, 'concept_database') and self.concept_database:
                from link_formatter import LinkFormatter
                content = LinkFormatter.format_concept_links(content, self.concept_database)
                note['content'] = content  # 更新处理后的内容
            
            # 提取相关概念
            related_concepts = re.findall(r'\[\[(.*?)\]\]', content)
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
        self.save_database_to_files()
    
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