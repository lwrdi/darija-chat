from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# إعداد قاعدة البيانات MongoDB Atlas
app.config["MONGO_URI"] = os.environ.get('MONGODB_URI', 'mongodb+srv://your-mongodb-uri')
mongo = PyMongo(app)

# الصفحة الرئيسية
@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('chat'))
    return render_template('index.html')

# تسجيل مستخدم جديد
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'username': request.form['username']})

        if existing_user is None:
            hashpass = generate_password_hash(request.form['password'])
            users.insert_one({
                'username': request.form['username'],
                'password': hashpass,
                'email': request.form['email'],
                'created_at': datetime.now()
            })
            session['username'] = request.form['username']
            return redirect(url_for('chat'))
        
        return 'اسم المستخدم موجود بالفعل!'
    
    return render_template('register.html')

# تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = mongo.db.users
        login_user = users.find_one({'username': request.form['username']})

        if login_user:
            if check_password_hash(login_user['password'], request.form['password']):
                session['username'] = request.form['username']
                return redirect(url_for('chat'))
        
        return 'كلمة المرور أو اسم المستخدم غير صحيح'
    
    return render_template('login.html')

# تسجيل الخروج
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

# صفحة المحادثة
@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', username=session['username'])

# إرسال رسالة
@app.route('/send_message', methods=['POST'])
def send_message():
    if 'username' not in session:
        return jsonify({'error': 'يجب تسجيل الدخول أولاً'})
    
    data = request.json
    messages = mongo.db.messages
    
    message = {
        'username': session['username'],
        'content': data['message'],
        'timestamp': datetime.now()
    }
    
    messages.insert_one(message)
    return jsonify({'status': 'success'})

# الحصول على الرسائل
@app.route('/get_messages')
def get_messages():
    if 'username' not in session:
        return jsonify({'error': 'يجب تسجيل الدخول أولاً'})
    
    messages = mongo.db.messages.find().sort('timestamp', -1).limit(50)
    return jsonify([{
        'username': msg['username'],
        'content': msg['content'],
        'timestamp': msg['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
    } for msg in messages])

if __name__ == '__main__':
    app.run(debug=True)
