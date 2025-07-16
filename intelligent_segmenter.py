# intelligent_segmenter.py - 修改版本：支持按知识点独立分段
import re
import json
from typing import List, Dict, Any, Optional, NamedTuple
from dataclasses import dataclass

# 时间范围类（保持不变）
@dataclass
class TimeRange:
    start: float
    end: float
    kp_ids: List[str]  # 关联的知识点ID列表
    
    @property
    def duration(self) -> float:
        return self.end - self.start

# 分段类（保持不变）
@dataclass
class Segment:
    text: str
    time_range: TimeRange
    knowledge_points: List[str]
    token_count: int
    buffer_info: Dict[str, Any] = None

class TimeParser:
    """时间解析工具类（保持不变）"""
    
    @staticmethod
    def parse_time_to_seconds(time_str: str) -> Optional[float]:
        """将时间字符串转换为秒数"""
        if not time_str:
            return None
        
        # 移除可能的方括号
        time_str = time_str.strip('[]')
        
        # 匹配不同的时间格式
        patterns = [
            r'^(\d{1,2}):(\d{2})\.(\d{1,3})$',  # MM:SS.mmm
            r'^(\d{1,2}):(\d{2}):(\d{2})\.(\d{1,3})$',  # HH:MM:SS.mmm
            r'^(\d{1,2}):(\d{2}):(\d{2}),(\d{1,3})$',  # HH:MM:SS,mmm (SRT格式)
            r'^(\d{1,2}):(\d{2})$',  # MM:SS
            r'^(\d{1,2}):(\d{2}):(\d{2})$',  # HH:MM:SS
        ]
        
        for pattern in patterns:
            match = re.match(pattern, time_str)
            if match:
                groups = match.groups()
                if len(groups) == 3:  # MM:SS.mmm
                    minutes, seconds, milliseconds = groups
                    return int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000
                elif len(groups) == 4:  # HH:MM:SS.mmm
                    hours, minutes, seconds, milliseconds = groups
                    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000
                elif len(groups) == 2:  # MM:SS
                    minutes, seconds = groups
                    return int(minutes) * 60 + int(seconds)
        
        return None
    
    @staticmethod
    def parse_time_range(time_range_str: str, kp_id: str) -> Optional[TimeRange]:
        """解析时间范围字符串"""
        if not time_range_str:
            return None
        
        # 匹配时间范围格式：start-end 或 start--end
        range_match = re.search(r'(.+?)-{1,2}(.+)', time_range_str)
        if not range_match:
            return None
        
        start_str = range_match.group(1).strip()
        end_str = range_match.group(2).strip()
        
        start_seconds = TimeParser.parse_time_to_seconds(start_str)
        end_seconds = TimeParser.parse_time_to_seconds(end_str)
        
        if start_seconds is not None and end_seconds is not None:
            # 确保开始时间小于结束时间
            if start_seconds > end_seconds:
                start_seconds, end_seconds = end_seconds, start_seconds
            
            return TimeRange(start_seconds, end_seconds, [kp_id])
        
        return None

class SubtitleParser:
    """字幕解析器（保持不变）"""
    
    @staticmethod
    def parse_lrc_content(content: str) -> List[Dict]:
        """解析LRC格式字幕"""
        lines = []
        lrc_pattern = r'\[(\d{1,2}:\d{2}(?:\.\d{1,3})?)\](.+)'
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            match = re.search(lrc_pattern, line)
            if match:
                time_str = match.group(1)
                text = match.group(2).strip()
                
                timestamp = TimeParser.parse_time_to_seconds(time_str)
                if timestamp is not None:
                    lines.append({
                        'timestamp': timestamp,
                        'text': text,
                        'original_time': time_str
                    })
        
        return lines
    
    @staticmethod
    def parse_srt_content(content: str) -> List[Dict]:
        """解析SRT格式字幕"""
        lines = []
        blocks = content.split('\n\n')
        
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            
            block_lines = block.split('\n')
            if len(block_lines) < 3:
                continue
            
            # 解析时间行
            time_line = block_lines[1]
            time_match = re.search(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', time_line)
            if not time_match:
                continue
            
            start_time_str = time_match.group(1).replace(',', '.')
            end_time_str = time_match.group(2).replace(',', '.')
            
            start_timestamp = TimeParser.parse_time_to_seconds(start_time_str)
            end_timestamp = TimeParser.parse_time_to_seconds(end_time_str)
            
            if start_timestamp is not None and end_timestamp is not None:
                # 合并文本行
                text = ' '.join(block_lines[2:]).strip()
                
                lines.append({
                    'timestamp': start_timestamp,
                    'end_timestamp': end_timestamp,
                    'text': text,
                    'original_time': f"{time_match.group(1)}-{time_match.group(2)}"
                })
        
        return lines
    
    @staticmethod
    def parse_txt_content(content: str) -> List[Dict]:
        """解析普通文本（按行处理）"""
        lines = []
        for i, line in enumerate(content.split('\n')):
            line = line.strip()
            if line:
                lines.append({
                    'timestamp': i,  # 使用行号作为虚拟时间戳
                    'text': line,
                    'original_time': f"line_{i+1}"
                })
        
        return lines
    
    @classmethod
    def parse_subtitle_content(cls, content: str, file_format: str = 'auto') -> List[Dict]:
        """解析字幕内容"""
        if file_format == 'auto':
            # 自动检测格式
            if re.search(r'\[\d{1,2}:\d{2}(?:\.\d{1,3})?\]', content):
                file_format = 'lrc'
            elif re.search(r'\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}', content):
                file_format = 'srt'
            else:
                file_format = 'txt'
        
        # 根据格式解析
        if file_format == 'lrc':
            return cls.parse_lrc_content(content)
        elif file_format == 'srt':
            return cls.parse_srt_content(content)
        else:  # txt 或其他
            return cls.parse_txt_content(content)


class IntelligentSegmenter:
    """智能分段处理器 - 修改版本：支持按知识点独立分段"""
    
    def __init__(self, buffer_seconds: float = 30.0, max_gap_seconds: float = 5.0):
        """
        初始化分段器
        
        Args:
            buffer_seconds: 缓冲区大小（秒）
            max_gap_seconds: 最大间隔时间（秒），小于此值的时间段将合并
        """
        self.buffer_seconds = buffer_seconds
        self.max_gap_seconds = max_gap_seconds
        self.subtitle_parser = SubtitleParser()
    
    def segment_by_knowledge_points(self, subtitle_content: str, analysis_result: Dict[str, Any],
                                  file_format: str = 'auto') -> List[Segment]:
        """
        按知识点独立分段（新方法）
        
        Args:
            subtitle_content: 字幕文件内容
            analysis_result: 第一步分析结果
            file_format: 字幕文件格式
            
        Returns:
            每个知识点对应一个分段的结果列表
        """
        try:
            print(f"🔧 按知识点独立分段处理 (格式: {file_format})")
            
            # 1. 解析字幕内容
            subtitle_lines = self.subtitle_parser.parse_subtitle_content(subtitle_content, file_format)
            
            if not subtitle_lines:
                print("⚠️ 字幕内容解析为空，将使用完整内容作为fallback")
                return self._create_individual_fallback_segments(subtitle_content, analysis_result)
            
            print(f"✅ 解析到 {len(subtitle_lines)} 行字幕")
            
            # 2. 从分析结果中提取知识点时间范围
            print("🔍 提取各知识点的时间范围")
            individual_ranges = self._extract_individual_knowledge_point_ranges(analysis_result)
            
            if not individual_ranges:
                print("⚠️ 未找到有效的时间范围，将使用完整内容")
                return self._create_individual_fallback_segments(subtitle_content, analysis_result)
            
            print(f"✅ 提取到 {len(individual_ranges)} 个独立知识点时间范围")
            
            # 3. 为每个知识点添加缓冲区（但不合并）
            print("🔧 为每个知识点添加独立缓冲区")
            max_duration = None
            if subtitle_lines and subtitle_lines[-1].get('timestamp'):
                max_duration = subtitle_lines[-1]['timestamp'] + 60  # 最后时间戳 + 1分钟缓冲
            
            buffered_ranges = self._add_individual_buffers(individual_ranges, max_duration)
            print(f"✅ 处理后得到 {len(buffered_ranges)} 个独立时间段")
            
            # 4. 为每个知识点提取对应的文本内容
            print("📝 为每个知识点提取对应字幕文本")
            segments = self._extract_individual_knowledge_point_texts(subtitle_lines, buffered_ranges)
            
            # 5. 统计和验证
            total_tokens = sum(seg.token_count for seg in segments)
            original_tokens = self._estimate_token_count(subtitle_content)
            
            print(f"📊 独立分段统计:")
            print(f"  - 知识点数量: {len(segments)}")
            print(f"  - 原始tokens: {original_tokens}")
            print(f"  - 分段后tokens: {total_tokens}")
            print(f"  - 每个知识点包含缓冲区内容")
            
            return segments
            
        except Exception as e:
            print(f"❌ 按知识点独立分段失败: {e}")
            return self._create_individual_fallback_segments(subtitle_content, analysis_result)
    
    def _extract_individual_knowledge_point_ranges(self, analysis_result: Dict[str, Any]) -> List[TimeRange]:
        """
        为每个知识点创建独立的时间范围
        
        Args:
            analysis_result: 第一步分析结果
            
        Returns:
            每个知识点对应一个独立时间范围的列表
        """
        individual_ranges = []
        
        # 从knowledge_points中提取时间范围
        knowledge_points = analysis_result.get('knowledge_points', [])
        
        for kp in knowledge_points:
            kp_id = kp.get('id', 'unknown')
            time_range_str = kp.get('time_range', '')
            
            if time_range_str:
                time_range = TimeParser.parse_time_range(time_range_str, kp_id)
                if time_range:
                    # 确保每个时间范围只包含一个知识点
                    time_range.kp_ids = [kp_id]
                    individual_ranges.append(time_range)
                    print(f"  ✅ {kp_id}: {time_range.start:.1f}-{time_range.end:.1f}s")
                else:
                    print(f"  ⚠️ 无法解析时间范围: {time_range_str} (知识点: {kp_id})")
            else:
                print(f"  ⚠️ 知识点 {kp_id} 没有时间范围信息")
        
        return individual_ranges
    
    def _add_individual_buffers(self, time_ranges: List[TimeRange], max_duration: Optional[float] = None) -> List[TimeRange]:
        """
        为每个知识点独立添加缓冲区（不合并重叠部分）
        
        Args:
            time_ranges: 原始时间范围列表
            max_duration: 最大时长限制
            
        Returns:
            添加缓冲区后的时间范围列表
        """
        buffered_ranges = []
        
        for time_range in time_ranges:
            # 添加缓冲区
            buffered_start = max(0, time_range.start - self.buffer_seconds)
            buffered_end = time_range.end + self.buffer_seconds
            
            # 应用最大时长限制
            if max_duration is not None:
                buffered_end = min(buffered_end, max_duration)
            
            buffered_range = TimeRange(
                start=buffered_start,
                end=buffered_end,
                kp_ids=time_range.kp_ids.copy()
            )
            
            buffered_ranges.append(buffered_range)
            
            print(f"  📍 {time_range.kp_ids[0]}: {time_range.start:.1f}-{time_range.end:.1f}s → {buffered_start:.1f}-{buffered_end:.1f}s (缓冲: ±{self.buffer_seconds}s)")
        
        return buffered_ranges
    
    def _extract_individual_knowledge_point_texts(self, subtitle_lines: List[Dict], time_ranges: List[TimeRange]) -> List[Segment]:
        """
        为每个知识点提取对应的字幕文本
        
        Args:
            subtitle_lines: 解析后的字幕行
            time_ranges: 时间范围列表（每个包含一个知识点）
            
        Returns:
            分段结果列表
        """
        segments = []
        
        for time_range in time_ranges:
            segment_text = []
            matched_lines = []
            kp_id = time_range.kp_ids[0]  # 每个时间范围只有一个知识点
            
            print(f"  🔍 处理知识点 {kp_id}: {time_range.start:.1f}-{time_range.end:.1f}s")
            
            # 如果是纯文本模式（没有时间戳），使用完整内容
            if not subtitle_lines or not subtitle_lines[0].get('timestamp'):
                print(f"    📝 没有时间戳信息，使用完整内容")
                full_text = '\n'.join([line.get('text', '') for line in subtitle_lines])
                segments.append(Segment(
                    text=full_text,
                    time_range=time_range,
                    knowledge_points=[kp_id],
                    token_count=self._estimate_token_count(full_text),
                    buffer_info={
                        'type': 'full_text',
                        'reason': 'no_timestamp',
                        'original_range': f"{time_range.start:.1f}-{time_range.end:.1f}s"
                    }
                ))
                continue
            
            # 对于有时间戳的字幕，按时间范围提取
            for line in subtitle_lines:
                timestamp = line['timestamp']
                
                # 检查时间戳是否在目标范围内
                if time_range.start <= timestamp <= time_range.end:
                    # 保留原始时间戳（LRC格式）
                    segment_text.append(f"[{line['original_time']}] {line['text']}")
                    matched_lines.append(line)
                # 对于SRT格式，还要检查结束时间
                elif 'end_timestamp' in line:
                    end_timestamp = line['end_timestamp']
                    # 如果字幕行与时间范围有重叠，则包含
                    if not (end_timestamp < time_range.start or timestamp > time_range.end):
                        # 保留原始时间戳（SRT格式）
                        segment_text.append(f"[{line['original_time']}] {line['text']}")
                        matched_lines.append(line)
            
            # 创建分段
            if segment_text:
                text = '\n'.join(segment_text)
                buffer_info = {
                    'type': 'individual_segment',
                    'knowledge_point': kp_id,
                    'original_range': f"{time_range.start:.1f}-{time_range.end:.1f}s",
                    'matched_lines': len(matched_lines),
                    'buffer_added': self.buffer_seconds,
                    'first_timestamp': matched_lines[0]['timestamp'] if matched_lines else None,
                    'last_timestamp': matched_lines[-1]['timestamp'] if matched_lines else None
                }
                
                segments.append(Segment(
                    text=text,
                    time_range=time_range,
                    knowledge_points=[kp_id],
                    token_count=self._estimate_token_count(text),
                    buffer_info=buffer_info
                ))
                
                print(f"    ✅ 提取到 {len(matched_lines)} 行字幕，{self._estimate_token_count(text)} tokens")
            else:
                # 如果没有匹配的文本，创建空分段并记录警告
                print(f"    ⚠️ 没有匹配的字幕内容")
                segments.append(Segment(
                    text="",
                    time_range=time_range,
                    knowledge_points=[kp_id],
                    token_count=0,
                    buffer_info={
                        'type': 'empty_segment',
                        'knowledge_point': kp_id,
                        'reason': 'no_matching_text',
                        'original_range': f"{time_range.start:.1f}-{time_range.end:.1f}s"
                    }
                ))
        
        return segments
    
    def _create_individual_fallback_segments(self, subtitle_content: str, analysis_result: Dict[str, Any]) -> List[Segment]:
        """
        为每个知识点创建独立的fallback分段（使用完整内容）
        
        Args:
            subtitle_content: 完整字幕内容
            analysis_result: 分析结果
            
        Returns:
            每个知识点对应一个使用完整内容的分段列表
        """
        knowledge_points = analysis_result.get('knowledge_points', [])
        segments = []
        
        print(f"🔄 创建 {len(knowledge_points)} 个独立fallback分段")
        
        for kp in knowledge_points:
            kp_id = kp.get('id', 'unknown')
            
            fallback_segment = Segment(
                text=subtitle_content,
                time_range=TimeRange(0, 0, [kp_id]),  # 时间范围设为0表示全部内容
                knowledge_points=[kp_id],
                token_count=self._estimate_token_count(subtitle_content),
                buffer_info={
                    'type': 'individual_fallback',
                    'knowledge_point': kp_id,
                    'reason': 'segmentation_failed',
                    'original_token_count': self._estimate_token_count(subtitle_content)
                }
            )
            
            segments.append(fallback_segment)
            print(f"  📝 知识点 {kp_id}: 使用完整内容 ({self._estimate_token_count(subtitle_content)} tokens)")
        
        return segments
    
    def _estimate_token_count(self, text: str) -> int:
        """
        估算文本的token数量
        
        Args:
            text: 要估算的文本
            
        Returns:
            估算的token数量
        """
        if not text:
            return 0
        
        # 简单估算：中文字符数 + 英文单词数 * 1.3
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        
        # 考虑标点符号和其他字符
        other_chars = len(text) - chinese_chars - sum(len(word) for word in re.findall(r'\b[a-zA-Z]+\b', text))
        
        estimated_tokens = chinese_chars + int(english_words * 1.3) + int(other_chars * 0.5)
        
        return max(estimated_tokens, 1)  # 至少1个token
    
    def segment_by_knowledge_points(self, subtitle_content: str, analysis_result: Dict[str, Any],
                              file_format: str = 'auto') -> List[Segment]:
        """
        按知识点独立分段（新方法）
        每个知识点对应一个独立的段落，添加缓冲区但不合并
        """
        try:
            print(f"🔧 按知识点独立分段处理 (格式: {file_format})")
            
            # 1. 解析字幕内容
            subtitle_lines = self.subtitle_parser.parse_subtitle_content(subtitle_content, file_format)
            
            if not subtitle_lines:
                print("⚠️ 字幕内容解析为空，将使用完整内容作为fallback")
                return self._create_individual_fallback_segments(subtitle_content, analysis_result)
            
            print(f"✅ 解析到 {len(subtitle_lines)} 行字幕")
            
            # 2. 从分析结果中提取知识点时间范围
            print("🔍 提取各知识点的时间范围")
            individual_ranges = self._extract_individual_knowledge_point_ranges(analysis_result)
            
            if not individual_ranges:
                print("⚠️ 未找到有效的时间范围，将使用完整内容")
                return self._create_individual_fallback_segments(subtitle_content, analysis_result)
            
            print(f"✅ 提取到 {len(individual_ranges)} 个独立知识点时间范围")
            
            # 3. 为每个知识点添加独立缓冲区（但不合并）
            print("🔧 为每个知识点添加独立缓冲区")
            max_duration = None
            if subtitle_lines and subtitle_lines[-1].get('timestamp'):
                max_duration = subtitle_lines[-1]['timestamp'] + 60
            
            buffered_ranges = self._add_individual_buffers(individual_ranges, max_duration)
            print(f"✅ 处理后得到 {len(buffered_ranges)} 个独立时间段")
            
            # 4. 为每个知识点提取对应的文本内容
            print("📝 为每个知识点提取对应字幕文本")
            segments = self._extract_individual_knowledge_point_texts(subtitle_lines, buffered_ranges)
            
            # 5. 统计和验证
            total_tokens = sum(seg.token_count for seg in segments)
            original_tokens = self._estimate_token_count(subtitle_content)
            
            print(f"📊 独立分段统计:")
            print(f"  - 知识点数量: {len(segments)}")
            print(f"  - 原始tokens: {original_tokens}")
            print(f"  - 分段后tokens: {total_tokens}")
            print(f"  - 每个知识点包含缓冲区内容")
            
            return segments
            
        except Exception as e:
            print(f"❌ 按知识点独立分段失败: {e}")
            return self._create_individual_fallback_segments(subtitle_content, analysis_result)
    
    # 保留原有的方法以兼容现有代码
    def segment_subtitle_content(self, subtitle_content: str, analysis_result: Dict[str, Any],
                                file_format: str = 'auto') -> List[Segment]:
        """
        智能分段主入口方法（保持兼容，默认使用新方法）
        
        Args:
            subtitle_content: 字幕文件内容
            analysis_result: 第一步分析结果
            file_format: 字幕文件格式
            
        Returns:
            分段结果列表
        """
        # 默认使用新的按知识点独立分段方法
        return self.segment_by_knowledge_points(subtitle_content, analysis_result, file_format)
    
    def extract_time_ranges_from_analysis(self, analysis_result: Dict[str, Any]) -> List[TimeRange]:
        """
        从第一步分析结果中提取时间范围（保持兼容）
        
        Args:
            analysis_result: 第一步分析结果
            
        Returns:
            时间范围列表
        """
        return self._extract_individual_knowledge_point_ranges(analysis_result)
    
    def _extract_individual_knowledge_point_ranges(self, analysis_result: Dict[str, Any]) -> List[TimeRange]:
        """为每个知识点创建独立的时间范围"""
        individual_ranges = []
        knowledge_points = analysis_result.get('knowledge_points', [])
        
        for kp in knowledge_points:
            kp_id = kp.get('id', 'unknown')
            time_range_str = kp.get('time_range', '')
            
            if time_range_str:
                time_range = TimeParser.parse_time_range(time_range_str, kp_id)
                if time_range:
                    # 确保每个时间范围只包含一个知识点
                    time_range.kp_ids = [kp_id]
                    individual_ranges.append(time_range)
                    print(f"  ✅ {kp_id}: {time_range.start:.1f}-{time_range.end:.1f}s")
                else:
                    print(f"  ⚠️ 无法解析时间范围: {time_range_str} (知识点: {kp_id})")
            else:
                print(f"  ⚠️ 知识点 {kp_id} 没有时间范围信息")
        
        return individual_ranges

    def _add_individual_buffers(self, time_ranges: List[TimeRange], max_duration: Optional[float] = None) -> List[TimeRange]:
        """为每个知识点独立添加缓冲区（不合并重叠部分）"""
        buffered_ranges = []
        
        for time_range in time_ranges:
            # 添加缓冲区
            buffered_start = max(0, time_range.start - self.buffer_seconds)
            buffered_end = time_range.end + self.buffer_seconds
            
            # 应用最大时长限制
            if max_duration is not None:
                buffered_end = min(buffered_end, max_duration)
            
            buffered_range = TimeRange(
                start=buffered_start,
                end=buffered_end,
                kp_ids=time_range.kp_ids.copy()
            )
            
            buffered_ranges.append(buffered_range)
            
            print(f"  📍 {time_range.kp_ids[0]}: {time_range.start:.1f}-{time_range.end:.1f}s → {buffered_start:.1f}-{buffered_end:.1f}s (缓冲: ±{self.buffer_seconds}s)")
        
        return buffered_ranges

    def _extract_individual_knowledge_point_texts(self, subtitle_lines: List[Dict], time_ranges: List[TimeRange]) -> List[Segment]:
        """为每个知识点提取对应的字幕文本"""
        segments = []
        
        for time_range in time_ranges:
            segment_text = []
            matched_lines = []
            kp_id = time_range.kp_ids[0]  # 每个时间范围只有一个知识点
            
            print(f"  🔍 处理知识点 {kp_id}: {time_range.start:.1f}-{time_range.end:.1f}s")
            
            # 如果是纯文本模式（没有时间戳），使用完整内容
            if not subtitle_lines or not subtitle_lines[0].get('timestamp'):
                print(f"    📝 没有时间戳信息，使用完整内容")
                full_text = '\n'.join([line.get('text', '') for line in subtitle_lines])
                segments.append(Segment(
                    text=full_text,
                    time_range=time_range,
                    knowledge_points=[kp_id],
                    token_count=self._estimate_token_count(full_text),
                    buffer_info={
                        'type': 'full_text',
                        'reason': 'no_timestamp',
                        'original_range': f"{time_range.start:.1f}-{time_range.end:.1f}s"
                    }
                ))
                continue
            
            # 对于有时间戳的字幕，按时间范围提取
            for line in subtitle_lines:
                timestamp = line['timestamp']
                
                # 检查时间戳是否在目标范围内
                if time_range.start <= timestamp <= time_range.end:
                    segment_text.append(line['text'])
                    matched_lines.append(line)
                # 对于SRT格式，还要检查结束时间
                elif 'end_timestamp' in line:
                    end_timestamp = line['end_timestamp']
                    # 如果字幕行与时间范围有重叠，则包含
                    if not (end_timestamp < time_range.start or timestamp > time_range.end):
                        segment_text.append(line['text'])
                        matched_lines.append(line)
            
            # 创建分段
            if segment_text:
                text = '\n'.join(segment_text)
                buffer_info = {
                    'type': 'individual_segment',
                    'knowledge_point': kp_id,
                    'original_range': f"{time_range.start:.1f}-{time_range.end:.1f}s",
                    'matched_lines': len(matched_lines),
                    'buffer_added': self.buffer_seconds,
                    'first_timestamp': matched_lines[0]['timestamp'] if matched_lines else None,
                    'last_timestamp': matched_lines[-1]['timestamp'] if matched_lines else None
                }
                
                segments.append(Segment(
                    text=text,
                    time_range=time_range,
                    knowledge_points=[kp_id],
                    token_count=self._estimate_token_count(text),
                    buffer_info=buffer_info
                ))
                
                print(f"    ✅ 提取到 {len(matched_lines)} 行字幕，{self._estimate_token_count(text)} tokens")
            else:
                # 如果没有匹配的文本，创建空分段并记录警告
                print(f"    ⚠️ 没有匹配的字幕内容")
                segments.append(Segment(
                    text="",
                    time_range=time_range,
                    knowledge_points=[kp_id],
                    token_count=0,
                    buffer_info={
                        'type': 'empty_segment',
                        'knowledge_point': kp_id,
                        'reason': 'no_matching_text',
                        'original_range': f"{time_range.start:.1f}-{time_range.end:.1f}s"
                    }
                ))
        
        return segments

    def _create_individual_fallback_segments(self, subtitle_content: str, analysis_result: Dict[str, Any]) -> List[Segment]:
        """为每个知识点创建独立的fallback分段（使用完整内容）"""
        knowledge_points = analysis_result.get('knowledge_points', [])
        segments = []
        
        print(f"🔄 创建 {len(knowledge_points)} 个独立fallback分段")
        
        for kp in knowledge_points:
            kp_id = kp.get('id', 'unknown')
            
            fallback_segment = Segment(
                text=subtitle_content,
                time_range=TimeRange(0, 0, [kp_id]),  # 时间范围设为0表示全部内容
                knowledge_points=[kp_id],
                token_count=self._estimate_token_count(subtitle_content),
                buffer_info={
                    'type': 'individual_fallback',
                    'knowledge_point': kp_id,
                    'reason': 'segmentation_failed',
                    'original_token_count': self._estimate_token_count(subtitle_content)
                }
            )
            
            segments.append(fallback_segment)
            print(f"  📝 知识点 {kp_id}: 使用完整内容 ({self._estimate_token_count(subtitle_content)} tokens)")
        
        return segments
    
    def get_segments_summary(self, segments: List[Segment]) -> Dict[str, Any]:
        """
        获取分段结果的摘要信息
        
        Args:
            segments: 分段结果列表
            
        Returns:
            摘要信息字典
        """
        if not segments:
            return {'total_segments': 0, 'total_tokens': 0, 'knowledge_points': []}
        
        total_tokens = sum(seg.token_count for seg in segments)
        all_kp_ids = []
        for seg in segments:
            all_kp_ids.extend(seg.knowledge_points)
        unique_kp_ids = list(set(all_kp_ids))
        
        time_ranges = []
        for seg in segments:
            if seg.time_range.start != seg.time_range.end:  # 不是fallback的情况
                time_ranges.append({
                    'start': seg.time_range.start,
                    'end': seg.time_range.end,
                    'duration': seg.time_range.duration,
                    'knowledge_points': seg.knowledge_points
                })
        
        summary = {
            'total_segments': len(segments),
            'total_tokens': total_tokens,
            'knowledge_points': unique_kp_ids,
            'time_ranges': time_ranges,
            'total_duration': sum(tr['duration'] for tr in time_ranges),
            'avg_segment_tokens': total_tokens / len(segments) if segments else 0,
            'has_fallback': any(seg.buffer_info and seg.buffer_info.get('type', '').endswith('fallback') for seg in segments),
            'individual_segments': len([seg for seg in segments if seg.buffer_info and seg.buffer_info.get('type') == 'individual_segment']),
            'processing_mode': 'individual_knowledge_points'
        }
        
        return summary


def test_individual_segmentation():
    """测试按知识点独立分段功能"""
    print("🧪 测试按知识点独立分段功能")
    
    # 模拟第一步分析结果
    mock_analysis = {
        'knowledge_points': [
            {
                'id': 'KP001',
                'concept_name': '物权的概念',
                'time_range': '02:15.30-05:45.60'
            },
            {
                'id': 'KP002', 
                'concept_name': '物权的特征',
                'time_range': '06:00-08:30'
            },
            {
                'id': 'KP003',
                'concept_name': '物权变动',
                'time_range': '09:15-12:45'
            }
        ]
    }
    
    # 模拟LRC格式字幕
    mock_lrc_content = """
[01:30.00]大家好，今天我们来讲物权法的基础概念
[02:00.00]首先我们要明确什么是物权
[02:15.30]物权是指权利人依法对特定的物享有直接支配和排他的权利
[03:00.00]这个定义包含了几个关键要素
[03:30.00]第一是直接支配性，第二是排他性
[04:00.00]接下来我们看具体的例子
[05:00.00]比如所有权就是最典型的物权
[06:00.00]物权有哪些特征呢
[06:30.00]第一个特征是对世性，也就是说物权的效力及于任何人
[07:00.00]第二个特征是追及性，物无论转移到哪里，物权都能追及
[08:00.00]第三个特征是优先性，物权优先于债权
[09:15.00]现在我们来讲物权变动
[10:00.00]物权变动是指物权的设立、变更、转让和消灭
[11:00.00]根据物权法的规定，不动产物权变动需要登记
[12:00.00]而动产物权变动一般以交付为准
"""
    
    # 创建分段器
    segmenter = IntelligentSegmenter(buffer_seconds=20.0)
    
    # 执行按知识点独立分段
    segments = segmenter.segment_by_knowledge_points(
        mock_lrc_content, 
        mock_analysis, 
        file_format='lrc'
    )
    
    # 输出结果
    print(f"\n📊 独立分段结果:")
    for i, segment in enumerate(segments, 1):
        print(f"\n知识点分段 {i}:")
        print(f"  知识点ID: {segment.knowledge_points[0]}")
        print(f"  时间范围: {segment.time_range.start:.1f}-{segment.time_range.end:.1f}s")
        print(f"  Token数量: {segment.token_count}")
        print(f"  文本长度: {len(segment.text)} 字符")
        print(f"  文本预览: {segment.text[:100]}...")
        
        if segment.buffer_info:
            print(f"  处理类型: {segment.buffer_info.get('type', '未知')}")
    
    # 获取摘要
    summary = segmenter.get_segments_summary(segments)
    print(f"\n📋 独立分段摘要:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n✅ 独立分段测试完成！")


if __name__ == "__main__":
    test_individual_segmentation()
