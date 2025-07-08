"""
智能分段核心类 - intelligent_segmenter.py

基于第一步分析结果的time_range，精准提取相关字幕片段，减少60-80%的token使用
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from time_parser import TimeParser, TimeRange


@dataclass
class Segment:
    """字幕分段数据类"""
    text: str                    # 字幕文本内容
    time_range: TimeRange        # 时间范围
    knowledge_points: List[str]  # 关联知识点ID
    token_count: int            # 估算token数量
    buffer_info: Dict[str, Any] # 缓冲区信息
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'text': self.text,
            'time_range': {
                'start': self.time_range.start,
                'end': self.time_range.end,
                'kp_ids': self.time_range.kp_ids
            },
            'knowledge_points': self.knowledge_points,
            'token_count': self.token_count,
            'buffer_info': self.buffer_info
        }


class SubtitleParser:
    """字幕文件解析器"""
    
    @staticmethod
    def parse_lrc_content(content: str) -> List[Dict[str, Any]]:
        """
        解析LRC格式字幕
        
        Args:
            content: LRC字幕内容
            
        Returns:
            时间戳和文本的列表
        """
        lines = []
        # LRC格式: [MM:SS.mm]文本内容
        lrc_pattern = re.compile(r'\[(\d{1,2}:\d{2}(?:\.\d{1,3})?)\](.*)')
        
        for line in content.split('\n'):
            line = line.strip()
            if line:
                match = lrc_pattern.match(line)
                if match:
                    time_str, text = match.groups()
                    timestamp = TimeParser.parse_time_string(time_str)
                    if timestamp is not None and text.strip():
                        lines.append({
                            'timestamp': timestamp,
                            'text': text.strip(),
                            'original_time': time_str
                        })
        
        return sorted(lines, key=lambda x: x['timestamp'])
    
    @staticmethod
    def parse_srt_content(content: str) -> List[Dict[str, Any]]:
        """
        解析SRT格式字幕
        
        Args:
            content: SRT字幕内容
            
        Returns:
            时间戳和文本的列表
        """
        lines = []
        # SRT格式分块处理
        blocks = re.split(r'\n\s*\n', content.strip())
        
        for block in blocks:
            block_lines = block.strip().split('\n')
            if len(block_lines) >= 3:
                # 第二行是时间戳
                time_line = block_lines[1]
                # SRT时间格式: HH:MM:SS,mmm --> HH:MM:SS,mmm
                time_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', time_line)
                
                if time_match:
                    start_str, end_str = time_match.groups()
                    # 转换逗号为点号
                    start_str = start_str.replace(',', '.')
                    end_str = end_str.replace(',', '.')
                    
                    start_time = TimeParser.parse_time_string(start_str)
                    end_time = TimeParser.parse_time_string(end_str)
                    
                    if start_time is not None and end_time is not None:
                        # 合并文本行
                        text = ' '.join(block_lines[2:]).strip()
                        if text:
                            lines.append({
                                'timestamp': start_time,
                                'end_timestamp': end_time,
                                'text': text,
                                'original_time': f"{start_str}-{end_str}"
                            })
        
        return sorted(lines, key=lambda x: x['timestamp'])
    
    @staticmethod
    def parse_txt_content(content: str) -> List[Dict[str, Any]]:
        """
        解析纯文本格式（无时间戳）
        
        Args:
            content: 文本内容
            
        Returns:
            文本行列表（时间戳为None）
        """
        lines = []
        for i, line in enumerate(content.split('\n')):
            line = line.strip()
            if line:
                lines.append({
                    'timestamp': None,
                    'text': line,
                    'line_number': i + 1
                })
        
        return lines
    
    @classmethod
    def parse_subtitle_content(cls, content: str, file_format: str = 'auto') -> List[Dict[str, Any]]:
        """
        自动识别并解析字幕内容
        
        Args:
            content: 字幕文件内容
            file_format: 文件格式 ('lrc', 'srt', 'txt', 'auto')
            
        Returns:
            解析后的字幕行列表
        """
        if not content or not content.strip():
            return []
        
        content = content.strip()
        
        # 自动识别格式
        if file_format == 'auto':
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
    """智能分段处理器"""
    
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
    
    def extract_time_ranges_from_analysis(self, analysis_result: Dict[str, Any]) -> List[TimeRange]:
        """
        从第一步分析结果中提取时间范围
        
        Args:
            analysis_result: 第一步分析结果
            
        Returns:
            时间范围列表
        """
        time_ranges = []
        
        # 从knowledge_points中提取时间范围
        knowledge_points = analysis_result.get('knowledge_points', [])
        
        for kp in knowledge_points:
            kp_id = kp.get('id', 'unknown')
            time_range_str = kp.get('time_range', '')
            
            if time_range_str:
                time_range = TimeParser.parse_time_range(time_range_str, kp_id)
                if time_range:
                    time_ranges.append(time_range)
                else:
                    print(f"⚠️ 无法解析时间范围: {time_range_str} (知识点: {kp_id})")
        
        return time_ranges
    
    def add_buffer_and_merge_ranges(self, time_ranges: List[TimeRange], 
                                   max_duration: float = None) -> List[TimeRange]:
        """
        为时间范围添加缓冲区并合并重叠/相邻的范围
        
        Args:
            time_ranges: 原始时间范围列表
            max_duration: 字幕最大时长（用于边界控制）
            
        Returns:
            处理后的时间范围列表
        """
        if not time_ranges:
            return []
        
        # 添加缓冲区
        buffered_ranges = TimeParser.add_buffer_to_ranges(
            time_ranges, 
            buffer_seconds=self.buffer_seconds,
            min_time=0.0,
            max_time=max_duration
        )
        
        # 标准化（合并重叠和相邻的范围）
        normalized_ranges = TimeParser.normalize_time_ranges(buffered_ranges)
        
        return normalized_ranges
    
    def extract_text_by_time_ranges(self, subtitle_lines: List[Dict[str, Any]], 
                                   time_ranges: List[TimeRange]) -> List[Segment]:
        """
        根据时间范围提取对应的字幕文本
        
        Args:
            subtitle_lines: 解析后的字幕行列表
            time_ranges: 目标时间范围列表
            
        Returns:
            分段结果列表
        """
        segments = []
        
        for time_range in time_ranges:
            segment_text = []
            matched_lines = []
            
            # 如果字幕没有时间戳（纯文本格式）
            if not subtitle_lines or subtitle_lines[0].get('timestamp') is None:
                # 对于纯文本，返回完整内容作为一个分段
                full_text = '\n'.join([line['text'] for line in subtitle_lines])
                segments.append(Segment(
                    text=full_text,
                    time_range=time_range,
                    knowledge_points=time_range.kp_ids.copy(),
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
                    'original_range': f"{time_range.start:.1f}-{time_range.end:.1f}s",
                    'matched_lines': len(matched_lines),
                    'buffer_added': self.buffer_seconds,
                    'first_timestamp': matched_lines[0]['timestamp'] if matched_lines else None,
                    'last_timestamp': matched_lines[-1]['timestamp'] if matched_lines else None
                }
                
                segments.append(Segment(
                    text=text,
                    time_range=time_range,
                    knowledge_points=time_range.kp_ids.copy(),
                    token_count=self._estimate_token_count(text),
                    buffer_info=buffer_info
                ))
            else:
                # 如果没有匹配的文本，创建空分段并记录警告
                print(f"⚠️ 时间范围 {time_range.start:.1f}-{time_range.end:.1f}s 没有匹配的字幕内容")
                segments.append(Segment(
                    text="",
                    time_range=time_range,
                    knowledge_points=time_range.kp_ids.copy(),
                    token_count=0,
                    buffer_info={
                        'type': 'empty_segment',
                        'reason': 'no_matching_text',
                        'original_range': f"{time_range.start:.1f}-{time_range.end:.1f}s"
                    }
                ))
        
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
    
    def segment_subtitle_content(self, subtitle_content: str, analysis_result: Dict[str, Any],
                                file_format: str = 'auto') -> List[Segment]:
        """
        智能分段主入口方法
        
        Args:
            subtitle_content: 字幕文件内容
            analysis_result: 第一步分析结果
            file_format: 字幕文件格式
            
        Returns:
            分段结果列表
        """
        try:
            # 1. 解析字幕内容
            print(f"📖 解析字幕内容 (格式: {file_format})")
            subtitle_lines = self.subtitle_parser.parse_subtitle_content(subtitle_content, file_format)
            
            if not subtitle_lines:
                print("⚠️ 字幕内容解析为空，将使用完整内容")
                return self._create_fallback_segment(subtitle_content, analysis_result)
            
            print(f"✅ 解析到 {len(subtitle_lines)} 行字幕")
            
            # 2. 从分析结果中提取时间范围
            print("🔍 提取知识点时间范围")
            time_ranges = self.extract_time_ranges_from_analysis(analysis_result)
            
            if not time_ranges:
                print("⚠️ 未找到有效的时间范围，将使用完整内容")
                return self._create_fallback_segment(subtitle_content, analysis_result)
            
            print(f"✅ 提取到 {len(time_ranges)} 个时间范围")
            
            # 3. 添加缓冲区并合并范围
            print("🔧 添加缓冲区并合并重叠范围")
            max_duration = None
            if subtitle_lines and subtitle_lines[-1].get('timestamp'):
                max_duration = subtitle_lines[-1]['timestamp'] + 60  # 最后时间戳 + 1分钟缓冲
            
            processed_ranges = self.add_buffer_and_merge_ranges(time_ranges, max_duration)
            print(f"✅ 处理后得到 {len(processed_ranges)} 个时间段")
            
            # 4. 提取对应的文本内容
            print("📝 提取对应时间段的字幕文本")
            segments = self.extract_text_by_time_ranges(subtitle_lines, processed_ranges)
            
            # 5. 统计和验证
            total_tokens = sum(seg.token_count for seg in segments)
            original_tokens = self._estimate_token_count(subtitle_content)
            reduction_ratio = (1 - total_tokens / original_tokens) * 100 if original_tokens > 0 else 0
            
            print(f"📊 分段统计:")
            print(f"  - 分段数量: {len(segments)}")
            print(f"  - 原始tokens: {original_tokens}")
            print(f"  - 分段后tokens: {total_tokens}")
            print(f"  - Token减少: {reduction_ratio:.1f}%")
            
            # 验证分段效果
            if reduction_ratio < 10:  # 如果减少比例小于10%，给出警告
                print("⚠️ Token减少比例较低，可能需要调整缓冲区参数")
            
            return segments
            
        except Exception as e:
            print(f"❌ 智能分段失败: {e}")
            return self._create_fallback_segment(subtitle_content, analysis_result)
    
    def _create_fallback_segment(self, subtitle_content: str, analysis_result: Dict[str, Any]) -> List[Segment]:
        """
        创建fallback分段（使用完整内容）
        
        Args:
            subtitle_content: 完整字幕内容
            analysis_result: 分析结果
            
        Returns:
            包含完整内容的分段列表
        """
        knowledge_points = analysis_result.get('knowledge_points', [])
        kp_ids = [kp.get('id', 'unknown') for kp in knowledge_points]
        
        fallback_segment = Segment(
            text=subtitle_content,
            time_range=TimeRange(0, 0, kp_ids),  # 时间范围设为0表示全部内容
            knowledge_points=kp_ids,
            token_count=self._estimate_token_count(subtitle_content),
            buffer_info={
                'type': 'fallback',
                'reason': 'segmentation_failed',
                'original_token_count': self._estimate_token_count(subtitle_content)
            }
        )
        
        return [fallback_segment]
    
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
                    'duration': seg.time_range.duration
                })
        
        summary = {
            'total_segments': len(segments),
            'total_tokens': total_tokens,
            'knowledge_points': unique_kp_ids,
            'time_ranges': time_ranges,
            'total_duration': sum(tr['duration'] for tr in time_ranges),
            'avg_segment_tokens': total_tokens / len(segments) if segments else 0,
            'has_fallback': any(seg.buffer_info.get('type') == 'fallback' for seg in segments)
        }
        
        return summary


def test_intelligent_segmenter():
    """测试智能分段器功能"""
    print("🧪 测试智能分段器")
    
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
    
    # 执行分段
    segments = segmenter.segment_subtitle_content(
        mock_lrc_content, 
        mock_analysis, 
        file_format='lrc'
    )
    
    # 输出结果
    print(f"\n📊 分段结果:")
    for i, segment in enumerate(segments, 1):
        print(f"\n分段 {i}:")
        print(f"  时间范围: {segment.time_range.start:.1f}-{segment.time_range.end:.1f}s")
        print(f"  关联知识点: {segment.knowledge_points}")
        print(f"  Token数量: {segment.token_count}")
        print(f"  文本长度: {len(segment.text)} 字符")
        print(f"  文本预览: {segment.text[:100]}...")
    
    # 获取摘要
    summary = segmenter.get_segments_summary(segments)
    print(f"\n📋 分段摘要:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    test_intelligent_segmenter()
