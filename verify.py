"""
验证脚本 - 检查 core/ 目录完整性及答案验证
学生完成每日漏洞修复后运行此脚本验证修复是否成功。
"""

import hashlib
import json
import os
import sys

# ============================================================
# 第一部分: core/ 完整性检查
# 确保核心漏洞模块未被修改（学生应修复 fix/ 而非 core/）
# ============================================================

EXPECTED_HASHES = {}

def compute_file_hash(filepath):
    """计算文件的 SHA256 哈希值。"""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def check_core_integrity():
    """检查 core/ 目录下所有文件的完整性。"""
    core_dir = os.path.join(os.path.dirname(__file__), 'core')
    if not os.path.exists(core_dir):
        print("❌ core/ 目录不存在！")
        return False

    all_ok = True
    files_checked = 0

    for filename in sorted(os.listdir(core_dir)):
        if filename.endswith('.py'):
            filepath = os.path.join(core_dir, filename)
            if filename == '__init__.py':
                continue  # __init__.py 可被安全扩展
            current_hash = compute_file_hash(filepath)
            expected = EXPECTED_HASHES.get(filename)
            if expected and current_hash != expected:
                print(f"⚠️  {filename}: 已被修改！")
                print(f"   期望: {expected[:16]}...")
                print(f"   当前: {current_hash[:16]}...")
                print(f"   提示: 修复应在 fix/ 目录中进行，而非修改 core/")
                all_ok = False
            else:
                print(f"✅ {filename}: 完整")
            files_checked += 1

    if all_ok:
        print(f"\n✅ core/ 完整性检查通过 ({files_checked} 个文件)")
    else:
        print(f"\n❌ core/ 完整性检查失败 - 某些文件已被修改")

    return all_ok


# ============================================================
# 第二部分: 漏洞验证 (由老师按天配置)
# ============================================================

def test_sql_injection():
    """测试 Day 3 SQL 注入漏洞是否已修复。"""
    print("\n--- Day 3: SQL 注入验证 ---")
    # 此测试需要应用在运行中
    print("   请在应用运行后，用以下 payload 测试登录:")
    print("   用户名: admin' OR '1'='1")
    print("   密码:   任意")
    print("   如果登录成功 → 漏洞仍存在")
    print("   如果登录失败 → 漏洞已修复")


def test_csrf():
    """测试 Day 7 CSRF 漏洞是否已修复。"""
    print("\n--- Day 7: CSRF 验证 ---")
    print("   检查密码修改请求是否包含 CSRF Token:")


# ============================================================
# 主函数
# ============================================================

if __name__ == '__main__':
    print("=" * 55)
    print("  简易用户信息管理平台 - 验证工具")
    print("=" * 55)

    print("\n[1/2] 检查 core/ 完整性...")
    integrity_ok = check_core_integrity()

    print("\n[2/2] 漏洞验证指引...")
    test_sql_injection()
    test_csrf()

    print("\n" + "=" * 55)
    if integrity_ok:
        print("  验证完成: core/ 模块完整")
    else:
        print("  验证完成: 部分文件已被修改")
    print("=" * 55)
