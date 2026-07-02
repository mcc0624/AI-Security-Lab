"""简易用户信息管理平台 - 基础框架"""
from flask import Flask, render_template, session, redirect

app = Flask(__name__)
app.secret_key = 'dev-secret-key-2025'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    print("=" * 50)
    print("  简易用户信息管理平台 已启动")
    print("  访问地址: http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
