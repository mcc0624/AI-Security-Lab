"""简易用户信息管理平台 - 基础框架"""
from flask import Flask, render_template, session, redirect, request, flash

app = Flask(__name__)
app.secret_key = 'dev-secret-key-2025'


# ────────────────────────────── 认证模块 ──────────────────────────────
def check_login(username: str, password: str) -> bool:
    """校验用户名/密码。

    占位实现 —— 导入核心认证模块后可替换此函数。
    返回 True 表示验证通过，否则返回 False。
    """
    # TODO: 从核心认证模块导入真实校验逻辑
    # from core_auth import authenticate
    # return authenticate(username, password)
    #
    # 下方为演示用临时账号，上线前请移除。
    DEMO_USERS = {
        "admin": "admin123",
        "user":  "pass123",
    }
    return username in DEMO_USERS and DEMO_USERS[username] == password


# ────────────────────────────── 路由 ──────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            return render_template('login.html', error='用户名和密码不能为空')

        if check_login(username, password):
            session['username'] = username
            flash(f'欢迎回来，{username}！', 'success')
            return redirect('/')
        else:
            return render_template('login.html', error='用户名或密码错误，请重试')

    # GET 请求：如果已登录则跳转首页
    if session.get('username'):
        return redirect('/')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('您已成功退出登录', 'info')
    return redirect('/')


# ────────────────────────────── 启动入口 ──────────────────────────────

if __name__ == '__main__':
    print("=" * 50)
    print("  简易用户信息管理平台 已启动")
    print("  访问地址: http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
