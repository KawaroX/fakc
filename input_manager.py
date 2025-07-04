import os
import re
from typing import Dict
from config import Config

class InputManager:
    @staticmethod
    def extract_url_from_text(text: str) -> str:
        """
        从文本中提取第一个URL。
        Args:
            text: 包含URL的文本。
        Returns:
            提取到的URL字符串，如果没有找到则返回空字符串。
        """
        # 匹配http或https开头的URL
        match = re.search(r'https?://[^\s]+', text)
        if match:
            return match.group(0)
        return ""

    def get_subtitle_info(self) -> Dict[str, str]:
        """交互式获取字幕文件信息"""
        print("=== 法考字幕处理器 ===")
        
        while True:
            file_path = input("请输入字幕文件路径: ").strip()
            if self.validate_file_exists(file_path):
                break
            print("❌ 文件不存在，请重新输入")
        
        # 显示可用科目
        print("\n📚 可用科目:")
        available_subjects = Config.list_available_subjects()
        for i, subject in enumerate(available_subjects, 1):
            folder_name = Config.get_subject_folder_name(subject)
            print(f"  {i:2d}. {subject} -> {folder_name}")
        
        print(f"  {len(available_subjects)+1:2d}. 其他（手动输入）")
        
        # 选择科目
        while True:
            try:
                choice = input(f"\n请选择科目 (1-{len(available_subjects)+1}): ").strip()
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(available_subjects):
                    subject = available_subjects[choice_num - 1]
                    break
                elif choice_num == len(available_subjects) + 1:
                    subject = input("请输入科目名称: ").strip()
                    if subject:
                        break
                    print("❌ 科目名称不能为空")
                else:
                    print(f"❌ 请输入 1-{len(available_subjects)+1} 之间的数字")
            except ValueError:
                print("❌ 请输入有效数字")
        
        episode_info = input("请输入集数/课程信息 (如: 第10集-物权法基础): ").strip()
        
        # 新增：输入课程链接，并自动提取URL
        raw_course_url = input("请输入课程视频链接 (可选，直接回车跳过): ").strip()
        course_url = self.extract_url_from_text(raw_course_url)
        if not course_url:
            course_url = ""
        
        # 确保科目目录存在
        Config.ensure_directories(subject)
        
        return {
            'file_path': file_path,
            'subject': subject,
            'subject_folder': Config.get_subject_folder_name(subject),
            'episode_info': episode_info,
            'source': f"{subject}-{episode_info}",
            'output_path': Config.get_output_path(subject),
            'course_url': course_url
        }
    
    def validate_file_exists(self, file_path: str) -> bool:
        """验证文件是否存在"""
        # 移除路径两端的引号，以防用户输入时为了处理空格而添加引号
        cleaned_file_path = file_path.strip('"\'')
        return os.path.isfile(cleaned_file_path)
    
    def read_subtitle_file(self, file_path: str) -> str:
        """读取字幕文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    return f.read()
            except UnicodeDecodeError:
                # 再尝试其他编码
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    return f.read()
