"""
RAG 知识库核心功能测试脚本

测试范围:
1. 工具函数 (extract_text, save_upload)
2. UI 模块导入 (upload, chat)
3. 工作区管理
4. 分类管理
5. 文件保存位置验证
"""

import os
import sys
from pathlib import Path

# 设置环境变量
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

# 添加项目根目录到路径
project_root = Path.cwd()
sys.path.insert(0, str(project_root))

print('=' * 60)
print('RAG 知识库核心功能测试')
print('=' * 60)

# 清理数据
for f in ['data/workspace_db.json', 'data/knowledge_meta.json', 'data/md5.text']:
    if os.path.exists(f):
        os.remove(f)
if os.path.exists('data/uploads'):
    import shutil
    shutil.rmtree('data/uploads')
print('[OK] 数据已清理')

# 测试 1: 工具函数
print('\n--- 测试 1: utils/logic/utils.py ---')
from utils.logic.utils import extract_text, save_upload, ALLOWED_EXTS
assert 'md' in ALLOWED_EXTS, "md should be in ALLOWED_EXTS"
test_content = b'Test content'
result = extract_text(test_content, 'txt')
assert result == 'Test content', f"Expected 'Test content', got '{result}'"
saved = save_upload(b'test', 'test.txt', 'txt')
assert saved.exists(), "File should exist"
saved.unlink()
print('[PASS] 工具函数测试通过')

# 测试 2: UI 模块导入
print('\n--- 测试 2: utils/ui/ 模块导入 ---')
from utils.ui.upload import handle_single_upload, VALID_EXTS, MAX_UPLOAD_SIZE
from utils.ui.chat import render_chat
print('[PASS] UI 模块导入测试通过')

# 测试 3: 工作区管理
print('\n--- 测试 3: 工作区管理 ---')
from core.workspace_manager import create_workspace, list_workspaces, delete_workspace
ws_id = create_workspace('测试工作区', '测试', '🧪')
workspaces = list_workspaces()
assert any(w['name'] == '测试工作区' for w in workspaces), "Workspace should exist"
delete_workspace(ws_id)
print('[PASS] 工作区管理测试通过')

# 测试 4: 分类管理
print('\n--- 测试 4: 分类管理 ---')
from core.workspace_manager import create_category, get_category_tree, delete_category
ws_id = create_workspace('分类测试', '测试', '📂')
root_cat = create_category('根分类', ws_id)
child = create_category('子分类', ws_id, parent_id=root_cat)
tree = get_category_tree(ws_id)
def count_nodes(nodes):
    count = 0
    for node in nodes:
        count += 1
        count += count_nodes(node.get('children', []))
    return count
total = count_nodes(tree)
assert total == 2, f'Expected 2 nodes, got {total}'
delete_category(root_cat)
delete_workspace(ws_id)
print('[PASS] 分类管理测试通过')

# 测试 5: 文件保存位置验证
print('\n--- 测试 5: 文件保存位置验证 ---')
saved_path = save_upload(b'test content', 'test.md', 'md')
expected_dir = project_root / 'data' / 'uploads' / 'md'
assert expected_dir.exists(), f'Directory not found: {expected_dir}'
files = list(expected_dir.glob('*.md'))
assert len(files) > 0, 'No files found'
saved_path.unlink()
print(f'[OK] 文件保存在：{saved_path.parent}')
print('[PASS] 文件保存位置测试通过')

print('\n' + '=' * 60)
print('[SUCCESS] 所有核心功能测试通过！')
print('=' * 60)
