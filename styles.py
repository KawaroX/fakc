"""
样式文件 - 包含所有Streamlit应用的CSS样式
完整版本，包含所有Notion风格样式和修复
"""

def get_notion_styles():
    """返回Notion风格的完整CSS样式"""
    return """
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
    
    /* 顶部标题栏 - 修复遮挡问题 */
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
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .notion-header h1 {
        font-size: 14px;
        font-weight: 500;
        color: #37352f;
        margin: 0;
    }
    
    /* 修复Streamlit默认标题的显示问题 */
    .main .element-container:has(h1) {
        padding-top: 20px;
        position: relative;
        z-index: 1;
    }
    
    /* 确保页面标题可见 */
    .main h1 {
        position: relative;
        z-index: 2;
        background: #ffffff;
        padding: 10px 0;
        margin-top: 0 !important;
    }
    
    /* 修复被遮挡的标题链接 */
    .main h1 a {
        color: inherit;
        text-decoration: none;
    }
    
    .main h1 span[data-testid="stHeaderActionElements"] {
        position: relative;
        z-index: 3;
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
        padding-top: 80px;  /* 增加顶部padding，避免被header遮挡 */
        max-width: 900px;
        margin: 0 auto;
    }
    
    /* 确保页面标题不被遮挡 */
    .main h1:first-of-type {
        margin-top: 20px;
        position: relative;
        z-index: 1;
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
    
    /* 卡片容器 - 修复内容在框内的问题 */
    .notion-card {
        background: #ffffff;
        border: 1px solid #e9e9e7;
        border-radius: 6px;
        padding: 20px;
        margin: 16px 0;
        transition: box-shadow 0.2s ease;
        box-sizing: border-box;
    }
    
    .notion-card:hover {
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }
    
    .notion-card h4 {
        margin-top: 0;
        margin-bottom: 12px;
        color: #37352f;
        font-weight: 600;
        font-size: 16px;
    }
    
    .notion-card ul {
        margin: 0;
        padding-left: 20px;
        list-style-type: disc;
    }
    
    .notion-card ol {
        margin: 0;
        padding-left: 20px;
    }
    
    .notion-card li {
        margin-bottom: 6px;
        color: #37352f;
        line-height: 1.5;
        font-size: 14px;
    }
    
    .notion-card p {
        margin: 0;
        color: #37352f;
        line-height: 1.5;
        font-size: 14px;
    }
    
    /* 修复Streamlit生成的空div */
    .notion-card + div[data-testid="stMarkdownContainer"] {
        display: none;
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
            padding-top: 60px;  /* 移动端减少padding */
        }
        
        section[data-testid="stSidebar"] {
            padding-top: 48px;
        }
        
        .notion-header {
            padding: 0 16px;  /* 移动端减少padding */
        }
        
        .notion-header h1 {
            font-size: 12px;  /* 移动端减小字体 */
        }
    }
    
    /* 特殊修复：确保页面标题总是可见 */
    .main > div > div:first-child h1 {
        position: relative !important;
        z-index: 10 !important;
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(10px);
        padding: 15px 0 !important;
        margin-top: 0 !important;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* 修复特定的Streamlit组件问题 */
    .element-container {
        width: 100% !important;
    }
    
    /* 确保容器内的内容正确显示 */
    div[data-testid="stVerticalBlock"] {
        width: 100%;
    }
    
    /* 修复markdown容器问题 */
    div[data-testid="stMarkdownContainer"] {
        width: 100%;
    }
    
    /* 笔记仓库浏览器样式 */
    .note-browser-sidebar {
        background: #f7f6f3;
        border-radius: 6px;
        padding: 16px;
        height: 600px;
        overflow-y: auto;
    }
    
    .note-browser-main {
        background: #ffffff;
        border: 1px solid #e9e9e7;
        border-radius: 6px;
        padding: 20px;
        height: 600px;
        overflow-y: auto;
    }
    
    /* 统计卡片样式 */
    .stats-card {
        background: #f7f6f3;
        border: 1px solid #e9e9e7;
        border-radius: 6px;
        padding: 16px;
        text-align: center;
        transition: transform 0.2s ease;
    }
    
    .stats-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    
    /* 配置表单样式 */
    .config-form {
        background: #f7f6f3;
        border-radius: 6px;
        padding: 20px;
        margin: 16px 0;
    }
    
    /* 状态指示器 */
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-online {
        background: #00c851;
    }
    
    .status-offline {
        background: #ff4444;
    }
    
    .status-warning {
        background: #ffbb33;
    }
    
    /* 导航按钮样式 */
    .nav-button {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: 4px;
        transition: all 0.2s ease;
    }
    
    .nav-button:hover {
        background: #f7f6f3;
    }
    
    /* 加载动画 */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 2px solid #f3f3f3;
        border-top: 2px solid #2383e2;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* 工具提示样式 */
    .tooltip {
        position: relative;
        display: inline-block;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #37352f;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 8px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 12px;
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
</style>

<!-- 顶部标题栏 -->
<div class="notion-header">
    <h1>🎓 法考字幕转Obsidian笔记处理器</h1>
</div>
"""

def get_custom_css(additional_styles=""):
    """
    获取自定义CSS样式
    
    Args:
        additional_styles: 额外的CSS样式
    
    Returns:
        完整的CSS样式字符串
    """
    base_styles = get_notion_styles()
    
    if additional_styles:
        # 移除base_styles的结束标签，添加额外样式，然后重新添加结束标签
        base_styles = base_styles.replace('</style>', f'{additional_styles}\n</style>')
    
    return base_styles

def apply_dark_theme():
    """应用暗色主题"""
    dark_styles = """
    /* 暗色主题覆盖 */
    .stApp {
        background: #1a1a1a !important;
    }
    
    .main {
        background: #1a1a1a !important;
    }
    
    .notion-card {
        background: #2d2d2d !important;
        border-color: #404040 !important;
    }
    
    .notion-card h4,
    .notion-card p,
    .notion-card li {
        color: #ffffff !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }
    
    .notion-header {
        background: #2d2d2d !important;
        border-bottom-color: #404040 !important;
    }
    
    .notion-header h1 {
        color: #ffffff !important;
    }
    
    section[data-testid="stSidebar"] {
        background: #2d2d2d !important;
        border-right-color: #404040 !important;
    }
    """
    
    return get_custom_css(dark_styles)