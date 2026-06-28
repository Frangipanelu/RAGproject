"""
工作区与分类管理
- 支持多工作区
- 支持多级嵌套分类（树形）
- 级联删除
"""
import os
import json
import uuid
from datetime import datetime
from typing import Optional


WORKSPACE_DB = "./workspace_db.json"


# ─────────────────────────────────────────────
# 数据库读写
# ─────────────────────────────────────────────

def load_db() -> dict:
    """加载工作区数据库"""
    if not os.path.exists(WORKSPACE_DB):
        return {"workspaces": {}, "categories": {}}
    try:
        with open(WORKSPACE_DB, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"workspaces": {}, "categories": {}}


def save_db(db: dict):
    """保存工作区数据库"""
    with open(WORKSPACE_DB, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _gen_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


# ─────────────────────────────────────────────
# 工作区操作
# ─────────────────────────────────────────────

def create_workspace(name: str, description: str = "", icon: str = "📁") -> str:
    """创建工作区"""
    db = load_db()
    ws_id = _gen_id("ws")
    db["workspaces"][ws_id] = {
        "id": ws_id,
        "name": name,
        "description": description,
        "icon": icon,
        "created_at": _now(),
    }
    save_db(db)
    return ws_id


def list_workspaces() -> list[dict]:
    """列出所有工作区"""
    db = load_db()
    workspaces = list(db["workspaces"].values())
    # 统计每个工作区的分类和文档数
    cat_counts = {}
    for cat in db["categories"].values():
        ws = cat["workspace_id"]
        cat_counts[ws] = cat_counts.get(ws, 0) + 1
    for ws in workspaces:
        ws["category_count"] = cat_counts.get(ws["id"], 0)
    # 按创建时间排序
    workspaces.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return workspaces


def get_workspace(ws_id: str) -> Optional[dict]:
    """获取单个工作区"""
    db = load_db()
    return db["workspaces"].get(ws_id)


def update_workspace(ws_id: str, name: str = None, description: str = None, icon: str = None) -> bool:
    """更新工作区信息"""
    db = load_db()
    if ws_id not in db["workspaces"]:
        return False
    if name is not None:
        db["workspaces"][ws_id]["name"] = name
    if description is not None:
        db["workspaces"][ws_id]["description"] = description
    if icon is not None:
        db["workspaces"][ws_id]["icon"] = icon
    save_db(db)
    return True


def delete_workspace(ws_id: str) -> bool:
    """删除工作区（级联删除所有分类）"""
    db = load_db()
    if ws_id not in db["workspaces"]:
        return False
    # 删除该工作区下所有分类
    db["categories"] = {
        k: v for k, v in db["categories"].items()
        if v["workspace_id"] != ws_id
    }
    # 删除工作区
    del db["workspaces"][ws_id]
    save_db(db)
    return True


# ─────────────────────────────────────────────
# 分类（目录）操作
# ─────────────────────────────────────────────

def create_category(name: str, workspace_id: str, parent_id: str = None) -> Optional[str]:
    """创建分类（支持多级嵌套）"""
    db = load_db()
    if workspace_id not in db["workspaces"]:
        return None
    if parent_id and parent_id not in db["categories"]:
        return None

    cat_id = _gen_id("cat")
    # 计算完整路径
    if parent_id:
        parent = db["categories"][parent_id]
        path = f"{parent['path']}/{name}"
    else:
        path = name

    db["categories"][cat_id] = {
        "id": cat_id,
        "name": name,
        "parent_id": parent_id,
        "workspace_id": workspace_id,
        "path": path,
        "level": (db["categories"][parent_id]["level"] + 1) if parent_id else 0,
        "created_at": _now(),
    }
    save_db(db)
    return cat_id


def list_categories(workspace_id: str) -> list[dict]:
    """列出工作区下所有分类（平铺）"""
    db = load_db()
    cats = [c for c in db["categories"].values() if c["workspace_id"] == workspace_id]
    cats.sort(key=lambda x: x.get("path", ""))
    return cats


def get_category(cat_id: str) -> Optional[dict]:
    """获取单个分类"""
    db = load_db()
    return db["categories"].get(cat_id)


def get_category_tree(workspace_id: str) -> list[dict]:
    """获取工作区的分类树（嵌套结构）"""
    db = load_db()
    cats = [c for c in db["categories"].values() if c["workspace_id"] == workspace_id]
    return _build_tree(cats, parent_id=None)


def _build_tree(cats: list, parent_id: Optional[str]) -> list:
    """递归构建树"""
    result = []
    for cat in cats:
        if cat["parent_id"] == parent_id:
            children = _build_tree(cats, cat["id"])
            result.append({**cat, "children": children})
    return result


def get_category_path(cat_id: str) -> Optional[str]:
    """获取分类的完整路径"""
    db = load_db()
    cat = db["categories"].get(cat_id)
    return cat["path"] if cat else None


def get_category_children(cat_id: str) -> list[dict]:
    """获取直接子分类"""
    db = load_db()
    return [c for c in db["categories"].values() if c["parent_id"] == cat_id]


def get_all_descendants(cat_id: str) -> list[str]:
    """获取所有后代分类ID（含子、孙等）"""
    db = load_db()
    result = []
    queue = [cat_id]
    while queue:
        current = queue.pop(0)
        children = [c["id"] for c in db["categories"].values() if c["parent_id"] == current]
        result.extend(children)
        queue.extend(children)
    return result


def update_category(cat_id: str, name: str = None) -> bool:
    """更新分类（重命名时同步更新所有后代路径）"""
    db = load_db()
    if cat_id not in db["categories"]:
        return False
    cat = db["categories"][cat_id]

    if name is not None and name != cat["name"]:
        old_path = cat["path"]
        if cat["parent_id"]:
            parent = db["categories"][cat["parent_id"]]
            new_path = f"{parent['path']}/{name}"
        else:
            new_path = name
        cat["name"] = name
        cat["path"] = new_path
        # 更新所有后代路径
        for c in db["categories"].values():
            if c["path"].startswith(old_path + "/"):
                c["path"] = new_path + c["path"][len(old_path):]
    save_db(db)
    return True


def delete_category(cat_id: str) -> bool:
    """删除分类（级联删除所有子分类）"""
    db = load_db()
    if cat_id not in db["categories"]:
        return False
    # 找出所有要删除的分类ID（含子、孙等）
    to_delete = [cat_id] + get_all_descendants(cat_id)
    for cid in to_delete:
        if cid in db["categories"]:
            del db["categories"][cid]
    save_db(db)
    return True


def move_category(cat_id: str, new_parent_id: Optional[str]) -> bool:
    """移动分类到新的父分类下"""
    db = load_db()
    if cat_id not in db["categories"]:
        return False
    # 防止移动到自己的后代下（会形成循环）
    if new_parent_id and new_parent_id in [cat_id] + get_all_descendants(cat_id):
        return False

    cat = db["categories"][cat_id]
    cat["parent_id"] = new_parent_id

    # 重新计算路径
    if new_parent_id:
        parent = db["categories"][new_parent_id]
        new_path = f"{parent['path']}/{cat['name']}"
    else:
        new_path = cat["name"]
    old_path = cat["path"]
    cat["path"] = new_path
    # 更新后代路径
    for c in db["categories"].values():
        if c["path"].startswith(old_path + "/"):
            c["path"] = new_path + c["path"][len(old_path):]
    save_db(db)
    return True


# ─────────────────────────────────────────────
# 统计
# ─────────────────────────────────────────────

def count_categories(workspace_id: str) -> int:
    """统计工作区下的分类数"""
    db = load_db()
    return sum(1 for c in db["categories"].values() if c["workspace_id"] == workspace_id)
