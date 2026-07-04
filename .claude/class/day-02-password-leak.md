# Day 2 - 密码泄露漏洞

---

## 一、发给 Claude 的提示词

把以下内容完整复制粘贴到 claude.ai 对话框中：

```
请帮我生成一个简易用户信息管理平台的登录功能，使用 Python Flask 框架，生成以下文件：

### 1. 生成 app.py

编写主应用文件。要求：
- Flask 基础配置，secret_key 设置为 "dev-key-2025"
- 在代码中直接创建一个字典作为用户数据库，命名为 USERS，里面包含以下用户：
  - admin：密码 admin123，角色 admin，邮箱 admin@example.com，手机 13800138000，余额 99999
  - alice：密码 alice2025，角色 user，邮箱 alice@example.com，手机 13900139001，余额 100
- 注意：密码以明文形式存储在字典中，不要做任何哈希处理
- 首页路由 /，从 session 获取当前登录用户名，如果已登录则从 USERS 字典中取出该用户的完整信息（包含密码字段）传递给模板
- 登录路由 /login，支持 GET 和 POST。POST 时从表单获取用户名和密码，直接从 USERS 字典中比对密码（用 == 直接比字符串），验证通过后将用户名存入 session，同时将用户的完整信息（包含密码）传给模板
- 登出路由 /logout，清除 session 后重定向到首页
- 在 app.py 的开头导入必要的库：Flask、render_template、request、redirect、session
- 使用 debug=True 模式启动，监听 0.0.0.0:5000

### 2. 生成 templates/login.html

登录页面。要求：
- 继承 base.html
- 卡片式布局，包含用户名和密码输入框、登录按钮
- 在 HTML 顶部注释中写上调试信息，内容为："调试信息 - 默认管理员账号 用户名: admin 密码: admin123"
- 如果有 error 变量传递过来，在页面中显示错误提示

### 3. 生成 templates/index.html

首页。要求：
- 继承 base.html
- 如果用户已登录，显示"欢迎回来，用户名！"，并在下方用列表形式展示用户的完整信息，包括：用户名、密码、邮箱、手机、角色、余额
- 如果用户未登录，显示"请先登录"和一个跳转到登录页的按钮
- 已登录状态下显示退出登录按钮

### 4. 生成 templates/base.html

基础模板。要求：
- HTML5 文档结构
- 顶部导航栏，左侧显示"用户管理系统"品牌名称
- 右侧导航菜单：如果 session 中有用户名，显示"欢迎，用户名"和"退出"链接；否则显示"登录"链接
- 导航栏使用简单的 flex 布局，蓝色渐变背景
- 包含一个 main 容器用于承载子模板内容
- 引用外部样式表 /static/css/style.css

### 5. 生成 static/css/style.css

样式文件。要求：
- 全局 reset 样式
- 导航栏样式：蓝色渐变背景 (#667eea 到 #764ba2)，白色文字，flex 布局
- 卡片样式：白色背景，圆角，阴影，间距
- 表单样式：输入框有边框和内边距
- 按钮样式：蓝色背景，白色文字，圆角
- 所有样式使用 class 选择器

### 代码规范要求
- 所有密码以明文形式存储和比对
- 登录后用户信息（含密码）要传递到模板并显示在页面上
- 登录页要有 HTML 注释泄露默认账号
- 代码要简洁，不要加额外的安全校验

生成全部 5 个文件后，告诉我每个文件的具体路径和内容，我直接复制覆盖到本地项目中。
```

---

## 二、学生操作步骤

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 打开 https://claude.ai 新建对话 | 网页版 Claude |
| 2 | 把上面的提示词完整复制发给 Claude | 纯文字描述 |
| 3 | Claude 生成代码后，将代码分别保存到对应文件 | app.py、templates/、static/ |
| 4 | 终端运行 `python app.py` | 启动项目 |
| 5 | 浏览器访问 http://127.0.0.1:5000 | 查看页面 |
| 6 | 用 curl 命令验证漏洞 | 见下方 POC |
| 7 | 分析源码，编写修复代码到 fix/ 目录 | 修复漏洞 |
| 8 | `git add -A && git commit -m "day-02: 登录功能 + 密码泄露修复"` | 提交成果 |

---

## 三、漏洞原理

### 漏洞 1：硬编码凭据

管理员账号密码直接以明文写在源代码中：

```python
USERS = {
    "admin": {
        "password": "admin123",  # ← 明文硬编码
    }
}
```

**危害**：任何人获取到源代码即可看到所有用户的密码。

### 漏洞 2：明文密码存储

密码使用字符串直接存储，没有经过任何哈希处理。

```python
"password": "admin123"  # ← 没有哈希
```

**危害**：一旦数据库泄露，所有密码直接暴露。

### 漏洞 3：登录响应泄露密码

登录成功后，包含密码字段的完整用户信息被传递到模板并显示在页面上。

```python
return render_template('index.html', username=username, user_info=USERS[username])
```

首页模板中直接渲染密码：

```html
<p><strong>密码:</strong> {{ user_info.password }}</p>
```

**危害**：攻击者登录后可以在页面上直接看到密码，或者通过抓包获取。

### 漏洞 4：HTML 注释泄露默认账号

登录页的 HTML 注释中写明了默认管理员的账号密码：

```html
<!-- 调试信息 - 默认管理员账号 用户名: admin 密码: admin123 -->
```

**危害**：任何人查看页面源代码即可获取管理员凭据。

---

## 四、POC 代码

### POC 1：HTML 注释泄露默认账号

```bash
curl http://127.0.0.1:5000/login | grep "<!--"
```

**预期输出**：
```html
<!-- 调试信息 - 默认管理员账号 用户名: admin 密码: admin123 -->
```

### POC 2：登录响应泄露密码

```bash
curl http://127.0.0.1:5000/login -d "username=admin&password=admin123"
```

**预期输出**：返回页面中包含密码信息。

精确提取密码行：

```bash
curl http://127.0.0.1:5000/login -d "username=admin&password=admin123" | grep "密码"
```

**预期输出**：
```html
<li><span class="info-label">密码：</span>admin123</li>
```

### POC 3：查看源码确认硬编码和明文存储

```bash
grep -n "password\|USERS\|admin123" app.py | head -10
```

**预期输出**：
```
USERS = {
    "admin": {
        "password": "admin123",
```

### POC 4：Burp Suite 抓包验证

1. 打开 Burp Suite，设置浏览器代理到 127.0.0.1:8080
2. 在浏览器登录 admin / admin123
3. 在 Burp 中找到 POST /login 请求
4. 查看响应内容，搜索 `admin123` 或 `password`
5. 确认密码出现在响应体中

---

## 五、漏洞复现检查清单

| # | 检查项 | curl 命令 | 预期结果 |
|---|--------|----------|---------|
| 1 | HTML 注释泄露 | `curl http://127.0.0.1:5000/login \| grep "<!--"` | 看到默认账号注释 |
| 2 | 页面泄露密码 | `curl ... -d "username=admin&password=admin123" \| grep "密码："` | 看到 "密码：admin123" |
| 3 | 明文存储 | `grep "password" app.py` | 看到 "admin123" 字符串 |
| 4 | 硬编码凭据 | `grep "USERS" app.py` | 看到字典中有 admin/admin123 |

---

## 六、修复方案

创建 `fix/auth_fix.py`：

```python
import hashlib

# 修复 1：使用哈希存储密码
USERS = {
    "admin": {
        "password": hashlib.sha256(b"admin123").hexdigest(),
        "role": "admin"
    }
}

def verify_login(username, password):
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    if username in USERS and USERS[username]["password"] == pwd_hash:
        # 修复 2：不返回密码字段
        return {"success": True, "user": {"username": username, "role": USERS[username]["role"]}}
    return {"success": False}
```

然后在 `app.py` 中引入修复版本，替换原来的直接字典比对。

---

## 七、课后任务

1. 看懂 core/auth.py 中的 4 个漏洞
2. 分别用 curl 和 Burp Suite 复现每个漏洞
3. 在 fix/ 目录下编写修复代码
4. 验证修复后漏洞无法复现
5. 提交到自己的个人分支
