"""
个人知识库服务
- 支持多格式文档上传（md/pdf/docx/txt/html/csv/json/yaml等）
- 自动分类、标签提取、层级管理
- 基于Chroma向量存储
"""
import os
import json
import hashlib
import re
import jieba
import jieba.analyse
import config_data as config
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from datetime import datetime
from pathlib import Path


# ─────────────────────────────────────────────
# 停用词表（中文常见无意义词）
# ─────────────────────────────────────────────

STOP_WORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你",
    "会", "着", "没有", "看", "好", "自己", "这", "那", "吗", "里", "就是", "还", "把", "比", "而且", "但是", "所以", "因为", "如果",
    "可以", "这个", "那个", "我们", "他们", "什么", "怎么", "如何", "通过", "进行", "需要", "应该", "可能", "已经", "一些", "不是",
    "就是", "根据", "对于", "关于", "只是", "还是", "以及", "或者", "其他", "其中", "因此", "由于", "虽然", "但是", "然后", "之后",
    "之前", "现在", "当时", "这里", "那里", "这样", "那样", "什么", "怎么", "为何", "因为", "所以", "于是", "因此", "此外", "另外",
    "首先", "其次", "最后", "总之", "综上", "所述", "例如", "比如", "一般", "通常", "主要", "重要", "必要", "必须", "应该", "一定",
    "一下", "一点", "一直", "一定", "一边", "一起", "一些", "一切", "一样", "一旦", "一方面", "另外", "同时", "同样", "相反",
    "方面", "角度", "观点", "看法", "意见", "建议", "想法", "做法", "方法", "方式", "情况", "状态", "结果", "效果", "影响", "作用",
    "进行", "实现", "完成", "使用", "采用", "应用", "利用", "通过", "对于", "关于", "根据", "按照", "依据", "基于", "出于",
    "有关", "相关", "某种", "某些", "所有", "任何", "每个", "各种", "一样", "一直", "一定", "一次", "一片", "一下", "一切",
    "信息技术", "服务范围", "明确", "服务器", "服务", "建议", "相关"
}


# ─────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────

def get_string_md5(input_str: str, encoding='utf-8') -> str:
    """将字符串转换为MD5"""
    str_bytes = input_str.encode(encoding=encoding)
    md5_obj = hashlib.md5()
    md5_obj.update(str_bytes)
    return md5_obj.hexdigest()


def check_md5(md5_str: str) -> bool:
    """检查MD5是否已存在（去重）"""
    if not os.path.exists(config.md5_path):
        open(config.md5_path, 'w', encoding='utf-8').close()
        return False
    for line in open(config.md5_path, 'r', encoding='utf-8').readlines():
        if line.strip() == md5_str:
            return True
    return False


def save_md5(md5_str: str):
    """记录MD5"""
    with open(config.md5_path, 'a', encoding="utf-8") as f:
        f.write(md5_str + '\n')


# ─────────────────────────────────────────────
# 自动分类 & 标签
# ─────────────────────────────────────────────

def auto_categorize(text: str) -> str:
    """根据关键词匹配自动分类文档"""
    text_lower = text.lower()
    scores = {}
    for category, keywords in config.AUTO_CATEGORIES.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > 0:
            scores[category] = score
    if not scores:
        return config.DEFAULT_CATEGORY
    # 返回得分最高的分类
    return max(scores, key=scores.get)


def extract_tags_with_jieba(text: str, max_tags: int = 8) -> list[str]:
    """使用 jieba 分词 + TF-IDF 提取关键词作为标签"""
    # 自定义词典（业务关键词优先）
    for word in ["人工智能", "机器学习", "深度学习", "大模型", "知识库", "向量数据库",
                 "提示词工程", "简历优化", "职业规划", "JD解析", "面试技巧", "项目管理"]:
        jieba.add_word(word)

    # 使用 jieba.analyse 提取关键词（基于 TF-IDF）
    try:
        keywords = jieba.analyse.extract_tags(
            text,
            topK=max_tags * 2,  # 多取一些，过滤后保留
            withWeight=False,
            allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'vn', 'eng')  # 只保留名词类
        )
    except Exception:
        # 降级方案：仅分词
        words = jieba.lcut(text)
        keywords = [w for w in words if 2 <= len(w) <= 6]

    # 过滤停用词和过短/过长的词
    tags = []
    for kw in keywords:
        kw = kw.strip()
        if not kw or len(kw) < 2 or len(kw) > 10:
            continue
        if kw in STOP_WORDS:
            continue
        # 过滤纯数字、纯英文
        if kw.isdigit() or (kw.isalpha() and not any('\u4e00' <= c <= '\u9fa5' for c in kw) and len(kw) < 3):
            continue
        if kw not in tags:
            tags.append(kw)
        if len(tags) >= max_tags:
            break

    return tags


def extract_tags_with_llm(text: str, max_tags: int = 8) -> list[str]:
    """使用 LLM 智能提取标签（最准确）"""
    # 截取前2000字避免token过多
    text_sample = text[:2000]

    prompt = f"""你是专业的文本标签提取助手。请从以下文本中提取最能代表其核心主题的 {max_tags} 个标签。

要求：
1. 标签应该是具体的名词或名词短语（如"机器学习"、"项目管理"、"Python入门"）
2. 不要提取过于宽泛的词（如"信息技术"、"应用"）
3. 标签长度2-8个字
4. 按重要性从高到低排序
5. 用中文顿号"、"分隔输出，不要其他内容

文本：
{text_sample}

标签："""

    try:
        llm = ChatOpenAI(
            model=config.chat_model_name,
            openai_api_key=config.SILICONFLOW_API_KEY,
            openai_api_base=config.SILICONFLOW_BASE_URL,
            temperature=0.3,  # 低温度保证稳定性
        )
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        # 解析：支持顿号、逗号、换行分隔
        content = content.strip()
        for sep in ['\n', '、', '，', ',', '；', ';']:
            if sep in content:
                tags = [t.strip() for t in content.split(sep) if t.strip()]
                break
        else:
            tags = [content]

        # 清理和验证
        result = []
        for t in tags:
            t = t.strip().strip('"\'""''【】[]()《》')
            # 移除编号前缀
            t = re.sub(r'^\d+[\.、]\s*', '', t)
            if 2 <= len(t) <= 10 and t not in STOP_WORDS and t not in result:
                result.append(t)
            if len(result) >= max_tags:
                break
        return result
    except Exception as e:
        print(f"[LLM标签提取失败] {e}")
        return []


def extract_tags(text: str, max_tags: int = 8, use_llm: bool = True) -> list[str]:
    """提取标签：优先 LLM，失败时降级到 jieba"""
    if not text or not text.strip():
        return []

    # 优先使用 LLM
    if use_llm:
        llm_tags = extract_tags_with_llm(text, max_tags)
        if llm_tags:
            return llm_tags

    # 降级方案：jieba
    return extract_tags_with_jieba(text, max_tags)


def detect_hierarchy(text: str) -> dict:
    """检测文档层级结构（基于标题标记）"""
    hierarchy = {"level": 0, "parent": None, "children": []}

    # 检测Markdown标题层级
    headings = re.findall(r'^(#{1,6})\s+(.+)$', text, re.MULTILINE)
    if headings:
        min_level = min(len(h[0]) for h in headings)
        hierarchy["level"] = min_level
        hierarchy["headings"] = [h[1].strip() for h in headings[:5]]  # 取前5个标题

    # 检测是否包含子主题关键词
    sub_indicators = ['子主题', '子章节', '附录', '补充', '扩展', '详细', '深入']
    for indicator in sub_indicators:
        if indicator in text:
            hierarchy["has_subtopics"] = True
            break

    return hierarchy


# ─────────────────────────────────────────────
# 元数据管理
# ─────────────────────────────────────────────

def load_meta_db() -> dict:
    """加载元数据数据库"""
    if not os.path.exists(config.meta_db_path):
        return {"documents": {}}
    with open(config.meta_db_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_meta_db(meta_db: dict):
    """保存元数据数据库"""
    with open(config.meta_db_path, 'w', encoding='utf-8') as f:
        json.dump(meta_db, f, ensure_ascii=False, indent=2)


def list_documents(
    workspace_id: str = None,
    category_id: str = None,
    category: str = None,
    tag: str = None,
) -> list[dict]:
    """列出文档，支持按工作区/分类/标签过滤"""
    meta_db = load_meta_db()
    docs = list(meta_db.get("documents", {}).values())

    if workspace_id:
        docs = [d for d in docs if d.get("workspace_id") == workspace_id]
    if category_id:
        docs = [d for d in docs if d.get("category_id") == category_id]
    if category:
        docs = [d for d in docs if d.get("category") == category]
    if tag:
        docs = [d for d in docs if tag in d.get("tags", [])]

    # 按上传时间倒序
    docs.sort(key=lambda x: x.get("upload_time", ""), reverse=True)
    return docs


def get_categories(workspace_id: str = None) -> dict[str, int]:
    """获取所有分类及其文档数量"""
    meta_db = load_meta_db()
    categories = {}
    for doc in meta_db.get("documents", {}).values():
        if workspace_id and doc.get("workspace_id") != workspace_id:
            continue
        cat = doc.get("category", config.DEFAULT_CATEGORY)
        categories[cat] = categories.get(cat, 0) + 1
    return categories


def get_all_tags(workspace_id: str = None) -> dict[str, int]:
    """获取所有标签及其出现次数"""
    meta_db = load_meta_db()
    tags = {}
    for doc in meta_db.get("documents", {}).values():
        if workspace_id and doc.get("workspace_id") != workspace_id:
            continue
        for tag in doc.get("tags", []):
            tags[tag] = tags.get(tag, 0) + 1
    # 按频率排序
    return dict(sorted(tags.items(), key=lambda x: x[1], reverse=True))


def delete_document(doc_id: str) -> bool:
    """删除文档"""
    meta_db = load_meta_db()
    if doc_id not in meta_db.get("documents", {}):
        return False

    doc = meta_db["documents"][doc_id]

    # 从Chroma中删除（通过metadata过滤）
    try:
        chroma = Chroma(
            collection_name=config.collection_name,
            embedding_function=config.get_embeddings(),
            persist_directory=config.persist_directory,
        )
        chroma._collection.delete(where={"doc_id": doc_id})
    except Exception:
        pass

    # 从元数据中删除
    del meta_db["documents"][doc_id]
    save_meta_db(meta_db)
    return True


# ─────────────────────────────────────────────
# 知识库服务类
# ─────────────────────────────────────────────

class KnowledgeBaseService:
    def __init__(self):
        os.makedirs(config.persist_directory, exist_ok=True)

        self.chroma = Chroma(
            collection_name=config.collection_name,
            embedding_function=config.get_embeddings(),
            persist_directory=config.persist_directory,
        )

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            separators=config.separators,
            length_function=len,
        )

    def upload_by_str(
        self,
        data: str,
        filename: str,
        workspace_id: str = None,
        category_id: str = None,
        category: str = None,
        tags: list[str] = None,
        source_type: str = "upload",  # upload / answer / note
    ) -> dict:
        """将文本存入知识库，返回上传结果"""
        md5_hex = get_string_md5(data)

        if check_md5(md5_hex):
            return {"status": "skipped", "message": "内容已存在知识库中"}

        # 自动分类
        if not category:
            category = auto_categorize(data)

        # 自动提取标签
        if not tags:
            tags = extract_tags(data)

        # 检测层级
        hierarchy = detect_hierarchy(data)

        # 解析分类路径
        category_path = ""
        if category_id:
            try:
                from workspace_manager import get_category_path
                category_path = get_category_path(category_id) or ""
            except Exception:
                category_path = ""

        # 文本分割
        if len(data) > config.max_split_char_number:
            chunks = self.splitter.split_text(data)
        else:
            chunks = [data]

        # 二次保护：超长 chunk 强制切分（BGE模型最大512 tokens）
        safe_chunks = []
        for chunk in chunks:
            if len(chunk) <= config.max_embedding_chars:
                safe_chunks.append(chunk)
            else:
                # 强制按 max_embedding_chars 切分
                step = config.max_embedding_chars - config.chunk_overlap
                for i in range(0, len(chunk), step):
                    safe_chunks.append(chunk[i:i + config.max_embedding_chars])
        chunks = safe_chunks

        doc_id = f"doc_{md5_hex[:12]}"

        metadata = {
            "doc_id": doc_id,
            "source": filename,
            "workspace_id": workspace_id or "",
            "category_id": category_id or "",
            "category_path": category_path,
            "category": category,
            "tags": json.dumps(tags, ensure_ascii=False),
            "level": hierarchy.get("level", 0),
            "headings": json.dumps(hierarchy.get("headings", []), ensure_ascii=False),
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "chunk_count": len(chunks),
            "source_type": source_type,
        }

        # 存入Chroma
        self.chroma.add_texts(
            chunks,
            metadatas=[metadata for _ in chunks],
            ids=[f"{doc_id}_chunk_{i}" for i in range(len(chunks))],
        )

        # 记录MD5
        save_md5(md5_hex)

        # 更新元数据数据库
        meta_db = load_meta_db()
        meta_db["documents"][doc_id] = {
            "doc_id": doc_id,
            "filename": filename,
            "workspace_id": workspace_id or "",
            "category_id": category_id or "",
            "category_path": category_path,
            "category": category,
            "tags": tags,
            "hierarchy": hierarchy,
            "upload_time": metadata["create_time"],
            "chunk_count": len(chunks),
            "md5": md5_hex,
            "source_type": source_type,
        }
        save_meta_db(meta_db)

        return {
            "status": "success",
            "message": f"成功载入知识库",
            "doc_id": doc_id,
            "workspace_id": workspace_id,
            "category_id": category_id,
            "category_path": category_path,
            "category": category,
            "tags": tags,
            "chunks": len(chunks),
        }

    def get_retriever(self, category: str = None, tags: list[str] = None):
        """获取带过滤条件的检索器"""
        filter_dict = {}
        if category:
            filter_dict["category"] = category
        # Chroma的metadata filter不支持list包含查询，这里用category过滤
        if filter_dict:
            return self.chroma.as_retriever(
                search_kwargs={"k": config.retrieve_top_k, "filter": filter_dict}
            )
        return self.chroma.as_retriever(search_kwargs={"k": config.retrieve_top_k})


if __name__ == '__main__':
    service = KnowledgeBaseService()
    result = service.upload_by_str("Python是一门编程语言，用于Web开发和数据分析", "test.md")
    print(result)
    print("分类统计:", get_categories())
    print("标签统计:", get_all_tags())