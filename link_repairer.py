import os
import re
import yaml
from typing import Dict, List, Set, Optional, Tuple
from config import Config

class LinkRepairer:
    """双链格式修复工具"""
    
    def __init__(self, vault_path: str):
        self.vault_path = vault_path
        self.all_note_titles = set()  # 存储所有笔记标题
        self.title_to_subject = {}    # 标题到科目的映射
        self.title_to_filepath = {}   # 标题到文件路径的映射
    
    def collect_all_note_titles(self) -> None:
        """收集所有笔记的标题和相关信息"""
        print("🔍 扫描所有笔记标题...")
        
        self.all_note_titles.clear()
        self.title_to_subject.clear()
        self.title_to_filepath.clear()
        
        total_notes = 0
        
        # 遍历所有科目文件夹
        for subject_name, folder_name in Config.SUBJECT_MAPPING.items():
            subject_path = os.path.join(self.vault_path, folder_name)
            
            if not os.path.exists(subject_path):
                continue
            
            subject_notes = 0
            
            # 遍历科目文件夹中的所有.md文件
            for root, dirs, files in os.walk(subject_path):
                for file in files:
                    if file.endswith('.md') and file not in ["概念数据库.md", "概念嵌入缓存_BGE.json"]:
                        file_path = os.path.join(root, file)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # 提取标题
                            title = self._extract_title_from_content(content, file)
                            
                            if title:
                                self.all_note_titles.add(title)
                                self.title_to_subject[title] = subject_name
                                self.title_to_filepath[title] = file_path
                                subject_notes += 1
                                total_notes += 1
                                
                        except Exception as e:
                            print(f"⚠️ 读取文件失败 {file_path}: {e}")
            
            if subject_notes > 0:
                print(f"  📂 {folder_name}: {subject_notes} 个笔记")
        
        print(f"📚 总计收集: {total_notes} 个笔记标题")
    
    def _extract_title_from_content(self, content: str, filename: str) -> Optional[str]:
        """从笔记内容中提取标题"""
        # 优先从YAML前置元数据中提取
        yaml_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if yaml_match:
            try:
                yaml_data = yaml.safe_load(yaml_match.group(1))
                title = yaml_data.get('title')
                if title:
                    return title
            except yaml.YAMLError:
                pass
        
        # 如果没有YAML或title字段，使用文件名
        return os.path.splitext(filename)[0]
    
    def repair_all_links(self) -> Dict[str, int]:
        """修复所有笔记中的双链格式"""
        print("\n🔧 开始修复所有笔记的双链格式...")
        
        # 首先收集所有笔记标题
        self.collect_all_note_titles()
        
        if not self.all_note_titles:
            print("❌ 没有找到任何笔记")
            return {'total': 0, 'repaired': 0, 'unchanged': 0, 'failed': 0}
        
        # 处理统计
        stats = {
            'total': len(self.all_note_titles),
            'repaired': 0,
            'unchanged': 0,
            'failed': 0
        }
        
        # 遍历所有笔记进行修复
        for i, (title, file_path) in enumerate(self.title_to_filepath.items(), 1):
            print(f"\n🔄 修复 {i}/{len(self.title_to_filepath)}: {title}")
            
            try:
                if self.repair_links_in_note(file_path):
                    stats['repaired'] += 1
                    print(f"  ✅ 修复成功")
                else:
                    stats['unchanged'] += 1
                    print(f"  ⚠️ 无需修复")
                    
            except Exception as e:
                stats['failed'] += 1
                print(f"  ❌ 修复失败: {e}")
        
        # 输出统计结果
        print(f"\n🎉 双链修复完成！")
        print(f"  📊 总计: {stats['total']} 个笔记")
        print(f"  ✅ 成功修复: {stats['repaired']} 个")
        print(f"  ⚠️ 无需修复: {stats['unchanged']} 个")
        print(f"  ❌ 修复失败: {stats['failed']} 个")
        
        return stats
    
    def repair_links_in_note(self, file_path: str) -> bool:
        """
        修复单个笔记中的双链格式
        
        Args:
            file_path: 笔记文件路径
            
        Returns:
            是否进行了修复
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # 修复链接
            repaired_content = self._repair_links_in_content(original_content)
            
            # 检查是否有修改
            if repaired_content == original_content:
                return False
            
            # 备份原文件
            backup_path = file_path + '.backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # 写入修复后的内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(repaired_content)
            
            # 删除备份文件
            os.remove(backup_path)
            
            return True
            
        except Exception as e:
            raise Exception(f"修复文件失败: {e}")
    
    def _repair_links_in_content(self, content: str) -> str:
        """修复内容中的双链格式"""
        # 修复规则：
        # 1. [[AAA|AAA']] -> [[【科目】AAA|AAA']] (如果存在【科目】AAA文件)
        # 2. [[AAA]] -> [[【科目】AAA|AAA]] (如果存在【科目】AAA文件)
        # 3. [[【科目】AAA]] -> [[【科目】AAA|AAA]]
        
        def replace_link(match):
            full_match = match.group(0)
            link_content = match.group(1)
            
            # 情况1: [[AAA|AAA']] 格式
            if '|' in link_content:
                target, display = link_content.split('|', 1)
                target = target.strip()
                display = display.strip()
                
                # 如果target不以【科目】开头，尝试找到对应的科目版本
                if not self._starts_with_subject_prefix(target):
                    subject_target = self._find_subject_version(target)
                    if subject_target:
                        return f"[[{subject_target}|{display}]]"
                
                return full_match
            
            # 情况2和3: [[AAA]] 格式
            else:
                target = link_content.strip()
                
                # 情况3: [[【科目】AAA]] -> [[【科目】AAA|AAA]]
                if self._starts_with_subject_prefix(target):
                    display_name = self._extract_display_name(target)
                    return f"[[{target}|{display_name}]]"
                
                # 情况2: [[AAA]] -> [[【科目】AAA|AAA]]
                else:
                    subject_target = self._find_subject_version(target)
                    if subject_target:
                        return f"[[{subject_target}|{target}]]"
                
                return full_match
        
        # 匹配所有双链: [[...]]
        link_pattern = r'\[\[([^\]]+)\]\]'
        return re.sub(link_pattern, replace_link, content)
    
    def _starts_with_subject_prefix(self, text: str) -> bool:
        """检查文本是否以【科目】开头"""
        return text.startswith('【') and '】' in text
    
    def _extract_display_name(self, title: str) -> str:
        """从带科目前缀的标题中提取显示名称"""
        if self._starts_with_subject_prefix(title):
            subject_end = title.find('】')
            if subject_end != -1:
                return title[subject_end + 1:]
        return title
    
    def _find_subject_version(self, target: str) -> Optional[str]:
        """
        查找目标的科目版本
        
        Args:
            target: 目标名称，如 "善意取得"
            
        Returns:
            科目版本标题，如 "【民法】善意取得"，如果不存在则返回None
        """
        # 直接查找是否存在 【任意科目】target 的标题
        for title in self.all_note_titles:
            if self._starts_with_subject_prefix(title):
                display_name = self._extract_display_name(title)
                if display_name == target:
                    return title
        
        return None
    
    def repair_specific_subject(self, subject: str) -> Dict[str, int]:
        """
        修复特定科目的双链格式
        
        Args:
            subject: 科目名称
            
        Returns:
            修复统计结果
        """
        print(f"\n🔧 修复 {subject} 科目的双链格式...")
        
        if subject not in Config.SUBJECT_MAPPING:
            print(f"❌ 未知科目: {subject}")
            return {'total': 0, 'repaired': 0, 'unchanged': 0, 'failed': 0}
        
        # 首先收集所有笔记标题（需要全部标题来进行匹配）
        self.collect_all_note_titles()
        
        # 筛选该科目的笔记
        subject_notes = {}
        for title, file_path in self.title_to_filepath.items():
            if self.title_to_subject.get(title) == subject:
                subject_notes[title] = file_path
        
        if not subject_notes:
            print(f"❌ {subject} 科目下没有找到笔记")
            return {'total': 0, 'repaired': 0, 'unchanged': 0, 'failed': 0}
        
        print(f"📝 找到 {len(subject_notes)} 个 {subject} 笔记")
        
        # 处理统计
        stats = {
            'total': len(subject_notes),
            'repaired': 0,
            'unchanged': 0,
            'failed': 0
        }
        
        # 遍历该科目的笔记进行修复
        for i, (title, file_path) in enumerate(subject_notes.items(), 1):
            print(f"\n🔄 修复 {i}/{len(subject_notes)}: {title}")
            
            try:
                if self.repair_links_in_note(file_path):
                    stats['repaired'] += 1
                    print(f"  ✅ 修复成功")
                else:
                    stats['unchanged'] += 1
                    print(f"  ⚠️ 无需修复")
                    
            except Exception as e:
                stats['failed'] += 1
                print(f"  ❌ 修复失败: {e}")
        
        # 输出统计结果
        print(f"\n🎉 {subject} 科目双链修复完成！")
        print(f"  📊 总计: {stats['total']} 个笔记")
        print(f"  ✅ 成功修复: {stats['repaired']} 个")
        print(f"  ⚠️ 无需修复: {stats['unchanged']} 个")
        print(f"  ❌ 修复失败: {stats['failed']} 个")
        
        return stats
    
    def preview_repairs(self, file_path: str) -> Optional[str]:
        """
        预览双链修复效果（不实际修改文件）
        
        Args:
            file_path: 笔记文件路径
            
        Returns:
            修复后的内容预览，如果无需修复则返回None
        """
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return None
        
        try:
            # 确保已收集所有标题
            if not self.all_note_titles:
                self.collect_all_note_titles()
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            repaired_content = self._repair_links_in_content(content)
            
            if repaired_content == content:
                return None
            else:
                return repaired_content
                
        except Exception as e:
            print(f"❌ 预览失败: {e}")
            return None
    
    def find_broken_links(self) -> List[Dict[str, str]]:
        """
        查找所有损坏的双链（指向不存在的笔记）
        
        Returns:
            损坏链接的列表，包含文件路径、链接内容等信息
        """
        print("\n🔍 查找损坏的双链...")
        
        # 确保已收集所有标题
        if not self.all_note_titles:
            self.collect_all_note_titles()
        
        broken_links = []
        
        for title, file_path in self.title_to_filepath.items():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 找到所有双链
                link_pattern = r'\[\[([^\]]+)\]\]'
                matches = re.finditer(link_pattern, content)
                
                for match in matches:
                    link_content = match.group(1)
                    
                    # 提取目标标题（忽略显示别名）
                    if '|' in link_content:
                        target = link_content.split('|')[0].strip()
                    else:
                        target = link_content.strip()
                    
                    # 检查目标是否存在
                    if target not in self.all_note_titles:
                        broken_links.append({
                            'file_path': file_path,
                            'file_title': title,
                            'broken_link': match.group(0),
                            'target': target,
                            'line_number': content[:match.start()].count('\n') + 1
                        })
                        
            except Exception as e:
                print(f"⚠️ 检查文件失败 {file_path}: {e}")
        
        print(f"🔍 发现 {len(broken_links)} 个损坏的双链")
        
        return broken_links


def main():
    """独立运行双链修复的主函数"""
    import sys
    
    repairer = LinkRepairer(Config.OBSIDIAN_VAULT_PATH)
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python link_repairer.py all                    # 修复所有笔记")
        print("  python link_repairer.py subject <科目名>        # 修复特定科目")
        print("  python link_repairer.py preview <文件路径>      # 预览修复效果")
        print("  python link_repairer.py broken                 # 查找损坏的链接")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'all':
        repairer.repair_all_links()
    elif command == 'subject' and len(sys.argv) >= 3:
        subject = sys.argv[2]
        repairer.repair_specific_subject(subject)
    elif command == 'preview' and len(sys.argv) >= 3:
        file_path = sys.argv[2]
        preview = repairer.preview_repairs(file_path)
        if preview:
            print("📝 修复预览:")
            print("-" * 50)
            print(preview)
            print("-" * 50)
        else:
            print("⚠️ 该文件无需修复")
    elif command == 'broken':
        broken_links = repairer.find_broken_links()
        if broken_links:
            print("\n❌ 发现以下损坏的双链:")
            for link in broken_links:
                print(f"  文件: {link['file_title']}")
                print(f"  链接: {link['broken_link']}")
                print(f"  行号: {link['line_number']}")
                print(f"  目标: {link['target']}")
                print("-" * 30)
        else:
            print("✅ 没有发现损坏的双链")
    else:
        print("❌ 无效命令")


if __name__ == "__main__":
    main()