"""
法考笔记处理系统 - Web界面 (Notion风格版)

这是一个基于Streamlit的Web应用，用于将法考视频字幕转换为结构化的Obsidian笔记。
主要功能包括：
- 处理字幕文件并提取知识点
- AI增强笔记内容和概念关系
- 管理笔记间的概念联系
- 自动处理时间戳链接
- 支持模型配置和切换

作者：Your Name
版本：2.0.0 (Notion Style)
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

# 动态导入项目模块
from ai_processor import AIProcessor
from concept_manager import ConceptManager
from config import Config
from input_manager import InputManager
from note_generator import ObsidianNoteGenerator
from siliconflow_concept_enhancer import SiliconFlowConceptEnhancer
from timestamp_linker import TimestampLinker

def extract_url_from_text(text: str) -> str:
    """
    从文本中提取第一个URL
    
    提取并返回文本中找到的第一个http或https链接。支持所有标准URL格式，
    包括域名后带路径、参数等复杂URL形式。

    Args:
        text: 包含URL的文本字符串

    Returns:
        str: 提取到的URL字符串。如果未找到URL则返回空字符串
    
    Examples:
        >>> extract_url_from_text("视频地址是 https://example.com/video?id=123")
        'https://example.com/video?id=123'
    """
    # 匹配http或https开头的URL
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

    def process_subtitle_file_streamlit(
        self,
        uploaded_file: "StreamlitUploadedFile",
        course_url: str,
        selected_subject: str,
        source_info: str
    ) -> List[str]:
        """
        处理单个字幕文件的完整流程，适配Streamlit界面

        完整处理字幕文件的工作流程，包括读取内容、提取知识点、
        增强概念关系、生成笔记文件等步骤，并在Streamlit界面实时
        展示处理进度。

        Args:
            uploaded_file: Streamlit上传的字幕文件对象
            course_url: 课程视频URL（用于时间戳链接）
            selected_subject: 选择的科目名称
            source_info: 笔记来源信息

        Returns:
            List[str]: 生成的笔记文件路径列表

        Raises:
            Exception: 处理过程中的错误会通过Streamlit界面展示
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

    def _collect_all_law_notes(self) -> List[Dict[str, str]]:
        """
        收集所有法考笔记的内容和元数据
        
        遍历所有科目文件夹，读取并解析所有.md笔记文件（除概念数据库外），
        提取笔记的标题、内容和元数据。

        Returns:
            List[Dict[str, str]]: 笔记信息列表，每个笔记包含：
                - title: 笔记标题
                - file_path: 文件路径
                - content: 笔记内容
                - subject: 所属科目
        """
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

    def show_concept_database_status(self) -> None:
        """
        在Streamlit界面展示概念数据库的详细状态
        
        显示的信息包括：
        - 总概念数量
        - 各科目的概念分布统计
        - 数据库文件的状态（大小、最后更新时间等）
        - 文件存在性检查结果
        """
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

    def show_subject_mapping(self) -> None:
        """
        在Streamlit界面展示科目与文件夹的映射关系
        
        显示所有科目的映射信息，包括：
        - 科目名称
        - 对应的文件夹路径
        - 文件夹存在状态的可视化提示
        """
        st.subheader("📚 科目文件夹映射:")
        st.markdown("---")
        for i, (subject, folder) in enumerate(Config.SUBJECT_MAPPING.items(), 1):
            folder_path = Config.get_output_path(subject)
            exists_icon = "✅" if os.path.exists(folder_path) else "📁"
            st.write(f"  {exists_icon} **{subject}** -> `{folder}`")
        st.markdown("---")

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

# Streamlit UI - Notion Style
st.set_page_config(
    page_title="法考字幕转Obsidian笔记处理器",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 注入Notion风格CSS
st.markdown("""
<style>
    /* Notion风格全局样式 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
    }
    
    /* 背景色 */
    .stApp {
        background: #ffffff;
    }
    
    .main {
        background: #ffffff;
        padding: 0;
    }
    
    /* 顶部标题栏 */
    .notion-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 48px;
        background: #ffffff;
        border-bottom: 1px solid #e9e9e7;
        z-index: 1000;
        display: flex;
        align-items: center;
        padding: 0 24px;
    }
    
    .notion-header h1 {
        font-size: 14px;
        font-weight: 500;
        color: #37352f;
        margin: 0;
    }
    
    /* 侧边栏样式 */
    section[data-testid="stSidebar"] {
        background: #f7f6f3;
        border-right: 1px solid #e9e9e7;
        padding-top: 48px;
    }
    
    section[data-testid="stSidebar"] > div {
        padding: 8px 0;
    }
    
    /* 主内容区域 */
    .main > div {
        padding-top: 64px;
        max-width: 900px;
        margin: 0 auto;
    }
    
    /* 标题样式 */
    h1, h2, h3, h4, h5, h6 {
        color: #37352f;
        font-weight: 600;
        letter-spacing: -0.01em;
    }
    
    h1 { font-size: 40px; margin: 32px 0 8px 0; }
    h2 { font-size: 24px; margin: 24px 0 8px 0; }
    h3 { font-size: 20px; margin: 16px 0 8px 0; }
    
    /* 卡片容器 */
    .notion-card {
        background: #ffffff;
        border: 1px solid #e9e9e7;
        border-radius: 3px;
        padding: 16px;
        margin: 8px 0;
        transition: box-shadow 0.2s ease;
    }
    
    .notion-card:hover {
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    
    /* 输入框样式 */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        background: #f7f6f3;
        border: none;
        border-radius: 3px;
        padding: 8px 12px;
        font-size: 14px;
        color: #37352f;
        transition: background 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        background: #ffffff;
        box-shadow: 0 0 0 2px #e9e9e7;
        outline: none;
    }
    
    /* 按钮样式 */
    .stButton > button {
        background: #ffffff;
        border: 1px solid #e9e9e7;
        border-radius: 3px;
        color: #37352f;
        font-size: 14px;
        font-weight: 500;
        padding: 4px 12px;
        height: 32px;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background: #f7f6f3;
        border-color: #d9d9d7;
    }
    
    .stButton > button:active {
        background: #eeedeb;
    }
    
    /* Primary按钮 */
    .stButton > button[kind="primary"] {
        background: #2383e2;
        border-color: #2383e2;
        color: #ffffff;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: #0b7bc7;
        border-color: #0b7bc7;
    }
    
    /* 文件上传器 */
    .uploadedFile {
        background: #f7f6f3;
        border: 2px dashed #e9e9e7;
        border-radius: 3px;
        padding: 24px;
        text-align: center;
    }
    
    section[data-testid="stFileUploadDropzone"] {
        background: #f7f6f3;
        border: 2px dashed #e9e9e7;
        border-radius: 3px;
    }
    
    section[data-testid="stFileUploadDropzone"]:hover {
        background: #ffffff;
        border-color: #d9d9d7;
    }
    
    /* 进度条 */
    .stProgress > div > div > div {
        background: #2383e2;
        border-radius: 2px;
    }
    
    .stProgress > div > div {
        background: #f7f6f3;
        border-radius: 2px;
    }
    
    /* 信息框 */
    .stAlert {
        background: #f7f6f3;
        border: none;
        border-radius: 3px;
        color: #37352f;
        padding: 12px 16px;
        font-size: 14px;
    }
    
    div[data-baseweb="notification"] {
        border-radius: 3px;
    }
    
    /* 展开器 */
    .streamlit-expanderHeader {
        background: #f7f6f3;
        border: none;
        border-radius: 3px;
        font-size: 14px;
        font-weight: 500;
        color: #37352f;
    }
    
    .streamlit-expanderHeader:hover {
        background: #eeedeb;
    }
    
    .streamlit-expanderContent {
        border: none;
        background: #ffffff;
        border: 1px solid #e9e9e7;
        border-top: none;
        border-radius: 0 0 3px 3px;
    }
    
    /* 代码块 */
    .stCodeBlock {
        background: #f7f6f3;
        border: 1px solid #e9e9e7;
        border-radius: 3px;
    }
    
    /* 分割线 */
    hr {
        margin: 16px 0;
        border: none;
        height: 1px;
        background: #e9e9e7;
    }
    
    /* 侧边栏菜单 */
    .css-1d391kg {
        padding: 12px;
    }
    
    /* Radio按钮组 */
    .stRadio > div {
        gap: 4px;
    }
    
    .stRadio > div > label {
        background: #ffffff;
        border: 1px solid #e9e9e7;
        border-radius: 3px;
        padding: 8px 12px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        color: #37352f;
        margin: 4px 0;
        transition: all 0.2s ease;
    }
    
    .stRadio > div > label:hover {
        background: #f7f6f3;
    }
    
    /* Checkbox */
    .stCheckbox {
        font-size: 14px;
        color: #37352f;
    }
    
    /* Tabs样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background: #f7f6f3;
        padding: 4px;
        border-radius: 3px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border: none;
        color: #787774;
        font-size: 14px;
        font-weight: 500;
        padding: 4px 12px;
        border-radius: 3px;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: #ffffff;
        color: #37352f;
    }
    
    .stTabs [aria-selected="true"] {
        background: #ffffff;
        color: #37352f;
    }
    
    /* 度量指标 */
    div[data-testid="metric-container"] {
        background: #f7f6f3;
        border: 1px solid #e9e9e7;
        border-radius: 3px;
        padding: 16px;
    }
    
    /* 移除Streamlit默认样式 */
    .css-18e3th9 {
        padding-top: 0;
    }
    
    footer {
        display: none;
    }
    
    .viewerBadge_container__1QSob {
        display: none;
    }
    
    /* 滚动条样式 */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #d9d9d7;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #a9a9a7;
    }
    
    /* 响应式调整 */
    @media (max-width: 768px) {
        .main > div {
            padding-top: 48px;
        }
        
        section[data-testid="stSidebar"] {
            padding-top: 48px;
        }
    }
</style>

<!-- 顶部标题栏 -->
<div class="notion-header">
    <h1>🎓 法考字幕转Obsidian笔记处理器</h1>
</div>
""", unsafe_allow_html=True)

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
    st.error("检测到以下必需的环境变量缺失或为空，请填写并更新 .env 文件：")
    env_updates = {}
    for var in missing_env_vars:
        env_updates[var] = st.text_input(f"请输入 {var} 的值:", value="", key=f"env_input_{var}")
    
    if st.button("更新 .env 文件并重启应用"):
        Config.update_env_file(env_updates)
        st.success("✅ .env 文件已更新。请手动重启应用以加载新配置。")
        st.stop() # 停止Streamlit应用，等待用户重启
else:
    # 初始化处理器
    # 重新加载Config模块，确保使用最新的环境变量
    importlib.reload(sys.modules['config'])
    from config import Config # 重新导入Config类
    
    if 'processor' not in st.session_state:
        st.session_state.processor = StreamlitLawExamNoteProcessor()
    processor = st.session_state.processor

    # 确保基础目录存在
    Config.ensure_directories()

    # 侧边栏菜单
    with st.sidebar:
        st.markdown("## 功能菜单")
        menu_choice = st.radio(
            "",
            ("处理新字幕文件", "直接输入AI格式文本", "增强现有笔记概念关系", 
             "时间戳链接化处理", "查看概念数据库状态", "科目文件夹映射", 
             "查看笔记仓库", "模型配置")
        )

    if menu_choice == "模型配置":
        st.header("⚙️ 模型配置")
        
        tabs = st.tabs(["字幕处理模型", "概念增强模型"])
        
        with tabs[0]:
            st.markdown("### 字幕处理模型配置")
            
            # 显示当前配置
            st.info(f"当前使用: {st.session_state.current_subtitle_config['name']}")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                # 选择已保存的配置
                saved_configs = list(st.session_state.model_configs.get('subtitle', {}).keys())
                if saved_configs:
                    selected_config = st.selectbox(
                        "选择已保存的配置",
                        ["新建配置"] + saved_configs,
                        key="subtitle_config_select"
                    )
                else:
                    selected_config = "新建配置"
            
            # 配置表单
            with st.form("subtitle_model_form"):
                if selected_config != "新建配置" and selected_config in st.session_state.model_configs.get('subtitle', {}):
                    config = st.session_state.model_configs['subtitle'][selected_config]
                    config_name = st.text_input("配置名称", value=selected_config)
                    api_key = st.text_input("API Key", value=config['api_key'], type="password")
                    base_url = st.text_input("Base URL", value=config['base_url'])
                    model = st.text_input("Model", value=config['model'])
                else:
                    config_name = st.text_input("配置名称", value="")
                    api_key = st.text_input("API Key", value="", type="password")
                    base_url = st.text_input("Base URL", value="https://openrouter.ai/api/v1")
                    model = st.text_input("Model", value="deepseek/deepseek-r1-0528:free")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    save_btn = st.form_submit_button("保存配置", use_container_width=True)
                with col2:
                    use_btn = st.form_submit_button("使用此配置", type="primary", use_container_width=True)
                with col3:
                    if selected_config != "新建配置":
                        delete_btn = st.form_submit_button("删除配置", use_container_width=True)
                    else:
                        delete_btn = False
                
                if save_btn:
                    if config_name and api_key and base_url and model:
                        if 'subtitle' not in st.session_state.model_configs:
                            st.session_state.model_configs['subtitle'] = {}
                        st.session_state.model_configs['subtitle'][config_name] = {
                            'api_key': api_key,
                            'base_url': base_url,
                            'model': model
                        }
                        save_model_configs(st.session_state.model_configs)
                        st.success(f"✅ 配置 '{config_name}' 已保存")
                        st.rerun()
                    else:
                        st.error("请填写所有字段")
                
                if use_btn:
                    if api_key and base_url and model:
                        # 更新当前配置
                        st.session_state.current_subtitle_config = {
                            'name': config_name or '临时配置',
                            'api_key': api_key,
                            'base_url': base_url,
                            'model': model
                        }
                        # 更新Config和处理器
                        Config.SUBTITLE_PROCESSING_API_KEY = api_key
                        Config.SUBTITLE_PROCESSING_BASE_URL = base_url
                        Config.SUBTITLE_PROCESSING_MODEL = model
                        processor.subtitle_ai_processor = AIProcessor(api_key, base_url, model)
                        st.success(f"✅ 已切换到配置: {config_name or '临时配置'}")
                    else:
                        st.error("请填写所有字段")
                
                if delete_btn:
                    if selected_config in st.session_state.model_configs.get('subtitle', {}):
                        del st.session_state.model_configs['subtitle'][selected_config]
                        save_model_configs(st.session_state.model_configs)
                        st.success(f"✅ 配置 '{selected_config}' 已删除")
                        st.rerun()
        
        with tabs[1]:
            st.markdown("### 概念增强模型配置")
            
            # 显示当前配置
            st.info(f"当前使用: {st.session_state.current_concept_config['name']}")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                # 选择已保存的配置
                saved_configs = list(st.session_state.model_configs.get('concept', {}).keys())
                if saved_configs:
                    selected_config = st.selectbox(
                        "选择已保存的配置",
                        ["新建配置"] + saved_configs,
                        key="concept_config_select"
                    )
                else:
                    selected_config = "新建配置"
            
            # 配置表单
            with st.form("concept_model_form"):
                if selected_config != "新建配置" and selected_config in st.session_state.model_configs.get('concept', {}):
                    config = st.session_state.model_configs['concept'][selected_config]
                    config_name = st.text_input("配置名称", value=selected_config)
                    api_key = st.text_input("API Key", value=config['api_key'], type="password")
                    base_url = st.text_input("Base URL", value=config['base_url'])
                    model = st.text_input("Model", value=config['model'])
                else:
                    config_name = st.text_input("配置名称", value="")
                    api_key = st.text_input("API Key", value="", type="password")
                    base_url = st.text_input("Base URL", value="https://openrouter.ai/api/v1")
                    model = st.text_input("Model", value="openrouter/cypher-alpha:free")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    save_btn = st.form_submit_button("保存配置", use_container_width=True)
                with col2:
                    use_btn = st.form_submit_button("使用此配置", type="primary", use_container_width=True)
                with col3:
                    if selected_config != "新建配置":
                        delete_btn = st.form_submit_button("删除配置", use_container_width=True)
                    else:
                        delete_btn = False
                
                if save_btn:
                    if config_name and api_key and base_url and model:
                        if 'concept' not in st.session_state.model_configs:
                            st.session_state.model_configs['concept'] = {}
                        st.session_state.model_configs['concept'][config_name] = {
                            'api_key': api_key,
                            'base_url': base_url,
                            'model': model
                        }
                        save_model_configs(st.session_state.model_configs)
                        st.success(f"✅ 配置 '{config_name}' 已保存")
                        st.rerun()
                    else:
                        st.error("请填写所有字段")
                
                if use_btn:
                    if api_key and base_url and model:
                        # 更新当前配置
                        st.session_state.current_concept_config = {
                            'name': config_name or '临时配置',
                            'api_key': api_key,
                            'base_url': base_url,
                            'model': model
                        }
                        # 更新Config和处理器
                        Config.CONCEPT_ENHANCEMENT_API_KEY = api_key
                        Config.CONCEPT_ENHANCEMENT_BASE_URL = base_url
                        Config.CONCEPT_ENHANCEMENT_MODEL = model
                        processor.concept_enhancement_ai_processor = AIProcessor(api_key, base_url, model)
                        st.success(f"✅ 已切换到配置: {config_name or '临时配置'}")
                    else:
                        st.error("请填写所有字段")
                
                if delete_btn:
                    if selected_config in st.session_state.model_configs.get('concept', {}):
                        del st.session_state.model_configs['concept'][selected_config]
                        save_model_configs(st.session_state.model_configs)
                        st.success(f"✅ 配置 '{selected_config}' 已删除")
                        st.rerun()

    elif menu_choice == "处理新字幕文件":
        st.header("处理新字幕文件")
        
        with st.container():
            st.markdown('<div class="notion-card">', unsafe_allow_html=True)
            st.markdown("""
            **功能说明**
            - 支持多种字幕文件格式：.lrc, .srt, .vtt, .txt, .ass, .bcc
            - AI自动提取知识点，生成结构化笔记
            - 自动增强概念关系，建立知识网络
            - 支持时间戳链接，方便回看视频原文
            """)
            st.markdown('</div>', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("上传字幕文件", type=["lrc", "srt", "vtt", "txt", "ass", "bcc"])
        
        # 初始化session state中的source_input默认值
        if 'source_input_default_subtitle' not in st.session_state:
            st.session_state.source_input_default_subtitle = ""

        # 当上传文件变化时，更新session state中的默认值
        if uploaded_file is not None and st.session_state.source_input_default_subtitle != uploaded_file.name:
            filename = uploaded_file.name
            filename_without_ext = os.path.splitext(filename)[0]
            filename_part = filename_without_ext.split('_')[0]
            processed_filename = filename_part.replace(' ', '-')
            st.session_state.source_input_default_subtitle = processed_filename

        raw_course_url = st.text_input("课程视频URL (可选，用于时间戳链接)", "", key="raw_course_url_subtitle")
        course_url = extract_url_from_text(raw_course_url)
        
        source_input = st.text_input("来源信息 (可选，默认为文件名)", value=st.session_state.source_input_default_subtitle, key="source_input_subtitle")
        
        subjects = list(Config.SUBJECT_MAPPING.keys())
        selected_subject = st.selectbox("选择科目", subjects, key="selected_subject_subtitle")
        
        if st.button("开始处理", type="primary"):
            if uploaded_file is not None:
                final_source = source_input 
                with st.spinner("正在处理，请稍候..."):
                    processor.process_subtitle_file_streamlit(uploaded_file, course_url, selected_subject, final_source)
            else:
                st.warning("请先上传字幕文件！")

    elif menu_choice == "直接输入AI格式文本":
        st.header("直接输入AI格式文本")
        
        with st.container():
            st.markdown('<div class="notion-card">', unsafe_allow_html=True)
            st.markdown("""
            **功能说明**
            - 直接粘贴AI生成的笔记格式文本
            - 自动解析并生成结构化的Obsidian笔记
            - 支持批量处理多个知识点
            - 自动添加课程链接和元数据
            """)
            st.markdown('</div>', unsafe_allow_html=True)
        
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
        col1, col2 = st.columns(2)
        
        with col1:
            raw_course_url = st.text_input("课程视频URL (可选)", "", help="用于生成时间戳链接", key="raw_course_url_ai_text")
            course_url = extract_url_from_text(raw_course_url)
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
            if st.button("开始处理", type="primary"):
                if ai_text.strip():
                    with st.spinner("正在处理，请稍候..."):
                        processor.process_ai_formatted_text(ai_text, course_url, selected_subject, source_input)
                else:
                    st.warning("请先输入AI格式的文本内容！")
        
        with col2:
            if st.button("清空内容"):
                st.rerun()

    elif menu_choice == "增强现有笔记概念关系":
        st.header("增强现有笔记概念关系")
        
        with st.container():
            st.markdown('<div class="notion-card">', unsafe_allow_html=True)
            st.markdown("""
            **功能说明**
            - 使用AI深度分析笔记内容，优化概念关系
            - 支持传统方式和BGE混合检索两种模式
            - 可选择处理全部或特定科目笔记
            - 自动更新概念数据库，构建知识图谱
            """)
            st.markdown('</div>', unsafe_allow_html=True)

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
            with st.expander("BGE混合检索参数配置", expanded=False):
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
            "",
            ("增强所有科目的笔记", "增强特定科目的笔记")
        )

        selected_subject_enhance = None
        if scope_choice == "增强特定科目的笔记":
            subjects_enhance = list(Config.SUBJECT_MAPPING.keys())
            selected_subject_enhance = st.selectbox("选择要增强的科目", subjects_enhance)

        if st.button("开始增强", type="primary"):
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
        
        with st.container():
            st.markdown('<div class="notion-card">', unsafe_allow_html=True)
            st.markdown("""
            **功能说明**
            - 自动处理笔记中的时间戳标记
            - 将时间戳转换为可跳转的视频链接
            - 支持批量处理所有科目或指定科目
            - 需要笔记中包含course_url字段
            """)
            st.markdown('</div>', unsafe_allow_html=True)

        timestamp_scope = st.radio(
            "选择处理范围:",
            ("处理所有科目的笔记", "处理特定科目的笔记")
        )

        selected_subject_timestamp = None
        if timestamp_scope == "处理特定科目的笔记":
            subjects_timestamp = list(Config.SUBJECT_MAPPING.keys())
            selected_subject_timestamp = st.selectbox("选择要处理的科目", subjects_timestamp)

        if st.button("开始时间戳链接化", type="primary"):
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
        
        with st.container():
            st.markdown('<div class="notion-card">', unsafe_allow_html=True)
            st.markdown("""
            **功能说明**
            - 查看概念数据库的详细统计信息
            - 了解各科目的概念分布情况
            - 检查数据库文件状态和更新时间
            - 确保数据库文件的完整性
            """)
            st.markdown('</div>', unsafe_allow_html=True)
        processor.show_concept_database_status()

    elif menu_choice == "查看笔记仓库":
        st.header("笔记仓库浏览器")
        
        # 使用columns创建左右分栏布局
        col_sidebar, col_main = st.columns([1.2, 3])
        
        with col_sidebar:
            st.markdown("### 法考笔记仓库")
            
            # 获取所有科目
            subjects = list(Config.SUBJECT_MAPPING.keys())
            
            # 创建科目导航
            for subject in subjects:
                with st.expander(f"📚 {subject}", expanded=False):
                    notes = processor._collect_subject_notes_by_name(subject)
                    if notes:
                        for note in notes:
                            # 使用单选框选择笔记
                            if st.button(
                                f"📄 {note['title']}",
                                key=f"note_{note['title']}",
                                use_container_width=True
                            ):
                                st.session_state.selected_note = note
                    else:
                        st.caption("该科目下暂无笔记")
        
        with col_main:
            if 'selected_note' in st.session_state and st.session_state.selected_note:
                selected_note = st.session_state.selected_note
                
                st.markdown('<div class="notion-card">', unsafe_allow_html=True)
                st.markdown(f"### {selected_note['title']}")
                st.markdown(f"*所属科目：{selected_note['subject']}*")
                st.divider()
                
                # 解析YAML元数据
                yaml_content = re.search(r'^---\n(.*?)\n---', selected_note['content'], re.DOTALL)
                if yaml_content:
                    try:
                        yaml_data = yaml.safe_load(yaml_content.group(1))
                        with st.expander("📌 元数据", expanded=False):
                            cols = st.columns(2)
                            for i, (k, v) in enumerate(yaml_data.items()):
                                cols[i%2].write(f"**{k}**: `{v}`")
                    except Exception as e:
                        st.error(f"YAML解析错误: {e}")
                
                # 处理双链并渲染内容
                processed_content = re.sub(
                    r'\[\[(.*?\|.*?)\]\]', 
                    lambda m: f'[{m.group(1).split("|")[0]}](#{m.group(1).split("|")[1]})', 
                    selected_note['content']
                )
                processed_content = re.sub(
                    r'\[\[(.*?)\]\]',
                    lambda m: f'[{m.group(1)}](#{m.group(1)})',
                    processed_content
                )
                
                # 移除原始YAML部分
                processed_content = re.sub(r'^---\n.*?\n---', '', processed_content, flags=re.DOTALL)
                
                # 显示处理后的内容
                st.markdown(processed_content)
                
                # 显示文件信息
                with st.expander("文件信息", expanded=False):
                    st.write(f"文件路径：`{selected_note['file_path']}`")
                    st.write(f"最后修改时间：{datetime.datetime.fromtimestamp(os.path.getmtime(selected_note['file_path'])).strftime('%Y-%m-%d %H:%M:%S')}")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("👈 请在左侧选择科目并点击笔记进行查看")

    elif menu_choice == "科目文件夹映射":
        st.header("科目文件夹映射")
        
        with st.container():
            st.markdown('<div class="notion-card">', unsafe_allow_html=True)
            st.markdown("""
            **功能说明**
            - 查看所有科目与文件夹的对应关系
            - 快速定位各科目的笔记存储位置
            - 验证文件夹的存在状态
            - 了解笔记的组织结构
            """)
            st.markdown('</div>', unsafe_allow_html=True)
        processor.show_subject_mapping()
