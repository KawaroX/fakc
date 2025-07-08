"""
时间解析工具类 - time_parser.py

负责解析各种时间格式，转换为秒数进行计算
支持的格式：MM:SS.mm-MM:SS.mm 和 HH:MM:SS.mm-HH:MM:SS.mm
"""

import re
from typing import Tuple, Optional, Union
from dataclasses import dataclass


@dataclass
class TimeRange:
    """时间范围数据类"""
    start: float  # 开始时间（秒）
    end: float    # 结束时间（秒）
    kp_ids: list  # 关联的知识点ID列表
    
    def __post_init__(self):
        """确保开始时间不大于结束时间"""
        if self.start > self.end:
            self.start, self.end = self.end, self.start
    
    @property
    def duration(self) -> float:
        """返回时间段长度（秒）"""
        return self.end - self.start
    
    def overlaps_with(self, other: 'TimeRange') -> bool:
        """检查是否与另一个时间范围重叠"""
        return not (self.end < other.start or self.start > other.end)
    
    def is_adjacent_to(self, other: 'TimeRange', max_gap: float = 5.0) -> bool:
        """检查是否与另一个时间范围相邻（间隔小于max_gap秒）"""
        gap = min(abs(self.end - other.start), abs(other.end - self.start))
        return gap <= max_gap
    
    def merge_with(self, other: 'TimeRange') -> 'TimeRange':
        """与另一个时间范围合并"""
        return TimeRange(
            start=min(self.start, other.start),
            end=max(self.end, other.end),
            kp_ids=list(set(self.kp_ids + other.kp_ids))
        )


class TimeParser:
    """时间解析器类"""
    
    # 时间格式正则表达式
    TIME_PATTERNS = {
        # HH:MM:SS.mmm 格式
        'hms_ms': re.compile(r'(\d{1,2}):(\d{2}):(\d{2})\.(\d{1,3})'),
        # HH:MM:SS 格式  
        'hms': re.compile(r'(\d{1,2}):(\d{2}):(\d{2})'),
        # MM:SS.mmm 格式
        'ms_ms': re.compile(r'(\d{1,2}):(\d{2})\.(\d{1,3})'),
        # MM:SS 格式
        'ms': re.compile(r'(\d{1,2}):(\d{2})'),
        # SS.mmm 格式
        's_ms': re.compile(r'(\d{1,2})\.(\d{1,3})'),
        # SS 格式
        's': re.compile(r'(\d{1,2})'),
    }
    
    # 时间范围分隔符
    RANGE_SEPARATORS = ['-', '~', 'to', '至', '到']
    
    @classmethod
    def parse_time_string(cls, time_str: str) -> Optional[float]:
        """
        解析单个时间字符串为秒数
        
        Args:
            time_str: 时间字符串，如 "12:34.56" 或 "01:23:45.67"
            
        Returns:
            时间对应的秒数，解析失败返回None
        """
        if not time_str or not isinstance(time_str, str):
            return None
        
        time_str = time_str.strip()
        
        # 尝试各种格式
        for pattern_name, pattern in cls.TIME_PATTERNS.items():
            match = pattern.fullmatch(time_str)
            if match:
                try:
                    return cls._convert_match_to_seconds(match, pattern_name)
                except (ValueError, IndexError):
                    continue
        
        return None
    
    @classmethod
    def _convert_match_to_seconds(cls, match, pattern_name: str) -> float:
        """将正则匹配结果转换为秒数"""
        groups = match.groups()
        
        if pattern_name == 'hms_ms':
            # HH:MM:SS.mmm
            hours, minutes, seconds, milliseconds = map(int, groups)
            return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
            
        elif pattern_name == 'hms':
            # HH:MM:SS
            hours, minutes, seconds = map(int, groups)
            return hours * 3600 + minutes * 60 + seconds
            
        elif pattern_name == 'ms_ms':
            # MM:SS.mmm
            minutes, seconds, milliseconds = map(int, groups)
            return minutes * 60 + seconds + milliseconds / 1000
            
        elif pattern_name == 'ms':
            # MM:SS
            minutes, seconds = map(int, groups)
            return minutes * 60 + seconds
            
        elif pattern_name == 's_ms':
            # SS.mmm
            seconds, milliseconds = map(int, groups)
            return seconds + milliseconds / 1000
            
        elif pattern_name == 's':
            # SS
            seconds = int(groups[0])
            return float(seconds)
        
        raise ValueError(f"Unknown pattern: {pattern_name}")
    
    @classmethod
    def parse_time_range(cls, range_str: str, kp_id: str = None) -> Optional[TimeRange]:
        """
        解析时间范围字符串
        
        Args:
            range_str: 时间范围字符串，如 "12:34.56-15:67.89"
            kp_id: 关联的知识点ID
            
        Returns:
            TimeRange对象，解析失败返回None
        """
        if not range_str or not isinstance(range_str, str):
            return None
        
        range_str = range_str.strip()
        
        # 尝试各种分隔符
        for separator in cls.RANGE_SEPARATORS:
            if separator in range_str:
                parts = range_str.split(separator, 1)
                if len(parts) == 2:
                    start_str, end_str = [p.strip() for p in parts]
                    start_seconds = cls.parse_time_string(start_str)
                    end_seconds = cls.parse_time_string(end_str)
                    
                    if start_seconds is not None and end_seconds is not None:
                        kp_ids = [kp_id] if kp_id else []
                        return TimeRange(start_seconds, end_seconds, kp_ids)
        
        # 如果没有分隔符，尝试解析为单个时间点（持续时间设为0）
        single_time = cls.parse_time_string(range_str)
        if single_time is not None:
            kp_ids = [kp_id] if kp_id else []
            return TimeRange(single_time, single_time, kp_ids)
        
        return None
    
    @classmethod
    def seconds_to_time_string(cls, seconds: float, include_ms: bool = True) -> str:
        """
        将秒数转换为时间字符串
        
        Args:
            seconds: 秒数
            include_ms: 是否包含毫秒
            
        Returns:
            格式化的时间字符串
        """
        if seconds < 0:
            seconds = 0
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        
        if include_ms:
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
            else:
                return f"{minutes:02d}:{secs:06.3f}"
        else:
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{int(secs):02d}"
            else:
                return f"{minutes:02d}:{int(secs):02d}"
    
    @classmethod
    def validate_time_range(cls, time_range: TimeRange) -> bool:
        """
        验证时间范围的有效性
        
        Args:
            time_range: 要验证的时间范围
            
        Returns:
            是否有效
        """
        if not isinstance(time_range, TimeRange):
            return False
        
        # 检查时间值的合理性
        if time_range.start < 0 or time_range.end < 0:
            return False
        
        if time_range.start > time_range.end:
            return False
        
        # 检查时间范围不要过长（超过24小时认为异常）
        if time_range.duration > 24 * 3600:
            return False
        
        return True
    
    @classmethod
    def normalize_time_ranges(cls, time_ranges: list[TimeRange]) -> list[TimeRange]:
        """
        标准化时间范围列表：排序、合并重叠和相邻的范围
        
        Args:
            time_ranges: 时间范围列表
            
        Returns:
            标准化后的时间范围列表
        """
        if not time_ranges:
            return []
        
        # 过滤无效的时间范围
        valid_ranges = [tr for tr in time_ranges if cls.validate_time_range(tr)]
        
        if not valid_ranges:
            return []
        
        # 按开始时间排序
        valid_ranges.sort(key=lambda tr: tr.start)
        
        # 合并重叠和相邻的范围
        merged = [valid_ranges[0]]
        
        for current in valid_ranges[1:]:
            last_merged = merged[-1]
            
            # 检查是否重叠或相邻
            if (last_merged.overlaps_with(current) or 
                last_merged.is_adjacent_to(current)):
                # 合并范围
                merged[-1] = last_merged.merge_with(current)
            else:
                # 添加新范围
                merged.append(current)
        
        return merged
    
    @classmethod
    def add_buffer_to_ranges(cls, time_ranges: list[TimeRange], 
                           buffer_seconds: float = 30.0,
                           min_time: float = 0.0,
                           max_time: float = None) -> list[TimeRange]:
        """
        为时间范围添加缓冲区
        
        Args:
            time_ranges: 时间范围列表
            buffer_seconds: 缓冲区大小（秒）
            min_time: 最小时间边界
            max_time: 最大时间边界
            
        Returns:
            添加缓冲区后的时间范围列表
        """
        if not time_ranges:
            return []
        
        buffered_ranges = []
        
        for tr in time_ranges:
            buffered_start = max(min_time, tr.start - buffer_seconds)
            buffered_end = tr.end + buffer_seconds
            
            if max_time is not None:
                buffered_end = min(max_time, buffered_end)
            
            buffered_ranges.append(TimeRange(
                start=buffered_start,
                end=buffered_end,
                kp_ids=tr.kp_ids.copy()
            ))
        
        # 重新标准化，合并因缓冲区而重叠的范围
        return cls.normalize_time_ranges(buffered_ranges)


def test_time_parser():
    """测试时间解析器的功能"""
    # 测试单个时间解析
    test_cases = [
        ("12:34.56", 12*60 + 34.56),
        ("01:23:45.67", 1*3600 + 23*60 + 45.67),
        ("05:30", 5*60 + 30),
        ("02:15:30", 2*3600 + 15*60 + 30),
        ("45.5", 45.5),
        ("120", 120),
    ]
    
    print("测试单个时间解析：")
    for time_str, expected in test_cases:
        result = TimeParser.parse_time_string(time_str)
        print(f"{time_str} -> {result} (期望: {expected})")
        assert abs(result - expected) < 0.001, f"解析失败: {time_str}"
    
    # 测试时间范围解析
    range_cases = [
        ("12:34.56-15:67.89", "kp001"),
        ("01:23:45-02:15:30", "kp002"),
        ("05:30~07:45", "kp003"),
    ]
    
    print("\n测试时间范围解析：")
    for range_str, kp_id in range_cases:
        result = TimeParser.parse_time_range(range_str, kp_id)
        if result:
            print(f"{range_str} -> {result.start:.3f}-{result.end:.3f}s (kp: {result.kp_ids})")
        else:
            print(f"{range_str} -> 解析失败")
    
    # 测试时间范围合并
    print("\n测试时间范围合并：")
    ranges = [
        TimeRange(60, 120, ["kp001"]),
        TimeRange(115, 180, ["kp002"]),  # 与第一个重叠
        TimeRange(200, 250, ["kp003"]),  # 与第二个相邻
    ]
    
    merged = TimeParser.normalize_time_ranges(ranges)
    for i, tr in enumerate(merged):
        print(f"合并后范围{i+1}: {tr.start:.1f}-{tr.end:.1f}s, kp_ids: {tr.kp_ids}")
    
    print("\n✅ 所有测试通过！")


if __name__ == "__main__":
    test_time_parser()
