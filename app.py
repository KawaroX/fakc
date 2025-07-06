"""
法考笔记处理系统 - Web界面 (完整修复版)

修复内容：
1. 删除自定义header，使用Streamlit原生header
2. 重新设计侧边栏按钮为Notion风格图标
3. 在原生header中央添加应用标题
4. 添加header阴影效果

作者：FAKC Team
版本：2.2.1 (Header修复版)
"""

import datetime
import importlib
import os
import re
import sys
import json
from typing import Dict, List, Optional, Union

import streamlit as st
import yaml

# 确保项目根目录在sys.path中，以便导入其他模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

# 导入分离的模块
from styles import get_notion_styles  # 使用修复后的样式
from ui_components import (
    render_feature_description, render_info_card, render_subject_selection,
    render_file_uploader, render_enhancement_method_selection, 
    render_scope_selection, render_model_config_tabs, render_bge_params_config,
    render_model_config_section, render_repair_stats, render_broken_links_list,
    render_concept_database_status, render_subject_mapping, render_note_browser,
    render_warning_box, render_success_box, render_error_box, render_code_example,
    render_enhanced_button, fix_material_icons_in_text, UIConstants
)
from app_constants import AppConstants, UIConfig, ModelConfig

# 动态导入项目模块
from ai_processor import AIProcessor
from concept_manager import ConceptManager
from config import Config
from input_manager import InputManager
from note_generator import ObsidianNoteGenerator
from siliconflow_concept_enhancer import SiliconFlowConceptEnhancer
from timestamp_linker import TimestampLinker
from link_repairer import LinkRepairer

def extract_url_from_text(text: str) -> str:
    """
    从文本中提取第一个URL
    
    Args:
        text: 包含URL的文本字符串

    Returns:
        str: 提取到的URL字符串。如果未找到URL则返回空字符串
    """
    match = re.search(r'https?://[^\s]+', text)
    if match:
        return match.group(0)
    return ""

class StreamlitLawExamNoteProcessor:
    """
    法考笔记处理器的Streamlit适配版本
    
    负责处理字幕文件、生成笔记、管理概念关系等核心功能的Web界面适配实现。
    所有方法都经过优化以配合Streamlit的界面交互模式，包括进度展示和状态反馈。
    """
    def __init__(self):
        # 确保每次初始化时都从Config类获取最新值
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
        self.link_repairer = LinkRepairer(Config.OBSIDIAN_VAULT_PATH)
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
                render_error_box("未能解析到有效的笔记格式，请检查文本格式")
                render_info_card("💡 提示：确保文本包含正确的 === NOTE_SEPARATOR === 分隔符和YAML/CONTENT部分")
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
            
            render_success_box(f"成功生成 {len(created_files)} 个笔记文件")
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
            render_error_box(f"处理过程中出错: {e}")
            st.exception(e)
            return []

    def process_subtitle_file_streamlit(
        self,
        uploaded_file: "StreamlitUploadedFile",
        course_url: str,
        selected_subject: str,
        source_info: str
    ) -> List[str]:
        """
        处理单个字幕文件的完整流程，适配Streamlit界面

        Args:
            uploaded_file: Streamlit上传的字幕文件对象
            course_url: 课程视频URL（用于时间戳链接）
            selected_subject: 选择的科目名称
            source_info: 笔记来源信息

        Returns:
            List[str]: 生成的笔记文件路径列表
        """
        st.info("🚀 开始处理字幕文件...")
        
        try:
            # 1. 从UploadedFile读取字幕内容
            st.write("📖 读取字幕文件...")
            subtitle_content = uploaded_file.getvalue().decode("utf-8")
            
            if not subtitle_content.strip():
                render_warning_box("字幕文件为空")
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
                render_warning_box("未能提取到知识点，请检查字幕内容")
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
            
            render_success_box(f"成功生成 {len(created_files)} 个笔记文件")
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
            render_error_box(f"处理过程中出错: {e}")
            st.exception(e)
            return []

    def _collect_all_law_notes(self) -> List[Dict[str, str]]:
        """收集所有法考笔记的内容和元数据"""
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

        render_success_box("处理完成！")
        st.write(f"  ✅ 成功增强: {enhanced_count} 个")
        st.write(f"  ⚠️ 无需修改: {len(notes) - enhanced_count - failed_count} 个")
        st.write(f"  ❌ 处理失败: {failed_count} 个")
        
        if enhanced_count > 0:
            st.info(f"\n📚 重新扫描更新概念数据库...")
            self.concept_manager.scan_existing_notes()

# 模型配置缓存文件路径
MODEL_CONFIG_CACHE_PATH = os.path.join(os.path.dirname(__file__), '.model_configs_cache.json')

def load_model_configs():
    """加载缓存的模型配置"""
    if os.path.exists(MODEL_CONFIG_CACHE_PATH):
        try:
            with open(MODEL_CONFIG_CACHE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_model_configs(configs):
    """保存模型配置到缓存"""
    try:
        with open(MODEL_CONFIG_CACHE_PATH, 'w', encoding='utf-8') as f:
            json.dump(configs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"保存模型配置失败: {e}")

# Streamlit页面配置
st.set_page_config(**UIConfig.PAGE_CONFIG)

# 注入修复后的样式 - 不再包含自定义header
st.markdown(get_notion_styles(), unsafe_allow_html=True)

# 初始化session state
if 'model_configs' not in st.session_state:
    st.session_state.model_configs = load_model_configs()

if 'current_subtitle_config' not in st.session_state:
    st.session_state.current_subtitle_config = {
        'name': 'Default',
        'api_key': Config.SUBTITLE_PROCESSING_API_KEY or '',
        'base_url': Config.SUBTITLE_PROCESSING_BASE_URL or '',
        'model': Config.SUBTITLE_PROCESSING_MODEL or ''
    }

if 'current_concept_config' not in st.session_state:
    st.session_state.current_concept_config = {
        'name': 'Default',
        'api_key': Config.CONCEPT_ENHANCEMENT_API_KEY or '',
        'base_url': Config.CONCEPT_ENHANCEMENT_BASE_URL or '',
        'model': Config.CONCEPT_ENHANCEMENT_MODEL or ''
    }

# 检查并处理缺失的环境变量
missing_env_vars = Config.check_and_get_missing_env()

if missing_env_vars:
    render_error_box("检测到以下必需的环境变量缺失或为空，请填写并更新 .env 文件：", "环境变量配置")
    
    env_updates = {}
    for var in missing_env_vars:
        env_updates[var] = st.text_input(f"请输入 {var} 的值:", value="", key=f"env_input_{var}")
    
    if st.button("更新 .env 文件并重启应用"):
        Config.update_env_file(env_updates)
        render_success_box(".env 文件已更新。请手动重启应用以加载新配置。")
        st.stop()
else:
    # 初始化处理器
    importlib.reload(sys.modules['config'])
    from config import Config
    
    if 'processor' not in st.session_state:
        st.session_state.processor = StreamlitLawExamNoteProcessor()
    processor = st.session_state.processor

    # 确保基础目录存在
    Config.ensure_directories()

    # 侧边栏菜单
    with st.sidebar:
        menu_choice = st.radio(" ", AppConstants.MENU_OPTIONS)  # 移除标题，使用空字符串

    # 主要的菜单处理逻辑
    if menu_choice == "📄 处理新字幕文件":
        st.header("处理新字幕文件")
        
        # 使用新的UI组件
        render_feature_description("功能说明", AppConstants.FEATURE_DESCRIPTIONS["📄 处理新字幕文件"])
        
        # 文件上传
        uploaded_file = render_file_uploader(
            AppConstants.SUPPORTED_SUBTITLE_FORMATS,
            AppConstants.HELP_TEXTS["file_upload"]
        )
        
        # 初始化默认值
        if 'source_input_default_subtitle' not in st.session_state:
            st.session_state.source_input_default_subtitle = ""

        # 当上传文件变化时，更新默认值
        if uploaded_file is not None and st.session_state.source_input_default_subtitle != uploaded_file.name:
            filename = uploaded_file.name
            filename_without_ext = os.path.splitext(filename)[0]
            filename_part = filename_without_ext.split('_')[0]
            processed_filename = filename_part.replace(' ', '-')
            st.session_state.source_input_default_subtitle = processed_filename

        # 配置输入
        col1, col2 = st.columns(UIConfig.COLUMN_LAYOUTS["two_equal"])
        
        with col1:
            raw_course_url = st.text_input(
                "课程视频URL (可选)", 
                "", 
                key="raw_course_url_subtitle",
                help=AppConstants.HELP_TEXTS["course_url"],
                placeholder=AppConstants.PLACEHOLDERS["course_url"]
            )
            course_url = extract_url_from_text(raw_course_url)
        
        with col2:
            source_input = st.text_input(
                "来源信息 (可选)", 
                value=st.session_state.source_input_default_subtitle, 
                key="source_input_subtitle",
                help=AppConstants.HELP_TEXTS["source_info"]
            )
        
        # 科目选择
        subjects = list(Config.SUBJECT_MAPPING.keys())
        selected_subject = render_subject_selection(subjects, key="selected_subject_subtitle")
        
        # 处理按钮
        if render_enhanced_button("🚀 开始处理", button_type="primary", use_container_width=True):
            if uploaded_file is not None:
                final_source = source_input 
                with st.spinner(UIConstants.MESSAGES['processing']):
                    processor.process_subtitle_file_streamlit(uploaded_file, course_url, selected_subject, final_source)
            else:
                render_warning_box(AppConstants.ERROR_MESSAGES["no_file"])

    elif menu_choice == "✍️ 格式化文本直录":
        st.header("格式化文本直录")
        
        render_feature_description("功能说明", AppConstants.FEATURE_DESCRIPTIONS["✍️ 格式化文本直录"])
        
        # 显示格式示例
        with st.expander(UIConfig.EXPANDER_CONFIG["ai_format_example"]["title"], 
                        expanded=UIConfig.EXPANDER_CONFIG["ai_format_example"]["expanded"]):
            render_code_example(AppConstants.AI_FORMAT_EXAMPLE, "markdown")
        
        # 输入区域
        ai_text = st.text_area(
            "粘贴AI格式的文本内容",
            height=UIConfig.COMPONENT_SIZES["text_area_height"],
            placeholder=AppConstants.PLACEHOLDERS["ai_text_input"],
            help=AppConstants.HELP_TEXTS["ai_text_format"],
            key="ai_text_input"
        )
        
        # 配置信息
        col1, col2 = st.columns(UIConfig.COLUMN_LAYOUTS["two_equal"])
        
        with col1:
            raw_course_url = st.text_input(
                "课程视频URL (可选)", 
                "", 
                help=AppConstants.HELP_TEXTS["course_url"], 
                key="raw_course_url_ai_text",
                placeholder=AppConstants.PLACEHOLDERS["course_url"]
            )
            course_url = extract_url_from_text(raw_course_url)
            source_input = st.text_input(
                "来源信息", 
                AppConstants.PLACEHOLDERS["source_info"], 
                help=AppConstants.HELP_TEXTS["source_info"], 
                key="source_input_ai_text"
            )
        
        with col2:
            subjects = list(Config.SUBJECT_MAPPING.keys())
            selected_subject = render_subject_selection(
                subjects, 
                key="selected_subject_ai_text"
            )
            
            # 获取用户输入变量
            input_vars = {
                'subject': selected_subject,
                'course_url': course_url,
                'source': source_input
            }
            
            # 生成带占位符的提示词模板
            # 注意：这里我们创建一个临时的AIProcessor实例来访问_build_extraction_prompt方法
            # 因为这个方法是实例方法，且我们只需要它的模板生成能力，不需要实际的API调用
            temp_ai_processor = AIProcessor("DUMMY_API_KEY", "DUMMY_BASE_URL", "DUMMY_MODEL")
            template = temp_ai_processor._build_extraction_prompt("YOUR_SUBTITLE_CONTENT_HERE", input_vars)
            
            if st.button("📝 生成提示词", use_container_width=True, key="generate_prompt_btn"):
                st.code(template, language="text")
                st.success("提示词已生成，可以直接复制!")
            else:
                st.info("需要提示词？填写上方信息后点击\"生成提示词\"按钮。")
        
        # 预览功能
        if ai_text.strip():
            with st.expander(UIConfig.EXPANDER_CONFIG["preview_result"]["title"], 
                           expanded=UIConfig.EXPANDER_CONFIG["preview_result"]["expanded"]):
                try:
                    preview_notes = processor.subtitle_ai_processor._parse_ai_response(ai_text)
                    if preview_notes:
                        render_success_box(f"可以解析到 {len(preview_notes)} 个笔记")
                        for i, note in enumerate(preview_notes, 1):
                            if 'yaml' in note and note['yaml']:
                                st.write(f"**笔记 {i}**: {note['yaml'].get('title', '未命名')}")
                    else:
                        render_error_box(AppConstants.ERROR_MESSAGES["parse_failed"])
                except Exception as e:
                    render_error_box(f"解析预览失败: {e}")
        
        # 处理按钮
        col1, col2 = st.columns(UIConfig.COLUMN_LAYOUTS["form_buttons"])
        with col1:
            if render_enhanced_button("🚀 开始处理", button_type="primary", use_container_width=True):
                if ai_text.strip():
                    with st.spinner(UIConstants.MESSAGES['processing']):
                        processor.process_ai_formatted_text(ai_text, course_url, selected_subject, source_input)
                else:
                    render_warning_box(AppConstants.ERROR_MESSAGES["no_text"])
        
        with col2:
            if render_enhanced_button("🗑️ 清空内容", use_container_width=True):
                st.rerun()

    elif menu_choice == "🔗 增强现有笔记关系":
        st.header("增强现有笔记关系")
        
        render_feature_description("功能说明", AppConstants.FEATURE_DESCRIPTIONS["🔗 增强现有笔记关系"])

        if not processor.concept_manager.load_database_from_file():
            render_warning_box(AppConstants.WARNING_MESSAGES["no_database"])
        
        # 使用新的UI组件
        enhance_method = render_enhancement_method_selection()

        # BGE参数配置
        bge_params = AppConstants.DEFAULT_BGE_PARAMS
        if enhance_method == AppConstants.ENHANCEMENT_METHODS[1]:  # BGE混合检索
            bge_params = render_bge_params_config(AppConstants.DEFAULT_BGE_PARAMS)

        st.subheader("选择处理范围")
        scope_choice = render_scope_selection("enhancement")

        selected_subject_enhance = None
        if scope_choice == AppConstants.SCOPE_OPTIONS["enhancement"][1]:  # 增强特定科目
            subjects_enhance = list(Config.SUBJECT_MAPPING.keys())
            selected_subject_enhance = render_subject_selection(
                subjects_enhance, 
                key="subject_enhance"
            )

        if render_enhanced_button("🚀 开始增强", button_type="primary", use_container_width=True):
            with st.spinner(UIConstants.MESSAGES['processing']):
                notes_to_enhance = []
                if scope_choice == AppConstants.SCOPE_OPTIONS["enhancement"][0]:  # 所有科目
                    notes_to_enhance = processor._collect_all_law_notes()
                elif scope_choice == AppConstants.SCOPE_OPTIONS["enhancement"][1] and selected_subject_enhance:  # 特定科目
                    notes_to_enhance = processor._collect_subject_notes_by_name(selected_subject_enhance)

                if not notes_to_enhance:
                    render_warning_box(AppConstants.ERROR_MESSAGES["no_notes_found"])
                else:
                    st.info(f"找到 {len(notes_to_enhance)} 个笔记需要处理。")
                    if enhance_method == AppConstants.ENHANCEMENT_METHODS[1]:  # BGE混合检索
                        enhancer = processor._get_siliconflow_enhancer()
                        if enhancer:
                            enhancer.batch_enhance_with_hybrid_search(
                                notes_to_enhance, False, 
                                bge_params['embedding_top_k'], 
                                bge_params['rerank_top_k'], 
                                bge_params['rerank_threshold']
                            )
                        else:
                            render_error_box(AppConstants.ERROR_MESSAGES["bge_init_failed"])
                    else:
                        processor._process_notes_enhancement(notes_to_enhance)
                    
                    render_success_box(AppConstants.SUCCESS_MESSAGES["enhancement_complete"])
                    st.info("📚 重新扫描更新概念数据库...")
                    processor.concept_manager.scan_existing_notes()

    elif menu_choice == "⏰ 时间戳链接化处理":
        st.header("时间戳链接化处理")
        
        render_feature_description("功能说明", AppConstants.FEATURE_DESCRIPTIONS["⏰ 时间戳链接化处理"])

        timestamp_scope = render_scope_selection("timestamp")

        selected_subject_timestamp = None
        if timestamp_scope == AppConstants.SCOPE_OPTIONS["timestamp"][1]:  # 特定科目
            subjects_timestamp = list(Config.SUBJECT_MAPPING.keys())
            selected_subject_timestamp = render_subject_selection(
                subjects_timestamp, 
                key="subject_timestamp"
            )

        if st.button("🔗 开始时间戳链接化", type="primary", use_container_width=True):
            with st.spinner("正在处理时间戳，请稍候..."):
                if timestamp_scope == AppConstants.SCOPE_OPTIONS["timestamp"][0]:  # 所有科目
                    result = processor.timestamp_linker.process_all_notes_with_course_url()
                elif timestamp_scope == AppConstants.SCOPE_OPTIONS["timestamp"][1] and selected_subject_timestamp:  # 特定科目
                    result = processor.timestamp_linker.process_subject_notes(selected_subject_timestamp)
                
                if result['total'] == 0:
                    render_warning_box(AppConstants.WARNING_MESSAGES["no_course_url"])
                render_success_box(AppConstants.SUCCESS_MESSAGES["timestamp_converted"])

    elif menu_choice == "🔧 双链格式修复":
        st.header("双链格式修复")
        
        render_feature_description("功能说明", AppConstants.FEATURE_DESCRIPTIONS["🔧 双链格式修复"])

        repair_scope = render_scope_selection("repair")

        if repair_scope == AppConstants.SCOPE_OPTIONS["repair"][0]:  # 修复所有科目
            render_warning_box(AppConstants.WARNING_MESSAGES["repair_all"])
            
            if st.button("🔧 开始修复所有双链", type="primary", use_container_width=True):
                with st.spinner(UIConstants.MESSAGES['processing']):
                    result = processor.link_repairer.repair_all_links()
                    
                    render_success_box("双链修复完成！")
                    render_repair_stats(result)
                    
                    if result['repaired'] > 0:
                        st.info("📚 正在更新概念数据库...")
                        processor.concept_manager.scan_existing_notes()
                        render_success_box(AppConstants.SUCCESS_MESSAGES["database_updated"])

        elif repair_scope == AppConstants.SCOPE_OPTIONS["repair"][1]:  # 修复特定科目
            subjects_repair = list(Config.SUBJECT_MAPPING.keys())
            selected_subject_repair = render_subject_selection(
                subjects_repair, 
                key="subject_repair"
            )
            
            render_warning_box(AppConstants.WARNING_MESSAGES["repair_subject"].format(subject=selected_subject_repair))
            
            if st.button(f"🔧 开始修复 {selected_subject_repair} 双链", type="primary", use_container_width=True):
                with st.spinner(UIConstants.MESSAGES['processing']):
                    result = processor.link_repairer.repair_specific_subject(selected_subject_repair)
                    
                    render_success_box(f"{selected_subject_repair} 科目双链修复完成！")
                    render_repair_stats(result)
                    
                    if result['repaired'] > 0:
                        st.info("📚 正在更新概念数据库...")
                        processor.concept_manager.scan_existing_notes()
                        render_success_box(AppConstants.SUCCESS_MESSAGES["database_updated"])

        elif repair_scope == AppConstants.SCOPE_OPTIONS["repair"][2]:  # 查找损坏链接
            if st.button("🔍 开始检查损坏双链", use_container_width=True):
                with st.spinner("正在检查损坏的双链..."):
                    broken_links = processor.link_repairer.find_broken_links()
                    render_broken_links_list(broken_links)

    elif menu_choice == "📊 查看概念数据库":
        st.header("概念数据库状态")
        render_concept_database_status(processor.concept_manager, Config)

    elif menu_choice == "📁 科目文件夹映射":
        st.header("科目文件夹映射")
        render_subject_mapping(Config)

    elif menu_choice == "📚 查看笔记仓库":
        render_note_browser(processor, Config)

    elif menu_choice == "⚙️ 模型配置":
        st.header("⚙️ 模型配置")
        
        tabs = render_model_config_tabs()
        
        with tabs[0]:  # 字幕处理模型
            saved_configs = st.session_state.model_configs.get('subtitle', {})
            result = render_model_config_section(
                "字幕处理模型配置",
                st.session_state.current_subtitle_config,
                saved_configs,
                "subtitle"
            )
            
            if result['save']:
                if result['config_name'] and result['api_key'] and result['base_url'] and result['model']:
                    if 'subtitle' not in st.session_state.model_configs:
                        st.session_state.model_configs['subtitle'] = {}
                    st.session_state.model_configs['subtitle'][result['config_name']] = {
                        'api_key': result['api_key'],
                        'base_url': result['base_url'],
                        'model': result['model']
                    }
                    save_model_configs(st.session_state.model_configs)
                    render_success_box(f"配置 '{result['config_name']}' 已保存")
                    st.rerun()
                else:
                    render_error_box("请填写所有字段")
            
            if result['use']:
                if result['api_key'] and result['base_url'] and result['model']:
                    # 更新当前配置
                    st.session_state.current_subtitle_config = {
                        'name': result['config_name'] or '临时配置',
                        'api_key': result['api_key'],
                        'base_url': result['base_url'],
                        'model': result['model']
                    }
                    # 更新Config和处理器
                    Config.SUBTITLE_PROCESSING_API_KEY = result['api_key']
                    Config.SUBTITLE_PROCESSING_BASE_URL = result['base_url']
                    Config.SUBTITLE_PROCESSING_MODEL = result['model']
                    processor.subtitle_ai_processor = AIProcessor(result['api_key'], result['base_url'], result['model'])
                    render_success_box(f"已切换到配置: {result['config_name'] or '临时配置'}")
                else:
                    render_error_box("请填写所有字段")
            
            if result['delete']:
                if result['selected_config'] in st.session_state.model_configs.get('subtitle', {}):
                    del st.session_state.model_configs['subtitle'][result['selected_config']]
                    save_model_configs(st.session_state.model_configs)
                    render_success_box(f"配置 '{result['selected_config']}' 已删除")
                    st.rerun()
        
        with tabs[1]:  # 概念增强模型
            saved_configs = st.session_state.model_configs.get('concept', {})
            result = render_model_config_section(
                "概念增强模型配置",
                st.session_state.current_concept_config,
                saved_configs,
                "concept"
            )
            
            if result['save']:
                if result['config_name'] and result['api_key'] and result['base_url'] and result['model']:
                    if 'concept' not in st.session_state.model_configs:
                        st.session_state.model_configs['concept'] = {}
                    st.session_state.model_configs['concept'][result['config_name']] = {
                        'api_key': result['api_key'],
                        'base_url': result['base_url'],
                        'model': result['model']
                    }
                    save_model_configs(st.session_state.model_configs)
                    render_success_box(f"配置 '{result['config_name']}' 已保存")
                    st.rerun()
                else:
                    render_error_box("请填写所有字段")
            
            if result['use']:
                if result['api_key'] and result['base_url'] and result['model']:
                    # 更新当前配置
                    st.session_state.current_concept_config = {
                        'name': result['config_name'] or '临时配置',
                        'api_key': result['api_key'],
                        'base_url': result['base_url'],
                        'model': result['model']
                    }
                    # 更新Config和处理器
                    Config.CONCEPT_ENHANCEMENT_API_KEY = result['api_key']
                    Config.CONCEPT_ENHANCEMENT_BASE_URL = result['base_url']
                    Config.CONCEPT_ENHANCEMENT_MODEL = result['model']
                    processor.concept_enhancement_ai_processor = AIProcessor(result['api_key'], result['base_url'], result['model'])
                    render_success_box(f"已切换到配置: {result['config_name'] or '临时配置'}")
                else:
                    render_error_box("请填写所有字段")
            
            if result['delete']:
                if result['selected_config'] in st.session_state.model_configs.get('concept', {}):
                    del st.session_state.model_configs['concept'][result['selected_config']]
                    save_model_configs(st.session_state.model_configs)
                    render_success_box(f"配置 '{result['selected_config']}' 已删除")
                    st.rerun()
        
        with tabs[2]:  # 高级设置
            st.markdown("### 高级设置")
            
            # 推荐模型信息
            with st.expander("📋 推荐模型", expanded=True):
                st.markdown("#### 🏆 高性能模型")
                for model in ModelConfig.RECOMMENDED_MODELS["high_performance"]:
                    st.markdown(f"- {model}")
                
                st.markdown("#### 💰 经济实惠模型")
                for model in ModelConfig.RECOMMENDED_MODELS["budget_friendly"]:
                    st.markdown(f"- {model}")
                
                st.markdown("#### 🎯 专业特化模型")
                for model in ModelConfig.RECOMMENDED_MODELS["specialized"]:
                    st.markdown(f"- {model}")
            
            # 模型测试
            st.markdown("#### 🧪 模型连接测试")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("测试字幕处理模型", use_container_width=True):
                    try:
                        test_processor = AIProcessor(
                            st.session_state.current_subtitle_config['api_key'],
                            st.session_state.current_subtitle_config['base_url'],
                            st.session_state.current_subtitle_config['model']
                        )
                        # 简单的测试请求
                        response = test_processor.client.chat.completions.create(
                            model=test_processor.model,
                            messages=[{"role": "user", "content": "测试连接"}],
                            max_tokens=10
                        )
                        render_success_box("字幕处理模型连接正常")
                    except Exception as e:
                        render_error_box(f"字幕处理模型连接失败: {e}")
            
            with col2:
                if st.button("测试概念增强模型", use_container_width=True):
                    try:
                        test_processor = AIProcessor(
                            st.session_state.current_concept_config['api_key'],
                            st.session_state.current_concept_config['base_url'],
                            st.session_state.current_concept_config['model']
                        )
                        # 简单的测试请求
                        response = test_processor.client.chat.completions.create(
                            model=test_processor.model,
                            messages=[{"role": "user", "content": "测试连接"}],
                            max_tokens=10
                        )
                        render_success_box("概念增强模型连接正常")
                    except Exception as e:
                        render_error_box(f"概念增强模型连接失败: {e}")
            
            # 缓存管理
            st.markdown("#### 🗂️ 缓存管理")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("清空模型配置缓存", use_container_width=True):
                    try:
                        if os.path.exists(MODEL_CONFIG_CACHE_PATH):
                            os.remove(MODEL_CONFIG_CACHE_PATH)
                        st.session_state.model_configs = {}
                        render_success_box("模型配置缓存已清空")
                        st.rerun()
                    except Exception as e:
                        render_error_box(f"清空缓存失败: {e}")
            
            with col2:
                if st.button("清空BGE嵌入缓存", use_container_width=True):
                    try:
                        bge_cache_file = os.path.join(Config.OBSIDIAN_VAULT_PATH, "概念嵌入缓存_BGE.json")
                        if os.path.exists(bge_cache_file):
                            os.remove(bge_cache_file)
                        render_success_box("BGE嵌入缓存已清空")
                    except Exception as e:
                        render_error_box(f"清空BGE缓存失败: {e}")
            
            with col3:
                if st.button("重置所有配置", use_container_width=True):
                    if st.button("确认重置", type="primary"):
                        try:
                            # 清空所有缓存
                            if os.path.exists(MODEL_CONFIG_CACHE_PATH):
                                os.remove(MODEL_CONFIG_CACHE_PATH)
                            
                            bge_cache_file = os.path.join(Config.OBSIDIAN_VAULT_PATH, "概念嵌入缓存_BGE.json")
                            if os.path.exists(bge_cache_file):
                                os.remove(bge_cache_file)
                            
                            # 重置session state
                            for key in ['model_configs', 'current_subtitle_config', 'current_concept_config']:
                                if key in st.session_state:
                                    del st.session_state[key]
                            
                            render_success_box("所有配置已重置")
                            st.rerun()
                        except Exception as e:
                            render_error_box(f"重置失败: {e}")
                    else:
                        render_warning_box("点击'确认重置'按钮确认操作")
            
            # 系统信息
            st.markdown("#### ℹ️ 系统信息")
            system_info = {
                "应用版本": AppConstants.VERSION,
                "Python版本": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "Streamlit版本": st.__version__,
                "工作目录": os.getcwd(),
                "配置文件": Config.OBSIDIAN_VAULT_PATH
            }
            
            for key, value in system_info.items():
                st.write(f"**{key}**: `{value}`")

# 页面底部信息
st.markdown("---")
st.markdown(
    f"""
    <div style="text-align: center; color: #787774; font-size: 12px; padding: 20px;">
        {AppConstants.APP_TITLE} v{AppConstants.VERSION} | 
        由 {AppConstants.AUTHOR} 开发 | 
        <a href="https://github.com/your-repo" style="color: #2383e2;">GitHub</a>
    </div>
    """, 
    unsafe_allow_html=True
)

# 错误处理和日志记录
if __name__ == "__main__":
    try:
        # 这里可以添加应用启动时的初始化逻辑
        pass
    except Exception as e:
        st.error(f"应用启动失败: {e}")
        st.exception(e)