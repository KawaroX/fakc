# ai_processor.py
import yaml
import re
import datetime
import json
from openai import OpenAI
from typing import List, Dict, Any, Optional

class AIProcessor:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
    
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

    # 第二步：详细笔记整理
    def generate_notes_step2(self, analysis_result: Dict, subtitle_content: str, metadata: Dict[str, str]) -> List[Dict[str, Any]]:
        """根据第一步结果生成最终笔记"""
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
            print(f"❌ 第二步笔记生成失败: {e}")
            return []

    # 旧版兼容方法（单步处理）
    def extract_all_knowledge_points(self, subtitle_content: str, metadata: Dict[str, str]) -> List[Dict[str, Any]]:
        """一次性处理整个字幕（兼容旧版）"""
        # 使用新两步法处理
        analysis = self.extract_knowledge_points_step1(subtitle_content, metadata)
        return self.generate_notes_step2(analysis, subtitle_content, metadata)
    
    # 新增提示词模板常量
    STEP1_PROMPT_TEMPLATE = """\
## 🎯 步骤一：知识点分析与架构构建

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

```json
（保持原始JSON结构不变）
```"""

    STEP2_PROMPT_TEMPLATE = """\
## 🎯 步骤二：详细笔记整理

你是专业的法考笔记整理专家。请根据前一步的分析结果和原始字幕内容，生成完整的Obsidian笔记。

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

**完全依据分析结果**：严格按照第一步识别的知识点列表生成笔记
**保持教学原味**：充分利用分析结果中的teacher_original、examples等信息
**结构智能设计**：根据concept_type设计最适合的章节结构
**双链精确建立**：使用relationships信息建立准确的概念关联

## 技术规范

**YAML元数据**：
```yaml
title: "【{subject}】{{concept_name}}"
aliases: ["{{concept_name}}"]
tags: ["{subject}", "根据concept_type确定"]
source: "{source}"
course_url: "{course_url}"
time_range: "{{time_range}}"
exam_importance: "{{importance_level}}"
```

**双链格式**：
- [[【{subject}】概念名|概念名]]
- 根据relationships精确建立

**时间戳格式**：
- 严格使用[MM:SS.mm]
- 从time_range中提取

## 输出格式

每个笔记使用以下格式：
```
=== NOTE_SEPARATOR ===
（保持原始笔记格式不变）
```"""
    
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
        """增强单个笔记的概念关系"""
        prompt = self._build_single_note_enhancement_prompt(note_content, note_title, existing_concepts)
        
        try:
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

            return self._parse_single_note_enhancement_response(
                response.choices[0].message.content, 
                note_content
            )
        except Exception as e:
            print(f"❌ AI增强单个笔记失败: {e}")
            return None
    
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

- [[【{metadata['subject']}】相关概念1/别名1]]
- [[【{metadata['subject']}】相关概念2/别名2]]
- [[【{metadata['subject']}】相关概念3/别名3]]

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
8. [时间戳]必须严格使用[MM:SS.mm]([分:秒.毫秒])格式，任何一位都不能省略。如[01:23.45]，如果分钟数为0，要保留，如[00:23.45]；秒和毫秒之间使用英文句点“.”


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
                        r'^\s*```[a-zA-Z0-9_+-]*\s*\n?(.*?)\s*```\s*$', 
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
                            enhanced_content = re.sub(r'\s*```\s*$', '', enhanced_content)
                        
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
