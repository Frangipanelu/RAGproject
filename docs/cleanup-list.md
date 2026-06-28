# 项目中不用的缓存和测试文档清单

## 📁 Python 缓存文件 (可以安全删除)

### __pycache__ 目录
```
./__pycache__/
├── answer_saver.cpython-39.pyc
├── app_main.cpython-312.pyc
├── config_data.cpython-310.pyc
├── config_data.cpython-312.pyc
├── config_data.cpython-39.pyc
├── file_history_store.cpython-310.pyc
├── file_history_store.cpython-312.pyc
├── file_history_store.cpython-39.pyc
├── knowledge_base.cpython-310.pyc
├── knowledge_base.cpython-312.pyc
├── knowledge_base.cpython-39.pyc
├── rag.cpython-310.pyc
├── rag.cpython-312.pyc
├── rag.cpython-39.pyc
├── vector_stores.cpython-310.pyc
├── vector_stores.cpython-312.pyc
├── vector_stores.cpython-39.pyc
└── workspace_manager.cpython-39.pyc

./core/__pycache__/
├── history.cpython-310.pyc
├── history.cpython-312.pyc
├── knowledge_base.cpython-310.pyc
├── knowledge_base.cpython-312.pyc
├── rag.cpython-310.pyc
├── rag.cpython-312.pyc
├── vector_stores.cpython-310.pyc
├── vector_stores.cpython-312.pyc
├── workspace_manager.cpython-310.pyc
├── workspace_manager.cpython-312.pyc
└── __init__.cpython-310.pyc
    └── __init__.cpython-312.pyc

./utils/__pycache__/
└── __init__.cpython-312.pyc
```

**总计**: 约 37 个 `.pyc` 文件，3 个 `__pycache__` 目录

---

## 🧪 测试文件 (可以选择性保留)

### 当前存在的测试文件
```
./test_core_functionality.py      # 核心功能测试 (3.1 KB) - ✅ 推荐保留
./test_full_functionality.py      # 完整功能测试 (16 KB) - ⚠️ 依赖 API，可能无法运行
./test_workspace.py               # 工作区测试 (3 KB) - ⚠️ 旧测试文件
```

**建议**:
- 保留 `test_core_functionality.py` - 轻量且独立
- 删除 `test_full_functionality.py` - 依赖外部 API，已不再使用
- 删除 `test_workspace.py` - 旧版本测试，已被新测试替代

---

## 📊 数据库和缓存数据 (可以清理)

### Chroma 向量数据库
```
data/chroma_db/
├── chroma.sqlite3              # 向量数据库主文件 (~1.7 MB)
├── chroma.sqlite3-journal      # SQLite 日志文件 (~8.7 KB)
├── 242966e0-b527-442f-aef2-3391e7180b85/  # 集合数据
└── 51843ca2-4ee4-463e-8849-9f70903cb104/ # 集合数据
```

**说明**: 
- 这是 RAG 系统的向量数据库
- 包含所有上传文档的向量化数据
- **不建议删除**，除非你想清空知识库

### 聊天历史记录
```
data/chat_history/
├── test_001                    # 测试聊天记录 (639 B)
└── user_001                    # 用户聊天记录 (27.8 KB)
```

**说明**:
- 保存对话历史
- `test_001` 是测试数据，可以删除
- `user_001` 是真实用户数据，建议保留或手动检查

### MD5 文本文件
```
data/md5.text                   # 空文件 (0 B)
```

**说明**: 用于文件校验，目前是空的，可以删除

---

## 📄 上传的文件 (实际内容)

### Markdown 文件
```
data/uploads/md/
├── 1-3-RAG、微调、续训与智能体选型_1.md     (~40 KB)
├── 1-3-RAG、微调、续训与智能体选型_2.md     (~40 KB)
├── 19-RAG 检索增强生成.md                  (~36 KB)
└── Swarm 育飞项目重构_1.md                 (~4.8 KB)
```

**说明**: 
- 这些都是实际上传的知识库文档
- **不要删除**，这是项目的核心内容

### TXT 文件
```
data/uploads/txt/             # 空目录
```

---

## 📋 计划文档

```
docs/superpowers/plans/
└── 2026-06-27-Refactor-Upload-Chat-Utils-AppMain.md  # 重构计划文档
```

**说明**: 项目重构的计划文档，可以保留作为参考

---

## 🗑️ 建议清理项

### 可以安全删除的项目:

1. **Python 缓存** (释放空间)
   ```bash
   find . -type d -name "__pycache__" ! -path "./.venv/*" -exec rm -rf {} +
   find . -type f -name "*.pyc" ! -path "./.venv/*" -delete
   ```

2. **测试文件** (如果不需要)
   ```bash
   rm -f test_full_functionality.py test_workspace.py
   ```

3. **测试聊天记录**
   ```bash
   rm -f data/chat_history/test_001
   ```

4. **空 MD5 文件**
   ```bash
   rm -f data/md5.text
   ```

### 不建议删除的项目:

1. **Chroma 数据库** (`data/chroma_db/`) - 包含向量数据
2. **上传的文件** (`data/uploads/`) - 包含实际文档内容
3. **用户聊天记录** (`data/chat_history/user_001`) - 真实用户数据
4. **核心测试文件** (`test_core_functionality.py`) - 验证功能完整性

---

## 💾 预计可释放空间

| 项目 | 大小 | 是否安全删除 |
|------|------|-------------|
| Python 缓存 | ~500 KB | ✅ 是 |
| 测试文件 | ~20 KB | ✅ 是 |
| 测试聊天记录 | ~639 B | ✅ 是 |
| MD5 文件 | 0 B | ✅ 是 |
| **总计可释放** | **~520 KB** | |

**注意**: 实际可释放空间较小，主要因为大部分数据（数据库、上传文件）都是有效内容。
