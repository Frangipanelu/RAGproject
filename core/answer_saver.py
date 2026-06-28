"""
回答整理入库
- 将 LLM 回答 + 用户问题 + 引用来源整理成 Markdown 文档
- 让用户选择工作区/分类保存
"""
import os
import json
from datetime import datetime
from typing import Optional


def build_answer_document(
    question: str,
    answer: str,
    sources: list[dict] = None,
    context_window: list[dict] = None,
) -> str:
    """
    将问答整理为 Markdown 文档
    :param question: 用户问题
    :param answer: LLM 回答
    :param sources: 引用的来源 [{"filename": ..., "snippet": ...}, ...]
    :param context_window: 对话上下文（多轮对话）
    :return: Markdown 文本
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    parts = []

    # 标题
    parts.append(f"# {question.strip()[:80]}")
    parts.append("")
    parts.append(f"> 保存时间：{now}  ")
    parts.append(f"> 来源：基于知识库对话沉淀  ")
    parts.append("")

    # 问题描述
    parts.append("## ❓ 问题")
    parts.append("")
    parts.append(question.strip())
    parts.append("")

    # 多轮上下文
    if context_window and len(context_window) > 1:
        parts.append("## 💬 对话上下文")
        parts.append("")
        for msg in context_window[:-1]:  # 排除最后一条（本轮问答）
            role = "🙋 用户" if msg.get("role") == "user" else "🤖 助手"
            content = msg.get("content", "").strip()
            if content:
                parts.append(f"**{role}**：{content}")
                parts.append("")

    # 答案
    parts.append("## ✅ 回答")
    parts.append("")
    parts.append(answer.strip())
    parts.append("")

    # 引用来源
    if sources:
        parts.append("## 📚 参考资料")
        parts.append("")
        for i, src in enumerate(sources, 1):
            filename = src.get("filename", "未知")
            snippet = src.get("snippet", "").strip()
            parts.append(f"**[{i}] {filename}**")
            if snippet:
                # 截断到 200 字
                if len(snippet) > 200:
                    snippet = snippet[:200] + "..."
                parts.append(f"> {snippet}")
            parts.append("")

    return "\n".join(parts)


def save_answer_to_kb(
    kb_service,
    question: str,
    answer: str,
    workspace_id: Optional[str] = None,
    category_id: Optional[str] = None,
    title: str = None,
    sources: list[dict] = None,
    context_window: list[dict] = None,
) -> dict:
    """
    将问答整理并入库
    :return: 上传结果
    """
    # 生成标题（取问题前 30 字）
    if not title:
        title = question.strip().split("\n")[0][:30]
        if not title:
            title = f"问答_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # 整理文档
    doc_content = build_answer_document(question, answer, sources, context_window)

    # 生成文件名
    safe_title = "".join(c for c in title if c.isalnum() or c in " _-中文")[:30]
    if not safe_title:
        safe_title = f"answer_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    filename = f"{safe_title}.md"

    # 入库
    return kb_service.upload_by_str(
        data=doc_content,
        filename=filename,
        workspace_id=workspace_id,
        category_id=category_id,
        source_type="answer",
    )


if __name__ == "__main__":
    # 测试
    doc = build_answer_document(
        question="Python 如何入门？",
        answer="Python 入门建议：1. 学习基础语法；2. 练手小项目；3. 阅读优秀代码。",
        sources=[
            {"filename": "Python教程.md", "snippet": "Python 是一门解释型语言..."},
        ],
        context_window=[
            {"role": "user", "content": "我想学编程"},
            {"role": "assistant", "content": "推荐 Python"},
            {"role": "user", "content": "Python 如何入门？"},
        ],
    )
    print(doc)
