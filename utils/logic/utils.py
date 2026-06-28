# utils/logic/utils.py
import os
import json
from io import BytesIO
from pathlib import Path

UPLOAD_ROOT = Path("data") / "uploads"
ALLOWED_EXTS = ["md", "txt", "pdf", "docx", "html", "csv", "json", "yaml", "yml"]

def extract_text(file_bytes: bytes, file_ext: str) -> str:
    """Extract textual content from various file types."""
    if file_ext in ("md", "txt", "yaml", "yml"):
        return file_bytes.decode("utf-8", errors="ignore")
    if file_ext == "pdf":
        from pypdf import PdfReader
        pdf = PdfReader(BytesIO(file_bytes))
        return "\n".join((p.extract_text() or "") for p in pdf.pages)
    if file_ext == "docx":
        from docx import Document
        doc = Document(BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
    if file_ext == "html":
        from html.parser import HTMLParser
        class TE(HTMLParser):
            def __init__(self): super().__init__(); self.t=[]; self.s=False
            def handle_starttag(self,t,a):
                if t in ("script","style"): self.s=True
            def handle_endtag(self,t):
                if t in ("script","style"): self.s=False
            def handle_data(self,d):
                if not self.s: self.t.append(d)
        e=TE(); e.feed(file_bytes.decode("utf-8", errors="ignore"))
        return "\n".join(e.t)
    if file_ext == "csv":
        import csv
        lines = file_bytes.decode("utf-8", errors="ignore").splitlines()
        return "\n".join(" | ".join(r) for r in csv.reader(lines))
    if file_ext == "json":
        return json.dumps(json.loads(file_bytes.decode("utf-8")), ensure_ascii=False, indent=2)
    raise ValueError(f"Unsupported file type: {file_ext}")

def save_upload(file_bytes: bytes, file_name: str, file_ext: str) -> Path:
    """Persist uploaded file to disk organized by extension."""
    type_dir = UPLOAD_ROOT / file_ext
    type_dir.mkdir(parents=True, exist_ok=True)
    save_path = type_dir / file_name
    base, suf = Path(file_name).stem, Path(file_name).suffix
    i = 1
    while save_path.exists():
        save_path = type_dir / f"{base}_{i}{suf}"
        i += 1
    save_path.write_bytes(file_bytes)
    return save_path