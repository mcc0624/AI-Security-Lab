"""
Day 7 - 密码管理模块
负责用户密码修改功能。
注意：本项目为教学用途，部分代码存在安全隐患。
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "users.db")


def change_password(username, new_password):
    """
    修改用户密码。

    ============================================================
    VULN-16: CSRF（跨站请求伪造）
    - 无 CSRF Token：请求中没有任何防跨站的 token 校验
    - 仅依赖 Cookie 自动携带：浏览器在跨站请求时自动带 Cookie
    - 无原密码验证：修改密码不需要确认旧密码
    - 支持 GET 请求修改（如果路由配置为 GET+POST）

    复现方法：
      1. 用户已登录（有 Cookie）
      2. 访问攻击者构造的恶意页面
      3. 恶意页面自动提交表单：
         <form action="http://target/change-password" method="POST">
           <input name="new_password" value="hacked">
         </form>
         <script>document.forms[0].submit();</script>
      4. 用户的密码被静默修改
    ============================================================
    """
    # 同时更新数据库和内存中的用户存储

    # 更新内存存储（auth.py 中的 USERS_DB）
    from core.auth import USERS_DB
    if username in USERS_DB:
        USERS_DB[username]["password"] = new_password

    # 更新数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 危险！直接修改密码，无任何二次验证
    cursor.execute(f"UPDATE users SET password = '{new_password}' WHERE username = '{username}'")
    conn.commit()
    conn.close()
    return {"success": True, "message": "密码修改成功"}
