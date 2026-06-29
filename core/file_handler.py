"""
Day 4 - 文件上传处理模块
负责用户头像等文件的上传与存储。
注意：本项目为教学用途，部分代码存在安全隐患。
"""

import os
from flask import request

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    """
    检查文件后缀是否允许上传。

    ============================================================
    VULN-08: 仅前端校验，无服务器端校验
    本函数虽定义了允许的后缀列表，但在 handle_file_upload
    中并未调用！攻击者可直接上传任意文件。
    ============================================================
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def handle_file_upload(file_storage):
    """
    处理文件上传。

    ============================================================
    VULN-09: 任意文件上传
    - 未验证文件后缀（本应调用 allowed_file 但未调用）
    - 未验证文件内容类型（Content-Type）
    - 使用原始文件名保存（可能包含路径穿越字符）
    - 上传目录可直接访问

    攻击者可上传 webshell（.php/.jsp/.py 等），
    然后通过 URL 直接访问并执行恶意代码。
    ============================================================
    """
    if file_storage.filename == '':
        return {"success": False, "message": "未选择文件"}

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # 危险！使用用户提供的原始文件名，不重命名
    filename = file_storage.filename  # VULN: 保留了用户原始文件名
    save_path = os.path.join(UPLOAD_FOLDER, filename)

    # 危险！未检查文件后缀和内容类型
    file_storage.save(save_path)

    # 返回可访问的 URL
    file_url = f"/static/uploads/{filename}"
    return {"success": True, "message": "上传成功", "file_url": file_url}


def get_upload_path(filename):
    """
    获取上传文件的完整路径。

    ============================================================
    VULN-10: 路径穿越
    filename 参数未做过滤，传入 ../etc/passwd 等
    可读取系统任意文件（与其他漏洞组合利用）。
    ============================================================
    """
    return os.path.join(UPLOAD_FOLDER, filename)
