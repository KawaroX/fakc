# ai_processor.py - 更新版本，集成智能分段功能
import yaml
import re
import datetime
import json
from openai import OpenAI
from typing import List, Dict, Any, Optional, Tuple

from intelligent_segmenter import IntelligentSegmenter, Segment
from concurrent_processor import run_concurrent_processing, ConcurrentConfig

class AIProcessor:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        # 初始化智能分段器
        self.segmenter = IntelligentSegmenter()

        # 新增：并发配置
        self.concurrent_config = ConcurrentConfig(
            max_concurrent=20,      # API限制
            max_retries=3,          # 最大重试次数
            retry_delay=1.0,        # 重试延迟
            timeout=60,             # 单个任务超时
            rate_limit_delay=60.0   # 速率限制等待时间
        )
        
        # 用于进度回调的属性
        self.progress_callback = None
    
    def _separate_markdown_content(self, full_content: str) -> tuple:
        """
        分离markdown的YAML frontmatter和正文内容
        
        Returns:
            tuple: (yaml_data: dict, content_only: str, has_yaml: bool)
        """
        
        full_content = full_content.strip()
        
        # 检查是否有YAML frontmatter
        if full_content.startswith('---'):
            # 使用正则表达式匹配YAML frontmatter
            yaml_match = re.match(r'^---\n(.*?)\n---\n?(.*)', full_content, re.DOTALL)
            if yaml_match:
                try:
                    yaml_content = yaml_match.group(1)
                    content_only = yaml_match.group(2).strip()
                    yaml_data = yaml.safe_load(yaml_content)
                    return yaml_data, content_only, True
                except yaml.YAMLError as e:
                    print(f"⚠️ YAML解析失败: {e}")
                    return {}, full_content, False
        
        # 没有YAML frontmatter
        return {}, full_content, False

    def _combine_markdown_content(self, yaml_data: dict, content_only: str, has_yaml: bool) -> str:
        """
        重新组合YAML frontmatter和正文内容
        
        Args:
            yaml_data: YAML数据字典
            content_only: 纯正文内容
            has_yaml: 原始文件是否有YAML
        
        Returns:
            str: 完整的markdown内容
        """
        if not has_yaml or not yaml_data:
            return content_only
        
        
        # 生成YAML frontmatter
        yaml_str = yaml.dump(yaml_data, allow_unicode=True, default_flow_style=False)
        
        return f"---\n{yaml_str}---\n\n{content_only}"

    # 第一步：知识点分析与架构构建
    def extract_knowledge_points_step1(self, subtitle_content: str, metadata: Dict[str, str]) -> Dict:
        """执行第一步分析，输出JSON结构"""
        prompt = self.STEP1_PROMPT_TEMPLATE.format(
            subtitle_content=subtitle_content,
            subject=metadata['subject'],
            source=metadata['source'],
            course_url=metadata.get('course_url', '未提供')
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0,
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"❌ 第一步分析失败: {e}")
            return {}

    # 第二步：详细笔记整理（集成智能分段）
    def generate_notes_step2(self, analysis_result: Dict, subtitle_content: str, 
                           metadata: Dict[str, str], use_segmentation: bool = True) -> List[Dict[str, Any]]:
        """
        根据第一步结果生成最终笔记（集成智能分段）
        
        Args:
            analysis_result: 第一步分析结果
            subtitle_content: 原始字幕内容
            metadata: 元数据
            use_segmentation: 是否使用智能分段（默认True）
            
        Returns:
            生成的笔记列表
        """
        try:
            # 如果启用智能分段
            if use_segmentation:
                print("🔧 启用智能分段处理...")
                
                # 检测字幕格式
                file_format = self._detect_subtitle_format(subtitle_content)
                
                # 执行智能分段
                segments = self.segmenter.segment_by_knowledge_points(
                    subtitle_content, 
                    analysis_result, 
                    file_format
                )
                
                # 获取分段摘要
                summary = self.segmenter.get_segments_summary(segments)
                print(f"📊 分段摘要: {summary['total_segments']}个分段, "
                      f"Token减少{(1-summary['total_tokens']/self.segmenter._estimate_token_count(subtitle_content))*100:.1f}%")
                
                # 使用独立分段内容生成笔记
                return self._generate_notes_from_individual_segments(segments, analysis_result, metadata)
            else:
                print("📝 使用传统方式处理...")
                # 传统方式：使用完整字幕内容
                return self._generate_notes_traditional(analysis_result, subtitle_content, metadata)
                
        except Exception as e:
            print(f"❌ 第二步笔记生成失败: {e}")
            # Fallback到传统方式
            return self._generate_notes_traditional(analysis_result, subtitle_content, metadata)
    
    def _detect_subtitle_format(self, content: str) -> str:
        """
        检测字幕文件格式
        
        Args:
            content: 字幕内容
            
        Returns:
            检测到的格式：'lrc', 'srt', 'txt'
        """
        if re.search(r'\[\d{1,2}:\d{2}(?:\.\d{1,3})?\]', content):
            return 'lrc'
        elif re.search(r'\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}', content):
            return 'srt'
        else:
            return 'txt'
    
    def _generate_notes_from_segments(self, segments: List[Segment], 
                                    analysis_result: Dict, metadata: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        基于分段结果生成笔记
        
        Args:
            segments: 智能分段结果
            analysis_result: 第一步分析结果
            metadata: 元数据
            
        Returns:
            生成的笔记列表
        """
        all_notes = []
        knowledge_points = analysis_result.get('knowledge_points', [])
        
        # 为每个分段构建对应的知识点组
        for segment in segments:
            if not segment.text.strip():  # 跳过空分段
                continue
                
            # 找到与此分段相关的知识点
            related_kps = []
            for kp in knowledge_points:
                if kp.get('id') in segment.knowledge_points:
                    related_kps.append(kp)
            
            if not related_kps:  # 如果没有关联的知识点，跳过
                continue
            
            # 构建分段处理的提示词
            segment_prompt = self._build_segment_prompt(
                segment, related_kps, analysis_result, metadata
            )
            
            try:
                # 调用AI处理分段
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": segment_prompt}],
                    temperature=0,
                )
                
                # 解析AI返回的笔记
                segment_notes = self._parse_ai_response(response.choices[0].message.content)
                if segment_notes:
                    all_notes.extend(segment_notes)
                    print(f"✅ 分段处理完成，生成 {len(segment_notes)} 个笔记")
                
            except Exception as e:
                print(f"⚠️ 分段处理失败，跳过: {e}")
                continue
        
        return all_notes
    
    # def _generate_notes_from_individual_segments(self, segments: List[Segment], 
    #                                        analysis_result: Dict, metadata: Dict[str, str]) -> List[Dict[str, Any]]:
    #     """
    #     基于独立分段结果生成笔记（每个知识点对应一个段落）
    #     """
    #     all_notes = []
    #     knowledge_points = analysis_result.get('knowledge_points', [])
        
    #     print(f"📝 开始处理 {len(segments)} 个独立段落...")
        
    #     # 为每个分段单独处理（每个分段只对应一个知识点）
    #     for i, segment in enumerate(segments, 1):
    #         if not segment.text.strip():  # 跳过空分段
    #             print(f"⚠️ 跳过空分段 {i}")
    #             continue
                
    #         # 每个分段应该只有一个知识点
    #         if len(segment.knowledge_points) != 1:
    #             print(f"⚠️ 分段 {i} 包含 {len(segment.knowledge_points)} 个知识点，跳过")
    #             continue
            
    #         kp_id = segment.knowledge_points[0]
            
    #         # 找到对应的知识点
    #         target_kp = None
    #         for kp in knowledge_points:
    #             if kp.get('id') == kp_id:
    #                 target_kp = kp
    #                 break
            
    #         if not target_kp:
    #             print(f"⚠️ 找不到知识点 {kp_id}，跳过分段 {i}")
    #             continue
            
    #         # 构建单个知识点的处理提示词
    #         single_kp_prompt = self._build_single_knowledge_point_prompt(
    #             segment, target_kp, analysis_result, metadata
    #         )
            
    #         try:
    #             print(f"🤖 处理知识点: {target_kp.get('concept_name', kp_id)} (分段 {i}/{len(segments)})")
                
    #             # 调用AI处理单个知识点
    #             response = self.client.chat.completions.create(
    #                 model=self.model,
    #                 messages=[{"role": "user", "content": single_kp_prompt}],
    #                 temperature=0,
    #             )
                
    #             # 解析AI返回的单个笔记（不包含分隔符）
    #             note_content = response.choices[0].message.content.strip()
                
    #             # 解析单个笔记
    #             parsed_note = self._parse_single_note_response(note_content, target_kp, metadata)
                
    #             if parsed_note:
    #                 all_notes.append(parsed_note)
    #                 print(f"✅ 成功生成笔记: {target_kp.get('concept_name', kp_id)}")
    #             else:
    #                 print(f"⚠️ 解析笔记失败: {target_kp.get('concept_name', kp_id)}")
                
    #         except Exception as e:
    #             print(f"⚠️ 处理知识点 {kp_id} 失败: {e}")
    #             continue
        
    #     print(f"✅ 独立分段处理完成，共生成 {len(all_notes)} 个笔记")
    #     return all_notes
    
    def _build_segment_prompt(self, segment: Segment, related_kps: List[Dict], 
                            analysis_result: Dict, metadata: Dict[str, str]) -> str:
        """
        构建分段处理的提示词
        
        Args:
            segment: 分段对象
            related_kps: 相关知识点列表
            analysis_result: 完整分析结果
            metadata: 元数据
            
        Returns:
            构建好的提示词
        """
        # 提取课程概览和教学洞察
        course_overview = analysis_result.get('course_overview', {})
        teaching_insights = analysis_result.get('teaching_insights', {})
        
        # 构建知识点信息
        kp_info = []
        for kp in related_kps:
            kp_summary = {
                'id': kp.get('id', ''),
                'concept_name': kp.get('concept_name', ''),
                'concept_type': kp.get('concept_type', ''),
                'importance_level': kp.get('importance_level', ''),
                'time_range': kp.get('time_range', ''),
                'core_definition': kp.get('core_definition', {}),
                'detailed_content': kp.get('detailed_content', {}),
                'exam_relevance': kp.get('exam_relevance', {}),
                'relationships': kp.get('relationships', {})
            }
            kp_info.append(kp_summary)
        
        return self.SEGMENT_PROMPT_TEMPLATE.format(
            segment_text=segment.text,
            time_range=f"{segment.time_range.start:.1f}-{segment.time_range.end:.1f}s",
            knowledge_points=json.dumps(kp_info, ensure_ascii=False, indent=2),
            course_overview=json.dumps(course_overview, ensure_ascii=False),
            teaching_insights=json.dumps(teaching_insights, ensure_ascii=False),
            subject=metadata['subject'],
            source=metadata['source'],
            course_url=metadata.get('course_url', '')
        )
    
    def _generate_notes_traditional(self, analysis_result: Dict, subtitle_content: str, 
                                  metadata: Dict[str, str]) -> List[Dict[str, Any]]:
        """传统方式生成笔记（使用完整字幕内容）"""
        prompt = self.STEP2_PROMPT_TEMPLATE.format(
            analysis_result=json.dumps(analysis_result, ensure_ascii=False),
            subtitle_content=subtitle_content,
            subject=metadata['subject'],
            source=metadata['source'],
            course_url=metadata.get('course_url', '')
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            
            return self._parse_ai_response(response.choices[0].message.content)
        except Exception as e:
            print(f"❌ 传统方式笔记生成失败: {e}")
            return []

    # 旧版兼容方法（单步处理）
    def extract_all_knowledge_points(self, subtitle_content: str, metadata: Dict[str, str]) -> List[Dict[str, Any]]:
        """一次性处理整个字幕（兼容旧版）"""
        # 使用新两步法处理
        analysis = self.extract_knowledge_points_step1(subtitle_content, metadata)
        if not analysis:
            return []
        return self.generate_notes_step2(analysis, subtitle_content, metadata)
    
    # 新增：分段处理的提示词模板
    SEGMENT_PROMPT_TEMPLATE = """\
你是专业的法考笔记整理专家。请根据第一步分析结果和对应的字幕片段，生成完整的Obsidian笔记。

## 输入内容

**字幕片段**（时间范围: {time_range}）：
{segment_text}

**相关知识点分析**：
{knowledge_points}

**课程概览**：
{course_overview}

**教学风格洞察**：
{teaching_insights}

**课程信息**：
- 科目：{subject}
- 来源：{source}
- 课程链接：{course_url}

## 处理要求

**精确对应**：严格基于提供的知识点分析结果，为每个knowledge_point生成对应笔记

**充分利用片段内容**：深度挖掘字幕片段中的信息，保留老师的原始表述和重要细节

**时间戳处理**：使用time_range信息添加准确的时间戳标记，格式为[MM:SS.mm]

**概念关联**：基于relationships信息建立准确的双链关系

## 笔记生成规则

**YAML元数据标准**：
```yaml
title: "【{subject}】{{concept_name}}"
aliases: ["{{concept_name}}", "其他别名"]
tags: ["{subject}", "根据concept_type确定", "根据importance_level确定"]
source: "{source}"
course_url: "{course_url}"
time_range: "{{time_range}}"
subject: "{subject}"
exam_importance: "{{importance_level}}"
concept_id: "{{id}}"
created: "当前时间"
```

**章节结构智能设计**：根据concept_type智能选择章节结构
- 定义性概念：核心定义 + 关键要素 + 典型案例
- 构成要件：要件概述 + 要件详解 + 举证责任
- 程序性知识：程序概述 + 操作步骤 + 注意事项
- 判断标准：标准概述 + 判断要素 + 适用情形
- 法条规定：条文内容 + 立法背景 + 适用情形
- 实务经验：经验概述 + 操作要点 + 实用技巧

**内容填充策略**：
- 核心定义：优先使用teacher_original，补充context信息
- 详细展开：基于detailed_content的main_explanation和examples
- 记忆要点：结合memory_tips、key_keywords、common_mistakes
- 相关概念：根据relationships建立双链

**输出格式**：
```
=== NOTE_SEPARATOR ===
YAML:
---
[YAML元数据]
---
CONTENT:
# 【{subject}】{{concept_name}}

## 核心定义

⏰ [时间戳]
[基于teacher_original和字幕片段的定义]

[智能选择的其他章节]

## 记忆要点

🔮 [关键记忆点] — [简洁解释]
📱 [应用场景] — [典型情况]  
💡 [重要提醒] — [易错提示]

## 相关概念

[基于relationships的双链列表]

---
*视频时间段：{time_range}*

=== NOTE_SEPARATOR ===
```

请严格按照上述要求，为提供的每个知识点生成对应的完整笔记。直接输出笔记内容，不需要额外说明。
"""
    
    # 第一步提示词模板
    STEP1_PROMPT_TEMPLATE = """\
你是专业的法考课程分析专家。请深度分析以下字幕内容，识别所有知识点并构建详细的学习架构。

字幕内容：
{subtitle_content}

课程信息：
- 科目：{subject}
- 来源：{source}
- 课程链接：{course_url}

## 分析目标

你需要为后续的笔记整理AI提供完整的指导，确保：
1. **无遗漏**：识别每个独立的法律概念
2. **保细节**：保留老师的重要表述、强调、举例
3. **建关联**：明确概念间的逻辑关系
4. **传风格**：准确传达老师的教学特点

## 知识点识别原则

**超细化拆分标准**：
- 每个有独立名称的法律概念都要单独识别
- 每个可能在考试中单独考查的知识点都要拆分
- 每个在实务中有独立应用的概念都要独立处理
- 宁可拆分过细，不要合并独立概念

**特别关注**：
- 法律条文中的具体规定
- 构成要件的每个要素
- 不同情形下的处理原则
- 例外规定和特殊情况
- 老师特别强调的要点

## 输出要求

请严格按照以下JSON格式输出分析结果：

{{
  "course_overview": {{
    "main_topic": "主要话题",
    "total_duration": "总时长",
    "teaching_style": "老师教学风格描述（举例多/理论强/实务导向等）",
    "key_emphasis": ["老师反复强调的要点1", "要点2"],
    "difficulty_level": "难度等级"
  }},
  
  "knowledge_points": [
    {{
      "id": "KP001",
      "concept_name": "概念名称",
      "concept_type": "定义性概念/程序性知识/判断标准/构成要件/法条规定/实务经验",
      "time_range": "MM:SS.mm-MM:SS.mm",
      "importance_level": "高/中/低",
      
      "core_definition": {{
        "teacher_original": "老师的原始表述（尽可能保持原话）",
        "key_keywords": ["关键词1", "关键词2"],
        "context": "定义的上下文背景"
      }},
      
      "detailed_content": {{
        "main_explanation": "主要解释内容",
        "examples": [
          {{
            "example_content": "具体例子内容", 
            "teacher_comment": "老师对例子的点评或强调"
          }}
        ],
        "special_notes": ["特别注意事项1", "注意事项2"],
        "common_mistakes": ["易错点1", "易错点2"],
        "memory_tips": "记忆技巧或口诀"
      }},
      
      "exam_relevance": {{
        "exam_frequency": "常考/偶考/基础",
        "question_types": ["选择题", "案例题", "论述题"],
        "key_test_points": ["考点1", "考点2"]
      }},
      
      "relationships": {{
        "parent_concept": "上位概念ID",
        "sub_concepts": ["子概念ID1", "子概念ID2"],
        "related_concepts": ["相关概念ID1", "相关概念ID2"],
        "contrast_concepts": ["对比概念ID1", "对比概念ID2"]
      }}
    }}
  ],
  
  "concept_structure": {{
    "hierarchy": "概念层次结构的文字描述",
    "main_logic_flow": "主要逻辑脉络",
    "cross_references": [
      {{
        "concept1": "概念ID1",
        "concept2": "概念ID2", 
        "relationship": "关系类型（包含/对比/依赖/并列等）"
      }}
    ]
  }},
  
  "teaching_insights": {{
    "teacher_preferences": "老师的教学偏好（爱举例/重理论/强调实务等）",
    "emphasis_pattern": "强调模式（重复说明/对比分析/案例解释等）",
    "student_attention": ["需要特别注意的学习要点"],
    "practical_tips": ["实务建议或经验分享"]
  }}
}}

## 特别要求

1. **保持原汁原味**：尽可能保留老师的原始表述，特别是定义、强调、举例
2. **时间戳精确**：每个知识点都要有准确的时间范围，格式为[MM:SS.mm-MM:SS.mm]
3. **关系清晰**：概念间的关系要准确，避免循环引用
4. **细节丰富**：为后续笔记整理提供充分的信息基础
5. **ID命名**：知识点ID使用KP001、KP002格式，便于引用

请开始分析，输出完整的JSON结构。"""

    # 第二步提示词模板
    STEP2_PROMPT_TEMPLATE = """\
你是专业的法考笔记整理专家。请根据前一步的分析结果和原始字幕内容，生成完整的Obsidian笔记。

## 输入内容

**知识点分析结果**：
{analysis_result}

**原始字幕内容**：
{subtitle_content}

**课程信息**：
- 科目：{subject}
- 来源：{source}
- 课程链接：{course_url}

## 整理目标

基于知识点分析，为每个识别出的概念创建完整的Obsidian笔记，实现：
1. **知识图谱节点**：每个笔记是图谱中的清晰节点
2. **Wiki百科条目**：独立完整，可单独阅读理解
3. **错题定位索引**：精准匹配考试知识点

## 核心原则

**完全依据分析结果**：严格按照第一步识别的知识点列表生成笔记，不遗漏、不新增

**保持教学原味**：充分利用分析结果中的teacher_original、examples、teacher_comment等信息

**结构智能设计**：根据每个概念的特点（concept_type）和详细内容设计最适合的章节结构

**双链精确建立**：使用分析结果中的relationships信息建立准确的概念关联

## 笔记生成规则

**必需章节**：每个笔记必须包含
- 核心定义
- 记忆要点  
- 相关概念

**自由章节**：根据概念特点智能创造
- 构成要件类：详细列举各个要件
- 程序性知识：步骤或流程说明
- 判断标准类：判断方法和标准
- 实务经验类：实际应用和注意事项
- 法条规定类：条文内容和适用情况

**章节设计指导**：
```
concept_type = "构成要件" → 可设计"构成要件详解"章节
concept_type = "程序性知识" → 可设计"操作流程"章节  
concept_type = "判断标准" → 可设计"判断方法"章节
concept_type = "实务经验" → 可设计"实务应用"章节
concept_type = "法条规定" → 可设计"条文解读"章节
```

## 内容填充策略

**核心定义**：优先使用teacher_original，补充context信息

**详细内容**：充分利用main_explanation、examples、special_notes

**记忆要点**：结合memory_tips、key_keywords、common_mistakes

**相关概念**：严格按照relationships中的信息建立双链

**案例举例**：详细展开examples中的内容，保留teacher_comment

## 技术规范

**YAML元数据**：
```yaml
title: "【{subject}】{{concept_name}}"
aliases: ["{{concept_name}}", "其他别名"]
tags: ["{subject}", "根据concept_type确定", "根据importance_level确定"]
source: "{source}"
course_url: "{course_url}"
time_range: "{{time_range}}"
subject: "{subject}"
exam_importance: "{{importance_level}}"
concept_id: "{{id}}"
created: "当前时间"
```

**双链格式**：
- 引用格式：[[【{subject}】概念名|概念名]]
- 根据relationships精确建立关联

**时间戳格式**：
- 严格使用[MM:SS.mm]格式
- 从time_range中提取

## 输出格式

每个笔记使用以下格式：

```
=== NOTE_SEPARATOR ===
YAML:
---
[YAML元数据]
---
CONTENT:
# 【{subject}】{{concept_name}}

## 核心定义

⏰ [{{time_range}}]
[基于teacher_original和core_definition的内容]

## [智能创造的章节标题]
[基于detailed_content和concept_type的具体内容]

## 记忆要点

🔮 [基于memory_tips的关键点] — [简洁解释]
📱 [基于examples的应用场景] — [典型情况]
💡 [基于common_mistakes的提醒] — [易错提示]

## 相关概念

[基于relationships精确建立的双链列表]

---
*视频时间段：{{time_range}}*

=== NOTE_SEPARATOR ===
```

## 质量要求

1. **一一对应**：analysis_result中每个knowledge_point都要生成对应笔记
2. **信息完整**：充分利用分析结果中的所有有用信息
3. **逻辑清晰**：概念间关系准确，双链有意义
4. **细节丰富**：案例详细，说明充分
5. **格式标准**：严格遵循技术规范

请开始根据分析结果生成完整的Obsidian笔记，按序号顺序处理每个知识点，不遗漏任何概念。严格按照格式输出，不需要额外说明。"""


    # 新增：单个知识点处理的提示词模板（不使用分隔符）
    SINGLE_KNOWLEDGE_POINT_PROMPT_TEMPLATE = """\
你是专业的法考笔记整理专家。请根据字幕片段和知识点分析，生成一个完整的Obsidian笔记。

## 输入内容

**字幕片段**（时间范围: {time_range}）：
{segment_text}

**目标知识点**：
{knowledge_point}

**课程概览**：
{course_overview}

**教学风格洞察**：
{teaching_insights}

**课程信息**：
- 科目：{subject}
- 来源：{source}
- 课程链接：{course_url}

## 处理要求

**精确对应**：严格基于提供的单个知识点，生成对应的完整笔记

**充分利用片段内容**：深度挖掘字幕片段中的信息，保留老师的原始表述和重要细节

**时间戳处理**：使用time_range信息添加准确的时间戳标记

**概念关联**：基于relationships信息建立准确的双链关系

## 输出格式

请直接输出一个完整的markdown笔记，格式如下：

---
title: "【{subject}】{{concept_name}}"
aliases: ["{{concept_name}}"]
tags: ["{subject}", "{{concept_type}}", "{{importance_level}}"]
source: "{source}"
course_url: "{course_url}"
time_range: "{{time_range}}"
subject: "{subject}"
exam_importance: "{{importance_level}}"
concept_id: "{{id}}"
created: "{{当前时间}}"
---
# 【{subject}】{{concept_name}}

## 核心定义

⏰ [时间戳]
[基于teacher_original和字幕片段的定义]

[智能选择的其他章节]

## 记忆要点

🔮 [关键记忆点] — [简洁解释]
📱 [应用场景] — [典型情况]  
💡 [重要提醒] — [易错提示]

## 相关概念

[基于relationships的双链列表]

---
*视频时间段：{time_range}*

注意：
1. 确保只有开头和结尾各一个"---"分隔符
2. YAML部分不要包含额外的分隔符
3. 直接输出markdown格式，不要用代码块包装

请严格按照上述要求，为提供的知识点生成对应的完整笔记。直接输出笔记内容，不需要额外说明。不要使用任何分隔符，直接输出一个完整的markdown笔记。
"""

    def _build_single_knowledge_point_prompt(self, segment: Segment, knowledge_point: Dict, 
                                       analysis_result: Dict, metadata: Dict[str, str]) -> str:
        """构建单个知识点的处理提示词（不使用分隔符）"""
        # 提取课程概览和教学洞察
        course_overview = analysis_result.get('course_overview', {})
        teaching_insights = analysis_result.get('teaching_insights', {})
        
        return self.SINGLE_KNOWLEDGE_POINT_PROMPT_TEMPLATE.format(
            segment_text=segment.text,
            time_range=f"{segment.time_range.start:.1f}-{segment.time_range.end:.1f}s",
            knowledge_point=json.dumps(knowledge_point, ensure_ascii=False, indent=2),
            course_overview=json.dumps(course_overview, ensure_ascii=False),
            teaching_insights=json.dumps(teaching_insights, ensure_ascii=False),
            subject=metadata['subject'],
            source=metadata['source'],
            course_url=metadata.get('course_url', '')
        )

    def _parse_single_note_response(self, response_content: str, knowledge_point: Dict, metadata: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """解析单个笔记的AI响应 - 正确处理多个---的版本"""
        try:
            response_content = response_content.strip()
            
            # 检查是否以---开头（标准markdown frontmatter格式）
            if response_content.startswith('---'):
                # 找到第一个---的结束位置
                first_separator_end = response_content.find('\n', 3)  # 跳过开头的---
                if first_separator_end == -1:
                    print("⚠️ 格式错误：找不到第一个---后的换行")
                    return None
                
                # 从第一个---后开始查找第二个---
                second_separator_start = response_content.find('\n---', first_separator_end)
                if second_separator_start == -1:
                    print("⚠️ 格式错误：找不到第二个---")
                    return None
                
                # 提取YAML内容（在两个---之间）
                yaml_content = response_content[first_separator_end + 1:second_separator_start].strip()
                
                # 找到第二个---行的结束位置
                second_separator_end = response_content.find('\n', second_separator_start + 4)
                if second_separator_end == -1:
                    second_separator_end = second_separator_start + 4
                
                # 提取markdown内容（第二个---之后的所有内容）
                markdown_content = response_content[second_separator_end + 1:].strip()
                
            else:
                print("⚠️ 不是标准frontmatter格式，使用默认处理")
                yaml_content = ""
                markdown_content = response_content
            
            # 解析YAML数据
            yaml_data = {}
            if yaml_content:
                try:
                    yaml_data = yaml.safe_load(yaml_content)
                    if yaml_data is None:
                        yaml_data = {}
                    print(f"✅ YAML解析成功，包含 {len(yaml_data)} 个字段")
                except yaml.YAMLError as e:
                    print(f"⚠️ YAML解析失败: {e}")
                    print(f"YAML内容前200字符: {yaml_content[:200]}")
                    yaml_data = {}
            
            # 如果YAML解析失败或为空，生成默认的元数据
            if not yaml_data:
                yaml_data = {
                    'title': f"【{metadata['subject']}】{knowledge_point.get('concept_name', '未命名概念')}",
                    'aliases': [knowledge_point.get('concept_name', '未命名概念')],
                    'tags': [metadata['subject'], knowledge_point.get('concept_type', '定义性概念')],
                    'source': metadata['source'],
                    'subject': metadata['subject'],
                    'concept_id': knowledge_point.get('id', ''),
                    'created': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                if metadata.get('course_url'):
                    yaml_data['course_url'] = metadata['course_url']
                if knowledge_point.get('time_range'):
                    yaml_data['time_range'] = knowledge_point['time_range']
                if knowledge_point.get('importance_level'):
                    yaml_data['exam_importance'] = knowledge_point['importance_level']
                
                print(f"✅ 使用默认YAML数据：{yaml_data.get('title', '未命名')}")
            
            # 确保必要字段存在
            if 'title' not in yaml_data:
                yaml_data['title'] = f"【{metadata['subject']}】{knowledge_point.get('concept_name', '未命名概念')}"
            
            # 返回标准数据结构（与原来保持一致）
            note = {
                'yaml': yaml_data,           # 使用 'yaml' 键名
                'content': markdown_content  # 使用 'content' 键名
            }
            
            print(f"✅ 笔记解析成功: {yaml_data.get('title', '未命名')}")
            return note
            
        except Exception as e:
            print(f"❌ 解析单个笔记失败: {e}")
            print(f"响应内容长度: {len(response_content)}")
            print(f"响应内容前500字符: {response_content[:500]}")
            return None
    
    def enhance_concept_relationships(self, all_notes: List[Dict], existing_concepts: Dict) -> List[Dict]:
        """让AI分析所有笔记内容，增强概念关系"""
        if not all_notes:
            return all_notes
            
        prompt = self._build_enhancement_prompt(all_notes, existing_concepts)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            
            enhanced_notes = self._parse_enhancement_response(response.choices[0].message.content, all_notes)
            return enhanced_notes
        except Exception as e:
            print(f"⚠️ 概念关系增强失败，使用原始结果: {e}")
            return all_notes
    
    def enhance_single_note_concepts(self, note_content: str, note_title: str, existing_concepts: Dict) -> Optional[Dict]:
        """增强单个笔记的概念关系 - 分离YAML处理版本"""
        
        # 1. 分离YAML和正文内容
        yaml_data, content_only, has_yaml = self._separate_markdown_content(note_content)
        
        # 2. 构建提示词（只传入正文内容）
        prompt = self._build_single_note_enhancement_prompt(content_only, note_title, existing_concepts)
        
        try:
            # 3. 调用AI处理
            if self.model == "gemini-2.5-flash":
                response = self.client.chat.completions.create(
                    reasoning_effort="medium",
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                )
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                )
            
            # 4. 解析AI响应
            enhancement_result = self._parse_single_note_enhancement_response(
                response.choices[0].message.content, content_only
            )
            
            if not enhancement_result or not enhancement_result.get('modified', False):
                return {'modified': False}
            
            # 5. 重新组合完整内容（YAML + 处理后的正文）
            enhanced_content_only = enhancement_result['enhanced_content']
            complete_enhanced_content = self._combine_markdown_content(
                yaml_data, enhanced_content_only, has_yaml
            )
            
            return {
                'modified': True,
                'enhanced_content': complete_enhanced_content
            }
            
        except Exception as e:
            print(f"⚠️ 概念关系增强失败: {e}")
            return {'modified': False}
    
    def _build_extraction_prompt(self, subtitle_content: str, metadata: Dict[str, str]) -> str:
        """构建提取知识点的提示词"""
        return f"""你是专业的法考笔记整理专家。请分析以下字幕内容，提取所有独立的知识点，为每个知识点生成一个完整的Obsidian笔记。

字幕内容：
{subtitle_content}

课程信息：
- 科目：{metadata['subject']}
- 来源：{metadata['source']}
- 课程链接：{metadata.get('course_url', '未提供')}

## 项目目标和意义

我们正在构建一个完整的法考知识体系，具有三个核心目标：

**目标一：构建Obsidian知识图谱**
通过双链笔记系统，将法考所有知识点连接成一个可视化的知识网络。每个概念都是图谱中的一个节点，相关概念通过双链形成知识脉络，帮助理解概念间的逻辑关系。

**目标二：建立法考Wiki百科**
创建类似维基百科的法考知识体系，每个法律概念都有独立详细的条目。学习者可以从任何一个概念出发，通过双链跳转到相关概念，实现知识的深度探索和关联学习。

**目标三：错题快速定位系统**
当整理错题时，能够快速定位到涉及的具体知识点。这要求每个可能在考试中独立出现的概念都要有对应的笔记，便于错题分析时精准关联到相关知识点。

## 核心指导原则

**内容完整性**：保留所有有价值的信息，包括老师的例子、案例、解释、强调、实务经验等。每个笔记都要像一个完整的百科条目，宁可详细也不要遗漏重要内容。

**细分优先策略**：极力倾向于将知识点拆分得更细致。想象你在为一个法考Wiki创建条目，每个具有独立名称、定义或考查价值的概念都应该有独立的条目。这种细分是构建知识图谱和实现错题精准定位的基础。

**双链连接逻辑**：将每个笔记视为知识图谱中的一个节点，通过双链与其他节点建立连接。上位概念通过双链连接下位概念，相关概念相互引用，形成立体的知识网络。

**Wiki式完整性**：每个笔记都应该能够独立阅读和理解，就像维基百科的条目一样。读者从任何一个笔记开始，都能通过双链深入学习相关知识。

**考试导向精确性**：考虑每个知识点在考试中的独立性。如果某个概念可能在选择题、案例题或论述题中单独出现，就应该有独立的笔记，便于错题整理时精确关联。

**结构智能性**：完全根据实际内容决定笔记结构。你需要分析老师的讲课重点和方式，然后设计最适合的章节结构来组织信息。不要被任何预设的模板限制。

**理解导向**：以帮助学生理解和掌握知识为目标，选择最有利于学习的信息组织方式，按照需要选择表格、mermaid等方式辅助表达，这点十分重要。

## 知识点识别和拆分策略

**超细化拆分标准**：
- 每个有独立名称的法律概念（无论大小）都应该独立成笔记
- 每个可能在考试中单独提及的知识点都要独立处理
- 每个在实务中有独立应用场景的概念都要拆分
- 宁可拆分过细也不要合并独立概念

**图谱节点设计的技术细节**：
- 节点要有明确的主题边界，不能模糊不清
- 节点间通过双链形成有向或无向的连接关系
- 避免创建过于庞大的"超级节点"，这会破坏图谱的清晰性

**错题匹配的具体场景**：
- 错题涉及"善意取得"，应该能直接找到对应笔记
- 错题涉及"返还原物请求权的构成要件"，每个要件都应该有对应的详细说明
- 错题涉及某个具体原则的适用，该原则应该有独立且完整的笔记

## 字幕格式处理

**支持格式**：主要接受lrc格式和srt格式的字幕文件，这些格式包含时间戳信息。也可能接收txt格式的纯文本文件，此类文件没有时间戳信息。

**时间戳处理**：
- 如果字幕文件包含时间戳，严格使用[MM:SS.mm]格式，如[01:23.45]、[00:23.45]
- 分钟数即使为0也要保留，如[00:23.45]
- 秒和毫秒之间使用英文句点"."分隔
- 如果是txt格式没有时间戳，则不添加时间戳标记

## 技术规范要求

**YAML前置元数据**：
- 严格按照指定格式，每个字段后面必须有空格
- title字段使用【科目】概念名格式
- aliases第一个别名必须是去掉科目前缀的概念名
- tags使用数组格式，不需要#号前缀
- 所有必需字段都必须包含

**双链引用规范**：
- 引用其他概念时使用[[【科目】概念名|概念名（或者别名）]]格式
- 显示文本使用（或别名）（无科目前缀）
- 链接目标使用完整标题（含科目前缀）
- 要建立有意义的双链关系，避免无关联的随意链接

**笔记结构要求**：
- 每个笔记都必须包含"核心定义"、"记忆要点"和"相关概念"三个章节
- "记忆要点"章节要根据笔记内容和老师讲课重点，提炼出便于记忆的关键信息，使用恰当的emoji符号
- 其他章节完全根据内容需要自由创造
- 章节标题要准确反映内容，便于快速定位信息
- 笔记内容要详细，包括但不限于：
  - 核心定义要准确、清晰、简洁
  - 记忆要点要突出重点、方便记忆
  - 相关概念要完整、准确、有意义
  - 案例或者示例要详细、清晰、有效

**分隔符使用**：
- 使用 === NOTE_SEPARATOR === 分隔不同的笔记
- 分隔符前后要有空行

## 内容组织自由度

除了上述固定技术要求外，你拥有完全的自由来：
- 创造最合适的章节标题，根据内容特点设计章节名称
- 决定章节数量和详略程度，重要内容详写，次要内容适度概括
- 调整信息重点和层次结构，把最重要的信息放在显眼位置
- 选择最有利于理解的组织方式，使用列表、引用、分级标题等
- 设计信息展示方式，如案例分析、要点列举、对比说明等

## 记忆要点设计指导

**记忆要点章节**是每个笔记的必需部分，用于提炼最关键的记忆信息：

**设计原则**：
- 基于老师的讲课重点和强调内容
- 使用简洁有力的表述，便于快速记忆
- 突出概念的核心特征和关键区别点
- 包含典型应用场景或考试要点

**表述方式**：
- 使用恰当的emoji符号增强视觉记忆
- 采用「关键词→核心含义」的简洁格式
- 可以使用口诀、对比、场景描述等记忆技巧
- 长度控制在1-3行，便于快速浏览

**常用emoji指引**：
- 🔮 用于核心概念或原理性内容
- 📱 用于典型场景或实际应用
- 💡 用于重要提醒或易错点
- ⚖️ 用于法律原则或判断标准
- 🎯 用于考试重点或答题要点
- ⚠️ 用于注意事项或例外情况

## 质量控制要点

- 确保每个笔记都能成为知识图谱中有价值的节点
- 双链关系要准确反映概念间的逻辑联系
- 避免孤立节点，每个概念都要与相关概念建立合理连接

**实用性质量**：
- 概念颗粒度要适合错题整理的需要
- 标签和分类要支持多角度检索
- 内容组织要便于快速定位和理解

## 分析和处理建议

1. **先理解再整理**：仔细分析老师的讲课内容和重点，理解知识点的核心价值
2. **以理解为目标**：思考什么样的组织方式最有助于学生理解和记忆
3. **保留教学特色**：如果老师善于举例，就重点保留例子；如果善于对比，就突出对比
4. **尊重内容特点**：有些概念适合逐层深入，有些适合要点列举，有些适合案例说明
5. **创造有意义的结构**：章节标题要准确反映内容，帮助快速定位信息

## 输出格式模板

=== NOTE_SEPARATOR ===
YAML:
---
title: "【{metadata['subject']}】具体概念名"
aliases: ["具体概念名", "相关别名"]
tags: ["{metadata['subject']}", "章节名称", "知识点类型", "重要程度"]
source: "{metadata['source']}"
course_url: "{metadata.get('course_url', '')}"
time_range: "开始时间-结束时间"
subject: "{metadata['subject']}"
exam_importance: "高/中/低"
created: "{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
---

CONTENT:
# 【{metadata['subject']}】具体概念名

## 核心定义

⏰ [MM:SS.mm]（如果有时间戳）
[准确的定义，保留老师的重要表述]

[根据实际内容智能创造最合适的章节结构]
[章节标题完全由你根据内容决定]
[可以是任何有助于理解的组织方式]

## 记忆要点

🔮 [关键记忆点1] — [简洁解释或记忆技巧]
📱 [关键记忆点2] — [典型场景或应用提示]
💡 [关键记忆点3] — [重要提醒或易错点]

## 相关概念

- [[【{metadata['subject']}】相关概念1|别名1]]
- [[【{metadata['subject']}】相关概念2|别名2]]
- [[【{metadata['subject']}】相关概念3|别名3]]

---
*视频时间段：[开始时间]-[结束时间]*（如果有时间戳）

=== NOTE_SEPARATOR ===

请开始分析字幕内容。记住：你正在为法考知识图谱创建节点，为法考Wiki创建条目，为错题整理系统创建知识点索引。每个笔记都要达到这三个目标的要求。倾向于超细化拆分，为每个独立概念创建完整而详细的笔记。无论如何，在将全部字幕转换成笔记之前，请不要停止输出，并且严格按照格式输出，不需要任何额外说明："""
    
    def _build_enhancement_prompt(self, all_notes: List[Dict], existing_concepts: Dict) -> str:
        """构建概念关系增强提示词"""
        notes_summary = "\n".join([f"- {note['yaml']['title']}" for note in all_notes])
        existing_concepts_list = existing_concepts.get('existing_concepts', [])
        
        return f"""你是法考知识体系专家。请分析以下新生成的笔记，优化其概念关系链接。

新生成的笔记：
{notes_summary}

现有概念库中的概念：
{existing_concepts_list[:50]}  # 限制长度

要求：
1. 检查每个笔记中的[[概念]]链接是否准确（格式为[[【科目】概念名|概念名（或者别名）]]）
2. 补充可能遗漏的重要概念关联
3. 确保链接的概念确实存在或应该存在
4. 移除无关或错误的概念链接
5. 只返回需要修改的笔记的概念链接部分

输出格式：
ENHANCEMENT:
笔记标题1:
- [[【科目】修正后的概念1|修正后的概念1（或者别名）]]
- [[【科目】修正后的概念2|修正后的概念2（或者别名）]]

笔记标题2:
- [[【科目】修正后的概念1|修正后的概念1（或者别名）]]
- [[【科目】修正后的概念2|修正后的概念2（或者别名）]]

如果某个笔记不需要修改，不要包含在输出中。"""
    
    def _build_single_note_enhancement_prompt(self, note_content: str, note_title: str, existing_concepts: Dict) -> str:
        """构建单个笔记增强的提示词"""
        existing_concepts_list = existing_concepts.get('existing_concepts', [])
        
        return f"""你是法考知识体系专家。请分析以下笔记，检查并优化其概念关系链接。

笔记标题：{note_title}

笔记内容：
{note_content}

现有概念库（前100个）：
{existing_concepts_list[:100]}

要求：
1. 检查笔记中现有的[[概念]]链接是否准确（格式为[[【科目】概念名|概念名（或者别名）]]）
2. 识别笔记中可能遗漏的重要概念关联
3. 只添加确实存在于概念库中的概念链接
4. 移除指向不存在概念的链接
5. 确保新增的概念链接与笔记内容高度相关
6. 双链格式要求：如果概念名有【科目】前缀，使用显示别名格式：[[【科目】概念名|概念名（或者别名）]]
7. 不要添加任何优化说明或额外内容
8. [时间戳]必须严格使用[MM:SS.mm]([分:秒.毫秒])格式，任何一位都不能省略。如[01:23.45]，如果分钟数为0，要保留，如[00:23.45]；秒和毫秒之间使用英文句点"."


如果需要修改，请输出：
MODIFIED: true
ENHANCED_CONTENT:
[修改后的完整笔记内容]

如果不需要修改，请输出：
MODIFIED: false

请开始分析，不要添加任何说明："""
    
    def _parse_ai_response(self, response_content: str) -> List[Dict[str, Any]]:
        """解析AI返回的多个笔记数据"""
        notes = []
        sections = response_content.split('=== NOTE_SEPARATOR ===')
        
        for section in sections:
            if section.strip():
                note_data = self._parse_single_note(section)
                if note_data:
                    notes.append(note_data)
        
        return notes
    
    def _parse_single_note(self, section: str) -> Optional[Dict[str, Any]]:
        """解析单个笔记的YAML和内容"""
        try:
            # 查找YAML和CONTENT部分
            yaml_start = section.find('YAML:')
            content_start = section.find('CONTENT:')
            
            if yaml_start == -1 or content_start == -1:
                return None
            
            yaml_section = section[yaml_start + 5:content_start].strip()
            content_section = section[content_start + 8:].strip()
            
            # 解析YAML
            yaml_content = yaml_section.replace('---', '').strip()
            # 尝试修复常见的YAML格式问题：确保冒号后有空格
            # 匹配行首的键名，后面紧跟冒号和非空白字符，并在冒号后添加空格
            yaml_content = re.sub(r'^(?P<key>\s*\S+?):(?P<value>\S.*)', r'\g<key>: \g<value>', yaml_content, flags=re.MULTILINE)
            yaml_data = yaml.safe_load(yaml_content)
            
            return {
                'yaml': yaml_data,
                'content': content_section
            }
        except Exception as e:
            print(f"⚠️ 解析笔记时出错: {e}")
            return None
    
    def _parse_enhancement_response(self, response: str, original_notes: List[Dict]) -> List[Dict]:
        """解析概念增强响应并应用到原始笔记"""
        try:
            # 提取增强部分
            enhancement_start = response.find('ENHANCEMENT:')
            if enhancement_start == -1:
                return original_notes
            
            enhancement_content = response[enhancement_start + 12:].strip()
            
            # 解析增强建议
            enhancements = {}
            current_title = None
            
            for line in enhancement_content.split('\n'):
                line = line.strip()
                if line.endswith(':') and not line.startswith('-'):
                    current_title = line[:-1]
                    enhancements[current_title] = []
                elif line.startswith('- [[') and current_title:
                    concept = re.findall(r'\[\[(.*?)\]\]', line)
                    if concept:
                        enhancements[current_title].append(f"[[{concept[0]}]]")
            
            # 应用增强到原始笔记
            enhanced_notes = []
            for note in original_notes:
                title = note['yaml']['title']
                if title in enhancements:
                    # 更新相关概念部分
                    content = note['content']
                    # 替换相关概念部分
                    concept_pattern = r'## 相关概念\n(.*?)(?=\n##|\n---|\Z)'
                    new_concepts = '\n'.join(f"- {concept}" for concept in enhancements[title])
                    content = re.sub(concept_pattern, f'## 相关概念\n{new_concepts}', content, flags=re.DOTALL)
                    note['content'] = content
                
                enhanced_notes.append(note)
            
            return enhanced_notes
        except Exception as e:
            print(f"⚠️ 应用概念增强时出错: {e}")
            return original_notes
    
    def _parse_single_note_enhancement_response(self, response: str, original_content: str) -> Optional[Dict]:
        """解析单个笔记增强响应"""
        try:
            if "MODIFIED: true" in response:
                content_start = response.find("ENHANCED_CONTENT:")
                if content_start != -1:
                    enhanced_content = response[content_start + 17:].strip()
                    
                    # 使用正则表达式处理可能的代码块包裹（支持语言标签）
                    # 匹配开头：```后跟可选的语言名称
                    # 匹配结尾：```可能前后有空白
                    code_block_pattern = re.compile(
                        r'^\s*```[a-zA-Z0-9_+-]*\s*\n?(.*?)\s*```\s*', 
                        re.DOTALL
                    )
                    
                    match = code_block_pattern.match(enhanced_content)
                    if match:
                        # 提取代码块内容
                        enhanced_content = match.group(1).strip()
                    else:
                        # 处理只有开头标记的情况
                        if enhanced_content.startswith('```'):
                            # 移除开头的```和可能存在的语言名称
                            enhanced_content = re.sub(r'^\s*```[a-zA-Z0-9_+-]*\s*', '', enhanced_content, 1)
                        
                        # 处理结尾标记
                        if enhanced_content.endswith('```'):
                            enhanced_content = re.sub(r'\s*```\s*', '', enhanced_content)
                        
                        # 确保去除多余空白
                        enhanced_content = enhanced_content.strip()
                    
                    return {
                        'modified': True,
                        'enhanced_content': enhanced_content
                    }
            
            return {'modified': False}
            
        except Exception as e:
            print(f"⚠️ 解析增强响应失败: {e}")
            return None
        
    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback
    
    def set_concurrent_config(self, config: ConcurrentConfig):
        """设置并发配置"""
        self.concurrent_config = config
    
    def _generate_notes_from_individual_segments(self, segments: List[Segment], 
                                           analysis_result: Dict, metadata: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        基于独立分段结果生成笔记（每个知识点对应一个段落）- 并发版本
        """
        knowledge_points = analysis_result.get('knowledge_points', [])
        
        # 验证分段数据
        valid_segments = []
        for i, segment in enumerate(segments, 1):
            if not segment.text.strip():
                print(f"⚠️ 跳过空分段 {i}")
                continue
                
            if len(segment.knowledge_points) != 1:
                print(f"⚠️ 分段 {i} 包含 {len(segment.knowledge_points)} 个知识点，跳过")
                continue
            
            kp_id = segment.knowledge_points[0]
            
            # 找到对应的知识点
            target_kp = None
            for kp in knowledge_points:
                if kp.get('id') == kp_id:
                    target_kp = kp
                    break
            
            if not target_kp:
                print(f"⚠️ 找不到知识点 {kp_id}，跳过分段 {i}")
                continue
            
            valid_segments.append((segment, target_kp))
        
        if not valid_segments:
            print("❌ 没有有效的分段可以处理")
            return []
        
        print(f"📝 开始并发处理 {len(valid_segments)} 个知识点...")
        
        # 检查是否应该使用并发处理
        if len(valid_segments) <= 2:
            # 如果知识点很少，使用传统的逐个处理方式
            print("🔄 知识点数量较少，使用传统方式处理...")
            return self._process_segments_traditionally(valid_segments, analysis_result, metadata)
        
        # 准备并发处理的数据
        knowledge_points_data = []
        for segment, target_kp in valid_segments:
            # 构建传递给并发处理器的数据结构
            kp_data = {
                'segment': segment,
                'target_kp': target_kp,
                'analysis_result': analysis_result,
                'metadata': metadata
            }
            kp_id = target_kp.get('id', 'unknown')
            knowledge_points_data.append((kp_id, kp_data))
        
        # 构建提示词生成函数
        def prompt_builder(kp_data):
            return self._build_single_knowledge_point_prompt(
                kp_data['segment'],
                kp_data['target_kp'],
                kp_data['analysis_result'],
                kp_data['metadata']
            )
        
        # 进度回调函数
        def progress_callback(completed, total):
            if self.progress_callback:
                self.progress_callback(completed, total)
            print(f"📊 处理进度: {completed}/{total} ({completed/total*100:.1f}%)")
        
        # 估计剩余的API调用次数（这里可以根据实际情况调整）
        estimated_remaining_calls = min(20, len(valid_segments))  # 保守估计
        
        try:
            # 执行并发处理
            results, stats = run_concurrent_processing(
                knowledge_points_data=knowledge_points_data,
                prompt_builder=prompt_builder,
                client=self.client,
                model=self.model,
                config=self.concurrent_config,
                progress_callback=progress_callback,
                estimated_remaining_calls=estimated_remaining_calls
            )
            
            # 处理并发结果
            all_notes = []
            failed_tasks = []
            
            for kp_id, original_data, result, error in results:
                if result is not None and error is None:
                    # 成功的任务
                    try:
                        parsed_note = self._parse_single_note_response(
                            result, 
                            original_data['target_kp'], 
                            original_data['metadata']
                        )
                        if parsed_note:
                            all_notes.append(parsed_note)
                            print(f"✅ 成功生成笔记: {original_data['target_kp'].get('concept_name', kp_id)}")
                        else:
                            print(f"⚠️ 解析笔记失败: {original_data['target_kp'].get('concept_name', kp_id)}")
                            failed_tasks.append((kp_id, original_data))
                    except Exception as e:
                        print(f"⚠️ 处理结果失败 {kp_id}: {e}")
                        failed_tasks.append((kp_id, original_data))
                else:
                    # 失败的任务
                    print(f"❌ 知识点处理失败 {kp_id}: {error}")
                    failed_tasks.append((kp_id, original_data))
            
            # 打印统计信息
            print(f"📊 并发处理统计:")
            print(f"  - 总任务数: {stats['total_tasks']}")
            print(f"  - 成功完成: {stats['completed_tasks']}")
            print(f"  - 失败任务: {stats['failed_tasks']}")
            print(f"  - 总重试次数: {stats['total_retries']}")
            print(f"  - 总处理时间: {stats['total_processing_time']:.2f}秒")
            print(f"  - 处理批次: {stats['batches_processed']}")
            
            # 如果有失败的任务，可以选择用传统方式重试
            if failed_tasks and len(failed_tasks) <= 3:  # 只对少量失败任务重试
                print(f"🔄 对 {len(failed_tasks)} 个失败任务使用传统方式重试...")
                retry_segments = [(data['segment'], data['target_kp']) for _, data in failed_tasks]
                retry_notes = self._process_segments_traditionally(retry_segments, analysis_result, metadata)
                all_notes.extend(retry_notes)
            
            print(f"✅ 并发处理完成，共生成 {len(all_notes)} 个笔记")

            if all_notes:
                print(f"\n🔍 调试输出：共 {len(all_notes)} 个笔记")
                for i, note in enumerate(all_notes[:3]):  # 只输出前3个避免太多日志
                    debug_note_structure(note, i)
                
                # ########################################################self._validate_notes_structure(all_notes)

            print(f"✅ 独立分段处理完成，共生成 {len(all_notes)} 个笔记")
            return all_notes
            
        except Exception as e:
            print(f"❌ 并发处理失败，回退到传统方式: {e}")
            return self._process_segments_traditionally(valid_segments, analysis_result, metadata)
    
    def _process_segments_traditionally(self, valid_segments: List[Tuple], 
                                      analysis_result: Dict, metadata: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        传统方式处理分段（逐个处理，作为并发处理的后备方案）
        """
        all_notes = []
        total_segments = len(valid_segments)
        
        for i, (segment, target_kp) in enumerate(valid_segments, 1):
            kp_id = target_kp.get('id', 'unknown')
            
            # 构建单个知识点的处理提示词
            single_kp_prompt = self._build_single_knowledge_point_prompt(
                segment, target_kp, analysis_result, metadata
            )
            
            try:
                print(f"🤖 处理知识点: {target_kp.get('concept_name', kp_id)} ({i}/{total_segments})")
                
                # 调用进度回调
                if self.progress_callback:
                    self.progress_callback(i-1, total_segments)
                
                # 调用AI处理单个知识点
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": single_kp_prompt}],
                    temperature=0,
                )
                
                # 解析AI返回的单个笔记（不包含分隔符）
                note_content = response.choices[0].message.content.strip()
                
                # 解析单个笔记
                parsed_note = self._parse_single_note_response(note_content, target_kp, metadata)
                
                if parsed_note:
                    all_notes.append(parsed_note)
                    print(f"✅ 成功生成笔记: {target_kp.get('concept_name', kp_id)}")
                else:
                    print(f"⚠️ 解析笔记失败: {target_kp.get('concept_name', kp_id)}")
                
            except Exception as e:
                print(f"⚠️ 处理知识点 {kp_id} 失败: {e}")
                continue
        
        # 最后一次调用进度回调
        if self.progress_callback:
            self.progress_callback(total_segments, total_segments)
        
        print(f"✅ 传统方式处理完成，共生成 {len(all_notes)} 个笔记")
        return all_notes
    
    def estimate_remaining_api_calls(self) -> int:
        """
        估计剩余的API调用次数
        
        这是一个简单的实现，实际项目中可能需要更复杂的逻辑
        比如跟踪实际的API使用情况
        
        Returns:
            估计的剩余调用次数
        """
        # 这里可以根据实际情况实现更复杂的逻辑
        # 比如记录开始时间，计算已用次数等
        return 20  # 保守估计

def debug_note_structure(note: Dict[str, Any], note_index: int = 0):
    """调试输出笔记结构"""
    print(f"\n=== 调试笔记 {note_index + 1} 结构 ===")
    print(f"笔记键: {list(note.keys())}")
    
    if 'yaml' in note:
        print(f"YAML类型: {type(note['yaml'])}")
        if isinstance(note['yaml'], dict):
            print(f"YAML键: {list(note['yaml'].keys())}")
            print(f"标题: {note['yaml'].get('title', '未找到标题')}")
        else:
            print(f"YAML内容: {note['yaml']}")
    else:
        print("❌ 缺少yaml字段")
    
    if 'content' in note:
        content_length = len(note['content']) if note['content'] else 0
        print(f"内容长度: {content_length}")
        print(f"内容前100字符: {note['content'][:100] if note['content'] else '空内容'}")
    else:
        print("❌ 缺少content字段")
    print("=" * 40)