# utils/ui/chat.py
import streamlit as st
from core.rag import RagService

def render_chat(workspace_id: str, chat_cat_id: str):
    """Render the conversation tab."""
    st.markdown('<div class="section-title">💬 AI 智能问答</div>', unsafe_allow_html=True)

    # Get categories for selector
    from core.workspace_manager import list_categories
    cats = list_categories(workspace_id)
    cat_options = [("🌐 全部文档", None)] + [(f"📂 {c['path']}", c["id"]) for c in cats]
    cat_labels = [x[0] for x in cat_options]
    cat_ids = [x[1] for x in cat_options]

    col_c1, col_c2, col_c3 = st.columns([3, 1, 1])
    with col_c1:
        sel = st.selectbox("检索范围", cat_labels, key="chat_range", label_visibility="collapsed")
        chat_cat_id = cat_ids[cat_labels.index(sel)]
    with col_c2:
        st.caption(f"💬 {len(st.session_state.get('chat_msgs', []))} 条消息")
    with col_c3:
        if st.button("🗑 清空对话", use_container_width=True):
            st.session_state["chat_msgs"] = []
            st.rerun()

    st.divider()

    # Message display
    for msg in st.session_state.get("chat_msgs", []):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    st.divider()

    # Input card
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
                    rag = RagService(workspace_id=workspace_id, category_id=chat_cat_id)
                    res = rag.chain.invoke({"input": prompt}, getattr(rag, 'session_config', {}))
                except Exception as e:
                    res = f"❌ 出错了：{e}"

            st.session_state["chat_msgs"].append({"role": "assistant", "content": res})
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)