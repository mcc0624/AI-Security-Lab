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
      GET /page?name=../../../etc/passwd      （读取系统文件）
      GET /page?name=../core/auth.py           （读取项目源码）
      GET /page?name=../app.py                 （读取主应用代码）

    VULN-15: 远程文件包含（RFI）
    若 allow_url_include 开启，甚至可包含远程文件。
    ============================================================
    """
    # 危险！直接拼接路径，未做白名单校验
    # 攻击者可通过路径穿越（../）读取系统任意文件
    file_path = os.path.join(PAGES_DIR, page_name)

    # 危险！先尝试精确路径，不存在则加 .html 后缀
    # 但未校验 ../ 等路径穿越字符，导致 LFI 漏洞
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"success": True, "content": content}

    # 尝试加 .html 后缀（正常页面访问）
    file_path_html = file_path + '.html'
    if os.path.exists(file_path_html):
        with open(file_path_html, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"success": True, "content": content}

    return {"success": False, "message": "页面不存在"}
