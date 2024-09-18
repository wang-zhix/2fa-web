from flask import Flask, render_template, request, redirect, flash
import cv2
import numpy as np
import pyotp
from pyzbar.pyzbar import decode
from PIL import Image
import re
import sqlite3
from urllib.parse import urlparse, parse_qs
import time

app = Flask(__name__)
DATABASE = '2fa.db'


# 创建数据库和表
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                issuer TEXT NOT NULL,
                oricode TEXT NOT NULL,
                secret TEXT NOT NULL
            )
        ''')
        conn.commit()

# 插入数据
def insert_user(username, issuer, oricode, secret):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, issuer, oricode, secret)
            VALUES (?,?,?,?)
        ''', (username, issuer, oricode, secret))
        conn.commit()

# 查询数据
def query_user(username):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM users WHERE username=?
        ''', (username,))
        result = cursor.fetchall()
        if result is None:
            return None
        else:
            return result

def get_secret(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get('secret', [None])[0]


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return '未选择文件'

    username = request.form['username']
    issuer = request.form['issuer']
    input_secret = request.form['secret']
    file = request.files['file']
    
    if input_secret != '':
        insert_user(username, issuer, "input_secret", secret)
        return '上传成功'
    
    if file.filename == '':
        return '未选择文件'
    try:
        img = Image.open(file.stream)
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        decoded_objects = decode(img_cv)
        if decoded_objects:
            qr_result = '<br>'.join([obj.data.decode('utf-8') for obj in decoded_objects])
            print(f"qr_result:{qr_result}")
            secret = get_secret(qr_result)
            if secret is None:
                return '二维码未解析出secret'
            # totp = pyotp.TOTP(secret)
            # current_otp = totp.now()
            insert_user(username, issuer, qr_result, secret)
            return '上传成功'
        else:
            return '解析二维码失败'
    except Exception as e:
        return '解析二维码失败'

@app.route('/download', methods=['POST'])
def download():
    username = request.form['username']
    userdatas = query_user(username)
    
    current_time = time.time()
    valid_period_seconds = 30
    # 剩余有效时间
    use_seconds = current_time % valid_period_seconds
    remaining_seconds = valid_period_seconds - use_seconds
    start_time = current_time - use_seconds
    end_time = start_time + valid_period_seconds
    start_time_readable = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))
    end_time_readable = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))
    remaining_time_readable = '剩余时间：' + str(int(remaining_seconds)) + '秒'
    otp_dict = {'st': start_time_readable, 'et': end_time_readable, 'rt': remaining_time_readable}
    for userdata in userdatas:
        issuer = userdata[2]
        oricode = userdata[3]
        secret = userdata[4]
        totp = pyotp.TOTP(secret)
        current_otp = totp.now()
        otp_dict[issuer] = current_otp
        print(issuer, current_otp)
    return str(otp_dict)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=2063)
