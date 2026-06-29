"""
Day 5 - 用户业务服务模块
负责个人中心信息查询、资料修改、充值等功能。
注意：本项目为教学用途，部分代码存在安全隐患。
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "users.db")


def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_user_profile(user_id):
    """
    根据用户 ID 获取个人资料。

    ============================================================
    VULN-11: 水平越权（IDOR）
    user_id 由客户端传入（URL 参数），后端未校验
    该 ID 是否属于当前登录用户。
    攻击者可遍历 user_id 获取所有用户信息。

    复现方法：
      GET /profile?user_id=1   → 查看自己的
      GET /profile?user_id=2   → 越权查看他人信息
      GET /profile?user_id=3   → ...
    ============================================================
    """
    conn = _get_connection()
    cursor = conn.cursor()
    # 直接使用客户端传入的 user_id，未验证归属
    cursor.execute(f"SELECT id, username, email, phone, role, balance FROM users WHERE id = {user_id}")
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def update_user_profile(user_id, email, phone):
    """
    更新用户资料。

    ============================================================
    VULN-12: 垂直越权
    未校验当前登录用户的角色，普通用户可修改管理员资料。
    user_id 由客户端传入，可越权修改他人信息。
    ============================================================
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE users SET email = '{email}', phone = '{phone}' WHERE id = {user_id}"
    )
    conn.commit()
    conn.close()
    return {"success": True, "message": "更新成功"}


def process_recharge(user_id, amount):
    """
    处理用户充值。

    ============================================================
    VULN-13: 支付逻辑漏洞
    - amount 由客户端传入，未校验正负
    - 攻击者可传入负数实现"盗刷"余额
    - 未做幂等校验，同一请求可重复发送

    复现方法：
      POST /recharge  user_id=1&amount=-10000
      用户 1 的余额将减少 10000（转给了谁？）
    ============================================================
    """
    conn = _get_connection()
    cursor = conn.cursor()
    # 危险！未校验 amount 是否为负数
    cursor.execute(f"UPDATE users SET balance = balance + {amount} WHERE id = {user_id}")
    conn.commit()
    conn.close()
    return {"success": True, "message": f"充值成功，金额: {amount}"}
