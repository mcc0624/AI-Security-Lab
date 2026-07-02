"""简易用户信息管理平台 - Day 6"""
from flask import Flask, request, render_template, redirect, session
from core.auth import verify_login
from core.database import add_user, search_users, init_db
from core.file_handler import handle_file_upload
from core.user_service import get_user_profile, update_user_profile, process_recharge
from core.page_loader import load_page
from core.password_manager import change_password
from core.url_fetcher import fetch_url

app = Flask(__name__)
app.secret_key = 'dev-secret-key-2025'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

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

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect('/login')
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

@app.route('/page')
def page():
    name = request.args.get('name', 'help')
    result = load_page(name)
    if result['success']:
        return render_template('index.html', page_content=result['content'])
    else:
        return render_template('index.html', page_error=result['message'])

@app.route('/change-password', methods=['POST'])
def change_user_password():
    if 'username' not in session:
        return redirect('/login')
    username = request.form.get('username', session.get('username', ''))
    new_password = request.form.get('new_password', '')
    result = change_password(username, new_password)
    return redirect('/profile')

@app.route('/fetch-url', methods=['POST'])
def fetch_url_route():
    if 'username' not in session:
        return redirect('/login')
    target_url = request.form.get('url', '')
    result = fetch_url(target_url)
    return render_template('index.html', fetch_result=result)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
