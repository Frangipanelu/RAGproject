# 个人知识库 RAG 项目

一个基于 **Streamlit + LangChain + Chroma + SiliconFlow API** 的本地个人知识库项目。

你可以把 Markdown、PDF、DOCX、TXT、HTML、CSV、JSON、YAML 等文档上传到知识库中，系统会自动解析文本、自动分类、提取标签、切分并向量化。之后可以在 AI 对话中基于已上传文档进行检索增强问答。

---

## ✨ 主要功能

- 多工作区管理
- 多级分类 / 分类树
- 多格式文档上传
- 文档内容自动解析
- 文档 MD5 去重
- 自动分类
- 自动标签提取
- 文档列表、搜索、标签筛选
- 文档详情查看
- 基于知识库的 AI 问答
- 多轮对话历史
- 低饱和暖灰风格 UI
- 卡片化上传区、聊天气泡、侧边栏与分类树

---

## 🧱 技术栈

| 类型 | 技术 |
|---|---|
| 前端界面 | Streamlit |
| RAG 编排 | LangChain |
| 向量数据库 | Chroma |
| Embedding | `BAAI/bge-large-zh-v1.5` |
| Chat 模型 | `nex-agi/Nex-N2-Pro` |
| 模型服务 | SiliconFlow OpenAI-Compatible API |
| PDF 解析 | `pypdf` |
| DOCX 解析 | `python-docx` |
| 中文分词 | `jieba` |
| 数据存储 | JSON + Chroma 本地持久化 |

---

## 📁 项目结构

```text
RAGProject/
├─ app_main.py                     # Streamlit 主入口
├─ config_data.py                  # 全局配置：路径、模型、Chroma、API
├─ pyproject.toml                  # Python 项目配置
├─ requirements.txt                # 依赖列表
├─ workspace_db.json               # 工作区与分类数据库
├─ 技术路线.md                     # 早期技术路线文档
├─ 技术路线v2.md                   # 当前项目技术路线文档
├─ core/
│  ├─ answer_saver.py              # 问答沉淀为 Markdown 的工具模块
│  ├─ history.py                   # 对话历史 JSON 文件存储
│  ├─ knowledge_base.py            # 知识库服务：解析、去重、切分、入库
│  ├─ rag.py                       # RAG 问答链
│  ├─ vector_stores.py             # Chroma 检索器封装
│  └─ workspace_manager.py         # 工作区与分类管理
└─ data/
   ├─ uploads/                     # 原始上传文件
   ├─ chroma_db/                   # Chroma 向量数据库
   ├─ chat_history/                # 多轮对话历史
   ├─ knowledge_meta.json          # 文档元数据
   └─ md5.text                     # 文档 MD5 去重记录
```

---

## 🚀 环境要求

推荐使用：

- Python `3.12+`
- Windows 11 / Windows 10
- `uv` 包管理器，推荐安装
- 可访问 SiliconFlow API

---

## 🛠️ 安装依赖

### 方式一：使用当前 `.venv`

当前项目目录下已经存在 `.venv`，并且已经安装过运行所需依赖。

可以直接运行：

```bash
.venv\Scripts\python.exe -m streamlit run app_main.py
```

### 方式二：使用 uv 创建或同步环境

```bash
cd d:\A-pythonProject\RAGProject
uv sync
```

由于当前项目实际还使用了 `jieba`、`python-dotenv`、`protobuf`，如果使用全新虚拟环境，建议额外安装：

```bash
uv pip install jieba python-dotenv protobuf
```

### 方式三：手动创建虚拟环境

```bash
cd d:\A-pythonProject\RAGProject
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
uv pip install -r requirements.txt
uv pip install jieba python-dotenv protobuf
```

---

## ⚙️ 模型与 API 配置

模型配置在：

```text
config_data.py
```

当前使用 SiliconFlow OpenAI-Compatible API：

| 配置项 | 当前值 |
|---|---|
| Base URL | `https://api.siliconflow.cn/v1` |
| Embedding 模型 | `BAAI/bge-large-zh-v1.5` |
| Chat 模型 | `nex-agi/Nex-N2-Pro` |

> 注意：`config_data.py` 中不应长期保存个人 API Key。当前项目为了本地快速运行已经将配置写入文件；如果后续要共享项目，建议把 API Key 迁移到环境变量或 `.env` 文件。

---

## ▶️ 启动项目

在项目根目录执行：

```bash
.venv\Scripts\python.exe -m streamlit run app_main.py --server.address localhost --server.port 8501
```

或使用：

```bash
uv run streamlit run app_main.py --server.address localhost --server.port 8501
```

启动成功后访问：

```text
http://localhost:8501
```

---

## 🧭 操作教程

### 1. 创建第一个工作区

首次进入页面时，左侧边栏会提示：

```text
👋 欢迎！请先创建工作区
```

操作：

1. 输入工作区名称，例如：
   - `技术学习`
   - `工作资料`
   - `读书笔记`
2. 选择一个图标。
3. 点击 `✨ 创建`。

创建后，系统会自动进入该工作区。

---

### 2. 切换工作区

如果已经创建多个工作区，可以在左侧边栏顶部看到：

```text
📚 当前工作区
```

使用下拉框切换即可。

切换工作区后：

- 当前分类会清空。
- 当前文档会清空。
- 文件管理和 AI 对话的检索范围会切换到新工作区。

---

### 3. 创建分类

在左侧边栏：

1. 找到 `📂 知识库`。
2. 点击 `➕ 新建顶级分类`。
3. 输入分类名，例如：
   - `AI`
   - `RAG`
   - `论文`
   - `面试`
   - `项目`
4. 点击 `✨ 创建`。

也可以在已有分类右侧点击 `⋮`，然后选择：

- 新建子分类
- 重命名
- 移动
- 删除

分类支持多级结构，例如：

```text
AI
└─ RAG
   └─ Embedding
```

---

### 4. 上传文档

进入主区域后，切换到：

```text
📁 文件管理
```

在上传区操作：

1. 选择目标分类。
2. 点击上传组件，选择文件。
3. 系统会解析文件内容并展示预览。
4. 系统会自动识别：
   - 自动分类
   - 自动标签
5. 点击：

```text
✅ 确认上传到知识库
```

即可入库。

#### 支持的格式

```text
md / txt / pdf / docx / html / csv / json / yaml / yml
```

#### 上传后会做什么？

```text
解析文本
    → MD5 去重
    → 自动分类
    → 标签提取
    → 文本切分
    → 向量化
    → 存入 Chroma
    → 更新文档元数据
```

如果内容已经存在，系统会提示：

```text
⚠️ 已存在
```

---

### 5. 新建笔记

上传区右侧有：

```text
📝 新建笔记
```

点击后可以输入：

- 标题
- 分类
- Markdown 内容
- 标签

例如：

```markdown
# Python 学习路线

## 基础语法
- 变量
- 函数
- 类
- 模块

## 推荐练习
- 写一个命令行记事本
- 写一个文件批量重命名工具
```

点击：

```text
💾 保存
```

笔记会以 Markdown 文档形式进入知识库。

---

### 6. 搜索与筛选文档

在 `📁 文件管理` 页面顶部有搜索框：

```text
🔍 搜索
```

可以搜索：

- 文件名
- 标签

也可以点击左侧标签云中的标签，例如：

```text
#Python
#RAG
#面试
```

点击后会筛选包含该标签的文档。

排序方式支持：

- 最新
- 最早
- 名称

---

### 7. 查看文档详情

点击文档列表中的文件名，可以查看：

- 文件图标
- 文件名
- 标签
- 上传日期
- 块数量
- 所属分类路径
- 文档内容

如果原始文件可以读取，会显示原始内容；如果原始文件不可读，会尝试从 Chroma 中读取切分后的文本。

---

### 8. 删除文档

文档列表右侧有删除按钮：

```text
🗑
```

点击后会：

1. 从 Chroma 向量库中删除对应向量。
2. 从 `data/knowledge_meta.json` 删除文档元数据。

文档详情页面右上角也有：

```text
🗑 删除
```

---

### 9. 使用 AI 对话

切换到主区域 Tab：

```text
💬 AI 对话
```

可以选择检索范围：

- `🌐 全部文档`
- 某个工作区分类

然后输入问题，例如：

```text
这个项目的整体架构是什么？
```

或：

```text
RAG 文档上传流程是怎样的？
```

系统会：

```text
读取用户问题
    → 读取对话历史
    → 按工作区/分类检索知识库
    → 构建 Prompt
    → 调用 Chat 模型
    → 返回基于知识库的回答
```

如果知识库中没有相关内容，系统会要求模型如实告知，而不是编造答案。

---

### 10. 清空对话

在 AI 对话区域右上角点击：

```text
🗑 清空对话
```

会清空当前聊天界面的消息列表。

---

## 🎨 UI 风格

当前界面采用低饱和暖灰风格：

| 用途 | 颜色 |
|---|---|
| 页面背景 | 暖雾灰 |
| 卡片背景 | 米白 / 白 |
| 边框 | 灰米色 |
| 主按钮 | 低饱和棕色 |
| 正文 | 石墨灰 |
| 次要文字 | 灰褐色 |

设计目标是：

- 简洁
- 柔和
- 长时间阅读不刺眼
- 适合知识库类应用

---

## 🧪 常见问题

### 1. 启动时报 `ModuleNotFoundError`

如果提示缺少某个模块，例如：

```text
ModuleNotFoundError: No module named 'jieba'
```

执行：

```bash
uv pip install jieba
```

如果缺多个依赖，可以执行：

```bash
uv pip install jieba python-dotenv protobuf
```

---

### 2. Streamlit 页面打不开

确认服务是否正常启动：

```bash
.venv\Scripts\python.exe -m streamlit run app_main.py
```

然后访问：

```text
http://localhost:8501
```

如果端口被占用，可以换一个端口：

```bash
.venv\Scripts\python.exe -m streamlit run app_main.py --server.port 8502
```

---

### 3. 上传 PDF 后内容为空

可能原因：

- PDF 是扫描件，没有可提取文本。
- PDF 加密或损坏。
- PDF 字体编码特殊。

建议：

- 使用可复制文字的 PDF。
- 或先转为 Markdown / TXT 后上传。

---

### 4. AI 回答没有引用知识库内容

可能原因：

- 当前工作区没有上传文档。
- 当前分类下没有相关文档。
- 检索范围选择了某个空分类。
- Embedding 或 Chat API 调用失败。

建议：

1. 切换到 `🌐 全部文档`。
2. 确认已经上传文档。
3. 检查控制台是否出现 API 错误。
4. 确认 `config_data.py` 中模型配置正确。

---

### 5. 上传时提示已存在

系统使用内容 MD5 去重。

如果两个文件内容完全相同，即使文件名不同，也会判定为重复。

如果需要重新入库，可以：

1. 删除旧文档。
2. 或修改 `data/md5.text` 中对应 MD5 记录。

一般不建议手动修改 `data/md5.text`，除非你知道自己在做什么。

---

### 6. 分类删除后文档还在吗？

当前分类删除只会删除分类结构。

文档是否删除取决于删除分类时的实现路径。当前 UI 中删除分类会先删除该分类及其子分类下的文档，再删除分类。

因此：

```text
删除分类
    → 删除该分类下文档
    → 删除子分类下文档
    → 删除分类结构
```

请谨慎删除分类。

---

## 🧹 清理缓存

可以清理 Python 编译缓存：

```bash
rm -rf __pycache__
```

Windows PowerShell：

```powershell
Remove-Item -Recurse -Force __pycache__
```

可以清理 uv 缓存：

```bash
uv cache clean
```

不要随意删除以下目录，否则知识库数据会丢失：

```text
data/
workspace_db.json
```

---

## 📝 开发建议

如果你要修改项目，建议优先看这些文件：

| 想改什么 | 看哪里 |
|---|---|
| 页面样式 | `app_main.py` 中的 `<style>` |
| 上传流程 | `app_main.py` 的 `extract_text()` 和 `KnowledgeBaseService.upload_by_str()` |
| 自动分类 | `config_data.py` 的 `AUTO_CATEGORIES` |
| 标签提取 | `core/knowledge_base.py` |
| RAG Prompt | `core/rag.py` |
| 检索过滤 | `core/vector_stores.py` |
| 工作区分类 | `core/workspace_manager.py` |
| 数据存储路径 | `config_data.py` |

---

## 🔒 注意事项

1. `workspace_db.json` 和 `data/knowledge_meta.json` 是核心数据文件，不要随意删除。
2. `data/chroma_db/` 是向量数据库，删除后 AI 问答将无法检索历史文档。
3. `data/uploads/` 是原始文件，删除后文档详情可能无法读取原文。
4. `data/md5.text` 是去重记录，删除后重复文档可能被重新入库。
5. API Key 不建议提交到公开仓库。
6. 当前项目适合个人本地使用，不建议直接作为多人生产系统部署。

---

## 📄 相关文档

- [技术路线 v2](技术路线v2.md)
- [早期技术路线](技术路线.md)
