"""
Sidebar rendering module - category tree, workspace selector, tag cloud, workspace management.
"""
from typing import Optional
import time
import streamlit as st

from core.workspace_manager import (
    create_workspace, list_workspaces, get_workspace, delete_workspace,
    create_category, list_categories, get_category_tree,
    delete_category, get_all_descendants, update_category, move_category,
)
from core.knowledge_base import list_documents, get_all_tags, delete_document


def render_sidebar(current_ws: Optional[str]) -> str:
    """Render the entire sidebar. Returns the current workspace ID.

    This function is responsible for the full sidebar UI:
    - Brand header
    - Workspace selector & creation
    - Category tree (Notion-style)
    - Tag cloud
    - Workspace management
    """
    # Brand
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

    # Resolve current_ws
    current_ws = st.session_state["current_ws"]
    if not current_ws or current_ws not in [w["id"] for w in workspaces]:
        current_ws = workspaces[0]["id"]
        st.session_state["current_ws"] = current_ws

    ws = get_workspace(current_ws)

    st.markdown(f"**{ws['icon']} 当前工作区**")

    # Workspace selector
    if len(workspaces) > 1:
        ws_options = {f"{w['icon']} {w['name']}": w['id'] for w in workspaces}
        current_label = next(k for k, v in ws_options.items() if v == current_ws)
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

    # Category tree
    st.markdown("##### 📂 知识库")

    if "tree_expanded" not in st.session_state:
        st.session_state["tree_expanded"] = set()

    cats = list_categories(current_ws)
    current_cat = st.session_state.get("current_cat")

    # Root node: 全部文档
    if st.button(
        "📚 全部文档",
        key="cat_all",
        use_container_width=True,
        type="primary" if not current_cat else "secondary",
    ):
        st.session_state["current_cat"] = None
        st.session_state["current_doc"] = None
        st.rerun()

    # 顶级新建分类
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

    # Render category tree
    tree = get_category_tree(current_ws)
    if not tree:
        st.caption("暂无分类，点击上方 ➕ 创建")
    else:
        for node in tree:
            _render_tree_node(node, level=0, current_cat=current_cat, current_ws=current_ws)

    st.divider()

    # Tag cloud
    st.markdown("### 🏷️ 标签")
    tags = get_all_tags(workspace_id=current_ws)
    active_tag = st.session_state.get("active_tag")
    if tags:
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

    # Workspace management
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

    return current_ws


def _render_tree_node(node: dict, level: int = 0, current_cat: Optional[str] = None, current_ws: str = ""):
    """Render a single category tree node (recursively)."""
    cat_id = node["id"]
    children = node.get("children", [])
    has_children = len(children) > 0
    is_active = current_cat == cat_id
    indent = " " * level  # 全角空格缩进

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
            if st.button(toggle, key=f"tog_{cat_id}", help="展开/折叠"):
                if expanded:
                    st.session_state["tree_expanded"].discard(cat_id)
                else:
                    st.session_state["tree_expanded"].add(cat_id)
                st.rerun()
        else:
            st.markdown(
                '<div class="tree-empty-dot">·</div>',
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
        with st.popover("⋮", help="操作菜单"):
            st.markdown(
                '<div class="popover-node-title">📂 <b>{}</b></div>'.format(node["name"]),
                unsafe_allow_html=True,
            )
            st.divider()

            # 新建子分类
            with st.form(f"add_child_{cat_id}", clear_on_submit=True):
                new_name = st.text_input("子分类名", key=f"newc_{cat_id}", placeholder="输入名称")
                if st.form_submit_button("➕ 新建子分类", use_container_width=True):
                    if new_name.strip():
                        create_category(new_name.strip(), current_ws, cat_id)
                        st.session_state["tree_expanded"].add(cat_id)
                        st.toast("✅ 已创建", icon="🎉")
                        time.sleep(0.3)
                        st.rerun()

            # 重命名
            with st.form(f"rename_{cat_id}", clear_on_submit=True):
                rn = st.text_input("新名称", value=node["name"], key=f"rn_{cat_id}")
                if st.form_submit_button("✏️ 重命名", use_container_width=True):
                    if rn.strip() and rn.strip() != node["name"]:
                        update_category(cat_id, rn.strip())
                        st.toast("✅ 已重命名", icon="✏️")
                        time.sleep(0.3)
                        st.rerun()

            # 移动
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

            # 删除
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
            _render_tree_node(child, level + 1, current_cat, current_ws)
