import streamlit as st
import os
import sys
import io
import re
import datetime
import yaml
import re

# 确保项目根目录在sys.path中，以便导入其他模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from config import Config
from input_manager import InputManager
from ai_processor import AIProcessor
from concept_manager import ConceptManager
from note_generator import ObsidianNoteGenerator
from timestamp_linker import TimestampLinker
from siliconflow_concept_enhancer import SiliconFlowConceptEnhancer

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

# 重新定义LawExamNoteProcessor类，使其适应Streamlit的输入/输出
class StreamlitLawExamNoteProcessor:
    def __init__(self):
        self.subtitle_ai_processor = AIProcessor(
            Config.SUBTITLE_PROCESSING_API_KEY, 
            Config.SUBTITLE_PROCESSING_BASE_URL, 
            Config.SUBTITLE_PROCESSING_MODEL
        )
        self.concept_enhancement_ai_processor = AIProcessor(
            Config.CONCEPT_ENHANCEMENT_API_KEY, 
            Config.CONCEPT_ENHANCEMENT_BASE_URL, 
            Config.CONCEPT_ENHANCEMENT_MODEL
        )
        self.concept_manager = ConceptManager(Config.OBSIDIAN_VAULT_PATH)
        self.note_generator = ObsidianNoteGenerator("temp")
        self.timestamp_linker = TimestampLinker(Config.OBSIDIAN_VAULT_PATH)
        self.siliconflow_enhancer = None

    def _get_siliconflow_enhancer(self):
        """获取SiliconFlow增强器实例（延迟初始化）"""
        if self.siliconflow_enhancer is None:
            try:
                self.siliconflow_enhancer = SiliconFlowConceptEnhancer(
                    Config.SILICONFLOW_API_KEY,
                    self.concept_enhancement_ai_processor,
                    self.concept_manager
                )
                st.success("✅ SiliconFlow BGE增强器已初始化")
            except Exception as e:
                st.error(f"❌ 初始化SiliconFlow增强器失败: {e}")
                return None
        return self.siliconflow_enhancer

    def process_ai_formatted_text(self, ai_text: str, course_url: str, selected_subject: str, source_info: str):
        """
        处理AI格式的文本，直接解析并生成笔记
        
        Args:
            ai_text: AI格式的文本内容
            course_url: 课程URL
            selected_subject: 选择的科目
            source_info: 来源信息
        """
        st.info("🚀 开始解析AI格式文本...")
        
        try:
            # 1. 解析AI格式的文本
            st.write("📖 解析文本内容...")
            all_notes = self.subtitle_ai_processor._parse_ai_response(ai_text)
            
            if not all_notes:
                st.warning("❌ 未能解析到有效的笔记格式，请检查文本格式")
                st.info("💡 提示：确保文本包含正确的 === NOTE_SEPARATOR === 分隔符和YAML/CONTENT部分")
                return []
            
            st.success(f"✅ 解析到 {len(all_notes)} 个笔记")
            
            # 2. 为每个笔记补充必要的元数据
            for note in all_notes:
                if 'yaml' in note and note['yaml']:
                    # 确保有必要的字段
                    note['yaml']['course_url'] = course_url
                    note['yaml']['source'] = source_info
                    note['yaml']['subject'] = selected_subject
                    
                    # 如果标题中没有科目前缀，添加上
                    title = note['yaml'].get('title', '')
                    if not title.startswith(f'【{selected_subject}】'):
                        note['yaml']['title'] = f'【{selected_subject}】{title}'
            
            # 3. 扫描现有概念库
            st.write("🔍 扫描现有概念库...")
            self.concept_manager.scan_existing_notes()
            existing_concepts = self.concept_manager.get_all_concepts_for_ai()
            
            # 4. AI增强：优化概念关系
            st.write("🔗 AI正在优化概念关系...")
            enhanced_notes = self.concept_enhancement_ai_processor.enhance_concept_relationships(
                all_notes, existing_concepts
            )
            
            # 5. 确定输出路径
            output_path = Config.get_output_path(selected_subject)
            os.makedirs(output_path, exist_ok=True)
            
            # 6. 生成笔记文件
            st.write(f"📝 生成笔记文件到: {output_path}")
            created_files = []
            for note_data in enhanced_notes:
                file_path = self.note_generator.create_note_file(
                    note_data, 
                    output_path
                )
                created_files.append(file_path)
            
            # 7. 更新概念数据库
            self.concept_manager.update_database(enhanced_notes)
            
            st.success(f"\n🎉 成功生成 {len(created_files)} 个笔记文件")
            st.write(f"📁 保存位置: {output_path}")
            
            st.subheader("📋 生成的笔记:")
            for file_path in created_files:
                filename = os.path.basename(file_path)
                st.markdown(f"  - `{filename}`")
            
            # 8. 自动进行时间戳链接化处理
            if course_url:
                st.info("\n🔗 自动进行时间戳链接化处理...")
                self.timestamp_linker.process_subject_notes(selected_subject)
                st.success("✅ 时间戳链接化处理完成。")
            
            return created_files
            
        except Exception as e:
            st.error(f"❌ 处理过程中出错: {e}")
            st.exception(e)
            return []

    def process_subtitle_file_streamlit(self, uploaded_file, course_url, selected_subject, source_info):
        """处理单个字幕文件的完整流程，适配Streamlit输入。"""
        st.info("🚀 开始处理字幕文件...")
        
        try:
            # 1. 从UploadedFile读取字幕内容
            st.write("📖 读取字幕文件...")
            subtitle_content = uploaded_file.getvalue().decode("utf-8")
            
            if not subtitle_content.strip():
                st.warning("❌ 字幕文件为空")
                return []
            
            # 确定输出路径
            output_path = Config.get_output_path(selected_subject)
            os.makedirs(output_path, exist_ok=True)
            
            # 模拟subtitle_info，加入course_url和source
            subtitle_info = {
                'file_path': uploaded_file.name,
                'course_url': course_url,
                'subject': selected_subject,
                'output_path': output_path,
                'source': source_info
            }
            
            # 2. 扫描现有概念库
            st.write("🔍 扫描现有概念库...")
            self.concept_manager.scan_existing_notes()
            existing_concepts = self.concept_manager.get_all_concepts_for_ai()
            
            # 3. AI处理：一次性提取所有知识点
            st.write("🤖 AI正在分析字幕内容，提取知识点...")
            all_notes = self.subtitle_ai_processor.extract_all_knowledge_points(
                subtitle_content, subtitle_info
            )
            
            if not all_notes:
                st.warning("❌ 未能提取到知识点，请检查字幕内容")
                return []
            
            st.success(f"✅ 提取到 {len(all_notes)} 个知识点")
            
            # 4. AI增强：优化概念关系
            st.write("🔗 AI正在优化概念关系...")
            enhanced_notes = self.concept_enhancement_ai_processor.enhance_concept_relationships(
                all_notes, existing_concepts
            )
            
            # 5. 生成笔记文件
            st.write(f"📝 生成笔记文件到: {output_path}")
            created_files = []
            for note_data in enhanced_notes:
                if 'yaml_front_matter' not in note_data:
                    note_data['yaml_front_matter'] = {}
                note_data['yaml_front_matter']['course_url'] = course_url
                
                file_path = self.note_generator.create_note_file(
                    note_data, 
                    output_path
                )
                created_files.append(file_path)
            
            # 6. 更新概念数据库
            self.concept_manager.update_database(enhanced_notes)
            
            st.success(f"\n🎉 成功生成 {len(created_files)} 个笔记文件")
            st.write(f"📁 保存位置: {output_path}")
            
            st.subheader("📋 生成的笔记:")
            for file_path in created_files:
                filename = os.path.basename(file_path)
                st.markdown(f"  - `{filename}`")
            
            # 7. 自动进行时间戳链接化处理
            st.info("\n🔗 自动进行时间戳链接化处理...")
            self.timestamp_linker.process_subject_notes(selected_subject)
            st.success("✅ 时间戳链接化处理完成。")

            return created_files
            
        except Exception as e:
            st.error(f"❌ 处理过程中出错: {e}")
            st.exception(e)
            return []

    def _collect_all_law_notes(self):
        """收集所有法考笔记，适配Streamlit输出"""
        notes = []
        
        for subject_name, folder_name in Config.SUBJECT_MAPPING.items():
            subject_path = os.path.join(Config.OBSIDIAN_VAULT_PATH, folder_name)
            
            if not os.path.exists(subject_path):
                st.warning(f"⚠️ 科目文件夹不存在: {subject_path}")
                continue
            
            for root, dirs, files in os.walk(subject_path):
                for file in files:
                    if file.endswith('.md') and file != "概念数据库.md":
                        file_path = os.path.join(root, file)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            yaml_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
                            if yaml_match:
                                yaml_data = yaml.safe_load(yaml_match.group(1))
                                title = yaml_data.get('title', os.path.splitext(file)[0])
                            else:
                                title = os.path.splitext(file)[0]
                            
                            notes.append({
                                'title': title,
                                'file_path': file_path,
                                'content': content,
                                'subject': subject_name
                            })
                            
                        except Exception as e:
                            st.warning(f"⚠️ 读取笔记失败 {file_path}: {e}")
        
        return notes

    def _collect_subject_notes_by_name(self, subject: str):
        """根据科目名称收集笔记，适配Streamlit输出"""
        subject_folder = Config.get_subject_folder_name(subject)
        subject_path = os.path.join(Config.OBSIDIAN_VAULT_PATH, subject_folder)
        
        if not os.path.exists(subject_path):
            st.error(f"❌ 科目文件夹不存在: {subject_folder}")
            return []
        
        notes = []
        for root, dirs, files in os.walk(subject_path):
            for file in files:
                if file.endswith('.md') and file not in ["概念数据库.md", "概念嵌入缓存_BGE.json"]:
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        yaml_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
                        if yaml_match:
                            yaml_data = yaml.safe_load(yaml_match.group(1))
                            title = yaml_data.get('title', os.path.splitext(file)[0])
                        else:
                            title = os.path.splitext(file)[0]
                        
                        notes.append({
                            'title': title,
                            'file_path': file_path,
                            'content': content,
                            'subject': subject
                        })
                    except Exception as e:
                        st.warning(f"⚠️ 读取失败 {file}: {e}")
        
        return notes

    def _process_notes_enhancement(self, notes):
        """批量处理笔记增强，适配Streamlit输出"""
        existing_concepts = self.concept_manager.get_all_concepts_for_ai()
        
        enhanced_count = 0
        failed_count = 0
        
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, note_info in enumerate(notes, 1):
            status_text.text(f"🔄 处理 {i}/{len(notes)}: {note_info['title']}")
            progress_bar.progress(i / len(notes))
            
            try:
                enhancement_result = self.concept_enhancement_ai_processor.enhance_single_note_concepts(
                    note_info['content'], 
                    note_info['title'],
                    existing_concepts
                )
                
                if enhancement_result and enhancement_result.get('modified', False):
                    backup_path = note_info['file_path'] + '.backup'
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(note_info['content'])
                    
                    with open(note_info['file_path'], 'w', encoding='utf-8') as f:
                        f.write(enhancement_result['enhanced_content'])
                    
                    os.remove(backup_path)
                    
                    enhanced_count += 1
                else:
                    pass
                    
            except Exception as e:
                failed_count += 1
                st.error(f"  ❌ 增强失败 {note_info['title']}: {e}")
        
        progress_bar.empty()
        status_text.empty()

        st.success(f"\n🎉 处理完成！")
        st.write(f"  ✅ 成功增强: {enhanced_count} 个")
        st.write(f"  ⚠️ 无需修改: {len(notes) - enhanced_count - failed_count} 个")
        st.write(f"  ❌ 处理失败: {failed_count} 个")
        
        if enhanced_count > 0:
            st.info(f"\n📚 重新扫描更新概念数据库...")
            self.concept_manager.scan_existing_notes()

    def show_concept_database_status(self):
        """查看概念数据库状态，适配Streamlit输出"""
        st.subheader("📊 概念数据库状态")
        st.markdown("---")
        
        if self.concept_manager.load_database_from_file():
            total_concepts = len(self.concept_manager.concept_database)
            st.success(f"✅ 数据库已存在: {total_concepts} 个概念")
            
            subject_stats = {}
            for concept, data in self.concept_manager.concept_database.items():
                subject = data.get('subject', '未知')
                subject_stats[subject] = subject_stats.get(subject, 0) + 1
            
            st.markdown("\n**📚 各科目概念统计:**")
            for subject, count in sorted(subject_stats.items()):
                folder_name = Config.get_subject_folder_name(subject) if subject in Config.SUBJECT_MAPPING else subject
                st.write(f"  - **{folder_name}**: {count} 个概念")
            
            st.markdown("\n**📄 数据库文件状态:**")
            
            md_file = os.path.join(Config.OBSIDIAN_VAULT_PATH, "概念数据库.md")
            if os.path.exists(md_file):
                file_size = os.path.getsize(md_file) / 1024
                mtime = os.path.getmtime(md_file)
                last_modified = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                st.write(f"  - 📝 `概念数据库.md`: {file_size:.1f} KB (更新: {last_modified})")
            else:
                st.warning(f"  - 📝 `概念数据库.md`: ❌ 不存在")
            
            json_file = os.path.join(Config.OBSIDIAN_VAULT_PATH, "概念数据库.json")
            if os.path.exists(json_file):
                file_size = os.path.getsize(json_file) / 1024
                mtime = os.path.getmtime(json_file)
                last_modified = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                st.write(f"  - 📊 `概念数据库.json`: {file_size:.1f} KB (更新: {last_modified})")
            else:
                st.warning(f"  - 📊 `概念数据库.json`: ❌ 不存在")
                
        else:
            st.error("❌ 概念数据库不存在")
            st.info("💡 建议: 先处理一些字幕文件或运行笔记增强功能来建立数据库")
        
        st.markdown("---")

    def show_subject_mapping(self):
        """显示科目文件夹映射，适配Streamlit输出"""
        st.subheader("📚 科目文件夹映射:")
        st.markdown("---")
        for i, (subject, folder) in enumerate(Config.SUBJECT_MAPPING.items(), 1):
            folder_path = Config.get_output_path(subject)
            exists_icon = "✅" if os.path.exists(folder_path) else "📁"
            st.write(f"  {exists_icon} **{subject}** -> `{folder}`")
        st.markdown("---")


# Streamlit UI
st.set_page_config(page_title="法考字幕转Obsidian笔记处理器", layout="wide")

st.title("🎓 法考字幕转Obsidian笔记处理器")
st.markdown("---")

# 初始化处理器
if 'processor' not in st.session_state:
    st.session_state.processor = StreamlitLawExamNoteProcessor()
processor = st.session_state.processor

# 确保基础目录存在
Config.ensure_directories()

# 侧边栏菜单
st.sidebar.header("菜单")
menu_choice = st.sidebar.radio(
    "选择功能",
    ("处理新字幕文件", "直接输入AI格式文本", "增强现有笔记概念关系", "时间戳链接化处理", "查看概念数据库状态", "科目文件夹映射")
)

if menu_choice == "处理新字幕文件":
    st.header("处理新字幕文件")
    
    uploaded_file = st.file_uploader("上传字幕文件 (.srt, .txt)", type=["srt", "txt", "lrc"])
    
    # 初始化session state中的source_input默认值
    if 'source_input_default_subtitle' not in st.session_state:
        st.session_state.source_input_default_subtitle = ""

    # 当上传文件变化时，更新session state中的默认值
    if uploaded_file is not None and st.session_state.source_input_default_subtitle != uploaded_file.name:
        st.session_state.source_input_default_subtitle = uploaded_file.name
        # Streamlit会在文件上传后自动重新运行脚本，所以这里不需要st.experimental_rerun()

    raw_course_url = st.text_input("输入课程视频URL (可选，用于时间戳链接)", "", key="raw_course_url_subtitle")
    course_url = extract_url_from_text(raw_course_url) # 立即提取URL
    
    source_input = st.text_input("输入来源信息 (可选，默认为文件名)", value=st.session_state.source_input_default_subtitle, key="source_input_subtitle")
    
    subjects = list(Config.SUBJECT_MAPPING.keys())
    selected_subject = st.selectbox("选择科目", subjects, key="selected_subject_subtitle")
    
    if st.button("开始处理"):
        if uploaded_file is not None:
            # final_source现在直接使用source_input的值，因为其默认值已动态更新
            final_source = source_input 
            with st.spinner("正在处理，请稍候..."):
                processor.process_subtitle_file_streamlit(uploaded_file, course_url, selected_subject, final_source)
        else:
            st.warning("请先上传字幕文件！")

elif menu_choice == "直接输入AI格式文本":
    st.header("直接输入AI格式文本")
    st.info("💡 在这里可以直接粘贴AI生成的笔记格式文本，系统会自动解析并生成Obsidian笔记。")
    
    # 显示格式示例
    with st.expander("查看AI格式示例"):
        st.code("""=== NOTE_SEPARATOR ===
YAML:
---
title: "【民法】物权法基础"
aliases: ["物权法基础", "物权基本概念"]
tags: ["民法", "物权法", "基础概念", "高"]
source: "法考精讲课程"
course_url: "https://www.bilibili.com/video/BV1xxx"
time_range: "00:00-05:30"
subject: "民法"
exam_importance: "高"
created: "{{date:YYYY-MM-DD}}"
---

CONTENT:
# 【民法】物权法基础

## 核心定义
⏰ [00:15.30]
物权是指权利人依法对特定的物享有直接支配和排他的权利...

## 物权的特征
⏰ [01:23.45]
1. 支配性：权利人可以直接支配物
2. 排他性：一物一权原则
...

## 相关概念
- [[【民法】债权|债权]]
- [[【民法】所有权|所有权]]

---
*视频时间段:[00:00]-[05:30]*

=== NOTE_SEPARATOR ===
[下一个笔记...]""", language="markdown")
    
    # 输入区域
    ai_text = st.text_area(
        "粘贴AI格式的文本内容",
        height=400,
        placeholder="将AI生成的完整格式文本粘贴到这里...\n\n确保包含：\n- === NOTE_SEPARATOR === 分隔符\n- YAML: 部分\n- CONTENT: 部分",
        help="请确保文本格式正确，包含所有必要的分隔符和标记",
        key="ai_text_input"
    )
    
    # 课程信息
    st.subheader("课程信息")
    col1, col2 = st.columns(2)
    
    with col1:
        raw_course_url = st.text_input("课程视频URL (可选)", "", help="用于生成时间戳链接", key="raw_course_url_ai_text")
        course_url = extract_url_from_text(raw_course_url) # 立即提取URL
        source_input = st.text_input("来源信息", "手动输入", help="笔记的来源说明", key="source_input_ai_text")
    
    with col2:
        subjects = list(Config.SUBJECT_MAPPING.keys())
        selected_subject = st.selectbox("选择科目", subjects, help="笔记将保存到对应科目文件夹", key="selected_subject_ai_text")
    
    # 预览功能
    if ai_text.strip():
        with st.expander("预览解析结果"):
            try:
                preview_notes = processor.subtitle_ai_processor._parse_ai_response(ai_text)
                if preview_notes:
                    st.success(f"✅ 可以解析到 {len(preview_notes)} 个笔记")
                    for i, note in enumerate(preview_notes, 1):
                        if 'yaml' in note and note['yaml']:
                            st.write(f"**笔记 {i}**: {note['yaml'].get('title', '未命名')}")
                else:
                    st.error("❌ 无法解析文本，请检查格式")
            except Exception as e:
                st.error(f"❌ 解析预览失败: {e}")
    
    # 处理按钮
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🚀 开始处理", type="primary"):
            if ai_text.strip():
                with st.spinner("正在处理，请稍候..."):
                    processor.process_ai_formatted_text(ai_text, course_url, selected_subject, source_input)
            else:
                st.warning("请先输入AI格式的文本内容！")
    
    with col2:
        if st.button("🧹 清空内容"):
            st.rerun()

elif menu_choice == "增强现有笔记概念关系":
    st.header("增强现有笔记概念关系")
    st.info("此功能将使用AI优化现有笔记中的概念关系。")

    if not processor.concept_manager.load_database_from_file():
        st.warning("📚 概念数据库不存在，请先处理一些字幕文件或运行笔记增强功能来建立数据库。")
    
    enhance_method = st.radio(
        "选择增强方式:",
        ("传统方式（发送所有概念给AI）", "BGE混合检索（embedding召回+reranker精排）🔥 推荐")
    )

    embedding_top_k = 100
    rerank_top_k = 15
    rerank_threshold = 0.98

    if enhance_method == "BGE混合检索（embedding召回+reranker精排）🔥 推荐":
        st.subheader("BGE混合检索参数配置")
        use_default_params = st.checkbox("使用默认参数（召回100个，精排15个，阈值0.98）", value=True)
        if not use_default_params:
            embedding_top_k = st.number_input("embedding召回数量 (建议50-200)", min_value=1, value=100)
            rerank_top_k = st.number_input("reranker精排数量 (建议10-20)", min_value=1, value=15)
            rerank_threshold = st.number_input("reranker分数阈值 (建议0.2-0.5)", min_value=0.0, max_value=1.0, value=0.98, step=0.01)
            st.info(f"已设置: 召回{embedding_top_k}个 → 精排{rerank_top_k}个 → 阈值{rerank_threshold}")
        else:
            st.info("使用默认参数: 召回100个 → 精排15个 → 阈值0.98")

    st.subheader("选择处理范围")
    scope_choice = st.radio(
        "选择处理范围:",
        ("增强所有科目的笔记", "增强特定科目的笔记")
    )

    selected_subject_enhance = None
    if scope_choice == "增强特定科目的笔记":
        subjects_enhance = list(Config.SUBJECT_MAPPING.keys())
        selected_subject_enhance = st.selectbox("选择要增强的科目", subjects_enhance)

    if st.button("开始增强"):
        with st.spinner("正在增强笔记，请稍候..."):
            notes_to_enhance = []
            if scope_choice == "增强所有科目的笔记":
                notes_to_enhance = processor._collect_all_law_notes()
            elif scope_choice == "增强特定科目的笔记" and selected_subject_enhance:
                notes_to_enhance = processor._collect_subject_notes_by_name(selected_subject_enhance)

            if not notes_to_enhance:
                st.warning("没有找到需要增强的笔记。")
            else:
                st.info(f"找到 {len(notes_to_enhance)} 个笔记需要处理。")
                if enhance_method == "BGE混合检索（embedding召回+reranker精排）🔥 推荐":
                    enhancer = processor._get_siliconflow_enhancer()
                    if enhancer:
                        enhancer.batch_enhance_with_hybrid_search(
                            notes_to_enhance, False, embedding_top_k, rerank_top_k, rerank_threshold
                        )
                    else:
                        st.error("BGE增强器未成功初始化。")
                else:
                    processor._process_notes_enhancement(notes_to_enhance)
                st.success("笔记增强处理完成！")
                st.info("📚 重新扫描更新概念数据库...")
                processor.concept_manager.scan_existing_notes()

elif menu_choice == "时间戳链接化处理":
    st.header("时间戳链接化处理")
    st.info("此功能将为笔记中的时间戳添加视频链接。")

    timestamp_scope = st.radio(
        "选择处理范围:",
        ("处理所有科目的笔记", "处理特定科目的笔记")
    )

    selected_subject_timestamp = None
    if timestamp_scope == "处理特定科目的笔记":
        subjects_timestamp = list(Config.SUBJECT_MAPPING.keys())
        selected_subject_timestamp = st.selectbox("选择要处理的科目", subjects_timestamp)

    if st.button("开始时间戳链接化"):
        with st.spinner("正在处理时间戳，请稍候..."):
            if timestamp_scope == "处理所有科目的笔记":
                result = processor.timestamp_linker.process_all_notes_with_course_url()
            elif timestamp_scope == "处理特定科目的笔记" and selected_subject_timestamp:
                result = processor.timestamp_linker.process_subject_notes(selected_subject_timestamp)
            
            if result['total'] == 0:
                st.warning("💡 提示：请确保笔记的YAML中包含course_url字段，例如：`course_url: \"https://www.bilibili.com/video/BV1xxx\"`")
            st.success("时间戳链接化处理完成！")

elif menu_choice == "查看概念数据库状态":
    st.header("概念数据库状态")
    processor.show_concept_database_status()

elif menu_choice == "科目文件夹映射":
    st.header("科目文件夹映射")
    processor.show_subject_mapping()
