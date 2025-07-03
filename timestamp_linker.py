# timestamp_linker.py

import os
import re
import yaml
from typing import Dict, List, Optional
from config import Config
from timestamp_processor import TimestampProcessor

class TimestampLinker:
    """独立的时间戳链接化处理器"""
    
    def __init__(self, vault_path: str):
        self.vault_path = vault_path
    
    def process_all_notes_with_course_url(self) -> Dict[str, int]:
        """
        处理所有包含course_url的笔记，将时间戳转换为链接
        
        Returns:
            包含处理结果统计的字典
        """
        print("🔗 开始处理所有笔记的时间戳链接...")
        
        # 收集所有包含course_url的笔记
        notes_with_url = self._collect_notes_with_course_url()
        
        if not notes_with_url:
            print("❌ 没有找到包含课程链接的笔记")
            return {'total': 0, 'processed': 0, 'unchanged': 0, 'failed': 0}
        
        print(f"📝 找到 {len(notes_with_url)} 个包含课程链接的笔记")
        
        return self._process_notes_batch(notes_with_url)
    
    def process_subject_notes(self, subject: str) -> Dict[str, int]:
        """
        处理特定科目中包含course_url的笔记
        
        Args:
            subject: 科目名称
            
        Returns:
            包含处理结果统计的字典
        """
        print(f"🔗 处理 {subject} 科目的时间戳链接...")
        
        if subject not in Config.SUBJECT_MAPPING:
            print(f"❌ 未知科目: {subject}")
            return {'total': 0, 'processed': 0, 'unchanged': 0, 'failed': 0}
        
        subject_folder = Config.get_subject_folder_name(subject)
        subject_path = os.path.join(self.vault_path, subject_folder)
        
        if not os.path.exists(subject_path):
            print(f"❌ 科目文件夹不存在: {subject_folder}")
            return {'total': 0, 'processed': 0, 'unchanged': 0, 'failed': 0}
        
        # 收集该科目的笔记
        notes_with_url = self._collect_subject_notes_with_url(subject_path)
        
        if not notes_with_url:
            print(f"❌ {subject} 科目下没有找到包含课程链接的笔记")
            return {'total': 0, 'processed': 0, 'unchanged': 0, 'failed': 0}
        
        print(f"📝 找到 {len(notes_with_url)} 个 {subject} 包含课程链接的笔记")
        
        return self._process_notes_batch(notes_with_url)
    
    def process_single_note(self, file_path: str) -> bool:
        """
        处理单个笔记文件的时间戳链接
        
        Args:
            file_path: 笔记文件路径
            
        Returns:
            是否成功处理
        """
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取YAML和course_url
            yaml_data, course_url = self._extract_course_url(content)
            
            if not course_url:
                print(f"⚠️ 文件中没有course_url: {os.path.basename(file_path)}")
                return False
            
            # 处理时间戳
            processed_content = self._process_timestamps_in_content(content, course_url)
            
            if processed_content == content:
                print(f"⚠️ 没有需要处理的时间戳: {os.path.basename(file_path)}")
                return False
            
            # 备份并写入
            backup_path = file_path + '.backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(processed_content)
            
            # 删除备份文件
            os.remove(backup_path)
            
            print(f"✅ 处理成功: {os.path.basename(file_path)}")
            return True
            
        except Exception as e:
            print(f"❌ 处理失败: {e}")
            return False
    
    def _collect_notes_with_course_url(self) -> List[Dict[str, str]]:
        """收集所有包含course_url的笔记"""
        notes = []
        
        for subject_name, folder_name in Config.SUBJECT_MAPPING.items():
            subject_path = os.path.join(self.vault_path, folder_name)
            
            if not os.path.exists(subject_path):
                continue
            
            subject_notes = self._collect_subject_notes_with_url(subject_path)
            notes.extend(subject_notes)
        
        return notes
    
    def _collect_subject_notes_with_url(self, subject_path: str) -> List[Dict[str, str]]:
        """收集特定科目下包含course_url的笔记"""
        notes = []
        
        for root, dirs, files in os.walk(subject_path):
            for file in files:
                if file.endswith('.md') and file not in ["概念数据库.md"]:
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        yaml_data, course_url = self._extract_course_url(content)
                        
                        if course_url:
                            notes.append({
                                'file_path': file_path,
                                'content': content,
                                'course_url': course_url,
                                'title': yaml_data.get('title', os.path.splitext(file)[0])
                            })
                            
                    except Exception as e:
                        print(f"⚠️ 读取文件失败 {file_path}: {e}")
        
        return notes
    
    def _extract_course_url(self, content: str) -> tuple[Optional[Dict], Optional[str]]:
        """从笔记内容中提取course_url"""
        yaml_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if yaml_match:
            try:
                yaml_data = yaml.safe_load(yaml_match.group(1))
                course_url = yaml_data.get('course_url', '')
                return yaml_data, course_url if course_url else None
            except yaml.YAMLError:
                pass
        
        return None, None
    
    def _process_timestamps_in_content(self, content: str, course_url: str) -> str:
        """处理内容中的时间戳"""
        # 找到YAML结束位置
        yaml_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if yaml_match:
            yaml_part = content[:yaml_match.end()]
            content_part = content[yaml_match.end():]
            
            # 处理内容部分的时间戳
            processed_content_part = TimestampProcessor.process_content_timestamps(content_part, course_url)
            
            return yaml_part + processed_content_part
        else:
            # 没有YAML前置，直接处理整个内容
            return TimestampProcessor.process_content_timestamps(content, course_url)
    
    def _process_notes_batch(self, notes: List[Dict[str, str]]) -> Dict[str, int]:
        """批量处理笔记的时间戳链接"""
        stats = {
            'total': len(notes),
            'processed': 0,
            'unchanged': 0,
            'failed': 0
        }
        
        for i, note_info in enumerate(notes, 1):
            print(f"\n🔄 处理 {i}/{len(notes)}: {note_info['title']}")
            
            try:
                # 处理时间戳
                processed_content = self._process_timestamps_in_content(
                    note_info['content'], 
                    note_info['course_url']
                )
                
                if processed_content == note_info['content']:
                    stats['unchanged'] += 1
                    print(f"  ⚠️ 没有需要处理的时间戳")
                    continue
                
                # 备份并写入
                file_path = note_info['file_path']
                backup_path = file_path + '.backup'
                
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(note_info['content'])
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(processed_content)
                
                # 删除备份文件
                os.remove(backup_path)
                
                stats['processed'] += 1
                print(f"  ✅ 处理成功")
                
            except Exception as e:
                stats['failed'] += 1
                print(f"  ❌ 处理失败: {e}")
        
        # 输出统计结果
        print(f"\n🎉 时间戳链接化处理完成！")
        print(f"  📊 总计: {stats['total']} 个笔记")
        print(f"  ✅ 成功处理: {stats['processed']} 个")
        print(f"  ⚠️ 无需处理: {stats['unchanged']} 个")
        print(f"  ❌ 处理失败: {stats['failed']} 个")
        
        return stats
    
    def preview_processing(self, file_path: str) -> Optional[str]:
        """
        预览时间戳处理效果（不实际修改文件）
        
        Args:
            file_path: 笔记文件路径
            
        Returns:
            处理后的内容预览，如果无需处理则返回None
        """
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            yaml_data, course_url = self._extract_course_url(content)
            
            if not course_url:
                print(f"⚠️ 文件中没有course_url")
                return None
            
            processed_content = self._process_timestamps_in_content(content, course_url)
            
            if processed_content == content:
                return None
            else:
                return processed_content
                
        except Exception as e:
            print(f"❌ 预览失败: {e}")
            return None


def main():
    """独立运行时间戳链接化的主函数"""
    import sys
    
    linker = TimestampLinker(Config.OBSIDIAN_VAULT_PATH)
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python timestamp_linker.py all                    # 处理所有笔记")
        print("  python timestamp_linker.py subject <科目名>        # 处理特定科目")
        print("  python timestamp_linker.py file <文件路径>         # 处理单个文件")
        print("  python timestamp_linker.py preview <文件路径>      # 预览处理效果")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'all':
        linker.process_all_notes_with_course_url()
    elif command == 'subject' and len(sys.argv) >= 3:
        subject = sys.argv[2]
        linker.process_subject_notes(subject)
    elif command == 'file' and len(sys.argv) >= 3:
        file_path = sys.argv[2]
        if linker.process_single_note(file_path):
            print("✅ 文件处理成功")
        else:
            print("❌ 文件处理失败或无需处理")
    elif command == 'preview' and len(sys.argv) >= 3:
        file_path = sys.argv[2]
        preview = linker.preview_processing(file_path)
        if preview:
            print("📝 处理预览:")
            print("-" * 50)
            print(preview)
            print("-" * 50)
        else:
            print("⚠️ 该文件无需处理")
    else:
        print("❌ 无效命令")


if __name__ == "__main__":
    main()