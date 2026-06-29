"""
Day 6 - 页面加载模块
负责动态加载页面内容，支持页面主题切换等功能。
注意：本项目为教学用途，部分代码存在安全隐患。
"""

import os

PAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pages")


def load_page(page_name):
    """
    加载指定名称的页面文件。

    ============================================================
    VULN-14: 本地文件包含（LFI）
    - page_name 参数直接拼入文件路径，未做任何过滤
    - 攻击者可通过路径穿越（../）读取系统任意文件
    - 文件内容直接返回，可实现任意文件读取

    复现方法：
      GET /page?name=../../etc/passwd
      GET /page?name=../../core/auth.py
      GET /page?name=../../../etc/shadow

    VULN-15: 远程文件包含（RFI）
    若 allow_url_include 开启，甚至可包含远程文件。
    ============================================================
    """
    # 危险！直接拼接路径，未做白名单校验
    file_path = os.path.join(PAGES_DIR, page_name)

    # 危险！添加了 .html 后缀但仍可绕过（使用 %00 截断或 ? 参数）
    # 在某些 Python 版本中，路径遍历仍然有效
    if not file_path.endswith('.html'):
        file_path = file_path + '.html'

    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"success": True, "content": content}
    else:
        return {"success": False, "message": "页面不存在"}
