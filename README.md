# 法考字幕转 Obsidian 笔记处理器 (FAKC)

🎓 **F**a**k**ao **C**ontent - 一个将法考课程字幕智能转换为结构化 Obsidian 笔记的工具，支持概念关系自动建立和知识图谱构建。

## 🎯 项目背景

法考备考过程中，学习者通常面临以下挑战：

- **海量视频课程**: 需要从数百小时的课程中提取关键知识点
- **知识点分散**: 同一概念可能在不同章节中反复出现，难以形成体系
- **概念关系复杂**: 法律概念间存在大量的逻辑关联，传统笔记难以表现
- **错题归因困难**: 做错题后难以快速定位到具体的知识薄弱环节

## 🚀 解决方案

FAKC 通过 AI 技术自动化处理法考学习过程中的核心痛点：

### 📚 从视频到知识图谱

1. **视频字幕提取** → 使用字幕下载工具获取课程内容
2. **AI 智能分析** → 自动识别每个独立的法律概念和知识点
3. **结构化笔记** → 将概念转换为标准化的 Obsidian 笔记格式
4. **关系网络构建** → 自动建立概念间的双链引用关系

### 🎨 三大核心目标

**🕸️ 目标一：构建法考知识图谱**

- 每个法律概念成为图谱中的一个节点
- 通过双链系统将相关概念连接成可视化网络
- 支持从任意概念出发探索整个知识体系

**📖 目标二：建立法考 Wiki 百科**

- 每个概念都是独立完整的"百科条目"
- 包含定义、特征、应用、案例等全面信息
- 支持概念间的无缝跳转和关联阅读

**🎯 目标三：精准错题定位系统**

- 超细化的概念拆分确保每个考点都有对应笔记
- 错题可以精确关联到具体知识点
- 支持针对性的知识薄弱点强化

## ✨ 核心功能

### 🤖 AI 驱动的笔记生成

- **智能内容分析**: 使用先进的 AI 模型分析字幕内容，自动识别独立知识点
- **超细化拆分**: 将每个法考概念拆分为独立的笔记，构建详细的知识节点
- **概念关系建立**: 自动识别概念间的关联关系，生成双链引用

### 📚 知识体系构建

- **法考 Wiki 百科**: 每个概念都是独立的"百科条目"，支持深度探索
- **可视化知识图谱**: 通过 Obsidian 的图谱功能查看概念间的关系网络
- **错题定位系统**: 便于将错题精确关联到具体知识点

### 🔗 智能概念增强

- **传统 AI 增强**: 基于全量概念库的 AI 分析
- **BGE 混合检索**: 使用 SiliconFlow 的 BGE-M3 模型进行 embedding 召回 + reranker 精排
- **时间戳链接化**: 自动将笔记中的时间戳转换为视频链接

## 🎬 字幕获取建议

### 推荐工具：Tampermonkey 插件

为了获取高质量的字幕文件，推荐使用以下方案：

1. **安装 Tampermonkey**: 在浏览器中安装 Tampermonkey 扩展
2. **字幕下载脚本**: 搜索并安装支持你所使用学习平台的字幕下载脚本
3. **格式选择**: **强烈推荐下载 LRC 格式**字幕

### 为什么推荐 LRC 格式？

- **📉 减少 Token 消耗**: LRC 格式相比 SRT 格式更简洁，能显著降低 AI 处理的 Token 使用量
- **⚡ 提高处理速度**: 更少的文本内容意味着更快的 AI 分析速度
- **💰 降低成本**: 减少 API 调用费用，特别是处理长视频时效果明显
- **✅ 完全兼容**: 系统完全支持 LRC 格式的时间戳和内容解析

### 支持的字幕格式

- ✅ **LRC** (推荐) - 简洁的歌词格式，Token 消耗最少
- ✅ **SRT** - 标准字幕格式，广泛支持
- ✅ **TXT** - 纯文本格式，适合已整理的内容

## 🚀 快速开始

### 1. 环境要求

- Python 3.11.9+
- 有效的 OpenAI API 或兼容 API 密钥
- (可选) SiliconFlow API 密钥 (用于 BGE 增强功能)

### 2. 安装

```bash
# 克隆项目
git clone https://github.com/KawaroX/fakc
cd fakc

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置

复制 `.env.example` 为 `.env` 并配置必要参数：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# AI处理配置
SUBTITLE_PROCESSING_API_KEY=your_api_key_here
SUBTITLE_PROCESSING_BASE_URL=https://openrouter.ai/api/v1
SUBTITLE_PROCESSING_MODEL=openrouter/cypher-alpha:free

CONCEPT_ENHANCEMENT_API_KEY=your_api_key_here
CONCEPT_ENHANCEMENT_BASE_URL=https://openrouter.ai/api/v1
CONCEPT_ENHANCEMENT_MODEL=openrouter/cypher-alpha:free

# BGE增强功能 (可选)
SILICONFLOW_API_KEY=your_siliconflow_api_key

# Obsidian保存路径
OBSIDIAN_VAULT_PATH=/Path/to/your/obsidian/vault
```

### 🤖 推荐 AI 模型

为了获得最佳的处理效果，强烈推荐使用以下高性能 AI 模型：

#### 🥇 首选推荐

- **DeepSeek-R1** - 性价比极高，中文理解能力强，特别适合法考内容分析
- **Claude 4 (Sonnet/Opus)** - 逻辑推理能力出色，概念关系建立准确
- **GPT-4.1** - 稳定可靠，对法律术语理解深入

#### 💡 模型选择建议

- **字幕处理**: 推荐使用 DeepSeek-R1 或 Claude 4，能够精确识别法律概念
- **概念增强**: 推荐使用 Claude 4 或 GPT-4.1，逻辑推理更严谨
- **成本考虑**: DeepSeek-R1 提供了极佳的性价比，是预算有限时的最佳选择

#### 🔧 API 配置示例

**使用 DeepSeek-R1:**

```env
SUBTITLE_PROCESSING_BASE_URL=https://api.deepseek.com/v1
SUBTITLE_PROCESSING_MODEL=deepseek-reasoner
```

**使用 Claude 4:**

```env
SUBTITLE_PROCESSING_BASE_URL=https://api.anthropic.com/v1
SUBTITLE_PROCESSING_MODEL=claude-4-sonnet-20241022
```

**使用 OpenRouter 访问多模型:**

```env
SUBTITLE_PROCESSING_BASE_URL=https://openrouter.ai/api/v1
SUBTITLE_PROCESSING_MODEL=deepseek/deepseek-r1
# 或者
SUBTITLE_PROCESSING_MODEL=anthropic/claude-4-sonnet
```

> ⚠️ **注意**: 不同 AI 模型的能力和成本差异很大，选择合适的模型对最终效果至关重要。免费或低成本模型可能无法达到理想的概念识别和关系建立效果。

### 4. 修改配置文件

编辑 `config.py` 中的 `OBSIDIAN_VAULT_PATH`：

```python
OBSIDIAN_VAULT_PATH = "/你的/Obsidian/文件夹/路径"
```

## 📖 使用方式

### 方式一：Streamlit Web 界面 (推荐)

```bash
streamlit run app.py
```

访问 `http://localhost:8501` 使用 Web 界面，支持：

- 🎬 上传字幕文件处理
- 📝 直接输入 AI 格式文本
- 🔗 增强现有笔记关系
- ⏰ 时间戳链接化处理
- 📊 查看概念数据库

### 方式二：命令行界面

```bash
python main.py
```

通过菜单选择功能：

1. 处理新字幕文件
2. 增强现有笔记关系
3. 时间戳链接化处理
4. 显示科目文件夹映射
5. 查看概念数据库

## 📂 项目结构

```
fakc/
├── app.py                      # Streamlit Web应用
├── main.py                     # 命令行主程序
├── config.py                   # 配置管理
├── ai_processor.py             # AI处理核心
├── concept_manager.py          # 概念数据库管理
├── note_generator.py           # 笔记文件生成
├── timestamp_linker.py         # 时间戳链接化
├── siliconflow_concept_enhancer.py  # BGE增强器
├── requirements.txt            # 项目依赖
└── .env.example               # 配置模板
```

## 🎯 支持的科目

系统预配置了 14 个法考科目，自动创建对应文件夹：

- 01 民法
- 02 刑法
- 03 行政法
- 04 民事诉讼法
- 05 刑事诉讼法
- 06 行政诉讼法
- 07 商法
- 08 经济法
- 09 国际法
- 10 国际私法
- 11 国际经济法
- 12 环境资源法
- 13 劳动社会保障法
- 14 司法制度和法律职业道德

## 🔧 详细功能说明

### 字幕文件处理

支持 `.srt`、`.lrc`、`.txt` 格式的字幕文件：

1. **获取字幕**: 使用 Tampermonkey 插件下载 LRC 格式字幕(推荐)
2. **上传字幕**: 选择字幕文件和对应科目
3. **AI 分析**: 自动识别知识点并拆分为独立概念
4. **生成笔记**: 创建标准化的 Obsidian 笔记文件
5. **建立关联**: 自动生成概念间的双链引用

### 概念关系增强

#### 传统增强模式

- 将所有已有概念发送给 AI 分析
- 适合概念数量较少的情况
- 提供全面的概念关系建议

#### BGE 混合检索模式 🔥 **推荐**

- **Embedding 召回**: 使用 BGE-M3 模型计算语义相似度
- **Reranker 精排**: 使用 BGE-reranker-v2-m3 精确排序
- **智能过滤**: 只向 AI 发送最相关的概念，提高准确性

参数配置：

- `embedding_top_k`: embedding 召回数量 (建议 50-200)
- `rerank_top_k`: reranker 精排数量 (建议 10-20)
- `rerank_threshold`: 分数阈值 (建议 0.2-0.5)

### 时间戳链接化

自动将笔记中的时间戳转换为可点击的视频链接：

- 支持格式：`[MM:SS]`、`[HH:MM:SS]`、`[MM:SS.ms]`
- 支持平台：YouTube、Bilibili、通用视频平台
- 转换示例：`[12:34]` → `⏰ [12:34](视频链接&t=754)`

## 📋 生成的笔记格式

每个笔记包含以下标准结构：

```markdown
---
title: "【民法】善意取得"
aliases: ["善意取得", "善意第三人"]
tags: ["民法", "物权法", "善意取得", "高"]
source: "法考精讲课程"
course_url: "https://www.bilibili.com/video/BV1xxx"
time_range: "12:30-15:45"
subject: "民法"
exam_importance: "高"
created: "2024-01-15"
---

# 【民法】善意取得

## 核心定义

⏰ [12:30.15](链接)
善意取得是指无权处分人将其占有的他人动产或不动产...

## 构成要件

⏰ [13:45.30](链接)

1. 受让人须为善意
2. 以合理价格转让
3. 转让的财产依法律规定应当登记的已经登记...

## 记忆要点

🔮 善意+合理价格+已登记 — 善意取得三要素
📱 买二手车场景 — 典型善意取得情形  
💡 恶意不得善意取得 — 明知非权利人

## 相关概念

- [[【民法】物权变动|物权变动]]
- [[【民法】无权处分|无权处分]]
- [[【民法】占有|占有]]

---

_视频时间段: [12:30]-[15:45]_
```

## 💾 数据管理

### 概念数据库

系统自动维护两个数据库文件：

- `概念数据库.md`: 人类可读的概念索引
- `概念数据库.json`: 程序使用的结构化数据

### BGE 嵌入缓存

使用 BGE 功能时会生成：

- `概念嵌入缓存_BGE.json`: 缓存概念的嵌入向量，避免重复计算

## ⚠️ 注意事项

### API 配置

- 确保 API 密钥有效且有足够余额
- SiliconFlow 密钥是 BGE 功能的必需项
- **强烈推荐使用 DeepSeek-R1、Claude 4 或 GPT-4.1 等高性能模型**
- 免费模型可能无法达到理想的概念识别效果

### 路径配置

- Obsidian 路径必须存在且有写入权限
- 建议使用绝对路径避免路径问题

### 性能优化

- BGE 增强模式首次使用需要构建嵌入向量，耗时较长
- 建议批量处理笔记以提高效率
- 概念数量过多时推荐使用 BGE 模式

## 🔍 故障排除

### 常见问题

**Q: AI 处理效果不佳？**

- 检查是否使用了推荐的高性能模型(DeepSeek-R1/Claude 4/GPT-4.1)
- 免费或低成本模型可能无法准确识别法律概念
- 考虑调整 AI 提示词或增加上下文信息
- 尝试使用不同模型进行对比测试

**Q: 如何获取高质量字幕？**

- 推荐使用 Tampermonkey 字幕下载插件
- 优先选择 LRC 格式以减少 Token 消耗
- 确保字幕内容完整且时间戳准确

**Q: 无法生成笔记**

- 检查 API 密钥是否正确配置
- 确认 Obsidian 路径存在且可写
- 查看控制台错误信息

**Q: BGE 增强失败**

- 确认 SiliconFlow API 密钥正确
- 检查网络连接
- 尝试降低批处理大小

**Q: 时间戳链接无效**

- 确认笔记的 YAML 中包含`course_url`字段
- 检查视频链接格式是否正确

**Q: 概念关系不准确**

- 尝试调整 BGE 参数（top_k, threshold）
- 检查概念数据库是否最新
- 考虑手动调整概念关系

### 日志查看

程序运行时会输出详细日志，包含：

- 处理进度信息
- 错误和警告信息
- API 调用结果
- 文件操作状态

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进项目！

## 📄 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

---

## 💡 使用建议

- **模型选择**: 优先使用 DeepSeek-R1、Claude 4 或 GPT-4.1 等高性能模型，确保最佳处理效果
- **字幕获取**: 使用 Tampermonkey 插件下载 LRC 格式字幕，既节省成本又提高效率
- **批量处理**: 建议按章节批量处理字幕文件，提高概念关联的准确性
- **定期增强**: 随着笔记增多，定期运行 BGE 增强功能优化概念关系网络
- **概念检查**: 生成笔记后及时检查概念关系，手动调整不准确的链接

**快速开始**: `streamlit run app.py` 然后访问 http://localhost:8501

**技术支持**: 如有问题请查看控制台输出或提交 Issue
