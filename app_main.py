"""
个人知识库 - 简洁版 v3
Streamlit 原生组件 + 简洁大方 + 卡片化布局
优化：粘性 Hero 使用 left:0 + width:100% 替代负边距；主题自适应 CSS 变量
"""

from typing import Optional
import json
import os
import sys
import time
from io import BytesIO
from pathlib import Path

# 将项目根目录加入 sys.path，使 core 包内模块能绝对导入 config_data
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

import config_data as config
from core.knowledge_base import (
    KnowledgeBaseService, list_documents, get_all_tags,
    delete_document, auto_categorize, extract_tags, load_meta_db,
)
from core.rag import RagService
from core.workspace_manager import (
    create_workspace, list_workspaces, get_workspace, delete_workspace,
    create_category, list_categories, get_category, get_category_tree,
    delete_category, get_all_descendants, update_category, move_category,
)
from utils.logic.utils import extract_text, save_upload

# 允许的文件扩展类型
ALLOWED_EXTS = ["md", "txt", "pdf", "docx", "html", "csv", "json", "yaml", "yml"]

# ════════════════════════════════════════════
# 主题样式
# ════════════════════════════════════════════
THEME_CSS = Path(__file__).parent / "assets" / "styles" / "talknexus.css"


def inject_css(css_path: Path) -> None:
    """将外部 CSS 注入 Streamlit 页面。"""
    if not css_path.exists():
        st.warning(f"主题样式文件不存在：{css_path}")
        return
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


# ════════════════════════════════════════════
# 工具函数（已迁移至 utils/logic/utils.py）
# extract_text, save_upload → utils.logic.utils
# ════════════════════════════════════════════



def get_kb():
    if "kb_service" not in st.session_state or st.session_state["kb_service"] is None:
        st.session_state["kb_service"] = KnowledgeBaseService()
    return st.session_state["kb_service"]


def get_doc_content(doc_id: str) -> str:
    meta = load_meta_db().get("documents", {}).get(doc_id)
    if not meta:
        return ""
    try:
        return Path(meta["filename"]).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        try:
            kb = get_kb()
            results = kb.chroma.get(where={"doc_id": doc_id})
            return "\n\n".join(results.get("documents", []))
        except Exception:
            return ""


def get_file_icon(ext: str) -> str:
    return {"md":"📝","txt":"📄","pdf":"📕","docx":"📘","html":"🌐","csv":"📊","json":"🔧","yaml":"⚙️"}.get(ext, "📄")


# ════════════════════════════════════════════
# 侧边栏分类树（Notion 风格）
# ════════════════════════════════════════════

def render_tree_node(node: dict, level: int = 0, current_cat: Optional[str] = None, current_ws: str = ""):
    """递归渲染分类树节点。"""
    cat_id = node["id"]
    children = node.get("children", [])
    has_children = len(children) > 0
    is_active = current_cat == cat_id
    indent = "　" * level  # 全角空格缩进

    # 展开状态
    if "tree_expanded" not in st.session_state:
        st.session_state["tree_expanded"] = set()
    if cat_id not in st.session_state["tree_expanded"] and level == 0:
        st.session_state["tree_expanded"].add(cat_id)
    expanded = cat_id in st.session_state["tree_expanded"]

    # 节点布局：▾/▸  |  名称按钮  |  ⋮ 菜单
    cols = st.columns([0.5, 4.5, 0.8])

    with cols[0]:
        if has_children:
            toggle = "▾" if expanded else "▸"
            if st.button(
                toggle, key=f"tog_{cat_id}",
                help="展开/折叠",
            ):
                if expanded:
                    st.session_state["tree_expanded"].discard(cat_id)
                else:
                    st.session_state["tree_expanded"].add(cat_id)
                st.rerun()
        else:
            st.markdown(
                f'<div style="text-align:center;color:#b8b0a0;">·</div>',
                unsafe_allow_html=True,
            )

    with cols[1]:
        icon = "📂" if has_children else "📁"
        active_style = "🌳" if is_active else icon
        label = f"{indent}{active_style} {node['name']}"
        if st.button(
            label,
            key=f"sel_{cat_id}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state["current_cat"] = cat_id
            st.session_state["current_doc"] = None
            st.rerun()

    with cols[2]:
        # 模拟右键菜单 - 使用 st.popover 原生组件
        with st.popover("⋮", help="操作菜单"):
            st.markdown(
                f'<div style="font-size:0.85rem;color:#6a6a6a;margin-bottom:0.4rem;">'
                f'📂 <b>{node["name"]}</b></div>',
                unsafe_allow_html=True,
            )
            st.divider()

            # ➕ 新建子分类
            with st.form(f"add_child_{cat_id}", clear_on_submit=True):
                new_name = st.text_input("子分类名", key=f"newc_{cat_id}", placeholder="输入名称")
                if st.form_submit_button("➕ 新建子分类", use_container_width=True):
                    if new_name.strip():
                        create_category(new_name.strip(), current_ws, cat_id)
                        st.session_state["tree_expanded"].add(cat_id)
                        st.toast("✅ 已创建", icon="🎉")
                        time.sleep(0.3)
                        st.rerun()

            # ✏️ 重命名
            with st.form(f"rename_{cat_id}", clear_on_submit=True):
                rn = st.text_input("新名称", value=node["name"], key=f"rn_{cat_id}")
                if st.form_submit_button("✏️ 重命名", use_container_width=True):
                    if rn.strip() and rn.strip() != node["name"]:
                        update_category(cat_id, rn.strip())
                        st.toast("✅ 已重命名", icon="✏️")
                        time.sleep(0.3)
                        st.rerun()

            # ⤴️ 移动到
            all_cats = list_categories(current_ws)
            move_opts = [("📁 根目录", None)] + [
                (f"📂 {c['path']}", c["id"]) for c in all_cats
                if c["id"] != cat_id and c["id"] not in [cat_id] + get_all_descendants(cat_id)
            ]
            if move_opts:
                with st.form(f"move_{cat_id}", clear_on_submit=True):
                    sel = st.selectbox(
                        "移动到", [x[0] for x in move_opts],
                        key=f"mvsel_{cat_id}", label_visibility="collapsed",
                    )
                    if st.form_submit_button("⤴️ 移动", use_container_width=True):
                        target = dict(move_opts)[sel]
                        if move_category(cat_id, target):
                            st.toast("✅ 已移动", icon="⤴️")
                            time.sleep(0.3)
                            st.rerun()

            st.divider()

            # 🗑 删除
            with st.form(f"del_{cat_id}"):
                st.caption("⚠️ 将级联删除子分类和文档")
                confirm = st.checkbox("确认删除", key=f"cf_{cat_id}")
                if st.form_submit_button("🗑 删除", type="primary", use_container_width=True):
                    if confirm:
                        for d in list_documents(category_id=cat_id):
                            delete_document(d["doc_id"])
                        for child in get_all_descendants(cat_id):
                            for d in list_documents(category_id=child):
                                delete_document(d["doc_id"])
                        delete_category(cat_id)
                        if current_cat == cat_id:
                            st.session_state["current_cat"] = None
                        st.toast("已删除", icon="🗑")
                        time.sleep(0.3)
                        st.rerun()

    # 递归子节点
    if expanded:
        for child in children:
            render_tree_node(child, level + 1, current_cat, current_ws)


# ════════════════════════════════════════════
# 页面配置
# ════════════════════════════════════════════

st.set_page_config(
    page_title="个人知识库",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css(THEME_CSS)

# 初始化 session
for k, v in {
    "current_ws": None, "current_cat": None, "current_doc": None,
    "active_tag": None, "show_new_note": False, "show_upload": False,
    "chat_msgs": [{"role": "assistant", "content": "👋 你好！我是你的知识库助手，可以基于上传的文档回答问题。"}],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ════════════════════════════════════════════
# 顶部 Hero - 粘性固定（改进版，使用 left:0 + width:100%）
# ════════════════════════════════════════════

# 获取当前统计数字（用于动态更新）
workspaces = list_workspaces()
if st.session_state.get("current_ws"):
    ws = get_workspace(st.session_state["current_ws"])
    ws_docs = list_documents(workspace_id=st.session_state["current_ws"])
    ws_cats = list_categories(st.session_state["current_ws"])
    doc_count = len(ws_docs)
    cat_count = len(ws_cats)
else:
    doc_count = 0
    cat_count = len(workspaces) if workspaces else 0

st.markdown(
    f"""
    <div class="hero-sticky">
        <div class="hero-inner">
            <div class="hero-left">
                <h1>📚 个人知识库</h1>
                <div class="sub">上传文档 · 自动分类 · 智能问答 · 知识管理一站式</div>
            </div>
            <div class="hero-right">
                <div class="stat-card">
                    <span class="stat-icon">📄</span>
                    <span class="stat-value">{doc_count}</span>
                    <span class="stat-label">文档</span>
                </div>
                <div class="stat-card">
                    <span class="stat-icon">⬆</span>
                    <span class="stat-value">{cat_count}</span>
                    <span class="stat-label">分类</span>
                </div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ════════════════════════════════════════════
# 侧边栏
# ════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-brand-title">📚 知识库</div>
        <div class="sidebar-brand-subtitle">Personal Knowledge Base</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("##### 🗂 导航")

    workspaces = list_workspaces()

    # 首次使用提示
    if not workspaces:
        st.info("👋 欢迎！请先创建工作区")
        with st.form("first_ws"):
            ws_name = st.text_input("工作区名称", placeholder="例如：技术学习")
            ws_icon = st.selectbox("图标", ["📚","💼","🎓","💡","🔬","🎨","📁","🏠","🌱","🚀"])
            if st.form_submit_button("✨ 创建", use_container_width=True, type="primary"):
                if ws_name.strip():
                    new_id = create_workspace(ws_name.strip(), "", ws_icon)
                    st.session_state["current_ws"] = new_id
                    st.toast("✅ 工作区已创建", icon="🎉")
                    time.sleep(0.3)
                    st.rerun()
        st.stop()

    # 工作区选择
    current_ws = st.session_state["current_ws"]
    if not current_ws or current_ws not in [w["id"] for w in workspaces]:
        current_ws = workspaces[0]["id"]
        st.session_state["current_ws"] = current_ws

    ws = get_workspace(current_ws)

    st.markdown(f"**{ws['icon']} 当前工作区**")

    if len(workspaces) > 1:
        ws_options = {f"{w['icon']} {w['name']}": w['id'] for w in workspaces}
        # 查找当前工作区的标签，如果不存在则使用第一个
        current_label = None
        for k, v in ws_options.items():
            if v == current_ws:
                current_label = k
                break
        if current_label is None and ws_options:
            current_label = list(ws_options.keys())[0]

        if current_label:
            sel_ws = st.selectbox(
                "切换工作区",
                list(ws_options.keys()),
                index=list(ws_options.keys()).index(current_label),
                label_visibility="collapsed",
            )
            new_ws = ws_options[sel_ws]
            if new_ws != current_ws:
                st.session_state["current_ws"] = new_ws
                st.session_state["current_cat"] = None
                st.session_state["current_doc"] = None
                st.rerun()

    with st.expander("➕ 新建工作区"):
        with st.form("new_ws_form", clear_on_submit=True):
            nw_name = st.text_input("名称")
            nw_icon = st.selectbox("图标", ["📚","💼","🎓","💡","🔬","🎨","📁","🏠","🌱","🚀"], key="nw_icon")
            if st.form_submit_button("创建", use_container_width=True):
                if nw_name.strip():
                    create_workspace(nw_name.strip(), "", nw_icon)
                    st.toast("✅ 已创建", icon="🎉")
                    time.sleep(0.3)
                    st.rerun()

    st.divider()

    # 分类树（Notion 风格层级）
    st.markdown("##### 📂 知识库")

    # 初始化 tree_expanded（render_tree_node 和新建分类按钮都需要）
    if "tree_expanded" not in st.session_state:
        st.session_state["tree_expanded"] = set()

    cats = list_categories(current_ws)
    current_cat = st.session_state.get("current_cat")

    # 根节点：全部文档
    if st.button(
        "📚 全部文档",
        key="cat_all",
        use_container_width=True,
        type="primary" if not current_cat else "secondary",
    ):
        st.session_state["current_cat"] = None
        st.session_state["current_doc"] = None
        st.rerun()

    # 顶级新建分类（在树外，方便操作）
    with st.popover("➕ 新建顶级分类", use_container_width=True):
        with st.form("new_root_cat", clear_on_submit=True):
            nc_name = st.text_input("分类名", placeholder="例如：个人/工作/学习")
            nc_icon = st.selectbox("图标", ["📁","📂","📚","�","🎓","💡","🔬","🎨","🏠","🌱","🚀","✈️","🎯","📊","🔧"], key="nri")
            if st.form_submit_button("✨ 创建", use_container_width=True, type="primary"):
                if nc_name.strip():
                    new_id = create_category(nc_name.strip(), current_ws, None)
                    st.session_state["current_cat"] = new_id
                    st.session_state["tree_expanded"].add(new_id)
                    st.toast("✅ 已创建", icon="🎉")
                    time.sleep(0.3)
                    st.rerun()

    # 递归渲染分类树
    tree = get_category_tree(current_ws)
    if not tree:
        st.caption("暂无分类，点击上方 ➕ 创建")
    else:
        for node in tree:
            render_tree_node(node, level=0, current_cat=current_cat, current_ws=current_ws)

    st.divider()

    # 标签
    st.markdown("### 🏷️ 标签")
    tags = get_all_tags(workspace_id=current_ws)
    active_tag = st.session_state.get("active_tag")
    if tags:
        # 标签云：每行 3 个
        tag_list = list(tags.items())[:12]
        for i in range(0, len(tag_list), 3):
            row = tag_list[i:i+3]
            cols = st.columns(3)
            for j, (t, c) in enumerate(row):
                with cols[j]:
                    is_active = active_tag == t
                    if st.button(
                        f"#{t}" if not is_active else f"✓ {t}",
                        key=f"tag_{t}",
                        use_container_width=True,
                        type="primary" if is_active else "secondary",
                        help=f"{c} 个文档",
                    ):
                        if is_active:
                            st.session_state["active_tag"] = None
                        else:
                            st.session_state["active_tag"] = t
                        st.rerun()
    else:
        st.caption("暂无标签")

    st.divider()

    # 工作区管理
    with st.expander("⚙️ 工作区管理"):
        st.caption(f"当前：{ws['icon']} {ws['name']}")
        st.caption(f"创建于：{(ws.get('created_at') or '')[:10]}")
        if st.button("🗑 删除工作区", type="secondary", use_container_width=True):
            if st.session_state.get("confirm_del_ws"):
                delete_workspace(current_ws)
                st.session_state["current_ws"] = None
                st.session_state["confirm_del_ws"] = False
                st.toast("工作区已删除", icon="🗑")
                time.sleep(0.3)
                st.rerun()
            else:
                st.session_state["confirm_del_ws"] = True
                st.warning("⚠️ 再点一次确认删除")


# ════════════════════════════════════════════
# 主区域
# ════════════════════════════════════════════

current_ws = st.session_state["current_ws"]
current_cat = st.session_state.get("current_cat")
current_doc = st.session_state.get("current_doc")

# 面包屑
breadcrumb_parts = [f"{ws['icon']} {ws['name']}"]
if current_cat:
    cat = get_category(current_cat)
    if cat:
        breadcrumb_parts.append(f"📂 {cat['path']}")
if current_doc:
    meta = load_meta_db().get("documents", {}).get(current_doc)
    if meta:
        fname = meta["filename"].split("/")[-1].split("\\")[-1]
        breadcrumb_parts.append(f"📄 {fname}")

st.caption(" › ".join(breadcrumb_parts))

# 2 个 Tab
tab_files, tab_chat = st.tabs([
    f"📁 文件管理  ·  {len(list_documents(workspace_id=current_ws, category_id=current_cat))}",
    "💬 AI 对话"
])


# ════════════════════════════════════════════
# Tab 1: 文件管理
# ════════════════════════════════════════════
with tab_files:
    # 统计 + 操作栏
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    docs = list_documents(workspace_id=current_ws, category_id=current_cat)
    tags_count = len(get_all_tags(workspace_id=current_ws))
    total_chunks = sum(d.get('chunk_count', 0) for d in docs)

    with col_stat1:
        st.metric("📄 文档", len(docs))
    with col_stat2:
        st.metric("📦 块", total_chunks)
    with col_stat3:
        st.metric("🏷️ 标签", tags_count)
    with col_stat4:
        st.metric("📂 分类", len(list_categories(current_ws)))

    st.write("")

    # 上传区
    with st.container():
        st.markdown("""
        <div class="upload-panel">
            <div class="upload-panel-title">📤 上传文档</div>
        """, unsafe_allow_html=True)

        cats = list_categories(current_ws)
        cat_options = [("📁 根目录", None)] + [(f"📂 {c['path']}", c["id"]) for c in cats]
        cat_labels = [x[0] for x in cat_options]
        cat_ids = [x[1] for x in cat_options]

        col_up1, col_up2, col_up3 = st.columns([2, 4, 1])
        with col_up1:
            st.caption("目标分类")
            sel_cat = st.selectbox("目标分类", cat_labels, key="upload_cat", label_visibility="collapsed")
            target_cat_id = cat_ids[cat_labels.index(sel_cat)]
        with col_up2:
            uploaded = st.file_uploader("选择文件", type=ALLOWED_EXTS, key="upload_widget", label_visibility="collapsed")
        with col_up3:
            show_new_note = st.button("📝 新建笔记", use_container_width=True)

        st.markdown("""
            <div class="upload-panel-hint">支持 md / txt / pdf / docx / html / csv / json / yaml / yml，上传后会自动分类并提取标签。</div>
        </div>
        """, unsafe_allow_html=True)

        if show_new_note:
            st.session_state["show_new_note"] = not st.session_state["show_new_note"]

        # 新建笔记弹层
        if st.session_state.get("show_new_note"):
            with st.form("new_note_form", clear_on_submit=True):
                col_n1, col_n2 = st.columns(2)
                with col_n1:
                    nt_title = st.text_input("标题")
                with col_n2:
                    nt_sel = st.selectbox("分类", cat_labels, key="nt_cat")
                    nt_target = cat_ids[cat_labels.index(nt_sel)]

                nt_content = st.text_area("内容 (Markdown)", height=200)
                nt_tags = st.text_input("标签 (逗号分隔)")

                col_btn1, col_btn2 = st.columns([1, 5])
                with col_btn1:
                    if st.form_submit_button("💾 保存", type="primary"):
                        if nt_title.strip() and nt_content.strip():
                            full = f"# {nt_title}\n\n{nt_content}"
                            tags_list = [t.strip() for t in nt_tags.split(",") if t.strip()] if nt_tags else extract_tags(full, use_llm=False)
                            safe = "".join(c for c in nt_title if c.isalnum() or c in " _-中文")[:30] or f"note_{int(time.time())}"
                            result = get_kb().upload_by_str(
                                data=full, filename=f"{safe}.md",
                                workspace_id=current_ws, category_id=nt_target,
                                category="笔记", tags=tags_list, source_type="note",
                            )
                            if result["status"] == "success":
                                st.session_state["show_new_note"] = False
                                st.toast("✅ 笔记已保存", icon="📝")
                                time.sleep(0.3)
                                st.rerun()
                            else:
                                st.warning("已存在")
                with col_btn2:
                    if st.form_submit_button("取消"):
                        st.session_state["show_new_note"] = False
                        st.rerun()

        if uploaded:
            file_name = uploaded.name
            file_ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
            file_bytes = uploaded.getvalue()

            try:
                text = extract_text(file_bytes, file_ext)
            except Exception as e:
                st.error(f"❌ 解析失败：{e}")
                text = None

            if text:
                # 预览
                with st.expander(f"📄 {file_name} 预览", expanded=True):
                    st.caption(f"字符数：{len(text)} | 类型：{file_ext}")
                    st.text(text[:600] + ("..." if len(text) > 600 else ""))

                # 自动识别
                with st.spinner("🤖 AI 识别中..."):
                    pred_cat = auto_categorize(text)
                    pred_tags = extract_tags(text, use_llm=False)

                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    st.success(f"🤖 **自动分类**：{pred_cat}")
                with col_p2:
                    st.info(f"🏷️ **自动标签**：{', '.join(pred_tags[:5])}")

                if st.button("✅ 确认上传到知识库", type="primary", use_container_width=True):
                    with st.spinner("处理中..."):
                        saved = save_upload(file_bytes, file_name, file_ext)
                        result = get_kb().upload_by_str(
                            data=text, filename=saved.as_posix(),
                            workspace_id=current_ws, category_id=target_cat_id,
                            category=pred_cat, tags=pred_tags,
                        )
                    if result["status"] == "skipped":
                        st.warning("⚠️ 已存在")
                    else:
                        st.toast("✅ 上传成功！", icon="🎉")
                        time.sleep(0.5)
                        st.rerun()

    st.divider()

    # 搜索 + 过滤
    col_search, col_filter = st.columns([4, 1])
    with col_search:
        search = st.text_input("🔍 搜索", placeholder="搜索文件名或标签...", key="search_box", label_visibility="collapsed")
    with col_filter:
        sort_by = st.selectbox("排序", ["最新", "最早", "名称"], label_visibility="collapsed")

    # 过滤
    active_tag = st.session_state.get("active_tag")
    if active_tag:
        st.info(f"🏷️ 当前标签筛选：**#{active_tag}** | [清除]")

    if search:
        s = search.lower()
        docs = [d for d in docs if s in d.get("filename", "").lower()
                or any(s in t.lower() for t in d.get("tags", []))]

    if active_tag:
        docs = [d for d in docs if active_tag in d.get("tags", [])]

    # 排序
    if sort_by == "最新":
        docs = sorted(docs, key=lambda x: x.get("upload_time", ""), reverse=True)
    elif sort_by == "最早":
        docs = sorted(docs, key=lambda x: x.get("upload_time", ""))
    else:
        docs = sorted(docs, key=lambda x: x.get("filename", ""))

    # 文档列表
    if not docs:
        st.info("📭 暂无文档，请上传或调整筛选条件")
    else:
        # 列表式布局（更清晰）
        for doc in docs:
            fname = doc["filename"].split("/")[-1].split("\\")[-1]
            ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else "md"
            icon = get_file_icon(ext)
            date = (doc.get("upload_time") or "")[:10]
            is_active = current_doc == doc["doc_id"]

            with st.container():
                col1, col2, col3, col4, col5 = st.columns([1, 5, 2, 1, 1])
                with col1:
                    st.markdown(f"## {icon}")
                with col2:
                    btn_type = "primary" if is_active else "secondary"
                    if st.button(
                        fname,
                        key=f"doc_{doc['doc_id']}",
                        use_container_width=True,
                        type=btn_type,
                    ):
                        st.session_state["current_doc"] = doc["doc_id"]
                        st.rerun()
                    # 标签
                    tags_d = doc.get("tags", [])[:3]
                    if tags_d:
                        st.caption(" ".join(f"`{t}`" for t in tags_d))
                with col3:
                    st.caption(f"📅 {date}")
                    st.caption(f"📦 {doc.get('chunk_count', 0)} 块")
                with col4:
                    cat_path = doc.get('category_path') or '根目录'
                    st.caption(f"📂 {cat_path}")
                with col5:
                    if st.button("🗑", key=f"del_{doc['doc_id']}", help="删除文档"):
                        delete_document(doc["doc_id"])
                        if current_doc == doc["doc_id"]:
                            st.session_state["current_doc"] = None
                        st.toast("已删除", icon="🗑")
                        time.sleep(0.3)
                        st.rerun()

    # 文档详情
    if current_doc:
        st.divider()
        meta = load_meta_db().get("documents", {}).get(current_doc)
        if meta:
            fname = meta["filename"].split("/")[-1].split("\\")[-1]
            ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else "md"
            icon = get_file_icon(ext)

            col_t1, col_t2 = st.columns([6, 1])
            with col_t1:
                st.markdown(f"## {icon} {fname}")
            with col_t2:
                if st.button("🗑 删除", key="del_doc_detail", type="secondary", use_container_width=True):
                    delete_document(current_doc)
                    st.session_state["current_doc"] = None
                    st.toast("已删除", icon="🗑")
                    time.sleep(0.3)
                    st.rerun()

            # 文档信息
            info_parts = []
            info_parts.append(f"📂 {meta.get('category_path') or '根目录'}")
            info_parts.append(f"📅 {(meta.get('upload_time') or '')[:10]}")
            info_parts.append(f"📦 {meta.get('chunk_count', 0)} 块")
            if meta.get('category'):
                info_parts.append(f"🏷️ {meta.get('category')}")
            st.caption("  ·  ".join(info_parts))

            tags = meta.get("tags", [])
            if tags:
                st.markdown(" ".join(f"`#{t}`" for t in tags))

            st.divider()

            # 内容
            content = get_doc_content(current_doc)
            if content:
                with st.container():
                    st.markdown(content)
            else:
                st.info("📭 无内容")
        else:
            st.warning("⚠️ 文档不存在")
            st.session_state["current_doc"] = None


# ════════════════════════════════════════════
# Tab 2: AI 对话
# ════════════════════════════════════════════
with tab_chat:
    st.markdown('<div class="section-title">💬 AI 智能问答</div>', unsafe_allow_html=True)

    cats = list_categories(current_ws)
    cat_options = [("🌐 全部文档", None)] + [(f"📂 {c['path']}", c["id"]) for c in cats]
    cat_labels = [x[0] for x in cat_options]
    cat_ids = [x[1] for x in cat_options]

    col_c1, col_c2, col_c3 = st.columns([3, 1, 1])
    with col_c1:
        sel = st.selectbox("检索范围", cat_labels, key="chat_range", label_visibility="collapsed")
        chat_cat_id = cat_ids[cat_labels.index(sel)]
    with col_c2:
        st.caption(f"💬 {len(st.session_state['chat_msgs'])} 条消息")
    with col_c3:
        if st.button("🗑 清空对话", use_container_width=True):
            st.session_state["chat_msgs"] = []
            st.rerun()

    st.divider()

    # 消息显示
    for msg in st.session_state["chat_msgs"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    st.divider()

    # 输入框（在消息列表下面）- 卡片化
    st.markdown("""
    <div class="chat-input-card">
        <div class="chat-input-label">💭 输入你的问题</div>
    """, unsafe_allow_html=True)
    with st.form("chat_input_form", clear_on_submit=True):
        prompt = st.text_area(
            "问题",
            placeholder="例如：这个项目的核心架构是什么？",
            height=80,
            label_visibility="collapsed",
        )
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])
        with col_btn1:
            submit = st.form_submit_button("📤 发送", type="primary", use_container_width=True)
        with col_btn2:
            st.form_submit_button("🔄 重新生成", use_container_width=True)

        if submit and prompt.strip():
            st.session_state["chat_msgs"].append({"role": "user", "content": prompt})

            with st.spinner("🤔 思考中..."):
                try:
                    rag = RagService(workspace_id=current_ws, category_id=chat_cat_id)
                    res = rag.chain.invoke({"input": prompt}, config.session_config)
                except Exception as e:
                    res = f"❌ 出错了：{e}"

            st.session_state["chat_msgs"].append({"role": "assistant", "content": res})
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)