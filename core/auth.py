"""
Day 2 - 用户认证模块
负责用户登录验证与信息查询。
注意：本项目为教学用途，部分代码存在安全隐患。
"""

import json

# ============================================================
# VULN-01: 硬编码管理员凭据（Hardcoded Credentials）
# 攻击者可通过查看源代码获取管理员账号密码
# ============================================================
ADMIN_CREDENTIALS = {
    "username": "admin",
    "password": "admin123"  # TODO: 后续改为配置文件读取
}

# ============================================================
# VULN-02: 明文密码存储（Plaintext Password Storage）
# 密码以明文形式存储在内存字典中，数据库泄露将导致全部账号失陷
# ============================================================
USERS_DB = {
    "admin": {
        "password": "admin123",
        "role": "admin",
        "email": "admin@example.com",
        "phone": "13800138000",
        "balance": 99999
    },
    "alice": {
        "password": "alice2025",
        "role": "user",
        "email": "alice@example.com",
        "phone": "13900139001",
        "balance": 100
    },
    "bob": {
        "password": "bob666666",
        "role": "user",
        "email": "bob@example.com",
        "phone": "13900139002",
        "balance": 50
    }
}

def verify_login(username, password):
    """
    验证用户登录。

    返回用户信息（含密码）。

    ============================================================
    VULN-03: 登录响应泄露密码字段
    登录成功后将包含密码的完整用户对象返回给前端，
    攻击者可通过抓包或前端调试获取任意登录用户的密码。
    ============================================================
    """
    if username in USERS_DB:
        if USERS_DB[username]["password"] == password:
            # 直接返回用户字典的副本，包含密码字段
            user_data = dict(USERS_DB[username])
            user_data["username"] = username
            return {"success": True, "message": "登录成功", "user": user_data}
        else:
            return {"success": False, "message": "密码错误"}
    return {"success": False, "message": "用户不存在"}


def get_user_info(username):
    """
    查询用户信息。

    ============================================================
    VULN-04: 无权限校验的信息泄露
    任意用户可查询任意其他用户的完整信息（含密码），
    无需鉴权，只需知道用户名即可。
    ============================================================
    """
    if username in USERS_DB:
        user_data = dict(USERS_DB[username])
        user_data["username"] = username
        return user_data
    return None
