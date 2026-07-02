"""简易用户信息管理平台 - Day 3"""
from flask import Flask, request, render_template, redirect, session
from core.auth import verify_login
from core.database import query_users, search_users, add_user, init_db

app = Flask(__name__)
app.secret_key = 'dev-secret-key-2025'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        result = verify_login(username, password)
        if result['success']:
            session['username'] = username
            session['role'] = result['user'].get('role', 'user')
            return render_template('index.html', user_info=result['user'])
        else:
            return render_template('login.html', error=result['message'])
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        try:
            add_user(username, password, email, phone)
            return render_template('login.html', message='注册成功，请登录')
        except Exception as e:
            return render_template('register.html', error=f'注册失败: {str(e)}')
    return render_template('register.html')

@app.route('/search')
def search():
    keyword = request.args.get('keyword', '')
    results = search_users(keyword)
    return render_template('index.html', search_results=results)

if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("  Day 3 - 简易用户信息管理平台")
    print("  访问地址: http://127.0.0.1:5000")
    print("  默认账号: admin / admin123")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
