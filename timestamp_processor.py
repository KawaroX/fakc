import re
from typing import Optional

class TimestampProcessor:
    """处理时间戳和链接的工具类"""
    
    @staticmethod
    def time_to_seconds(time_str: str) -> Optional[float]:
        """
        将时间字符串转换为秒数 (支持毫秒)
        支持格式: HH:MM:SS, MM:SS, MM:SS.mm, SS
        """
        try:
            time_str = time_str.strip()
            
            # 检查是否包含毫秒
            if '.' in time_str:
                all_parts = time_str.split(':')
                if len(all_parts) == 2:  # MM:SS.mm
                    minutes = int(all_parts[0])
                    seconds_float = float(all_parts[1])
                    return minutes * 60 + seconds_float
                elif len(all_parts) == 3:  # HH:MM:SS.mm
                    hours = int(all_parts[0])
                    minutes = int(all_parts[1])
                    seconds_float = float(all_parts[2])
                    return hours * 3600 + minutes * 60 + seconds_float
                elif len(all_parts) == 1: # SS.mm
                    return float(time_str)
                else:
                    return None
            else:  # 不包含毫秒，按原有逻辑处理
                parts = time_str.split(':')
                if len(parts) == 3:  # HH:MM:SS
                    hours, minutes, seconds = map(int, parts)
                    return float(hours * 3600 + minutes * 60 + seconds)
                elif len(parts) == 2:  # MM:SS
                    minutes, seconds = map(int, parts)
                    return float(minutes * 60 + seconds)
                elif len(parts) == 1:  # SS
                    return float(parts[0])
                else:
                    return None
        except (ValueError, IndexError):
            return None
    
    @staticmethod
    def create_timestamp_link(timestamp: str, course_url: str) -> str:
        """
        创建带时间戳的课程链接
        
        Args:
            timestamp: 时间戳字符串，如 "12:34", "01:23:45", "12:34.56"
            course_url: 课程视频链接
            
        Returns:
            格式化的链接，如 "⏰ [12:34.56](URL&t=754)"
        """
        if not course_url:
            return f"⏰ [{timestamp}]"
        
        seconds_float = TimestampProcessor.time_to_seconds(timestamp)
        if seconds_float is None:
            return f"⏰ [{timestamp}]"
        
        # 视频平台通常只支持整数秒，所以将浮点数秒转换为整数
        seconds = int(seconds_float)
        
        # 处理不同视频平台的时间戳格式
        if 'youtube.com' in course_url or 'youtu.be' in course_url:
            # YouTube格式: &t=123s 或 ?t=123s
            separator = '&' if '?' in course_url else '?'
            return f"⏰ [{timestamp}]({course_url}{separator}t={seconds}s)"
        elif 'bilibili.com' in course_url:
            # B站格式: &t=123
            separator = '&' if '?' in course_url else '?'
            return f"⏰ [{timestamp}]({course_url}{separator}t={seconds})"
        else:
            # 通用格式: &t=123
            separator = '&' if '?' in course_url else '?'
            return f"⏰ [{timestamp}]({course_url}{separator}t={seconds})"
    
    @staticmethod
    def process_content_timestamps(content: str, course_url: str) -> str:
        """
        处理笔记内容中的所有时间戳，将其转换为链接
        
        Args:
            content: 笔记内容
            course_url: 课程视频链接
            
        Returns:
            处理后的内容
        """
        if not course_url:
            return content
        
        # 匹配 ⏰ [HH:MM:SS], ⏰ [MM:SS], ⏰ [MM:SS.mm] 格式
        # \d{1,2} 匹配1或2位数字 (小时或分钟)
        # :\d{2} 匹配冒号和两位数字 (秒)
        # (?:\.\d{1,3})? 匹配可选的毫秒部分 (. 后跟1到3位数字)
        # (?::\d{2})? 匹配可选的HH:MM:SS中的HH部分
        timestamp_pattern = r'⏰ \[(\d{1,2}:\d{2}(?:\.\d{1,3})?(?::\d{2}(?:\.\d{1,3})?)?)\]'
        
        def replace_timestamp(match):
            timestamp = match.group(1)
            return TimestampProcessor.create_timestamp_link(timestamp, course_url)
        
        return re.sub(timestamp_pattern, replace_timestamp, content)
