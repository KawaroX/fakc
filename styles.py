"""
样式文件 - 修复版本，基于Streamlit原生header
完全移除自定义header，重新设计原生header样式和侧边栏按钮
"""

def get_notion_styles():
    """返回基于Streamlit原生header的Notion风格样式"""
    return """
<style>
    /* Notion风格全局样式 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
    }

    /* 确保Material Icons正确显示 */
    .material-icons {
        font-family: 'Material Icons';
        font-weight: normal;
        font-style: normal;
        font-size: 18px;
        display: inline-block;
        line-height: 1;
        text-transform: none;
        letter-spacing: normal;
        word-wrap: normal;
        white-space: nowrap;
        direction: ltr;
        -webkit-font-smoothing: antialiased;
        text-rendering: optimizeLegibility;
        -moz-osx-font-smoothing: grayscale;
        font-feature-settings: 'liga';
    }
    
    /* ===== 删除自定义header ===== */
    .notion-header {
        display: none !important;
    }
    
    /* ===== 重新设计Streamlit原生header和工具栏 ===== */
    header[data-testid="stHeader"] {
        background: #ffffff !important;
        border-bottom: 1px solid #e9e9e7 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
        height: 48px !important;
        z-index: 1000 !important;
    }
    
    /* Header工具栏样式 */
    div[data-testid="stToolbar"] {
        height: 48px !important;
        padding: 0 16px !important;
        position: relative !important;
    }
    
    /* 修复透明工具栏容器 - 这是导致侧边栏空白的元素 */
    .st-emotion-cache-1j22a0y.e4x2yc34 {
        background: #ffffff !important;
        height: 48px !important;
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 999 !important;
        border-bottom: 1px solid #e9e9e7 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        padding: 0 16px !important;
    }
    
    /* 工具栏左侧区域 */
    .st-emotion-cache-70qvj9.e4x2yc35 {
        display: flex !important;
        align-items: center !important;
        height: 100% !important;
    }
    
    /* 工具栏右侧区域 */
    .st-emotion-cache-scp8yw.e4x2yc36 {
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        height: 100% !important;
    }
    
    /* 在工具栏左侧添加应用标题 */
    .st-emotion-cache-70qvj9.e4x2yc35::after {
        content: "🎓 法考字幕转Obsidian笔记处理器";
        font-size: 14px;
        font-weight: 500;
        color: #37352f;
        margin-left: 16px;
        white-space: nowrap;
    }
    
    /* ===== 重新设计侧边栏按钮 ===== */
    
    /* 展开侧边栏时的按钮样式 */
    button[data-testid="stExpandSidebarButton"] {
        background: transparent !important;
        border: none !important;
        width: 32px !important;
        height: 32px !important;
        border-radius: 3px !important;
        transition: all 0.2s ease !important;
        position: relative !important;
        margin-right: 8px !important;
    }
    
    button[data-testid="stExpandSidebarButton"]:hover {
        background: #f7f6f3 !important;
    }
    
    button[data-testid="stExpandSidebarButton"]:active {
        background: #eeedeb !important;
    }
    
    /* 收起侧边栏时的按钮样式 */
    button[data-testid="stBaseButton-headerNoPadding"] {
        background: transparent !important;
        border: none !important;
        width: 32px !important;
        height: 32px !important;
        border-radius: 3px !important;
        transition: all 0.2s ease !important;
        position: relative !important;
        margin-right: 8px !important;
    }
    
    button[data-testid="stBaseButton-headerNoPadding"]:hover {
        background: #f7f6f3 !important;
    }
    
    button[data-testid="stBaseButton-headerNoPadding"]:active {
        background: #eeedeb !important;
    }
    
    /* 隐藏所有侧边栏按钮的原有内容 */
    button[data-testid="stExpandSidebarButton"] span,
    button[data-testid="stBaseButton-headerNoPadding"] span {
        display: none !important;
    }
    
    /* 隐藏原有的Material Icons */
    button[data-testid="stExpandSidebarButton"] span[data-testid="stIconMaterial"],
    button[data-testid="stBaseButton-headerNoPadding"] span[data-testid="stIconMaterial"] {
        display: none !important;
    }
    
    /* 展开状态时的汉堡菜单图标 */
    button[data-testid="stExpandSidebarButton"]::before {
        content: "";
        position: absolute;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        width: 18px;
        height: 18px;
        background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23787774' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='3' y1='6' x2='21' y2='6'%3E%3C/line%3E%3Cline x1='3' y1='12' x2='21' y2='12'%3E%3C/line%3E%3Cline x1='3' y1='18' x2='21' y2='18'%3E%3C/line%3E%3C/svg%3E") no-repeat center;
        background-size: 18px 18px;
        z-index: 10;
    }
    
    /* 收起状态时的展开图标 */
    button[data-testid="stBaseButton-headerNoPadding"]::before {
        content: "";
        position: absolute;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        width: 18px;
        height: 18px;
        background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%23787774' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6,9 12,15 18,9'%3E%3C/polyline%3E%3C/svg%3E") no-repeat center;
        background-size: 18px 18px;
        z-index: 10;
        transform: translate(-50%, -50%) rotate(-90deg);
    }
    
    /* 右侧按钮区域样式调整 */
    div[data-testid="stToolbarActions"] {
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
    }
    
    /* Deploy按钮样式 */
    div[data-testid="stAppDeployButton"] button {
        background: transparent !important;
        border: 1px solid #e9e9e7 !important;
        border-radius: 3px !important;
        color: #37352f !important;
        font-size: 12px !important;
        font-weight: 500 !important;
        padding: 4px 8px !important;
        height: 28px !important;
        transition: all 0.2s ease !important;
    }
    
    div[data-testid="stAppDeployButton"] button:hover {
        background: #f7f6f3 !important;
        border-color: #d9d9d7 !important;
    }
    
    /* 主菜单按钮样式 */
    span[data-testid="stMainMenu"] button {
        background: transparent !important;
        border: none !important;
        width: 32px !important;
        height: 32px !important;
        border-radius: 3px !important;
        transition: background 0.2s ease !important;
    }
    
    span[data-testid="stMainMenu"] button:hover {
        background: #f7f6f3 !important;
    }
    
    span[data-testid="stMainMenu"] button svg {
        color: #787774 !important;
        width: 18px !important;
        height: 18px !important;
    }
    
    /* ===== 全局样式 ===== */
    
    /* 背景色 */
    .stApp {
        background: #ffffff;
    }
    
    .main {
        background: #ffffff;
        padding-top: 48px !important; /* 为header留出空间 */
    }
    
    /* 侧边栏样式 - 修复定位问题 */
    section[data-testid="stSidebar"] {
        background: #f7f6f3;
        border-right: 1px solid #e9e9e7;
        top: 48px !important; /* 紧贴修复后的header */
        height: calc(100vh - 48px) !important;
        padding: 0 !important;
        margin: 0 !important;
        box-sizing: border-box !important;
        z-index: 998 !important; /* 确保在header下方 */
    }
    
    /* 侧边栏的第一层子容器 */
    section[data-testid="stSidebar"] > div {
        padding: 0 !important;
        margin: 0 !important;
        height: 100% !important;
        box-sizing: border-box !important;
    }
    
    /* 侧边栏的所有子容器 */
    section[data-testid="stSidebar"] * {
        box-sizing: border-box !important;
    }
    
    /* 移除可能的顶部间距 */
    section[data-testid="stSidebar"] .stBlock:first-child {
        margin-top: 0 !important;
        padding-top: 8px !important; /* 给第一个元素一点顶部间距 */
    }
    
    /* 移除任何可能的伪元素 */
    section[data-testid="stSidebar"]::before,
    section[data-testid="stSidebar"]::after {
        display: none !important;
    }
    
    /* 深度重置所有可能的容器 */
    section[data-testid="stSidebar"] .css-1d391kg,
    section[data-testid="stSidebar"] .stVerticalBlock,
    section[data-testid="stSidebar"] .element-container {
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* 特殊处理：Streamlit可能的隐藏元素 */
    section[data-testid="stSidebar"] div[data-testid*="stVerticalBlock"]:first-child {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* 主内容区域 */
    .main > div {
        padding-top: 20px !important;
        max-width: 900px;
        margin: 0 auto;
    }
    
    /* 标题样式 */
    h1, h2, h3, h4, h5, h6 {
        color: #37352f;
        font-weight: 600;
        letter-spacing: -0.01em;
    }
    
    h1 { 
        font-size: 40px; 
        margin: 0 0 8px 0 !important; /* 移除顶部margin */
    }
    h2 { font-size: 24px; margin: 24px 0 8px 0; }
    h3 { font-size: 20px; margin: 16px 0 8px 0; }
    
    /* 卡片容器 */
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
    
    /* 侧边栏菜单容器 */
    section[data-testid="stSidebar"] .css-1d391kg {
        padding: 8px !important;
    }
    
    /* 侧边栏整体容器 */
    section[data-testid="stSidebar"] .stBlock {
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* 侧边栏元素容器 */
    section[data-testid="stSidebar"] .element-container {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* ===== Notion风格的侧边栏Radio按钮 ===== */
    
    /* 隐藏"功能菜单"标题 */
    section[data-testid="stSidebar"] h2 {
        display: none !important;
    }
    
    /* 侧边栏菜单容器 */
    section[data-testid="stSidebar"] .stRadio {
        margin: 0 !important;
        padding: 8px !important;
    }
    
    /* Radio按钮组容器 */
    section[data-testid="stSidebar"] .stRadio > div {
        gap: 0 !important;
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }
    
    /* 完全隐藏原有的radio圆圈和相关元素 */
    section[data-testid="stSidebar"] .stRadio input[type="radio"] {
        display: none !important;
    }
    
    /* 隐藏所有圆圈选择器相关的div */
    section[data-testid="stSidebar"] .stRadio div[class*="st-au"],
    section[data-testid="stSidebar"] .stRadio div[class*="st-bx"],
    section[data-testid="stSidebar"] .stRadio div[class*="st-e1"],
    section[data-testid="stSidebar"] .stRadio div[class*="st-c0"],
    section[data-testid="stSidebar"] .stRadio > div > label > div:first-child {
        display: none !important;
    }
    
    /* 通用隐藏：所有可能的圆圈容器 */
    section[data-testid="stSidebar"] .stRadio [class*="st-au"][class*="st-bx"],
    section[data-testid="stSidebar"] .stRadio [class*="st-e1"][class*="st-c0"] {
        display: none !important;
    }
    
    /* Radio标签样式 - Notion风格 */
    section[data-testid="stSidebar"] .stRadio > div > label {
        background: transparent !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 8px 12px !important;
        margin: 1px 0 !important;
        cursor: pointer !important;
        font-size: 14px !important;
        font-weight: 400 !important;
        color: #37352f !important;
        transition: all 0.15s ease !important;
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        box-sizing: border-box !important;
        text-align: left !important;
        min-height: 36px !important;
        line-height: 1.2 !important;
        position: relative !important;
    }
    
    /* 确保label内容正确显示 */
    section[data-testid="stSidebar"] .stRadio > div > label > div:last-child {
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        margin-left: 0 !important;
    }
    
    /* Hover状态 */
    section[data-testid="stSidebar"] .stRadio > div > label:hover {
        background: rgba(55, 53, 47, 0.08) !important;
        color: #37352f !important;
    }
    
    /* 选中状态 */
    section[data-testid="stSidebar"] .stRadio input[type="radio"]:checked + label,
    section[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {
        background: rgba(35, 131, 226, 0.1) !important;
        color: #2383e2 !important;
        border: 1px solid rgba(35, 131, 226, 0.3) !important;
        font-weight: 500 !important;
    }
    
    /* 选中状态的hover */
    section[data-testid="stSidebar"] .stRadio input[type="radio"]:checked + label:hover,
    section[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"]:hover {
        background: rgba(35, 131, 226, 0.15) !important;
        border-color: rgba(35, 131, 226, 0.4) !important;
    }
    
    /* 活动状态 */
    section[data-testid="stSidebar"] .stRadio > div > label:active {
        background: rgba(55, 53, 47, 0.12) !important;
        transform: scale(0.98) !important;
    }
    
    /* 移除label的before和after伪元素（如果有的话） */
    section[data-testid="stSidebar"] .stRadio > div > label::before,
    section[data-testid="stSidebar"] .stRadio > div > label::after {
        display: none !important;
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
        /* 移动端工具栏标题调整 */
        .st-emotion-cache-70qvj9.e4x2yc35::after {
            font-size: 12px;
            margin-left: 8px;
        }
        
        /* 移动端工具栏容器调整 */
        .st-emotion-cache-1j22a0y.e4x2yc34 {
            padding: 0 12px !important;
        }
        
        /* 移动端侧边栏按钮调整 */
        button[data-testid="stExpandSidebarButton"],
        button[data-testid="stBaseButton-headerNoPadding"] {
            width: 28px !important;
            height: 28px !important;
        }
        
        /* 移动端主内容调整 */
        .main {
            padding-top: 48px !important;
        }
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
    
    header[data-testid="stHeader"] {
        background: #2d2d2d !important;
        border-bottom-color: #404040 !important;
    }
    
    div[data-testid="stToolbar"]::before {
        color: #ffffff !important;
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
    
    section[data-testid="stSidebar"] {
        background: #2d2d2d !important;
        border-right-color: #404040 !important;
    }
    """
    
    return get_custom_css(dark_styles)