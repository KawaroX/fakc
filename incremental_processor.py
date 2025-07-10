import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

class IncrementalProcessor:
    """增量处理管理器 - 智能检测哪些笔记需要重新增强"""
    
    def __init__(self, vault_path: str):
        self.vault_path = vault_path
        self.tracking_file = os.path.join(vault_path, "note_change_tracking.json")
        self.tracking_data = {
            'last_full_enhancement': None,
            'note_hashes': {},       # 文件路径 -> 内容哈希
            'concept_count_at_last_enhancement': 0,
            'enhancement_history': []
        }
        self.load_tracking_data()
    
    def load_tracking_data(self) -> None:
        """加载追踪数据"""
        try:
            if os.path.exists(self.tracking_file):
                with open(self.tracking_file, 'r', encoding='utf-8') as f:
                    self.tracking_data = json.load(f)
                print(f"📖 加载增量追踪数据: {len(self.tracking_data['note_hashes'])} 个笔记记录")
            else:
                print("✨ 初始化增量追踪系统")
        except Exception as e:
            print(f"⚠️ 加载追踪数据失败: {e}")
    
    def save_tracking_data(self) -> None:
        """保存追踪数据"""
        try:
            with open(self.tracking_file, 'w', encoding='utf-8') as f:
                json.dump(self.tracking_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 保存追踪数据失败: {e}")
    
    def get_notes_needing_enhancement(self, all_notes: List[Dict], concept_manager) -> List[Dict]:
        """识别需要增强的笔记"""
        current_concept_count = len(concept_manager.concept_database) if concept_manager.concept_database else 0
        notes_to_process = []
        
        # 情况1：概念库有新增概念
        if current_concept_count > self.tracking_data['concept_count_at_last_enhancement']:
            new_concept_count = current_concept_count - self.tracking_data['concept_count_at_last_enhancement']
            print(f"🆕 检测到 {new_concept_count} 个新概念，寻找相关笔记...")
            
            # 简化策略：如果新概念较多，处理所有笔记；如果较少，只处理变化的笔记
            if new_concept_count > 10:
                print("📝 新概念较多，建议全量处理")
                return all_notes
        
        # 情况2：笔记内容发生变化
        changed_notes = []
        for note in all_notes:
            if self._note_content_changed(note):
                changed_notes.append(note)
                notes_to_process.append(note)
        
        if changed_notes:
            print(f"📝 检测到 {len(changed_notes)} 个笔记内容变化")
        
        # 如果没有变化，返回空列表
        if not notes_to_process:
            print("✅ 所有笔记都是最新的，无需增强")
        
        return notes_to_process
    
    def _note_content_changed(self, note: Dict) -> bool:
        """检查笔记内容是否发生变化"""
        file_path = note['file_path']
        current_hash = self._get_content_hash(note['content'])
        stored_hash = self.tracking_data['note_hashes'].get(file_path)
        
        return stored_hash != current_hash
    
    def _get_content_hash(self, content: str) -> str:
        """获取内容的MD5哈希值"""
        # 标准化内容后计算哈希
        normalized_content = self._normalize_content_for_hash(content)
        return hashlib.md5(normalized_content.encode('utf-8')).hexdigest()
    
    def _normalize_content_for_hash(self, content: str) -> str:
        """标准化内容用于哈希计算"""
        import re
        
        # 移除时间戳、日期等容易变化的内容
        content = re.sub(r'\d{4}-\d{2}-\d{2}', '', content)
        content = re.sub(r'\d{2}:\d{2}:\d{2}', '', content)
        
        # 标准化空白字符
        content = re.sub(r'\s+', ' ', content.strip())
        
        return content
    
    def update_tracking_after_enhancement(self, processed_notes: List[Dict], concept_manager) -> None:
        """增强完成后更新追踪信息"""
        # 更新笔记哈希
        for note in processed_notes:
            file_path = note['file_path']
            content_hash = self._get_content_hash(note['content'])
            self.tracking_data['note_hashes'][file_path] = content_hash
        
        # 更新概念数量
        current_concept_count = len(concept_manager.concept_database) if concept_manager.concept_database else 0
        self.tracking_data['concept_count_at_last_enhancement'] = current_concept_count
        self.tracking_data['last_full_enhancement'] = datetime.now().isoformat()
        
        # 记录增强历史
        self.tracking_data['enhancement_history'].append({
            'timestamp': datetime.now().isoformat(),
            'processed_notes': len(processed_notes),
            'total_concepts': current_concept_count,
            'type': 'incremental' if processed_notes else 'full'
        })
        
        self.save_tracking_data()
        print(f"📊 增量追踪已更新: {len(processed_notes)} 个笔记, {current_concept_count} 个概念")
    
    def force_full_rebuild(self) -> None:
        """强制重置追踪状态，下次将进行完整增强"""
        self.tracking_data['note_hashes'] = {}
        self.tracking_data['concept_count_at_last_enhancement'] = 0
        self.tracking_data['last_full_enhancement'] = None
        self.save_tracking_data()
        print("🔄 已重置增量追踪状态，下次将进行完整增强")