"""
Day 8 - URL 请求模块
负责代理用户请求外部 URL（如头像 URL 抓取）。
注意：本项目为教学用途，部分代码存在安全隐患。
"""

import requests
import os


def fetch_url(target_url):
    """
    抓取指定 URL 的内容。

    ============================================================
    VULN-17: SSRF（服务端请求伪造）
    - 未限制目标 URL 的协议（支持 file://, gopher:// 等）
    - 未阻止内网 IP 访问（可扫描内网 127.0.0.1, 10.x.x.x）
    - 未做 DNS 解析校验（可绕过域名黑名单）

    复现方法 - 内网端口扫描：
      POST /fetch-url  url=http://127.0.0.1:22    → SSH 端口
      POST /fetch-url  url=http://127.0.0.1:3306  → MySQL 端口
      POST /fetch-url  url=http://127.0.0.1:5000  → Flask 自身

    复现方法 - 读取本地文件：
      POST /fetch-url  url=file:///etc/passwd

    复现方法 - 云服务元数据：
      POST /fetch-url  url=http://169.254.169.254/latest/meta-data/
    ============================================================
    """
    try:
        # 危险！未对 URL 做任何过滤和限制
        response = requests.get(target_url, timeout=10)

        return {
            "success": True,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": response.text[:5000]  # 限制返回长度
        }
    except Exception as e:
        return {"success": False, "message": f"请求失败: {str(e)}"}
