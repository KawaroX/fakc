import os
import re
from typing import List, Dict, Any, Optional
from ai_processor import AIProcessor
from enhanced_concept_manager import EnhancedConceptManager
import config as Config

class NoteEnhancer:
    def __init__(self, ai_processor: AIProcessor, concept_manager: EnhancedConceptManager):
        self.ai_processor = ai_processor
        self.concept_manager = concept_manager
    
    def enhance_all_notes(self) -> None:
        """遍历所有法考笔记，使用AI增强概念关系"""
        print("🔄 开始增强现有笔记的概念关系...")
        
        # 确保概念数据库是最新的
        if not self.concept_manager.load_database_from_file():
            print("📚 重新扫描笔记建立概念数据库...")
            self.concept_manager.scan_law_notes_only()
        
        # 获取所有需要处理的笔记
        notes_to_enhance = self._collect_all_law_notes()
        
        if not notes_to_enhance:
            print("❌ 没有找到需要增强的笔记")
            return
        
        print(f"📝 找到 {len(notes_to_enhance)} 个笔记需要处理")
        
        # 批量处理笔记
        enhanced_count = 0
        failed_count = 0
        
        for i, note_info in enumerate(notes_to_enhance, 1):
            print(f"\\n🔄 处理笔记 {i}/{len(notes_to_enhance)}: {note_info['title']}")
            
            try:
                if self._enhance_single_note(note_info):
                    enhanced_count += 1
                    print(f"  ✅ 增强成功")
                else:
                    print(f"  ⚠️ 无需修改")
                    
            except Exception as e:
                failed_count += 1
                print(f"  ❌ 增强失败: {e}")
        
        print(f"\\n🎉 处理完成！")
        print(f"  ✅ 成功增强: {enhanced_count} 个")
        print(f"  ⚠️ 无需修改: {len(notes_to_enhance) - enhanced_count - failed_count} 个")
        print(f"  ❌ 处理失败: {failed_count} 个")
        
        # 重新扫描更新概念数据库
        print(f"\\n📚 更新概念数据库...")
        self.concept_manager.scan_law_notes_only()
    
    def _collect_all_law_notes(self) -> List[Dict[str, Any]]:
        """收集所有法考笔记的信息"""
        notes = []
        
        for subject_name, folder_name in self.concept_manager.concept_database.items():
            subject_path = os.path.join(self.concept_manager.vault_path, 
                                       Config.get_subject_folder_name(subject_name))
            
            if not os.path.exists(subject_path):
                continue
            
            for root, dirs, files in os.walk(subject_path):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # 提取标题
                            yaml_match = re.match(r'^---\\n(.*?)\\n---', content, re.DOTALL)
                            if yaml_match:
                                import yaml
                                yaml_data = yaml.safe_load(yaml_match.group(1))
                                title = yaml_data.get('title', os.path.splitext(file)[0])
                            else:
                                title = os.path.splitext(file)[0]
                            
                            notes.append({
                                'title': title,
                                'file_path': file_path,
                                'content': content,
                                'subject': subject_name
                            })
                            
                        except Exception as e:
                            print(f"⚠️ 读取笔记失败 {file_path}: {e}")
        
        return notes
    
    def _enhance_single_note(self, note_info: Dict[str, Any]) -> bool:
        """增强单个笔记的概念关系"""
        # 获取现有概念信息
        existing_concepts = self.concept_manager.get_all_concepts_for_ai()
        
        # 调用AI分析并增强概念关系
        enhancement_result = self.ai_processor.enhance_single_note_concepts(
            note_info['content'], 
            note_info['title'],
            existing_concepts
        )
        
        if not enhancement_result or not enhancement_result.get('modified', False):
            return False
        
        # 应用AI建议的修改
        new_content = enhancement_result['enhanced_content']
        
        # 备份原文件
        backup_path = note_info['file_path'] + '.backup'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(note_info['content'])
        
        # 写入增强后的内容
        with open(note_info['file_path'], 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # 删除备份文件（如果写入成功）
        os.remove(backup_path)
        
        return True
    
    def enhance_specific_subject(self, subject: str) -> None:
        """增强特定科目的笔记"""
        print(f"🔄 增强 {subject} 科目的笔记...")
        
        subject_folder = Config.get_subject_folder_name(subject)
        subject_path = os.path.join(self.concept_manager.vault_path, subject_folder)
        
        if not os.path.exists(subject_path):
            print(f"❌ 科目文件夹不存在: {subject_folder}")
            return
        
        # 收集该科目的所有笔记
        notes = []
        for root, dirs, files in os.walk(subject_path):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        notes.append({
                            'title': os.path.splitext(file)[0],
                            'file_path': file_path,
                            'content': content,
                            'subject': subject
                        })
                    except Exception as e:
                        print(f"⚠️ 读取失败 {file}: {e}")
        
        if not notes:
            print(f"❌ {subject} 科目下没有找到笔记")
            return
        
        print(f"📝 找到 {len(notes)} 个 {subject} 笔记")
        
        # 处理笔记
        enhanced_count = 0
        for i, note_info in enumerate(notes, 1):
            print(f"🔄 处理 {i}/{len(notes)}: {note_info['title']}")
            
            try:
                if self._enhance_single_note(note_info):
                    enhanced_count += 1
                    print(f"  ✅ 增强成功")
                else:
                    print(f"  ⚠️ 无需修改")
            except Exception as e:
                print(f"  ❌ 增强失败: {e}")
        
        print(f"\\n🎉 {subject} 科目处理完成，成功增强 {enhanced_count} 个笔记")

