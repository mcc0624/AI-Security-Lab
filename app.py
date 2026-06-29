"""
简易用户信息管理平台 - 主应用入口
AI+安全实训项目

本文件是应用的主路由配置。学生可以在此添加新的路由，
但不应删除或修改 core/ 中已导入的功能模块。
"""

import os
import sys
from flask import (
    Flask, request, render_template, redirect,
    session, jsonify, flash
)

# ===== 从核心模块导入功能 =====
# 这些模块来自 core/ 目录，包含课程各天对应的漏洞代码
# 学生可以增加新的导入，但不要删除现有导入
from core.auth import verify_login, get_user_info
from core.database import query_users, search_users, add_user, init_db
from core.file_handler import handle_file_upload
from core.user_service import get_user_profile, update_user_profile, process_recharge
from core.page_loader import load_page
from core.password_manager import change_password
from core.url_fetcher import fetch_url
from core.command_runner import run_ping
from core.xml_processor import parse_xml_data

app = Flask(__name__)

# ============================================================
# VULN: 硬编码 Secret Key
# Flask 的 session 使用此密钥进行签名。
# 源码泄露后攻击者可伪造任意 session。
# ============================================================
app.secret_key = 'dev-secret-key-2025-do-not-use-in-production'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB


# ===================================================================
#  首页
# ===================================================================
@app.route('/')
def index():
    return render_template('index.html')


# ===================================================================
#  Day 2: 用户登录 / 登出
#  对应漏洞: 密码泄露
# ===================================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        result = verify_login(username, password)
        if result['success']:
            session['username'] = username
            session['role'] = result['user'].get('role', 'user')
            # VULN: 登录成功后将包含密码的用户信息传递到模板
            # 会在 HTML 中泄露用户密码
            return render_template('index.html', user_info=result['user'])
        else:
            return render_template('login.html', error=result['message'])
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ===================================================================
#  Day 3: 用户注册 + SQL 注入漏洞
#  对应漏洞: SQL 注入
# ===================================================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        try:
            # 调用 core/database.py 中带 SQL 注入漏洞的函数
            user_id = add_user(username, password, email, phone)
            return render_template('login.html', message='注册成功，请登录')
        except Exception as e:
            return render_template('register.html', error=f'注册失败: {str(e)}')
    return render_template('register.html')


@app.route('/search')
def search():
    keyword = request.args.get('keyword', '')
    # 调用 core/database.py 中带 SQL 注入漏洞的搜索函数
    results = search_users(keyword)
    return render_template('index.html', search_results=results)


# ===================================================================
#  Day 4: 文件上传
#  对应漏洞: 任意文件上传
# ===================================================================
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        return redirect('/login')
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('upload.html', error='未选择文件')
        file = request.files['file']
        result = handle_file_upload(file)
        if result['success']:
            return render_template('upload.html', file_url=result['file_url'])
        else:
            return render_template('upload.html', error=result['message'])
    return render_template('upload.html')


# ===================================================================
#  Day 5: 个人中心 / 充值
#  对应漏洞: 水平越权 + 支付逻辑漏洞
# ===================================================================
@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect('/login')
    # VULN: user_id 从 URL 参数获取，可越权查看他人信息
    user_id = request.args.get('user_id', '1')
    profile_data = get_user_profile(user_id)
    return render_template('profile.html', profile=profile_data)


@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'username' not in session:
        return redirect('/login')
    user_id = request.form.get('user_id', '1')
    email = request.form.get('email', '')
    phone = request.form.get('phone', '')
    result = update_user_profile(user_id, email, phone)
    return redirect('/profile?user_id=' + user_id)


@app.route('/recharge', methods=['POST'])
def recharge():
    if 'username' not in session:
        return redirect('/login')
    user_id = request.form.get('user_id', '1')
    amount = request.form.get('amount', '0')
    result = process_recharge(user_id, amount)
    return redirect('/profile?user_id=' + user_id)


# ===================================================================
#  Day 6: 动态页面加载
#  对应漏洞: 本地文件包含 (LFI)
# ===================================================================
@app.route('/page')
def page():
    name = request.args.get('name', 'help')
    result = load_page(name)
    if result['success']:
        return render_template('index.html', page_content=result['content'])
    else:
        return render_template('index.html', page_error=result['message'])


# ===================================================================
#  Day 7: 密码修改
#  对应漏洞: CSRF
# ===================================================================
@app.route('/change-password', methods=['POST'])
def change_user_password():
    if 'username' not in session:
        return redirect('/login')
    username = request.form.get('username', session.get('username', ''))
    new_password = request.form.get('new_password', '')
    result = change_password(username, new_password)
    return redirect('/profile')


# ===================================================================
#  Day 8: URL 请求
#  对应漏洞: SSRF
# ===================================================================
@app.route('/fetch-url', methods=['POST'])
def fetch_url_route():
    if 'username' not in session:
        return redirect('/login')
    target_url = request.form.get('url', '')
    result = fetch_url(target_url)
    return render_template('index.html', fetch_result=result)


# ===================================================================
#  Day 9: Ping 命令
#  对应漏洞: 命令注入
# ===================================================================
@app.route('/ping', methods=['GET', 'POST'])
def ping():
    if 'username' not in session:
        return redirect('/login')
    if request.method == 'POST':
        ip = request.form.get('ip', '127.0.0.1')
        result = run_ping(ip)
        if result['success']:
            return render_template('ping.html', output=result['output'])
        else:
            return render_template('ping.html', error=result['message'])
    return render_template('ping.html')


# ===================================================================
#  Day 10: XML 数据导入
#  对应漏洞: XXE
# ===================================================================
@app.route('/xml-import', methods=['GET', 'POST'])
def xml_import():
    if 'username' not in session:
        return redirect('/login')
    if request.method == 'POST':
        xml_data = request.form.get('xml_data', '')
        result = parse_xml_data(xml_data)
        import json
        return render_template('xml_import.html', result=json.dumps(result, ensure_ascii=False, indent=2))
    return render_template('xml_import.html')


# ===================================================================
#  初始化数据库 + 启动
# ===================================================================
if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("  简易用户信息管理平台 已启动")
    print("  访问地址: http://127.0.0.1:5000")
    print("  默认账号: admin / admin123")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
