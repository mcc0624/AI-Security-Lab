"""
Day 3 - 数据库操作模块
负责用户数据的持久化存储与查询。
注意：本项目为教学用途，部分代码存在安全隐患。
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "users.db")


def get_db_connection():
    """获取数据库连接。"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    return conn


def init_db():
    """初始化数据库表结构。"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            role TEXT DEFAULT 'user',
            balance REAL DEFAULT 0
        )
    """)
    # 插入默认用户（如已存在则忽略）
    default_users = [
        ("admin", "admin123", "admin@example.com", "13800138000", "admin", 99999),
        ("alice", "alice2025", "alice@example.com", "13900139001", "user", 100),
        ("bob", "bob666666", "bob@example.com", "13900139002", "user", 50),
    ]
    for u in default_users:
        try:
            cursor.execute(
                "INSERT INTO users (username, password, email, phone, role, balance) VALUES (?, ?, ?, ?, ?, ?)",
                u
            )
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()


def query_users(username, password):
    """
    根据用户名和密码查询用户（用于登录）。

    ============================================================
    VULN-05: SQL 注入 - 字符串拼接查询
    直接将用户输入拼接到 SQL 语句中，攻击者可通过
    注入 ' OR '1'='1 等 payload 绕过登录验证。

    复现方法：
      用户名: admin' OR '1'='1
      密码:  任意
    ============================================================
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    # 危险！直接字符串拼接 SQL 查询
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    print(f"[DEBUG] 执行查询: {query}")  # 调试日志，方便观察注入效果
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return result


def search_users(keyword):
    """
    根据关键词搜索用户。

    ============================================================
    VULN-06: SQL 注入 - 搜索功能
    使用字符串拼接构建 LIKE 查询，攻击者可进行
    盲注或 UNION 注入获取数据库全部数据。

    复现方法：
      关键词: ' UNION SELECT * FROM users --
    ============================================================
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    # 危险！直接拼接
    query = f"SELECT * FROM users WHERE username LIKE '%{keyword}%' OR email LIKE '%{keyword}%'"
    print(f"[DEBUG] 执行查询: {query}")
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results


def add_user(username, password, email, phone):
    """
    添加新用户。

    ============================================================
    VULN-07: SQL 注入 - 注册功能
    注册时用户名未做过滤，可注入恶意 SQL。
    利用堆叠查询可在注册的同时修改其他数据。

    复现方法：
      用户名: hacker', 'pass', 'h@x.com', '123'); DELETE FROM users; --
    ============================================================
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    # 危险！直接拼接 INSERT 语句
    query = f"INSERT INTO users (username, password, email, phone) VALUES ('{username}', '{password}', '{email}', '{phone}')"
    print(f"[DEBUG] 执行查询: {query}")
    cursor.execute(query)
    conn.commit()
    conn.close()
    return cursor.lastrowid
