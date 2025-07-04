# ai_processor.py
import yaml
import re
from openai import OpenAI
from typing import List, Dict, Any, Optional

class AIProcessor:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
    
    def extract_all_knowledge_points(self, subtitle_content: str, metadata: Dict[str, str]) -> List[Dict[str, Any]]:
        """一次性处理整个字幕，返回所有知识点的结构化数据"""
        prompt = self._build_extraction_prompt(subtitle_content, metadata)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            
            return self._parse_ai_response(response.choices[0].message.content)
        except Exception as e:
            print(f"❌ AI处理出错: {e}")
            return []
    
    def enhance_concept_relationships(self, all_notes: List[Dict], existing_concepts: Dict) -> List[Dict]:
        """让AI分析所有笔记内容，增强概念关系"""
        if not all_notes:
            return all_notes
            
        prompt = self._build_enhancement_prompt(all_notes, existing_concepts)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
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
        return f"""你是专业的法考笔记整理专家。请分析以下字幕内容,提取所有独立的知识点,为每个知识点生成一个完整的Obsidian笔记。

字幕内容:
{subtitle_content}

课程信息:
- 科目:{metadata['subject']}
- 来源:{metadata['source']}
- 课程链接:{metadata.get('course_url', '未提供')}

## 核心指导原则

**内容完整性**:保留所有有价值的信息,包括老师的例子、案例、解释、强调、实务经验等。宁可详细也不要遗漏。

**结构智能性**:完全根据实际内容决定笔记结构。分析老师的讲课重点和方式,设计最适合的章节结构来组织信息。

**理解导向**:以帮助学生理解和掌握知识为目标,选择最有利于学习的信息组织方式。

**合理粒度**:正确识别知识点的独立性和包含关系,既不过度合并也不过度拆分。

## 知识点拆分原则

**应该拆分的情况:**
- 并列的概念要素(如法律关系三要素:主体、客体、内容)
- 不同类型的分类(如请求权的物权请求权、债权请求权、人格权请求权)
- 相互独立的原则或制度(如平等原则、自愿原则、诚信原则)
- 具有独立定义和特征的概念(如支配权vs请求权)

**应该合并的情况:**
- 某个制度的例外情形(如违约损害赔偿的几种例外情形)
- 某个概念下的具体细节要求(如合同成立的具体要件)
- 程序性的连续步骤(如诉讼的各个阶段)

**双重处理原则:**
如果某个大概念包含多个重要的子概念,可以采用"总-分"模式:
- 创建一个总览性笔记(概述整体框架和相互关系)
- 为每个重要子概念创建独立的详细笔记
- 通过双链建立清晰的层次关系

## 固定要求(不可更改)

1. **YAML结构**:严格按照指定格式,字段后必须有空格
2. **分隔符**:使用 === NOTE_SEPARATOR === 分隔不同笔记
3. **时间戳格式**:必须使用[MM:SS.mm]格式,如[01:23.45]、[00:23.45]
4. **标题格式**:【{metadata['subject']}】具体概念名
5. **别名设置**:第一个别名必须是去掉科目前缀的概念名
6. **双链格式**:引用其他概念时使用[[【科目】概念名|概念名]]格式
7. **必需章节**:每个笔记都必须有"核心定义"和"相关概念"两个章节
8. **不要添加额外说明**:严格按内容生成,不要在末尾添加总结或说明

## 示例说明

**正确拆分示例:**
如果老师讲"民事法律关系三要素",应该创建:
- 【民法】民事法律关系三要素(总览)
- 【民法】民事法律关系主体
- 【民法】民事法律关系客体  
- 【民法】民事法律关系内容

**正确合并示例:**
如果老师讲"违约损害赔偿的例外情形",包含无偿合同和几种特殊有偿合同,应该创建:
- 【民法】违约损害赔偿的例外情形(包含所有例外情形)

## 内容组织的自由度

除固定要求外,你有完全自由来:
- 创造最合适的章节标题
- 决定章节数量和详略程度
- 调整信息重点和层次结构
- 选择最有利于理解的组织方式

## 输出格式

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
created: "{{date:YYYY-MM-DD}}"
---

CONTENT:
# 【{metadata['subject']}】具体概念名

## 核心定义
⏰ [MM:SS.mm]
[准确的定义,保留老师的重要表述]

[根据内容智能创造最合适的章节结构]

## 相关概念
- [[【{metadata['subject']}】相关概念1|相关概念1]]
- [[【{metadata['subject']}】相关概念2|相关概念2]]

---
*视频时间段:[开始时间]-[结束时间]*

=== NOTE_SEPARATOR ===

请分析字幕内容,正确识别每个独立的知识点,合理判断拆分粒度,为每个知识点设计最适合的笔记结构:你是专业的法考笔记整理专家。请分析以下字幕内容，提取所有独立的知识点，为每个知识点生成一个完整的Obsidian笔记。

字幕内容：
{subtitle_content}

课程信息：
- 科目：{metadata['subject']}
- 来源：{metadata['source']}
- 课程链接：{metadata.get('course_url', '未提供')}

## 核心指导原则

**内容完整性**：保留所有有价值的信息，包括老师的例子、案例、解释、强调、实务经验等。宁可详细也不要遗漏。

**结构智能性**：完全根据实际内容决定笔记结构。你需要分析老师的讲课重点和方式，然后设计最适合的章节结构来组织信息。不要被任何预设的模板限制。

**理解导向**：以帮助学生理解和掌握知识为目标，选择最有利于学习的信息组织方式。

## 固定要求（不可更改）

1. **YAML结构**：严格按照指定格式
2. **分隔符**：使用 === NOTE_SEPARATOR === 分隔不同笔记
3. **时间戳格式**：必须使用[HH:MM.SS]格式，如[01:23.45]
4. **标题格式**：【{metadata['subject']}】具体概念名
5. **别名设置**：第一个别名必须是去掉科目前缀的概念名
6. **双链格式**：引用其他概念时使用[[【科目】概念名|概念名]]格式
7. **必需章节**：每个笔记都必须有"核心定义"和"相关概念"两个章节
8. **不要添加额外说明**：严格按内容生成，不要在末尾添加总结或说明

## 内容组织的自由度

除了上述固定要求外，你有完全的自由来：

- **创造章节标题**：根据内容需要创造最合适的章节名称
- **决定章节数量**：可以是3个章节，也可以是8个章节，完全由内容决定
- **调整信息重点**：把最重要的信息放在最显眼的位置
- **选择详略程度**：重要内容详写，次要内容简写
- **设计信息层次**：使用不同级别的标题、列表、引用等来组织信息

## 分析和处理建议

1. **先理解再整理**：仔细分析老师的讲课内容和重点，理解知识点的核心价值
2. **以理解为目标**：思考什么样的组织方式最有助于学生理解和记忆
3. **保留教学特色**：如果老师善于举例，就重点保留例子；如果善于对比，就突出对比
4. **尊重内容特点**：有些概念适合逐层深入，有些适合要点列举，有些适合案例说明
5. **创造有意义的结构**：章节标题要准确反映内容，帮助快速定位信息

## 输出格式

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
created: "{{date:YYYY-MM-DD}}"
---

CONTENT:
# 【{metadata['subject']}】具体概念名

## 核心定义
⏰ [HH:MM.SS]
[准确的定义，保留老师的重要表述]

[在这里根据实际内容智能创造最合适的章节结构]
[章节标题完全由你根据内容决定]
[可以是任何有助于理解的组织方式]

## 相关概念
- [[【{metadata['subject']}】相关概念1|相关概念1]]
- [[【{metadata['subject']}】相关概念2|相关概念2]]

---
*视频时间段：[开始时间]-[结束时间]*

=== NOTE_SEPARATOR ===

请分析字幕内容，智能判断每个知识点的特点，为每个知识点设计最适合的笔记结构："""
    
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
1. 检查每个笔记中的[[概念]]链接是否准确
2. 补充可能遗漏的重要概念关联
3. 确保链接的概念确实存在或应该存在
4. 移除无关或错误的概念链接
5. 只返回需要修改的笔记的概念链接部分

输出格式：
ENHANCEMENT:
笔记标题1:
- [[修正后的概念1]]
- [[修正后的概念2]]

笔记标题2:
- [[修正后的概念1]]
- [[修正后的概念2]]

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
1. 检查笔记中现有的[[概念]]链接是否准确
2. 识别笔记中可能遗漏的重要概念关联
3. 只添加确实存在于概念库中的概念链接
4. 移除指向不存在概念的链接
5. 确保新增的概念链接与笔记内容高度相关
6. 双链格式要求：如果概念名有【科目】前缀，使用显示别名格式：[[【科目】概念名|概念名]]
7. 不要添加任何优化说明或额外内容
8. [时间戳]必须严格使用[MM:SS.mm](分:秒.毫秒])格式，任何一位都不能省略。如[01:23.45]，如果分钟数为0，要保留，如[00:23.45]；秒和毫秒之间使用英文句点“.”


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
                    return {
                        'modified': True,
                        'enhanced_content': enhanced_content
                    }
            
            return {'modified': False}
            
        except Exception as e:
            print(f"⚠️ 解析增强响应失败: {e}")
            return None
