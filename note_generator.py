import os
import yaml
from datetime import datetime
from typing import Dict, Any

class ObsidianNoteGenerator:
    def __init__(self, output_path: str):
        self.output_path = output_path
        os.makedirs(output_path, exist_ok=True)
    
    def create_note_file(self, note_data: Dict[str, Any], output_path: str = None) -> str:
        """创建单个笔记文件"""
        yaml_data = note_data['yaml']
        content = note_data['content']
        
        # 使用指定的输出路径或默认路径
        target_path = output_path or self.output_path
        
        # 生成文件名
        title = yaml_data['title']
        safe_filename = self._make_safe_filename(title)
        file_path = os.path.join(target_path, f"{safe_filename}.md")
        
        # 添加创建日期
        yaml_data['created'] = datetime.now().strftime('%Y-%m-%d')
        
        # 处理时间戳链接（如果有课程URL）
        course_url = yaml_data.get('course_url', '')
        if course_url:
            from timestamp_processor import TimestampProcessor
            content = TimestampProcessor.process_content_timestamps(content, course_url)
        
        # 生成完整文件内容
        full_content = self._generate_full_content(yaml_data, content)
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        print(f"✅ 创建笔记: {os.path.basename(target_path)}/{safe_filename}.md")
        return file_path
    
    def _make_safe_filename(self, title: str) -> str:
        """生成安全的文件名"""
        # 移除不安全字符
        unsafe_chars = '<>:"/\\|?*'
        safe_filename = title
        for char in unsafe_chars:
            safe_filename = safe_filename.replace(char, '_')
        
        # 限制长度
        return safe_filename[:100]
    
    def _generate_full_content(self, yaml_data: Dict, content: str) -> str:
        """生成完整的文件内容"""
        # 生成YAML前置元数据
        yaml_content = yaml.dump(yaml_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        return f"""---
{yaml_content}---

{content}
"""