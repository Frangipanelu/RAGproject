# utils/ui/upload.py
import streamlit as st
import re
from typing import Optional
from core.knowledge_base import KnowledgeBaseService, auto_categorize, extract_tags
from utils.logic.utils import UPLOAD_ROOT, ALLOWED_EXTS, save_upload, extract_text

# Configuration constants
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB
VALID_EXTS = [ext for ext in ALLOWED_EXTS if ext != 'htaccess']


def handle_single_upload(target_category: Optional[str] = None, show_preview: bool = True):
    """
    Manages file upload and processing with proper validation
    """
    uploaded_file = st.file_uploader(
        "📁 上传文件",
        type=VALID_EXTS,
        help="支持：MD/TXT/PDF/HTML/Docx/H5, 最大 100MB"
    )
    if uploaded_file is not None:
        if uploaded_file.size > MAX_UPLOAD_SIZE:
            st.toast(f"⚠️ 文件过大 ({uploaded_file.size/(1024*1024):.1f}MB)", icon="⚠️")
            return None

        file_name = uploaded_file.name
        file_ext = file_name.rsplit(".", 1)[-1].lower()
        content_type = uploaded_file.type
        timestamp = re.sub(r'[^\\w-]', ' ', file_name)
        safe_name = re.sub(r'\s+', '_', timestamp).strip('_')

        file_bytes = uploaded_file.getvalue()

        try:
            text = extract_text(file_bytes, file_ext)
        except Exception as e:
            st.error(f"❌ 解析失败：{e}")
            return None

        if text:
            # Show preview
            if show_preview:
                with st.expander(f"📄 {file_name} 预览", expanded=True):
                    st.caption(f"字符数：{len(text)} | 类型：{file_ext}")
                    st.text(text[:600] + ("..." if len(text) > 600 else ""))

            # Auto classification
            with st.spinner("🤖 AI 识别中..."):
                pred_cat = auto_categorize(text)
                pred_tags = extract_tags(text, use_llm=False)

            col1, col2 = st.columns(2)
            with col1:
                st.success(f"🤖 **自动分类**：{pred_cat}")
            with col2:
                st.info(f"🏷️ **自动标签**：{', '.join(pred_tags[:5])}")

            if st.button("✅ 确认上传到知识库", type="primary", use_container_width=True):
                with st.spinner("处理中..."):
                    try:
                        saved_path = save_upload(file_bytes, file_name, file_ext)
                        kb = KnowledgeBaseService()
                        result = kb.upload_by_str(
                            data=text,
                            filename=saved_path.as_posix(),
                            workspace_id=target_category or st.session_state.get("current_ws"),
                            category=pred_cat,
                            tags=pred_tags,
                        )
                        if result.get("status") == "skipped":
                            st.warning("⚠️ 已存在")
                        else:
                            st.toast("✅ 上传成功！", icon="🎉")
                            return True
                    except Exception as e:
                        st.error(f"❌ 上传出错：{e}")
    return None
