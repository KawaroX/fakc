import streamlit as st
import os
import sys
import io
import re
import datetime
import yaml

# 确保项目根目录在sys.path中，以便导入其他模块
# 假设app.py在项目根目录
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from config import Config
from input_manager import InputManager
from ai_processor import AIProcessor
from concept_manager import ConceptManager
from note_generator import ObsidianNoteGenerator
from timestamp_linker import TimestampLinker
from siliconflow_concept_enhancer import SiliconFlowConceptEnhancer # 导入SiliconFlow增强器

# 重新定义LawExamNoteProcessor类，使其适应Streamlit的输入/输出
class StreamlitLawExamNoteProcessor:
    def __init__(self):
        # Streamlit应用中不需要InputManager来获取命令行输入
        # self.input_manager = InputManager() 
        
        self.subtitle_ai_processor = AIProcessor(
            Config.OPENAI_API_KEY, 
            Config.OPENAI_BASE_URL, 
            Config.SUBTITLE_PROCESSING_MODEL
        )
        self.concept_enhancement_ai_processor = AIProcessor(
            Config.OPENAI_API_KEY, 
            Config.OPENAI_BASE_URL, 
            Config.CONCEPT_ENHANCEMENT_MODEL
        )
        self.concept_manager = ConceptManager(Config.OBSIDIAN_VAULT_PATH)
        self.note_generator = ObsidianNoteGenerator("temp") # 临时路径
        self.timestamp_linker = TimestampLinker(Config.OBSIDIAN_VAULT_PATH)
        self.siliconflow_enhancer = None # 延迟初始化

    def _get_siliconflow_enhancer(self):
        """获取SiliconFlow增强器实例（延迟初始化）"""
        if self.siliconflow_enhancer is None:
            try:
                self.siliconflow_enhancer = SiliconFlowConceptEnhancer(
                    Config.SILICONFLOW_API_KEY,
                    self.concept_enhancement_ai_processor, # 使用概念增强AI处理器
                    self.concept_manager
                )
                st.success("✅ SiliconFlow BGE增强器已初始化")
            except Exception as e:
                st.error(f"❌ 初始化SiliconFlow增强器失败: {e}")
                return None
        return self.siliconflow_enhancer

    def process_subtitle_file_streamlit(self, uploaded_file, course_url, selected_subject):
        """
        处理单个字幕文件的完整流程，适配Streamlit输入。
        uploaded_file: Streamlit的UploadedFile对象
        course_url: 课程URL字符串
        selected_subject: 用户选择的科目名称
        """
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
            os.makedirs(output_path, exist_ok=True) # 确保科目文件夹存在
            
            # 模拟subtitle_info，加入course_url和source
            subtitle_info = {
                'file_path': uploaded_file.name, # 仅用于显示，实际不读取
                'course_url': course_url,
                'subject': selected_subject,
                'output_path': output_path, # 传递给note_generator
                'source': "Uploaded Subtitle" # 为AI处理器提供来源信息
            }
            
            # 2. 扫描现有概念库
            st.write("🔍 扫描现有概念库...")
            self.concept_manager.scan_existing_notes()
            existing_concepts = self.concept_manager.get_all_concepts_for_ai()
            
            # 3. AI处理：一次性提取所有知识点 (使用字幕处理模型)
            st.write("🤖 AI正在分析字幕内容，提取知识点...")
            all_notes = self.subtitle_ai_processor.extract_all_knowledge_points(
                subtitle_content, subtitle_info
            )
            
            if not all_notes:
                st.warning("❌ 未能提取到知识点，请检查字幕内容")
                return []
            
            st.success(f"✅ 提取到 {len(all_notes)} 个知识点")
            
            # 4. AI增强：优化概念关系 (使用概念增强模型)
            st.write("🔗 AI正在优化概念关系...")
            enhanced_notes = self.concept_enhancement_ai_processor.enhance_concept_relationships(
                all_notes, existing_concepts
            )
            
            # 5. 生成笔记文件（保存到指定科目文件夹）
            st.write(f"📝 生成笔记文件到: {output_path}")
            created_files = []
            for note_data in enhanced_notes:
                # 在这里将course_url添加到note_data的YAML front matter
                if 'yaml_front_matter' not in note_data:
                    note_data['yaml_front_matter'] = {}
                note_data['yaml_front_matter']['course_url'] = course_url
                
                file_path = self.note_generator.create_note_file(
                    note_data, 
                    output_path # 使用科目特定的输出路径
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
            # 假设时间戳链接器可以直接处理已创建的文件
            # 或者，如果需要，可以传入一个列表给timestamp_linker
            # 这里为了简化，直接调用处理所有笔记的方法，确保新生成的笔记也被处理
            self.timestamp_linker.process_subject_notes(selected_subject)
            st.success("✅ 时间戳链接化处理完成。")

            return created_files
            
        except Exception as e:
            st.error(f"❌ 处理过程中出错: {e}")
            st.exception(e) # 显示详细错误信息
            return []

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
    ("处理新字幕文件", "增强现有笔记概念关系", "时间戳链接化处理", "查看概念数据库状态", "科目文件夹映射")
)

if menu_choice == "处理新字幕文件":
    st.header("处理新字幕文件")
    
    uploaded_file = st.file_uploader("上传字幕文件 (.srt, .txt)", type=["srt", "txt"])
    course_url = st.text_input("输入课程视频URL (可选，用于时间戳链接)", "")
    
    subjects = list(Config.SUBJECT_MAPPING.keys())
    selected_subject = st.selectbox("选择科目", subjects)
    
    if st.button("开始处理"):
        if uploaded_file is not None:
            with st.spinner("正在处理，请稍候..."):
                processor.process_subtitle_file_streamlit(uploaded_file, course_url, selected_subject)
        else:
            st.warning("请先上传字幕文件！")

elif menu_choice == "增强现有笔记概念关系":
    st.header("增强现有笔记概念关系")
    st.info("此功能将使用AI优化现有笔记中的概念关系。")

    # 先尝试加载现有概念数据库
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
                else: # 传统方式
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
