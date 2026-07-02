"""简易用户信息管理平台 - Day 2"""
from flask import Flask, request, render_template, redirect, session
from core.auth import verify_login

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
            return render_template('index.html', user_info=result['user'])
        else:
            return render_template('login.html', error=result['message'])
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    print("=" * 50)
    print("  Day 2 - 简易用户信息管理平台")
    print("  访问地址: http://127.0.0.1:5000")
    print("  默认账号: admin / admin123")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
