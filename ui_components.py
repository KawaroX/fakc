"""
UI组件文件 - 包含可复用的UI组件函数
完整版本，包含所有界面组件和修复后的布局，新增模型选择和第一步结果展示组件
"""

import streamlit as st
import json
import yaml
import math
from typing import List, Dict, Any, Optional, Callable
from intelligent_segmenter import Segment

def fix_material_icons_in_text(text: str) -> str:
    """
    修复文本中的Material Icons名称，转换为emoji
    
    Args:
        text: 包含Material Icons名称的文本
        
    Returns:
        修复后的文本
    """
    # Material Icons到emoji的映射 (仅保留非Material Icons的替换，或根据需要移除所有替换)
    # 由于用户希望显示Material Icons，这里不再进行替换，而是依赖CSS加载
    # 如果有其他非Material Icons的文本需要替换为emoji，可以在这里添加
    # 例如：
    # icon_mapping = {
    #     'custom_icon_name': '✨'
    # }
    # for material_name, emoji in icon_mapping.items():
    #     text = text.replace(material_name, emoji)
    
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

def render_model_selector(config_type: str, saved_configs: dict, current_config: dict, 
                         label: str = None, help_text: str = None, key: str = None):
    """
    渲染模型选择器组件
    
    Args:
        config_type: 配置类型 (subtitle/concept)
        saved_configs: 已保存的配置字典
        current_config: 当前配置
        label: 选择器标签
        help_text: 帮助文本
        key: Streamlit组件的key
        
    Returns:
        选择的配置信息
    """
    if not label:
        label = f"🤖 选择{config_type}模型配置"
    
    # 构建选项列表
    options = []
    option_data = {}
    
    # 添加当前配置选项
    current_name = current_config.get('name', '当前配置')
    options.append(f"✅ {current_name} (当前)")
    option_data[f"✅ {current_name} (当前)"] = current_config
    
    # 添加已保存的配置选项
    for config_name, config_data in saved_configs.items():
        if config_name != current_name:
            options.append(f"💾 {config_name}")
            option_data[f"💾 {config_name}"] = {
                'name': config_name,
                **config_data
            }
    
    # 如果没有其他配置，添加提示
    if len(options) == 1:
        st.info("💡 提示：可以在⚙️模型配置页面保存更多配置方案")
    
    # 选择器
    selected_option = st.selectbox(
        label,
        options,
        index=0,
        help=help_text or "选择要使用的AI模型配置",
        key=key
    )
    
    selected_config = option_data[selected_option]
    
    # 显示配置详情
    with st.expander(f"📋 {selected_config['name']} 配置详情", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Base URL**: `{selected_config['base_url']}`")
            st.write(f"**Model**: `{selected_config['model']}`")
        with col2:
            api_key_display = selected_config['api_key'][:8] + "..." if len(selected_config['api_key']) > 8 else selected_config['api_key']
            st.write(f"**API Key**: `{api_key_display}`")
    
    return selected_config

def render_step1_result_viewer(analysis_result: dict, allow_edit: bool = True):
    """
    渲染第一步分析结果查看器
    
    Args:
        analysis_result: 第一步分析结果
        allow_edit: 是否允许编辑
        
    Returns:
        用户操作结果和可能修改的分析结果
    """
    st.subheader("📋 第一步分析结果")
    
    if not analysis_result:
        st.error("❌ 第一步分析结果为空")
        return {'action': 'retry', 'result': None}
    
    # 显示课程概览
    if 'course_overview' in analysis_result:
        overview = analysis_result['course_overview']
        st.markdown("### 📚 课程概览")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**主要话题**: {overview.get('main_topic', '未知')}")
            st.write(f"**总时长**: {overview.get('total_duration', '未知')}")
            st.write(f"**难度等级**: {overview.get('difficulty_level', '未知')}")
        
        with col2:
            st.write(f"**教学风格**: {overview.get('teaching_style', '未知')}")
            if overview.get('key_emphasis'):
                st.write(f"**重点强调**: {', '.join(overview['key_emphasis'][:3])}")
    
    # 显示知识点统计
    if 'knowledge_points' in analysis_result:
        knowledge_points = analysis_result['knowledge_points']
        st.markdown("### 📊 知识点统计")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总知识点", len(knowledge_points))
        with col2:
            high_importance = len([kp for kp in knowledge_points if kp.get('importance_level') == '高'])
            st.metric("高重要性", high_importance)
        with col3:
            concept_types = set([kp.get('concept_type', '未知') for kp in knowledge_points])
            st.metric("概念类型", len(concept_types))
        with col4:
            avg_time = "计算中..." if knowledge_points else "无数据"
            st.metric("平均时长", avg_time)
        
        # 显示知识点列表
        st.markdown("### 📝 知识点详情")
        
        # 分重要性显示
        for importance in ['高', '中', '低']:
            filtered_kps = [kp for kp in knowledge_points if kp.get('importance_level') == importance]
            if filtered_kps:
                with st.expander(f"🎯 {importance}重要性知识点 ({len(filtered_kps)}个)", expanded=(importance == '高')):
                    for i, kp in enumerate(filtered_kps, 1):
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.write(f"**{i}. {kp.get('concept_name', '未命名')}**")
                            if kp.get('core_definition', {}).get('teacher_original'):
                                st.caption(f"💬 {kp['core_definition']['teacher_original'][:100]}...")
                        with col2:
                            st.write(f"🏷️ {kp.get('concept_type', '未知')}")
                        with col3:
                            st.write(f"⏰ {kp.get('time_range', '未知')}")
    
    # 显示概念结构
    if 'concept_structure' in analysis_result:
        structure = analysis_result['concept_structure']
        with st.expander("🗺️ 概念结构关系", expanded=False):
            if structure.get('hierarchy'):
                st.write(f"**层次结构**: {structure['hierarchy']}")
            if structure.get('main_logic_flow'):
                st.write(f"**逻辑脉络**: {structure['main_logic_flow']}")
            if structure.get('cross_references'):
                st.write(f"**交叉引用**: {len(structure['cross_references'])}个关系")
    
    # 显示教学洞察
    if 'teaching_insights' in analysis_result:
        insights = analysis_result['teaching_insights']
        with st.expander("👨‍🏫 教学风格分析", expanded=False):
            if insights.get('teacher_preferences'):
                st.write(f"**教学偏好**: {insights['teacher_preferences']}")
            if insights.get('emphasis_pattern'):
                st.write(f"**强调模式**: {insights['emphasis_pattern']}")
            if insights.get('student_attention'):
                st.write("**学习要点**:")
                for attention in insights['student_attention']:
                    st.write(f"  - {attention}")
    
    st.markdown("---")
    
    # 操作按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ 确认继续", type="primary", use_container_width=True):
            return {'action': 'continue', 'result': analysis_result}
    
    with col2:
        if st.button("✏️ 手动编辑", use_container_width=True):
            return {'action': 'edit', 'result': analysis_result}
    
    with col3:
        if st.button("🔄 重新分析", use_container_width=True):
            return {'action': 'retry', 'result': None}
    
    return {'action': 'none', 'result': analysis_result}

def render_step1_result_editor(analysis_result: dict):
    """
    渲染第一步结果编辑器
    
    Args:
        analysis_result: 第一步分析结果
        
    Returns:
        编辑后的分析结果
    """
    st.subheader("✏️ 编辑第一步分析结果")
    st.info("💡 您可以直接编辑下面的JSON内容，修改分析结果")
    
    # 将结果转换为格式化的JSON字符串
    json_content = json.dumps(analysis_result, ensure_ascii=False, indent=2)
    
    # 文本编辑器
    edited_content = st.text_area(
        "编辑分析结果 (JSON格式)",
        value=json_content,
        height=400,
        help="请保持有效的JSON格式"
    )
    
    # 验证和保存按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 验证格式", use_container_width=True):
            try:
                json.loads(edited_content)
                st.success("✅ JSON格式正确")
            except json.JSONDecodeError as e:
                st.error(f"❌ JSON格式错误: {e}")
    
    with col2:
        if st.button("💾 保存修改", type="primary", use_container_width=True):
            try:
                edited_result = json.loads(edited_content)
                st.success("✅ 修改已保存")
                return {'action': 'save', 'result': edited_result}
            except json.JSONDecodeError as e:
                st.error(f"❌ 无法保存，JSON格式错误: {e}")
                return {'action': 'error', 'result': analysis_result}
    
    with col3:
        if st.button("❌ 取消编辑", use_container_width=True):
            return {'action': 'cancel', 'result': analysis_result}
    
    return {'action': 'none', 'result': analysis_result}

def render_two_step_progress(current_step: int, step1_completed: bool = False, step2_completed: bool = False):
    """
    渲染两步走进度指示器
    
    Args:
        current_step: 当前步骤 (1 或 2)
        step1_completed: 第一步是否完成
        step2_completed: 第二步是否完成
    """
    col1, col2 = st.columns(2)
    
    with col1:
        if current_step == 1:
            if step1_completed:
                st.success("✅ 第一步：知识点分析 - 已完成")
            else:
                st.info("🔄 第一步：知识点分析 - 进行中")
        else:
            if step1_completed:
                st.success("✅ 第一步：知识点分析 - 已完成")
            else:
                st.write("⏸️ 第一步：知识点分析 - 待完成")
    
    with col2:
        if current_step == 2:
            if step2_completed:
                st.success("✅ 第二步：笔记生成 - 已完成")
            else:
                st.info("🔄 第二步：笔记生成 - 进行中")
        elif step1_completed:
            st.write("⏭️ 第二步：笔记生成 - 准备中")
        else:
            st.write("⏸️ 第二步：笔记生成 - 等待第一步完成")

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

def render_segmentation_summary(segments: List[Segment], original_token_count: int):
    """
    渲染智能分段结果摘要
    
    Args:
        segments: 分段结果列表
        original_token_count: 原始token数量
    """
    if not segments:
        st.warning("⚠️ 没有分段结果")
        return
    
    total_tokens = sum(seg.token_count for seg in segments)
    reduction_ratio = (1 - total_tokens / original_token_count) * 100 if original_token_count > 0 else 0
    
    # 统计卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="分段数量",
            value=len(segments),
            help="智能分段后的片段总数"
        )
    
    with col2:
        st.metric(
            label="Token减少",
            value=f"{reduction_ratio:.1f}%",
            delta=f"-{original_token_count - total_tokens}",
            help="相比原始字幕的token减少比例"
        )
    
    with col3:
        st.metric(
            label="原始Tokens",
            value=f"{original_token_count:,}",
            help="原始字幕的预估token数量"
        )
    
    with col4:
        st.metric(
            label="分段后Tokens", 
            value=f"{total_tokens:,}",
            help="分段处理后的预估token数量"
        )
    
    # 效果评估
    if reduction_ratio >= 60:
        st.success(f"🎉 分段效果优秀！Token减少了{reduction_ratio:.1f}%")
    elif reduction_ratio >= 30:
        st.info(f"👍 分段效果良好！Token减少了{reduction_ratio:.1f}%")
    elif reduction_ratio >= 10:
        st.warning(f"⚠️ 分段效果一般，Token减少了{reduction_ratio:.1f}%")
    else:
        st.error(f"❌ 分段效果较差，仅减少了{reduction_ratio:.1f}%")

def render_segment_details(segments: List[Segment], show_content: bool = False):
    """
    渲染分段详细信息
    
    Args:
        segments: 分段结果列表
        show_content: 是否显示分段内容
    """
    if not segments:
        return
    
    st.subheader("📊 分段详情")
    
    for i, segment in enumerate(segments, 1):
        with st.expander(f"分段 {i}: {segment.time_range.start:.1f}s - {segment.time_range.end:.1f}s"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write("**基本信息:**")
                st.write(f"- 时间范围: {segment.time_range.start:.1f}s - {segment.time_range.end:.1f}s")
                st.write(f"- 时长: {segment.time_range.duration:.1f}s")
                st.write(f"- Token数量: {segment.token_count}")
                st.write(f"- 关联知识点: {len(segment.knowledge_points)}个")
                
                if segment.knowledge_points:
                    st.write("**关联知识点ID:**")
                    for kp_id in segment.knowledge_points:
                        st.write(f"  - `{kp_id}`")
            
            with col2:
                st.write("**缓冲区信息:**")
                buffer_info = segment.buffer_info
                
                if buffer_info.get('type') == 'fallback':
                    st.warning("⚠️ Fallback模式")
                    st.caption(f"原因: {buffer_info.get('reason', '未知')}")
                elif buffer_info.get('type') == 'full_text':
                    st.info("📄 完整文本模式")
                    st.caption(f"原因: {buffer_info.get('reason', '未知')}")
                else:
                    st.write(f"- 匹配行数: {buffer_info.get('matched_lines', 'N/A')}")
                    st.write(f"- 缓冲区: ±{buffer_info.get('buffer_added', 0)}s")
                    
                    first_ts = buffer_info.get('first_timestamp')
                    last_ts = buffer_info.get('last_timestamp')
                    if first_ts is not None and last_ts is not None:
                        st.write(f"- 实际范围: {first_ts:.1f}s - {last_ts:.1f}s")
            
            # 显示分段内容
            if show_content and segment.text.strip():
                st.write("**分段内容:**")
                with st.container():
                    # 限制显示长度
                    display_text = segment.text
                    if len(display_text) > 500:
                        display_text = display_text[:500] + "..."
                    
                    st.text_area(
                        f"分段{i}内容",
                        value=display_text,
                        height=150,
                        disabled=True,
                        key=f"segment_content_{i}"
                    )

def render_segmentation_controls():
    """
    渲染分段参数控制界面
    
    Returns:
        分段参数配置字典
    """
    st.subheader("🔧 智能分段参数配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        buffer_seconds = st.slider(
            "缓冲区大小（秒）",
            min_value=0.0,
            max_value=60.0,
            value=30.0,
            step=5.0,
            help="为每个时间段前后添加的缓冲时间"
        )
        
        use_segmentation = st.checkbox(
            "启用智能分段",
            value=True,
            help="是否使用智能分段来减少token使用"
        )
    
    with col2:
        max_gap_seconds = st.slider(
            "最大间隔（秒）",
            min_value=0.0,
            max_value=30.0,
            value=5.0,
            step=1.0,
            help="小于此值的时间段将合并"
        )
        
        show_segment_details = st.checkbox(
            "显示分段详情",
            value=False,
            help="是否在处理过程中显示详细的分段信息"
        )
    
    # 预设配置
    st.write("**预设配置:**")
    preset_col1, preset_col2, preset_col3 = st.columns(3)
    
    with preset_col1:
        if st.button("🚀 高效模式", use_container_width=True):
            st.session_state.buffer_seconds = 20.0
            st.session_state.max_gap_seconds = 3.0
            st.rerun()
    
    with preset_col2:
        if st.button("⚖️ 平衡模式", use_container_width=True):
            st.session_state.buffer_seconds = 30.0
            st.session_state.max_gap_seconds = 5.0
            st.rerun()
    
    with preset_col3:
        if st.button("🔍 精准模式", use_container_width=True):
            st.session_state.buffer_seconds = 45.0
            st.session_state.max_gap_seconds = 10.0
            st.rerun()
    
    return {
        'buffer_seconds': buffer_seconds,
        'max_gap_seconds': max_gap_seconds,
        'use_segmentation': use_segmentation,
        'show_details': show_segment_details
    }

def render_segmentation_preview(segments: List[Segment], max_preview: int = 3):
    """
    渲染分段预览
    
    Args:
        segments: 分段结果列表
        max_preview: 最大预览数量
    """
    if not segments:
        return
    
    st.subheader("👁️ 分段预览")
    
    preview_segments = segments[:max_preview]
    
    for i, segment in enumerate(preview_segments, 1):
        with st.container():
            st.markdown(f"**分段 {i}** - {segment.time_range.start:.1f}s到{segment.time_range.end:.1f}s")
            
            # 显示关联知识点
            if segment.knowledge_points:
                kp_text = ", ".join([f"`{kp}`" for kp in segment.knowledge_points])
                st.caption(f"关联知识点: {kp_text}")
            
            # 显示内容预览
            if segment.text.strip():
                preview_text = segment.text[:200] + "..." if len(segment.text) > 200 else segment.text
                st.text(preview_text)
            else:
                st.caption("（空分段）")
            
            # 显示token信息
            st.caption(f"Token数量: {segment.token_count} | 文本长度: {len(segment.text)}字符")
            
            st.divider()
    
    if len(segments) > max_preview:
        st.info(f"仅显示前{max_preview}个分段，共有{len(segments)}个分段")

def render_segmentation_status(processing_status: str, current_step: str = "", progress: float = 0.0):
    """
    渲染分段处理状态
    
    Args:
        processing_status: 处理状态 (processing, success, error, warning)
        current_step: 当前步骤描述
        progress: 进度百分比 (0.0-1.0)
    """
    status_icons = {
        'processing': '🔄',
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️'
    }
    
    status_colors = {
        'processing': '#2383e2',
        'success': '#00c851',
        'error': '#ff4444',
        'warning': '#ffbb33',
        'info': '#33b5e5'
    }
    
    icon = status_icons.get(processing_status, '🔄')
    color = status_colors.get(processing_status, '#2383e2')
    
    # 状态显示
    status_html = f"""
    <div style="
        background: {color}15;
        border-left: 4px solid {color};
        padding: 12px 16px;
        border-radius: 0 6px 6px 0;
        margin: 8px 0;
    ">
        <div style="color: {color}; font-weight: 500; margin-bottom: 4px;">
            {icon} 智能分段处理状态
        </div>
        <div style="color: #37352f; font-size: 14px;">
            {current_step}
        </div>
    </div>
    """
    
    st.markdown(status_html, unsafe_allow_html=True)
    
    # 进度条
    if processing_status == 'processing' and progress > 0:
        st.progress(progress)

def render_token_comparison_chart(original_tokens: int, segmented_tokens: int):
    """
    渲染Token使用对比图表
    
    Args:
        original_tokens: 原始token数量
        segmented_tokens: 分段后token数量
    """
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        
        # 计算减少比例
        reduction_ratio = (1 - segmented_tokens / original_tokens) * 100 if original_tokens > 0 else 0
        
        # 创建对比图
        fig = go.Figure()
        
        # 添加柱状图
        fig.add_trace(go.Bar(
            name='原始Token',
            x=['Token使用量'],
            y=[original_tokens],
            marker_color='#ff6b6b',
            text=[f'{original_tokens:,}'],
            textposition='auto',
        ))
        
        fig.add_trace(go.Bar(
            name='分段后Token',
            x=['Token使用量'],
            y=[segmented_tokens],
            marker_color='#4ecdc4',
            text=[f'{segmented_tokens:,}'],
            textposition='auto',
        ))
        
        # 更新布局
        fig.update_layout(
            title=f'Token使用量对比 - 减少{reduction_ratio:.1f}%',
            yaxis_title='Token数量',
            barmode='group',
            height=400,
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except ImportError:
        # Fallback：使用简单的metrics显示
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "原始Token",
                f"{original_tokens:,}",
                help="原始字幕的token数量"
            )
        
        with col2:
            st.metric(
                "分段后Token",
                f"{segmented_tokens:,}",
                delta=f"-{original_tokens - segmented_tokens:,}",
                help="智能分段后的token数量"
            )
        
        with col3:
            reduction_ratio = (1 - segmented_tokens / original_tokens) * 100 if original_tokens > 0 else 0
            st.metric(
                "减少比例",
                f"{reduction_ratio:.1f}%",
                help="token减少的百分比"
            )

def render_segmentation_settings_panel():
    """
    渲染分段设置面板
    
    Returns:
        配置设置字典
    """
    with st.sidebar:
        st.markdown("### 🔧 智能分段设置")
        
        # 基础设置
        st.markdown("#### 基础参数")
        
        buffer_seconds = st.number_input(
            "缓冲区大小（秒）",
            min_value=0.0,
            max_value=120.0,
            value=30.0,
            step=5.0,
            help="为时间段前后添加的缓冲时间"
        )
        
        max_gap_seconds = st.number_input(
            "合并间隔（秒）",
            min_value=0.0,
            max_value=60.0,
            value=5.0,
            step=1.0,
            help="小于此值的时间段将自动合并"
        )
        
        # 高级设置
        st.markdown("#### 高级选项")
        
        enable_fallback = st.checkbox(
            "启用Fallback机制",
            value=True,
            help="分段失败时自动使用完整内容"
        )
        
        min_segment_duration = st.number_input(
            "最小分段时长（秒）",
            min_value=1.0,
            max_value=60.0,
            value=5.0,
            step=1.0,
            help="小于此时长的分段将被合并"
        )
        
        # 显示选项
        st.markdown("#### 显示选项")
        
        show_processing_details = st.checkbox(
            "显示处理详情",
            value=True,
            help="显示分段处理的详细信息"
        )
        
        show_token_chart = st.checkbox(
            "显示Token对比图",
            value=True,
            help="显示token使用量的对比图表"
        )
        
        max_preview_segments = st.number_input(
            "预览分段数量",
            min_value=1,
            max_value=10,
            value=3,
            help="预览模式下显示的分段数量"
        )
        
        return {
            'buffer_seconds': buffer_seconds,
            'max_gap_seconds': max_gap_seconds,
            'enable_fallback': enable_fallback,
            'min_segment_duration': min_segment_duration,
            'show_processing_details': show_processing_details,
            'show_token_chart': show_token_chart,
            'max_preview_segments': max_preview_segments
        }

def render_time_range_visualization(segments: List[Segment], total_duration: float = None):
    """
    渲染时间范围可视化
    
    Args:
        segments: 分段列表
        total_duration: 总时长（秒）
    """
    if not segments:
        return
    
    st.subheader("⏰ 时间范围分布")
    
    # 如果没有提供总时长，从分段中计算
    if total_duration is None:
        total_duration = max(seg.time_range.end for seg in segments)
    
    # 创建时间线可视化
    timeline_data = []
    colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffd93d', '#ff9ff3']
    
    for i, segment in enumerate(segments):
        color = colors[i % len(colors)]
        timeline_data.append({
            'segment': f'分段{i+1}',
            'start': segment.time_range.start,
            'end': segment.time_range.end,
            'duration': segment.time_range.duration,
            'tokens': segment.token_count,
            'knowledge_points': len(segment.knowledge_points),
            'color': color
        })
    
    # 使用HTML和CSS创建简单的时间线
    timeline_html = """
    <div style="margin: 20px 0;">
        <div style="position: relative; height: 60px; background: #f7f6f3; border-radius: 6px; overflow: hidden;">
    """
    
    for data in timeline_data:
        left_percent = (data['start'] / total_duration) * 100
        width_percent = (data['duration'] / total_duration) * 100
        
        timeline_html += f"""
            <div style="
                position: absolute;
                left: {left_percent:.1f}%;
                width: {width_percent:.1f}%;
                height: 100%;
                background: {data['color']};
                border-radius: 3px;
                margin: 5px 1px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 12px;
                font-weight: 500;
                opacity: 0.8;
            " title="{data['segment']}: {data['start']:.1f}s - {data['end']:.1f}s ({data['tokens']} tokens)">
                {data['segment']}
            </div>
        """
    
    timeline_html += """
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 8px; font-size: 12px; color: #787774;">
            <span>0s</span>
            <span>""" + f"{total_duration:.1f}s" + """</span>
        </div>
    </div>
    """
    
    st.markdown(timeline_html, unsafe_allow_html=True)
    
    # 显示分段统计表格
    if st.checkbox("显示详细统计表格", value=False):
        import pandas as pd
        
        df_data = []
        for i, data in enumerate(timeline_data, 1):
            df_data.append({
                '分段': f'分段{i}',
                '开始时间': f"{data['start']:.1f}s",
                '结束时间': f"{data['end']:.1f}s", 
                '持续时间': f"{data['duration']:.1f}s",
                'Token数量': data['tokens'],
                '知识点数': data['knowledge_points']
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)

def render_segmentation_debug_info(segments: List[Segment]):
    """
    渲染分段调试信息（开发调试用）
    
    Args:
        segments: 分段列表
    """
    if not st.checkbox("🐛 显示调试信息", value=False):
        return
    
    st.subheader("🔍 调试信息")
    
    for i, segment in enumerate(segments, 1):
        with st.expander(f"调试 - 分段{i}"):
            st.json({
                'time_range': {
                    'start': segment.time_range.start,
                    'end': segment.time_range.end,
                    'duration': segment.time_range.duration,
                    'kp_ids': segment.time_range.kp_ids
                },
                'knowledge_points': segment.knowledge_points,
                'token_count': segment.token_count,
                'text_length': len(segment.text),
                'buffer_info': segment.buffer_info,
                'text_preview': segment.text[:100] + "..." if len(segment.text) > 100 else segment.text
            })

# 以下是集成函数，用于在app.py中调用

def render_complete_segmentation_interface(segments: List[Segment], 
                                         original_tokens: int,
                                         show_controls: bool = True,
                                         show_details: bool = True) -> Dict[str, Any]:
    """
    渲染完整的智能分段界面
    
    Args:
        segments: 分段结果列表
        original_tokens: 原始token数量
        show_controls: 是否显示控制面板
        show_details: 是否显示详细信息
        
    Returns:
        用户交互结果
    """
    result = {'action': 'none'}
    
    if not segments:
        st.warning("⚠️ 没有分段结果")
        return result
    
    # 1. 显示摘要
    render_segmentation_summary(segments, original_tokens)
    
    # 2. 显示Token对比图（如果可用）
    if len(segments) > 0:
        total_segmented_tokens = sum(seg.token_count for seg in segments)
        
        if st.checkbox("📊 显示Token对比图表", value=True):
            render_token_comparison_chart(original_tokens, total_segmented_tokens)
    
    # 3. 显示时间范围可视化
    if st.checkbox("⏰ 显示时间范围分布", value=True):
        render_time_range_visualization(segments)
    
    # 4. 显示分段预览
    if st.checkbox("👁️ 显示分段预览", value=True):
        max_preview = st.slider("预览数量", 1, min(10, len(segments)), 3)
        render_segmentation_preview(segments, max_preview)
    
    # 5. 显示详细信息
    if show_details and st.checkbox("📊 显示详细分段信息", value=False):
        show_content = st.checkbox("显示分段内容", value=False)
        render_segment_details(segments, show_content)
    
    # 6. 调试信息
    render_segmentation_debug_info(segments)
    
    # 7. 操作按钮
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ 确认使用分段结果", type="primary", use_container_width=True):
            result['action'] = 'confirm'
    
    with col2:
        if st.button("🔄 重新分段", use_container_width=True):
            result['action'] = 'retry'
    
    with col3:
        if st.button("❌ 使用完整内容", use_container_width=True):
            result['action'] = 'fallback'
    
    return result

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
        'left_arrow': 'keyboard_arrow_left',  # 使用Material Icons名称
        'right_arrow': 'keyboard_arrow_right',  # 使用Material Icons名称
        'double_left': 'keyboard_double_arrow_left',   # 使用Material Icons名称
        'double_right': 'keyboard_double_arrow_right',  # 使用Material Icons名称
        'up_arrow': 'keyboard_arrow_up',
        'down_arrow': 'keyboard_arrow_down',
        'play': 'play_arrow',
        'pause': 'pause',
        'stop': 'stop',
        'refresh': 'refresh',
        'home': 'home',
        'back': 'arrow_back',
        'forward': 'arrow_forward',
        'check': 'check',
        'cross': 'close',
        'plus': 'add',
        'minus': 'remove',
        'star': 'star',
        'heart': 'favorite',
        'fire': 'local_fire_department',
        'thumbs_up': 'thumb_up',
        'thumbs_down': 'thumb_down'
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

def render_concurrent_processing_status(stats: dict = None, current_batch: int = 1, total_batches: int = 1):
    """
    渲染并发处理状态显示
    
    Args:
        stats: 处理统计信息字典
        current_batch: 当前批次
        total_batches: 总批次数
    """
    with st.expander("📊 并发处理状态", expanded=True):
        if stats is None:
            stats = {
                'total_tasks': 0,
                'completed_tasks': 0,
                'failed_tasks': 0,
                'total_retries': 0,
                'current_concurrent': 0,
                'max_concurrent': 20
            }
        
        # 第一行：主要指标
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "总任务数", 
                stats.get('total_tasks', 0),
                help="需要处理的知识点总数"
            )
        
        with col2:
            completed = stats.get('completed_tasks', 0)
            total = stats.get('total_tasks', 1)
            completion_rate = (completed / total * 100) if total > 0 else 0
            st.metric(
                "已完成", 
                f"{completed}/{total}",
                delta=f"{completion_rate:.1f}%",
                help="已完成的任务数和完成率"
            )
        
        with col3:
            current_concurrent = stats.get('current_concurrent', 0)
            max_concurrent = stats.get('max_concurrent', 20)
            st.metric(
                "当前并发数", 
                f"{current_concurrent}/{max_concurrent}",
                help="当前活跃的API调用数"
            )
        
        with col4:
            failed = stats.get('failed_tasks', 0)
            retries = stats.get('total_retries', 0)
            st.metric(
                "失败/重试", 
                f"{failed}/{retries}",
                help="失败任务数和总重试次数"
            )
        
        # 第二行：进度条和批次信息
        if total_batches > 1:
            st.write("**批次处理进度:**")
            batch_progress = (current_batch - 1) / total_batches if total_batches > 0 else 0
            st.progress(batch_progress)
            st.caption(f"当前批次: {current_batch}/{total_batches}")
        
        # 第三行：处理时间统计
        if 'total_processing_time' in stats and stats['total_processing_time'] > 0:
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "已用时间", 
                    f"{stats['total_processing_time']:.1f}s",
                    help="已消耗的处理时间"
                )
            with col2:
                # 估算剩余时间
                if completed > 0:
                    avg_time_per_task = stats['total_processing_time'] / completed
                    remaining_tasks = total - completed
                    estimated_remaining = avg_time_per_task * remaining_tasks
                    st.metric(
                        "预计剩余", 
                        f"{estimated_remaining:.1f}s",
                        help="根据当前速度估算的剩余时间"
                    )

def render_concurrent_settings():
    """
    渲染并发处理设置界面
    """
    with st.expander("🚀 并发处理设置", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            enable_concurrent = st.checkbox(
                "启用并发处理", 
                value=True, 
                help="对于多个知识点，使用并发方式可显著提高处理速度",
                key="enable_concurrent_processing"
            )
            
            if enable_concurrent:
                max_concurrent = st.slider(
                    "最大并发数",
                    min_value=1,
                    max_value=20,
                    value=20,
                    help="同时进行的API调用数量，不建议超过API限制",
                    key="max_concurrent_limit"
                )
        
        with col2:
            if enable_concurrent:
                max_retries = st.slider(
                    "最大重试次数",
                    min_value=1,
                    max_value=5,
                    value=3,
                    help="单个任务失败后的最大重试次数",
                    key="max_retries_setting"
                )
                
                timeout_seconds = st.slider(
                    "单个任务超时(秒)",
                    min_value=30,
                    max_value=180,
                    value=60,
                    help="单个知识点处理的超时时间",
                    key="task_timeout_setting"
                )
        
        if enable_concurrent:
            st.info("💡 **并发处理优势:**")
            advantages = [
                "🚀 显著提高处理速度（通常快50-70%）",
                "🔄 智能重试机制，提高成功率", 
                "📊 实时进度显示，处理状态清晰",
                "⚡ 自动批次优化，避免API限制",
                "🛡️ 失败任务自动降级到传统方式"
            ]
            
            for advantage in advantages:
                st.write(f"- {advantage}")
        else:
            st.warning("⚠️ 禁用并发处理将使用传统的逐个处理方式，速度较慢但更稳定。")
        
        return {
            'enable_concurrent': enable_concurrent,
            'max_concurrent': max_concurrent if enable_concurrent else 1,
            'max_retries': max_retries if enable_concurrent else 2,
            'timeout': timeout_seconds if enable_concurrent else 60
        }

def render_concurrent_strategy_info(num_knowledge_points: int):
    """
    显示针对当前知识点数量的并发策略信息
    
    Args:
        num_knowledge_points: 知识点数量
    """
    st.subheader("🎯 并发处理策略")
    
    # 根据知识点数量显示不同的策略信息
    if num_knowledge_points <= 2:
        st.info("📝 **策略**: 知识点较少，将使用传统逐个处理方式")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("处理方式", "逐个处理")
        with col2:
            st.metric("预计时间", "正常")
    
    elif num_knowledge_points <= 10:
        recommended_concurrent = min(10, num_knowledge_points)
        st.info(f"⚡ **策略**: 使用适中并发处理 (并发数: {recommended_concurrent})")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("并发数", recommended_concurrent)
        with col2:
            st.metric("预计批次", "1")
        with col3:
            st.metric("预计提速", "50-60%")
    
    else:
        batches = math.ceil(num_knowledge_points / 20)
        st.success(f"🚀 **策略**: 使用最大并发处理 (分{batches}个批次)")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("并发数", "20")
        with col2:
            st.metric("批次数", batches)
        with col3:
            st.metric("预计提速", "60-70%")
        with col4:
            st.metric("批次间隔", "~60s")
        
        if batches > 2:
            st.info("💡 **优化提示**: 系统将智能分配批次，第一批处理完成后会调整后续批次的并发数")

def render_processing_progress_live(progress_container=None):
    """
    渲染实时处理进度显示
    
    Args:
        progress_container: Streamlit容器对象，如果为None则创建新容器
    """
    if progress_container is None:
        progress_container = st.container()
    
    with progress_container:
        # 进度条占位符
        if 'progress_bar' not in st.session_state:
            st.session_state.progress_bar = st.progress(0)
        
        # 进度文本占位符
        if 'progress_text' not in st.session_state:
            st.session_state.progress_text = st.text("准备开始处理...")
        
        # 统计信息占位符
        if 'stats_container' not in st.session_state:
            st.session_state.stats_container = st.empty()
    
    return {
        'progress_bar': st.session_state.progress_bar,
        'progress_text': st.session_state.progress_text,
        'stats_container': st.session_state.stats_container
    }

def update_processing_progress(current: int, total: int, status: str = ""):
    """
    更新处理进度显示
    
    Args:
        current: 当前完成数量
        total: 总数量  
        status: 状态信息
    """
    if 'progress_bar' in st.session_state:
        progress = current / total if total > 0 else 0
        st.session_state.progress_bar.progress(progress)
    
    if 'progress_text' in st.session_state:
        progress_percent = (current / total * 100) if total > 0 else 0
        text = f"处理进度: {current}/{total} ({progress_percent:.1f}%)"
        if status:
            text += f" - {status}"
        st.session_state.progress_text.text(text)

def render_concurrent_results_summary(results_data: dict):
    """
    渲染并发处理结果摘要
    
    Args:
        results_data: 处理结果数据字典
    """
    st.subheader("📊 处理结果摘要")
    
    # 基本统计
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "总知识点", 
            results_data.get('total_knowledge_points', 0),
            help="需要处理的知识点总数"
        )
    
    with col2:
        success_count = results_data.get('successful_notes', 0)
        total_count = results_data.get('total_knowledge_points', 1)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        st.metric(
            "成功生成", 
            success_count,
            delta=f"{success_rate:.1f}%",
            help="成功生成笔记的数量和成功率"
        )
    
    with col3:
        processing_time = results_data.get('total_processing_time', 0)
        st.metric(
            "总用时", 
            f"{processing_time:.1f}s",
            help="总的处理时间"
        )
    
    with col4:
        if results_data.get('used_concurrent', False):
            time_saved = results_data.get('estimated_time_saved', 0)
            st.metric(
                "节省时间", 
                f"{time_saved:.1f}s",
                delta=f"-{time_saved/processing_time*100:.1f}%" if processing_time > 0 else "0%",
                help="相比传统方式节省的时间"
            )
        else:
            st.metric("处理方式", "传统", help="使用了传统的逐个处理方式")
    
    # 详细统计
    if results_data.get('concurrent_stats'):
        with st.expander("📈 详细统计信息", expanded=False):
            stats = results_data['concurrent_stats']
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**API调用统计:**")
                st.write(f"- 总重试次数: {stats.get('total_retries', 0)}")
                st.write(f"- 失败任务数: {stats.get('failed_tasks', 0)}")
                st.write(f"- 处理批次数: {stats.get('batches_processed', 0)}")
            
            with col2:
                st.write("**时间分析:**")
                avg_time = stats.get('total_processing_time', 0) / max(stats.get('completed_tasks', 1), 1)
                st.write(f"- 平均每个知识点: {avg_time:.2f}s")
                st.write(f"- 最大并发数: {stats.get('max_concurrent', 0)}")
                
                if stats.get('batches_processed', 0) > 1:
                    st.write(f"- 批次间平均间隔: ~60s")
