# Day 2 - 密码泄露漏洞 完整操作步骤

---

## 课前须知

```
今日漏洞：密码泄露（4个）
今日种子：core/auth.py
今日功能：用户登录
```

---

## Step 1：确认分支

打开终端，输入：

```bash
cd AI-Security-Lab
git branch
```

确保显示：`* 张三-project`（你的名字）

如果不是，先切回来：

```bash
git checkout 张三-project
```

---

## Step 2：导入漏洞种子代码（★ 关键：先于 Claude 生成）

```bash
git checkout origin/day-02 -- core/auth.py
```

然后创建 `core/__init__.py`：

```bash
echo 'from .auth import verify_login, get_user_info, USERS_DB' > core/__init__.py
```

验证种子已导入：

```bash
head -5 core/auth.py
```

应该能看到 `ADMIN_CREDENTIALS` 和 `USERS_DB` 等代码。

---

## Step 3：打开网页版 Claude，发送提示词

打开浏览器 → https://claude.ai → 新建对话

**把以下内容完整复制发给 Claude：**

> 我的本地项目在 `C:/Users/xxx/AI-Security-Lab`（或者你的实际路径），已导入核心认证模块 `core/auth.py`，其中提供了以下可直接调用的函数：
>
> ```python
> def verify_login(username, password):
>     """登录校验，返回 {"success": bool, "user": {...}, "message": "..."}"""
> ```
>
> 请基于这个已有的 `verify_login` 函数，帮我完成登录功能：
>
> 1. 生成登录页面 `templates/login.html`（用户名密码输入框 + 登录按钮）
> 2. 在 `app.py` 中从 `core.auth` 导入 `verify_login`，调用它做登录验证
> 3. 登录成功后 session['username'] = username，跳转首页显示"欢迎回来"
> 4. 登录失败显示错误提示
> 5. 添加登出路由 /logout
> 6. 更新导航栏：未登录显示"登录"，已登录显示"欢迎，用户名"和"退出"
> 7. 首页登录后显示用户信息和操作入口
> 8. 页面用卡片式布局，现代简洁风格

**⚠️ 注意：** 第 2 步（导入种子）**必须先于**第 3 步（发提示词）执行。

---

## Step 4：把 Claude 生成的代码保存到本地

Claude 回复后，把代码复制到对应文件：

| Claude 给的代码 | 保存到 |
|---------------|--------|
| HTML 登录页面 | `templates/login.html` |
| 更新后的导航栏 | `templates/base.html`（覆盖） |
| 更新后的首页 | `templates/index.html`（覆盖） |
| app.py 完整代码 | `app.py`（覆盖） |

确认 `app.py` 中包含了：

```python
from core.auth import verify_login
```

如果 Claude 没写这句，手动加上。

---

## Step 5：运行项目

```bash
python app.py
```

浏览器打开 http://127.0.0.1:5000

可以正常登录：用户名 `admin`，密码 `admin123`

---

## Step 6：发现漏洞

### 漏洞 1：HTML 注释泄露

浏览器右键 → 查看页面源代码 → 找到注释部分

会看到：
```html
<!-- 默认账号: admin / admin123 -->
```

### 漏洞 2：登录响应泄露密码

登录成功后，页面上会直接显示密码。

用 curl 验证：

```bash
curl http://127.0.0.1:5000/login -d "username=admin&password=admin123"
```

搜索 `admin123` 或 `密码泄露`，能看到密码在页面中。

### 漏洞 3：查看源码中的硬编码

打开 `core/auth.py`：

```
第 8-10 行：ADMIN_CREDENTIALS 硬编码
第 15-30 行：USERS_DB 明文存储密码
第 68 行：verify_login 返回的数据中包含 password 字段
```

---

## Step 7：漏洞复现

```bash
# POC 1：HTML 注释泄露
curl http://127.0.0.1:5000/login | grep "admin123"

# POC 2：登录响应含密码
curl http://127.0.0.1:5000/login -d "username=admin&password=admin123" | grep "admin123"
```

---

## Step 8：修复漏洞

创建 `fix/auth_fix.py`：

```python
import hashlib

USERS_DB = {
    "admin": {
        "password": hashlib.sha256(b"admin123").hexdigest(),
        "role": "admin"
    }
}

def verify_login_fixed(username, password):
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    if username in USERS_DB and USERS_DB[username]["password"] == pwd_hash:
        return {"success": True, "user": {"username": username, "role": USERS_DB[username]["role"]}}
    return {"success": False}
```

修改 `app.py` 中的导入：

```python
# 原来的（有漏洞）：
from core.auth import verify_login

# 改为（修复版）：
from fix.auth_fix import verify_login_fixed as verify_login
```

重启项目，验证漏洞无法复现。

---

## Step 9：提交到个人分支

```bash
git add -A
git commit -m "day-02: 实现登录功能，修复密码泄露漏洞"
```

---

## 📋 关键提醒

| 顺序 | 操作 | 在哪儿执行 |
|------|------|-----------|
| 1 | `git branch` 确认分支 | 终端 |
| 2 | **先**导入种子：`git checkout origin/day-02 -- core/auth.py` | 终端 |
| 3 | **再**发提示词给 Claude（告诉它已有 verify_login 函数） | 网页版 Claude |
| 4 | 把 AI 生成的代码保存到本地文件 | VSCode/记事本 |
| 5 | `python app.py` 运行 | 终端 |
| 6 | 找漏洞 | 浏览器 + core/auth.py |
| 7 | 写 `fix/auth_fix.py` | VSCode |
| 8 | 提交 `git commit` | 终端 |

**核心原则：先导入种子，再发提示词。** 顺序反了漏洞就不出现。
