"""
UI组件文件 - 包含可复用的UI组件函数
完整版本，包含所有界面组件和修复后的布局
"""

import streamlit as st
from typing import List, Dict, Any, Optional, Callable

def fix_material_icons_in_text(text: str) -> str:
    """
    修复文本中的Material Icons名称，转换为emoji
    
    Args:
        text: 包含Material Icons名称的文本
        
    Returns:
        修复后的文本
    """
    # Material Icons到emoji的映射
    icon_mapping = {
        'keyboard_double_arrow_left': '⏪',
        'keyboard_double_arrow_right': '⏩',
        'keyboard_arrow_left': '⬅️',
        'keyboard_arrow_right': '➡️',
        'keyboard_arrow_up': '⬆️',
        'keyboard_arrow_down': '⬇️',
        'play_arrow': '▶️',
        'pause': '⏸️',
        'stop': '⏹️',
        'refresh': '🔄',
        'home': '🏠',
        'search': '🔍',
        'settings': '⚙️',
        'folder': '📁',
        'file_present': '📄',
        'save': '💾',
        'delete': '🗑️',
        'edit': '✏️',
        'visibility': '👁️',
        'check': '✅',
        'close': '❌',
        'warning': '⚠️',
        'info': 'ℹ️',
        'error': '❌',
        'success': '✅'
    }
    
    # 替换所有匹配的图标名称
    for material_name, emoji in icon_mapping.items():
        text = text.replace(material_name, emoji)
    
    return text

def render_enhanced_button(text: str, key: str = None, button_type: str = "secondary", 
                          use_container_width: bool = False, disabled: bool = False):
    """
    渲染增强的按钮，自动修复图标问题
    
    Args:
        text: 按钮文字（可能包含Material Icons名称）
        key: 按钮的key
        button_type: 按钮类型
        use_container_width: 是否使用容器宽度
        disabled: 是否禁用
        
    Returns:
        按钮是否被点击
    """
    # 修复文字中的图标
    fixed_text = fix_material_icons_in_text(text)
    
    return st.button(
        fixed_text,
        key=key,
        type=button_type,
        use_container_width=use_container_width,
        disabled=disabled
    )
    """
    渲染功能说明卡片
    
    Args:
        title: 卡片标题
        features: 功能列表
        icon: 图标
    """
    features_html = "\n".join([f"<li>{feature}</li>" for feature in features])
    
    card_html = f"""
    <div class="notion-card">
        <h4>{icon} {title}</h4>
        <ul>
            {features_html}
        </ul>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)

def render_info_card(content: str, card_type: str = "info"):
    """
    渲染信息卡片
    
    Args:
        content: 卡片内容
        card_type: 卡片类型 (info, warning, success, error)
    """
    icons = {
        "info": "ℹ️",
        "warning": "⚠️", 
        "success": "✅",
        "error": "❌"
    }
    
    icon = icons.get(card_type, "ℹ️")
    
    card_html = f"""
    <div class="notion-card">
        <p>{icon} {content}</p>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)

def render_process_steps(steps: list, title: str = "处理步骤"):
    """
    渲染处理步骤卡片
    
    Args:
        steps: 步骤列表
        title: 卡片标题
    """
    steps_html = "\n".join([f"<li>{step}</li>" for step in steps])
    
    card_html = f"""
    <div class="notion-card">
        <h4>⚙️ {title}</h4>
        <ol>
            {steps_html}
        </ol>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)

def render_feature_description(feature_name: str, descriptions: list):
    """
    渲染功能描述卡片 - 修复了文字在框里的问题
    
    Args:
        feature_name: 功能名称
        descriptions: 描述列表
    """
    desc_html = "\n".join([f"<li>{desc}</li>" for desc in descriptions])
    
    card_html = f"""
    <div class="notion-card">
        <h4>📖 {feature_name}</h4>
        <ul>
            {desc_html}
        </ul>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)

def render_navigation_buttons(prev_text: str = None, next_text: str = None, 
                            prev_callback: Callable = None, next_callback: Callable = None):
    """
    渲染导航按钮
    
    Args:
        prev_text: 上一步按钮文字
        next_text: 下一步按钮文字  
        prev_callback: 上一步回调函数
        next_callback: 下一步回调函数
    """
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if prev_text and prev_callback:
            if st.button(f"⬅️ {prev_text}", use_container_width=True):
                prev_callback()
    
    with col3:
        if next_text and next_callback:
            if st.button(f"{next_text} ➡️", use_container_width=True, type="primary"):
                next_callback()

def render_stats_cards(stats: dict):
    """
    渲染统计信息卡片
    
    Args:
        stats: 统计数据字典
    """
    cols = st.columns(len(stats))
    
    for i, (label, value) in enumerate(stats.items()):
        with cols[i]:
            st.metric(label=label, value=value)

def render_subject_selection(subjects: list, default_index: int = 0, key: str = None):
    """
    渲染科目选择器
    
    Args:
        subjects: 科目列表
        default_index: 默认选择的索引
        key: Streamlit组件的key
        
    Returns:
        选择的科目
    """
    return st.selectbox(
        "📚 选择科目",
        subjects,
        index=default_index,
        key=key,
        help="选择要处理的法考科目"
    )

def render_file_uploader(accepted_types: list, help_text: str = None, key: str = None):
    """
    渲染文件上传器
    
    Args:
        accepted_types: 接受的文件类型列表
        help_text: 帮助文本
        key: Streamlit组件的key
        
    Returns:
        上传的文件对象
    """
    return st.file_uploader(
        "📁 上传文件",
        type=accepted_types,
        help=help_text or f"支持的格式: {', '.join(accepted_types)}",
        key=key
    )

def render_progress_indicator(current_step: int, total_steps: int, step_names: list = None):
    """
    渲染进度指示器
    
    Args:
        current_step: 当前步骤 (1-based)
        total_steps: 总步骤数
        step_names: 步骤名称列表
    """
    progress = current_step / total_steps
    st.progress(progress)
    
    if step_names and len(step_names) >= current_step:
        st.caption(f"步骤 {current_step}/{total_steps}: {step_names[current_step-1]}")
    else:
        st.caption(f"步骤 {current_step}/{total_steps}")

def render_collapsible_section(title: str, content_func: Callable, expanded: bool = False, icon: str = "📄"):
    """
    渲染可折叠区域
    
    Args:
        title: 区域标题
        content_func: 内容渲染函数
        expanded: 是否默认展开
        icon: 图标
    """
    with st.expander(f"{icon} {title}", expanded=expanded):
        content_func()

def render_config_form(config_data: dict, form_key: str):
    """
    渲染配置表单
    
    Args:
        config_data: 配置数据字典
        form_key: 表单的key
        
    Returns:
        表单提交结果和更新的配置数据
    """
    with st.form(form_key):
        updated_config = {}
        
        for key, value in config_data.items():
            if isinstance(value, str):
                if "password" in key.lower() or "key" in key.lower():
                    updated_config[key] = st.text_input(
                        key.replace('_', ' ').title(), 
                        value=value, 
                        type="password"
                    )
                else:
                    updated_config[key] = st.text_input(
                        key.replace('_', ' ').title(), 
                        value=value
                    )
            elif isinstance(value, bool):
                updated_config[key] = st.checkbox(
                    key.replace('_', ' ').title(), 
                    value=value
                )
            elif isinstance(value, (int, float)):
                updated_config[key] = st.number_input(
                    key.replace('_', ' ').title(), 
                    value=value
                )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            save_btn = st.form_submit_button("💾 保存", use_container_width=True)
        with col2:
            apply_btn = st.form_submit_button("✅ 应用", type="primary", use_container_width=True)
        with col3:
            reset_btn = st.form_submit_button("🔄 重置", use_container_width=True)
        
        return {
            'save': save_btn,
            'apply': apply_btn, 
            'reset': reset_btn,
            'config': updated_config
        }

def render_model_config_tabs():
    """渲染模型配置选项卡"""
    return st.tabs(["🤖 字幕处理模型", "🔗 概念增强模型", "⚙️ 高级设置"])

def render_enhancement_method_selection():
    """渲染增强方式选择"""
    return st.radio(
        "🔧 选择增强方式:",
        ("传统方式（发送所有概念给AI）", "BGE混合检索（embedding召回+reranker精排）🔥 推荐"),
        help="BGE混合检索能提供更精准的概念关联"
    )

def render_scope_selection(scope_type: str = "enhancement"):
    """
    渲染范围选择器
    
    Args:
        scope_type: 范围类型 (enhancement, timestamp, repair等)
    """
    scope_options = {
        "enhancement": ("增强所有科目的笔记", "增强特定科目的笔记"),
        "timestamp": ("处理所有科目的笔记", "处理特定科目的笔记"), 
        "repair": ("修复所有科目的双链", "修复特定科目的双链", "查找损坏的双链")
    }
    
    options = scope_options.get(scope_type, ("处理所有", "处理特定"))
    
    return st.radio(
        "📂 选择处理范围:",
        options,
        help="建议先从特定科目开始测试"
    )

def render_bge_params_config(default_params: dict):
    """
    渲染BGE参数配置
    
    Args:
        default_params: 默认参数字典
        
    Returns:
        配置的参数字典
    """
    with st.expander("⚙️ BGE混合检索参数配置", expanded=False):
        use_default_params = st.checkbox("使用默认参数（召回100个，精排15个，阈值0.98）", value=True)
        
        if not use_default_params:
            embedding_top_k = st.number_input(
                "embedding召回数量 (建议50-200)", 
                min_value=1, 
                value=default_params.get('embedding_top_k', 100)
            )
            rerank_top_k = st.number_input(
                "reranker精排数量 (建议10-20)", 
                min_value=1, 
                value=default_params.get('rerank_top_k', 15)
            )
            rerank_threshold = st.number_input(
                "reranker分数阈值 (建议0.2-0.5)", 
                min_value=0.0, 
                max_value=1.0, 
                value=default_params.get('rerank_threshold', 0.98), 
                step=0.01
            )
            render_info_card(f"已设置: 召回{embedding_top_k}个 → 精排{rerank_top_k}个 → 阈值{rerank_threshold}")
            
            return {
                'embedding_top_k': embedding_top_k,
                'rerank_top_k': rerank_top_k,
                'rerank_threshold': rerank_threshold
            }
        else:
            render_info_card("使用默认参数: 召回100个 → 精排15个 → 阈值0.98")
            return default_params

def render_status_indicator(status: str, text: str = ""):
    """
    渲染状态指示器
    
    Args:
        status: 状态 (online, offline, warning)
        text: 状态文本
    """
    status_colors = {
        'online': '#00c851',
        'offline': '#ff4444', 
        'warning': '#ffbb33'
    }
    
    color = status_colors.get(status, '#787774')
    
    status_html = f"""
    <div style="display: flex; align-items: center; margin: 8px 0;">
        <div style="width: 8px; height: 8px; border-radius: 50%; background: {color}; margin-right: 8px;"></div>
        <span style="font-size: 14px; color: #37352f;">{text}</span>
    </div>
    """
    
    st.markdown(status_html, unsafe_allow_html=True)

def render_loading_indicator(text: str = "处理中..."):
    """渲染加载指示器"""
    loading_html = f"""
    <div style="display: flex; align-items: center; justify-content: center; padding: 20px;">
        <div class="loading-spinner"></div>
        <span style="margin-left: 10px; color: #37352f;">{text}</span>
    </div>
    """
    
    st.markdown(loading_html, unsafe_allow_html=True)

def render_code_example(code: str, language: str = "markdown", title: str = None):
    """
    渲染代码示例
    
    Args:
        code: 代码内容
        language: 代码语言
        title: 示例标题
    """
    if title:
        st.subheader(f"📄 {title}")
    
    st.code(code, language=language)

def render_warning_box(message: str, title: str = "注意"):
    """
    渲染警告框
    
    Args:
        message: 警告消息
        title: 警告标题
    """
    warning_html = f"""
    <div class="notion-card" style="border-left: 4px solid #ffbb33; background: #fff8e1;">
        <h4 style="color: #ff8f00; margin-bottom: 8px;">⚠️ {title}</h4>
        <p style="color: #37352f; margin: 0;">{message}</p>
    </div>
    """
    
    st.markdown(warning_html, unsafe_allow_html=True)

def render_success_box(message: str, title: str = "成功"):
    """
    渲染成功框
    
    Args:
        message: 成功消息
        title: 成功标题
    """
    success_html = f"""
    <div class="notion-card" style="border-left: 4px solid #00c851; background: #e8f5e8;">
        <h4 style="color: #00c851; margin-bottom: 8px;">✅ {title}</h4>
        <p style="color: #37352f; margin: 0;">{message}</p>
    </div>
    """
    
    st.markdown(success_html, unsafe_allow_html=True)

def render_error_box(message: str, title: str = "错误"):
    """
    渲染错误框
    
    Args:
        message: 错误消息
        title: 错误标题
    """
    error_html = f"""
    <div class="notion-card" style="border-left: 4px solid #ff4444; background: #ffebee;">
        <h4 style="color: #ff4444; margin-bottom: 8px;">❌ {title}</h4>
        <p style="color: #37352f; margin: 0;">{message}</p>
    </div>
    """
    
    st.markdown(error_html, unsafe_allow_html=True)

def render_model_config_section(config_name: str, current_config: dict, saved_configs: dict, config_type: str):
    """
    渲染模型配置区域
    
    Args:
        config_name: 配置名称
        current_config: 当前配置
        saved_configs: 已保存的配置
        config_type: 配置类型 (subtitle/concept)
        
    Returns:
        表单操作结果
    """
    st.markdown(f"### {config_name}")
    
    # 显示当前配置
    render_info_card(f"当前使用: {current_config['name']}")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        # 选择已保存的配置
        if saved_configs:
            selected_config = st.selectbox(
                "选择已保存的配置",
                ["新建配置"] + list(saved_configs.keys()),
                key=f"{config_type}_config_select"
            )
        else:
            selected_config = "新建配置"
    
    # 配置表单
    with st.form(f"{config_type}_model_form"):
        if selected_config != "新建配置" and selected_config in saved_configs:
            config = saved_configs[selected_config]
            config_name_input = st.text_input("配置名称", value=selected_config)
            api_key = st.text_input("API Key", value=config['api_key'], type="password")
            base_url = st.text_input("Base URL", value=config['base_url'])
            model = st.text_input("Model", value=config['model'])
        else:
            config_name_input = st.text_input("配置名称", value="")
            api_key = st.text_input("API Key", value="", type="password")
            base_url = st.text_input("Base URL", value="https://openrouter.ai/api/v1")
            model = st.text_input("Model", value="deepseek/deepseek-r1-0528:free" if config_type == "subtitle" else "openrouter/cypher-alpha:free")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            save_btn = st.form_submit_button("💾 保存配置", use_container_width=True)
        with col2:
            use_btn = st.form_submit_button("✅ 使用此配置", type="primary", use_container_width=True)
        with col3:
            if selected_config != "新建配置":
                delete_btn = st.form_submit_button("🗑️ 删除配置", use_container_width=True)
            else:
                delete_btn = False
        
        return {
            'save': save_btn,
            'use': use_btn,
            'delete': delete_btn,
            'config_name': config_name_input,
            'api_key': api_key,
            'base_url': base_url,
            'model': model,
            'selected_config': selected_config
        }

def render_repair_stats(stats: dict):
    """
    渲染修复统计信息
    
    Args:
        stats: 统计数据字典
    """
    stats_html = f"""
    <div class="notion-card">
        <h4>📊 修复统计</h4>
        <ul>
            <li>总计: {stats.get('total', 0)} 个笔记</li>
            <li>成功修复: {stats.get('repaired', 0)} 个</li>
            <li>无需修复: {stats.get('unchanged', 0)} 个</li>
            <li>修复失败: {stats.get('failed', 0)} 个</li>
        </ul>
    </div>
    """
    
    st.markdown(stats_html, unsafe_allow_html=True)

def render_broken_links_list(broken_links: list):
    """
    渲染损坏链接列表
    
    Args:
        broken_links: 损坏链接列表
    """
    if broken_links:
        st.error(f"❌ 发现 {len(broken_links)} 个损坏的双链")
        
        st.subheader("损坏的双链列表:")
        for i, link in enumerate(broken_links, 1):
            with st.expander(f"{i}. {link['file_title']} (行 {link['line_number']})"):
                st.write(f"**损坏链接**: `{link['broken_link']}`")
                st.write(f"**目标**: `{link['target']}`")
                st.write(f"**文件路径**: `{link['file_path']}`")
        
        render_info_card("可以使用双链修复功能自动修复部分问题", card_type="info")
    else:
        st.success("✅ 没有发现损坏的双链")

def render_concept_database_status(concept_manager, config_class):
    """
    渲染概念数据库状态
    
    Args:
        concept_manager: 概念管理器实例
        config_class: 配置类
    """
    import os
    import datetime
    
    st.subheader("📊 概念数据库状态")
    st.markdown("---")
    
    if concept_manager.load_database_from_file():
        total_concepts = len(concept_manager.concept_database)
        st.success(f"✅ 数据库已存在: {total_concepts} 个概念")
        
        subject_stats = {}
        for concept, data in concept_manager.concept_database.items():
            subject = data.get('subject', '未知')
            subject_stats[subject] = subject_stats.get(subject, 0) + 1
        
        st.markdown("\n**📚 各科目概念统计:**")
        for subject, count in sorted(subject_stats.items()):
            folder_name = config_class.get_subject_folder_name(subject) if hasattr(config_class, 'get_subject_folder_name') else subject
            st.write(f"  - **{folder_name}**: {count} 个概念")
        
        st.markdown("\n**📄 数据库文件状态:**")
        
        md_file = os.path.join(config_class.OBSIDIAN_VAULT_PATH, "概念数据库.md")
        if os.path.exists(md_file):
            file_size = os.path.getsize(md_file) / 1024
            mtime = os.path.getmtime(md_file)
            last_modified = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            st.write(f"  - 📝 `概念数据库.md`: {file_size:.1f} KB (更新: {last_modified})")
        else:
            st.warning(f"  - 📝 `概念数据库.md`: ❌ 不存在")
        
        json_file = os.path.join(config_class.OBSIDIAN_VAULT_PATH, "概念数据库.json")
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

def render_subject_mapping(config_class):
    """
    渲染科目文件夹映射
    
    Args:
        config_class: 配置类
    """
    import os
    
    st.subheader("📚 科目文件夹映射:")
    st.markdown("---")
    for i, (subject, folder) in enumerate(config_class.SUBJECT_MAPPING.items(), 1):
        folder_path = config_class.get_output_path(subject)
        exists_icon = "✅" if os.path.exists(folder_path) else "📁"
        st.write(f"  {exists_icon} **{subject}** -> `{folder}`")
    st.markdown("---")

def render_note_browser(processor, config_class):
    """
    渲染笔记浏览器
    
    Args:
        processor: 处理器实例
        config_class: 配置类
    """
    import os
    import re
    import yaml
    import datetime
    
    st.header("笔记仓库浏览器")
    
    # 使用columns创建左右分栏布局
    col_sidebar, col_main = st.columns([1.2, 3])
    
    with col_sidebar:
        st.markdown("### 法考笔记仓库")
        
        # 获取所有科目
        subjects = list(config_class.SUBJECT_MAPPING.keys())
        
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

class UIConstants:
    """UI常量类"""
    
    # 图标常量 - 修复图标显示问题
    ICONS = {
        'success': '✅',
        'error': '❌', 
        'warning': '⚠️',
        'info': 'ℹ️',
        'processing': '🔄',
        'file': '📄',
        'folder': '📁',
        'settings': '⚙️',
        'ai': '🤖',
        'link': '🔗',
        'repair': '🔧',
        'database': '📊',
        'search': '🔍',
        'upload': '📤',
        'download': '📥',
        'save': '💾',
        'delete': '🗑️',
        'edit': '✏️',
        'view': '👁️',
        'left_arrow': '⬅️',  # 替代 keyboard_double_arrow_left
        'right_arrow': '➡️',  # 替代 keyboard_double_arrow_right
        'double_left': '⏪',   # 双箭头左
        'double_right': '⏩',  # 双箭头右
        'up_arrow': '⬆️',
        'down_arrow': '⬇️',
        'play': '▶️',
        'pause': '⏸️',
        'stop': '⏹️',
        'refresh': '🔄',
        'home': '🏠',
        'back': '↩️',
        'forward': '↪️',
        'check': '✓',
        'cross': '✗',
        'plus': '➕',
        'minus': '➖',
        'star': '⭐',
        'heart': '❤️',
        'fire': '🔥',
        'thumbs_up': '👍',
        'thumbs_down': '👎'
    }
    
    # 颜色常量
    COLORS = {
        'primary': '#2383e2',
        'success': '#00c851', 
        'warning': '#ffbb33',
        'error': '#ff4444',
        'info': '#33b5e5',
        'background': '#ffffff',
        'card_bg': '#f7f6f3',
        'border': '#e9e9e7',
        'text': '#37352f',
        'text_secondary': '#787774',
        'hover': '#f7f6f3',
        'active': '#eeedeb'
    }
    
    # 文字常量
    MESSAGES = {
        'processing': '正在处理，请稍候...',
        'success': '处理完成！',
        'error': '处理失败，请检查输入',
        'no_files': '没有找到相关文件',
        'file_uploaded': '文件上传成功',
        'config_saved': '配置已保存',
        'config_applied': '配置已应用',
        'config_deleted': '配置已删除',
        'confirm_action': '确认执行此操作？',
        'operation_cancelled': '操作已取消',
        'database_updated': '数据库已更新',
        'backup_created': '备份已创建',
        'backup_restored': '备份已恢复'
    }
    
    # 布局常量
    LAYOUTS = {
        'two_columns': [1, 1],
        'three_columns': [1, 1, 1],
        'sidebar_main': [1.2, 3],
        'form_actions': [1, 1, 1],
        'nav_buttons': [1, 2, 1],
        'config_section': [3, 1]
    }
    
    # 组件尺寸
    SIZES = {
        'text_area_height': 400,
        'code_block_height': 300,
        'browser_height': 600,
        'card_padding': 20,
        'button_height': 32
    }