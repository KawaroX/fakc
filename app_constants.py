"""
应用常量配置文件 - 完整版本
包含所有应用级别的常量、配置和文本内容
"""

class AppConstants:
    """应用常量类"""
    
    # 版本信息
    VERSION = "2.2.0"
    APP_TITLE = "法考字幕转Obsidian笔记处理器"
    DESCRIPTION = "基于AI的法考笔记智能生成和管理系统"
    AUTHOR = "FAKC Team"
    
    # 支持的文件格式
    SUPPORTED_SUBTITLE_FORMATS = ["lrc", "srt", "vtt", "txt", "ass", "bcc"]
    
    # 菜单选项
    MENU_OPTIONS = [
        "处理新字幕文件",
        "直接输入AI格式文本", 
        "增强现有笔记概念关系",
        "时间戳链接化处理",
        "双链格式修复",
        "查看概念数据库状态",
        "科目文件夹映射",
        "查看笔记仓库",
        "模型配置"
    ]
    
    # 功能描述
    FEATURE_DESCRIPTIONS = {
        "处理新字幕文件": [
            "支持多种字幕文件格式：.lrc, .srt, .vtt, .txt, .ass, .bcc",
            "AI自动提取知识点，生成结构化笔记",
            "自动增强概念关系，建立知识网络", 
            "支持时间戳链接，方便回看视频原文"
        ],
        "直接输入AI格式文本": [
            "直接粘贴AI生成的笔记格式文本",
            "自动解析并生成结构化的Obsidian笔记",
            "支持批量处理多个知识点",
            "自动添加课程链接和元数据"
        ],
        "增强现有笔记概念关系": [
            "使用AI深度分析笔记内容，优化概念关系",
            "支持传统方式和BGE混合检索两种模式",
            "可选择处理全部或特定科目笔记",
            "自动更新概念数据库，构建知识图谱"
        ],
        "时间戳链接化处理": [
            "自动处理笔记中的时间戳标记",
            "将时间戳转换为可跳转的视频链接",
            "支持批量处理所有科目或指定科目",
            "需要笔记中包含course_url字段"
        ],
        "双链格式修复": [
            "自动修复笔记中不规范的双链格式",
            "将无前缀链接转换为带科目前缀的标准格式", 
            "为带前缀但无显示别名的链接添加显示别名",
            "支持查找和显示损坏的双链"
        ],
        "查看概念数据库状态": [
            "查看概念数据库的详细统计信息",
            "了解各科目的概念分布情况",
            "检查数据库文件状态和更新时间",
            "确保数据库文件的完整性"
        ],
        "科目文件夹映射": [
            "查看所有科目与文件夹的对应关系",
            "快速定位各科目的笔记存储位置",
            "验证文件夹的存在状态",
            "了解笔记的组织结构"
        ],
        "查看笔记仓库": [
            "浏览所有已生成的法考笔记",
            "支持按科目分类查看",
            "实时预览笔记内容和元数据",
            "快速检索和定位特定笔记"
        ],
        "模型配置": [
            "配置和管理AI模型参数",
            "支持多个模型配置保存和切换",
            "字幕处理和概念增强分别配置",
            "支持测试模型连接状态"
        ]
    }
    
    # AI格式示例
    AI_FORMAT_EXAMPLE = """=== NOTE_SEPARATOR ===
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
[下一个笔记...]"""
    
    # 增强方式选项
    ENHANCEMENT_METHODS = [
        "传统方式（发送所有概念给AI）",
        "BGE混合检索（embedding召回+reranker精排）🔥 推荐"
    ]
    
    # 处理范围选项
    SCOPE_OPTIONS = {
        "enhancement": [
            "增强所有科目的笔记",
            "增强特定科目的笔记"
        ],
        "timestamp": [
            "处理所有科目的笔记", 
            "处理特定科目的笔记"
        ],
        "repair": [
            "修复所有科目的双链",
            "修复特定科目的双链",
            "查找损坏的双链"
        ]
    }
    
    # 默认BGE参数
    DEFAULT_BGE_PARAMS = {
        "embedding_top_k": 100,
        "rerank_top_k": 15,
        "rerank_threshold": 0.98
    }
    
    # 帮助文本
    HELP_TEXTS = {
        "course_url": "用于生成时间戳链接，支持B站、YouTube等平台",
        "source_info": "笔记的来源标识，默认使用文件名",
        "subject_selection": "选择要处理的法考科目",
        "file_upload": "建议使用LRC格式以减少Token消耗",
        "ai_text_format": "请确保文本格式正确，包含所有必要的分隔符和标记",
        "bge_params": "BGE混合检索能提供更精准的概念关联",
        "scope_selection": "建议先从特定科目开始测试",
        "model_config": "配置AI模型的API密钥、基础URL和模型名称",
        "enhancement_method": "选择概念关系增强的方式，BGE混合检索效果更好",
        "repair_scope": "选择双链修复的范围，建议先测试单个科目",
        "timestamp_processing": "将笔记中的时间戳转换为可点击的视频链接"
    }
    
    # 占位符文本
    PLACEHOLDERS = {
        "ai_text_input": """将AI生成的完整格式文本粘贴到这里...

确保包含：
- === NOTE_SEPARATOR === 分隔符
- YAML: 部分  
- CONTENT: 部分""",
        "course_url": "https://www.bilibili.com/video/BV1xxx",
        "source_info": "手动输入",
        "api_key": "请输入API密钥",
        "base_url": "https://api.example.com/v1",
        "model_name": "模型名称"
    }
    
    # 警告消息
    WARNING_MESSAGES = {
        "repair_all": "这将修复所有笔记的双链格式，建议先备份重要数据",
        "repair_subject": "这将修复 {subject} 科目的所有双链格式",
        "no_database": "概念数据库不存在，请先处理一些字幕文件或运行笔记增强功能来建立数据库。",
        "no_course_url": "请确保笔记的YAML中包含course_url字段，例如：`course_url: \"https://www.bilibili.com/video/BV1xxx\"`",
        "backup_recommended": "建议在执行此操作前备份重要数据",
        "irreversible_action": "此操作不可逆，请谨慎执行",
        "large_dataset": "数据量较大，处理可能需要较长时间",
        "api_key_missing": "API密钥缺失或无效，请检查配置",
        "network_required": "此操作需要网络连接",
        "disk_space": "请确保有足够的磁盘空间"
    }
    
    # 成功消息
    SUCCESS_MESSAGES = {
        "processing_complete": "处理完成！",
        "repair_complete": "双链修复完成！",
        "enhancement_complete": "概念增强完成！",
        "database_updated": "概念数据库已更新",
        "file_uploaded": "文件上传成功",
        "config_saved": "配置已保存",
        "config_applied": "配置已应用",
        "config_deleted": "配置已删除",
        "backup_created": "备份已创建",
        "backup_restored": "备份已恢复",
        "notes_generated": "笔记生成成功",
        "links_processed": "链接处理完成",
        "timestamp_converted": "时间戳转换完成",
        "database_scanned": "数据库扫描完成",
        "operation_successful": "操作执行成功"
    }
    
    # 错误消息
    ERROR_MESSAGES = {
        "no_file": "请先上传字幕文件！",
        "no_text": "请先输入AI格式的文本内容！",
        "parse_failed": "无法解析文本，请检查格式",
        "processing_failed": "处理失败，请检查输入",
        "no_notes_found": "没有找到需要处理的笔记",
        "bge_init_failed": "BGE增强器未成功初始化",
        "api_error": "API调用失败，请检查网络和配置",
        "file_not_found": "找不到指定文件",
        "permission_denied": "权限不足，无法访问文件",
        "invalid_format": "文件格式不支持",
        "network_error": "网络连接失败",
        "timeout_error": "操作超时，请重试",
        "config_error": "配置错误，请检查设置",
        "database_error": "数据库操作失败",
        "unknown_error": "未知错误，请联系技术支持"
    }
    
    # 信息消息
    INFO_MESSAGES = {
        "first_time_setup": "首次使用，正在初始化配置...",
        "loading_database": "正在加载概念数据库...",
        "scanning_files": "正在扫描文件...",
        "building_cache": "正在构建缓存...",
        "analyzing_content": "正在分析内容...",
        "generating_embeddings": "正在生成嵌入向量...",
        "updating_relationships": "正在更新关系...",
        "cleaning_up": "正在清理临时文件...",
        "preparing_output": "正在准备输出...",
        "validating_data": "正在验证数据..."
    }
    
    # 确认消息
    CONFIRM_MESSAGES = {
        "delete_config": "确认删除此配置？",
        "repair_all_links": "确认修复所有双链？此操作将修改多个文件。",
        "enhance_all_notes": "确认增强所有笔记？这可能需要较长时间。",
        "clear_cache": "确认清空缓存？",
        "reset_database": "确认重置数据库？所有数据将丢失。",
        "overwrite_file": "文件已存在，是否覆盖？",
        "large_operation": "这是一个大型操作，确认继续？"
    }

class UIConfig:
    """UI配置类"""
    
    # 页面配置
    PAGE_CONFIG = {
        "page_title": AppConstants.APP_TITLE,
        "layout": "wide", 
        "initial_sidebar_state": "expanded",
        "page_icon": "🎓"
    }
    
    # 列布局配置
    COLUMN_LAYOUTS = {
        "two_equal": [1, 1],
        "three_equal": [1, 1, 1],
        "four_equal": [1, 1, 1, 1],
        "sidebar_main": [1.2, 3],
        "form_buttons": [1, 3],
        "config_buttons": [3, 1],
        "nav_buttons": [1, 2, 1],
        "stats_display": [1, 1, 1, 1],
        "action_buttons": [1, 1, 1]
    }
    
    # 表单配置
    FORM_CONFIG = {
        "model_config": {
            "save_btn_text": "💾 保存",
            "apply_btn_text": "✅ 应用",
            "reset_btn_text": "🔄 重置",
            "delete_btn_text": "🗑️ 删除"
        },
        "processing": {
            "start_btn_text": "🚀 开始处理",
            "stop_btn_text": "⏹️ 停止处理",
            "pause_btn_text": "⏸️ 暂停",
            "resume_btn_text": "▶️ 继续"
        },
        "repair": {
            "repair_btn_text": "🔧 开始修复",
            "check_btn_text": "🔍 检查",
            "preview_btn_text": "👁️ 预览"
        }
    }
    
    # 展开器配置
    EXPANDER_CONFIG = {
        "ai_format_example": {
            "title": "📄 查看AI格式示例",
            "expanded": False
        },
        "preview_result": {
            "title": "👁️ 预览解析结果", 
            "expanded": False
        },
        "bge_params": {
            "title": "⚙️ BGE混合检索参数配置",
            "expanded": False
        },
        "advanced_settings": {
            "title": "🔧 高级设置",
            "expanded": False
        },
        "file_info": {
            "title": "📄 文件信息",
            "expanded": False
        },
        "metadata": {
            "title": "📌 元数据",
            "expanded": False
        }
    }
    
    # 组件尺寸
    COMPONENT_SIZES = {
        "text_area_height": 400,
        "code_block_height": 300,
        "browser_height": 600,
        "sidebar_height": 500,
        "card_min_height": 120,
        "button_width": "100%",
        "progress_height": 10
    }
    
    # 动画配置
    ANIMATION_CONFIG = {
        "fade_duration": "0.3s",
        "slide_duration": "0.2s",
        "hover_transition": "0.2s",
        "loading_speed": "1s"
    }

class ModelConfig:
    """模型配置类"""
    
    # 模型选项卡
    MODEL_TABS = [
        "🤖 字幕处理模型",
        "🔗 概念增强模型", 
        "⚙️ 高级设置"
    ]
    
    # 默认模型配置
    DEFAULT_MODELS = {
        "subtitle_processing": {
            "base_url": "https://openrouter.ai/api/v1",
            "model": "deepseek/deepseek-r1-0528:free"
        },
        "concept_enhancement": {
            "base_url": "https://openrouter.ai/api/v1", 
            "model": "openrouter/cypher-alpha:free"
        }
    }
    
    # 推荐模型
    RECOMMENDED_MODELS = {
        "high_performance": [
            "DeepSeek-R1 - 性价比极高，中文理解能力强",
            "Claude 4 (Sonnet/Opus) - 逻辑推理能力出色", 
            "GPT-4.1 - 稳定可靠，对法律术语理解深入"
        ],
        "budget_friendly": [
            "OpenRouter/Cypher-Alpha:free - 免费可用",
            "DeepSeek/DeepSeek-R1:free - 免费高性能",
            "Qwen/Qwen2.5-72B:free - 免费大模型"
        ],
        "specialized": [
            "Claude-3.5-Sonnet - 最佳逻辑推理",
            "GPT-4-Turbo - 最快响应速度",
            "Gemini-1.5-Pro - 最大上下文长度"
        ]
    }
    
    # 模型参数配置
    MODEL_PARAMS = {
        "temperature": {
            "min": 0.0,
            "max": 2.0,
            "default": 0.0,
            "step": 0.1
        },
        "max_tokens": {
            "min": 100,
            "max": 8192,
            "default": 4096,
            "step": 100
        },
        "top_p": {
            "min": 0.0,
            "max": 1.0,
            "default": 1.0,
            "step": 0.1
        }
    }

class ProcessingConfig:
    """处理配置类"""
    
    # 处理模式
    PROCESSING_MODES = {
        "single_file": "单文件处理",
        "batch_files": "批量文件处理",
        "ai_text": "AI文本处理",
        "enhancement": "概念增强",
        "repair": "双链修复",
        "timestamp": "时间戳处理"
    }
    
    # 质量等级
    QUALITY_LEVELS = {
        "fast": {
            "name": "快速模式",
            "description": "快速处理，适合大批量文件",
            "embedding_top_k": 50,
            "rerank_top_k": 10
        },
        "balanced": {
            "name": "平衡模式", 
            "description": "平衡速度和质量",
            "embedding_top_k": 100,
            "rerank_top_k": 15
        },
        "high": {
            "name": "高质量模式",
            "description": "最佳质量，处理速度较慢",
            "embedding_top_k": 200,
            "rerank_top_k": 25
        }
    }
    
    # 支持的视频平台
    SUPPORTED_PLATFORMS = {
        "bilibili": {
            "name": "哔哩哔哩",
            "url_pattern": r"bilibili\.com",
            "timestamp_format": "&t={seconds}"
        },
        "youtube": {
            "name": "YouTube",
            "url_pattern": r"youtube\.com|youtu\.be",
            "timestamp_format": "&t={seconds}s"
        },
        "generic": {
            "name": "通用平台",
            "url_pattern": r".*",
            "timestamp_format": "&t={seconds}"
        }
    }
    
    # 批处理配置
    BATCH_CONFIG = {
        "max_files": 100,
        "max_file_size": 50 * 1024 * 1024,  # 50MB
        "chunk_size": 10,
        "timeout": 300,  # 5分钟
        "retry_times": 3
    }

class DatabaseConfig:
    """数据库配置类"""
    
    # 数据库文件名
    DATABASE_FILES = {
        "markdown": "概念数据库.md",
        "json": "概念数据库.json",
        "cache": "概念嵌入缓存_BGE.json",
        "backup": "概念数据库_backup_{timestamp}.json"
    }
    
    # 数据库结构版本
    DATABASE_VERSION = "1.2"
    
    # 备份配置
    BACKUP_CONFIG = {
        "auto_backup": True,
        "max_backups": 10,
        "backup_interval": 24 * 60 * 60,  # 24小时
        "compress": True
    }
    
    # 清理配置
    CLEANUP_CONFIG = {
        "max_cache_age": 7 * 24 * 60 * 60,  # 7天
        "max_log_files": 20,
        "cleanup_on_start": True
    }

class ValidationConfig:
    """验证配置类"""
    
    # 文件验证规则
    FILE_VALIDATION = {
        "max_size": 100 * 1024 * 1024,  # 100MB
        "min_size": 10,  # 10字节
        "required_extensions": AppConstants.SUPPORTED_SUBTITLE_FORMATS,
        "encoding": ["utf-8", "gbk", "utf-8-sig"]
    }
    
    # 内容验证规则
    CONTENT_VALIDATION = {
        "min_content_length": 50,
        "max_content_length": 10 * 1024 * 1024,  # 10MB
        "required_separators": ["=== NOTE_SEPARATOR ==="],
        "required_sections": ["YAML:", "CONTENT:"]
    }
    
    # API验证规则
    API_VALIDATION = {
        "timeout": 30,
        "max_retries": 3,
        "required_headers": ["Authorization", "Content-Type"],
        "valid_status_codes": [200, 201, 202]
    }

class LoggingConfig:
    """日志配置类"""
    
    # 日志级别
    LOG_LEVELS = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50
    }
    
    # 日志格式
    LOG_FORMATS = {
        "simple": "%(levelname)s: %(message)s",
        "detailed": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "json": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
    }
    
    # 日志文件配置
    LOG_FILES = {
        "app": "logs/app.log",
        "error": "logs/error.log",
        "api": "logs/api.log",
        "performance": "logs/performance.log"
    }

class SecurityConfig:
    """安全配置类"""
    
    # API密钥验证
    API_KEY_VALIDATION = {
        "min_length": 16,
        "max_length": 128,
        "allowed_chars": r"[a-zA-Z0-9\-_\.]",
        "mask_display": True
    }
    
    # 文件安全
    FILE_SECURITY = {
        "allowed_paths": [".", "./uploads", "./temp"],
        "blocked_extensions": [".exe", ".bat", ".sh", ".ps1"],
        "scan_content": True,
        "max_depth": 5
    }
    
    # 网络安全
    NETWORK_SECURITY = {
        "allowed_domains": ["api.openai.com", "api.anthropic.com", "openrouter.ai", "api.siliconflow.cn"],
        "ssl_verify": True,
        "timeout": 30,
        "max_redirects": 3
    }

class PerformanceConfig:
    """性能配置类"""
    
    # 缓存配置
    CACHE_CONFIG = {
        "enable_memory_cache": True,
        "enable_disk_cache": True,
        "cache_ttl": 3600,  # 1小时
        "max_cache_size": 100 * 1024 * 1024,  # 100MB
        "cleanup_interval": 300  # 5分钟
    }
    
    # 并发配置
    CONCURRENCY_CONFIG = {
        "max_workers": 4,
        "max_concurrent_requests": 10,
        "queue_size": 100,
        "timeout": 60
    }
    
    # 内存配置
    MEMORY_CONFIG = {
        "max_memory_usage": 512 * 1024 * 1024,  # 512MB
        "gc_threshold": 100 * 1024 * 1024,  # 100MB
        "enable_memory_monitoring": True
    }

class ThemeConfig:
    """主题配置类"""
    
    # 预设主题
    THEMES = {
        "light": {
            "name": "浅色主题",
            "primary_color": "#2383e2",
            "background_color": "#ffffff",
            "text_color": "#37352f",
            "card_background": "#f7f6f3"
        },
        "dark": {
            "name": "深色主题", 
            "primary_color": "#4A90E2",
            "background_color": "#1a1a1a",
            "text_color": "#ffffff",
            "card_background": "#2d2d2d"
        },
        "blue": {
            "name": "蓝色主题",
            "primary_color": "#1976d2",
            "background_color": "#f5f5f5",
            "text_color": "#333333",
            "card_background": "#e3f2fd"
        }
    }
    
    # 字体配置
    FONT_CONFIG = {
        "primary_font": "Inter",
        "fallback_fonts": [
            "-apple-system", 
            "BlinkMacSystemFont", 
            "Segoe UI", 
            "PingFang SC", 
            "Hiragino Sans GB", 
            "Microsoft YaHei",
            "Helvetica Neue", 
            "Helvetica", 
            "Arial", 
            "sans-serif"
        ],
        "code_font": "Consolas, Monaco, Courier New, monospace"
    }