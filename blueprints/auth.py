from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template, send_from_directory
import os
import time
from werkzeug.security import generate_password_hash, check_password_hash
import re
from extensions import get_db, check_limit, oauth, HAS_AUTHLIB, ADMIN_EMAIL, AVATAR_FOLDER
from models import UserRepository
from markupsafe import escape
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    if check_limit('heavy'):
        return jsonify({'error': 'Слишком много попыток. Подождите минуту.'}), 429

    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password')
    email = data.get('email')
    
    if not username or not password:
        return jsonify({'error': 'Заполните все поля'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Пароль должен быть не менее 6 символов'}), 400
    
    if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({'error': 'Введите корректный Email адрес'}), 400

    with get_db() as conn:
        if conn.execute('SELECT 1 FROM users WHERE LOWER(username) = ?', (username.lower(),)).fetchone():
            return jsonify({'error': 'Пользователь с таким именем уже существует'}), 400
        
        if email and conn.execute('SELECT 1 FROM users WHERE LOWER(email) = ?', (email.lower(),)).fetchone():
            return jsonify({'error': 'Этот Email уже зарегистрирован'}), 400

        hashed_pw = generate_password_hash(password)
        
        try:
            cursor = conn.execute('INSERT INTO users (username, password, email, created_at) VALUES (?, ?, ?, ?)', (username, hashed_pw, email, datetime.now()))
            conn.commit()
            
            session.permanent = True # Запоминаем пользователя
            session['user_id'] = cursor.lastrowid
            session['username'] = username
            session['avatar_url'] = None
            
            return jsonify({'success': True})
        except Exception as e:
            if "UNIQUE constraint failed" in str(e) or "unique constraint" in str(e):
                return jsonify({'error': 'Пользователь с таким именем уже существует'}), 400
            else:
                return jsonify({'error': f'Ошибка регистрации: {e}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    if check_limit('heavy'):
        return jsonify({'error': 'Слишком много попыток входа. Подождите минуту.'}), 429

    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password')
    
    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE LOWER(username) = ?', (username.lower(),)).fetchone()
    
    if user:
        # Проверка на бан
        if user['banned_until']:
            try:
                ban_end = datetime.fromisoformat(user['banned_until'])
                if ban_end > datetime.now():
                    return jsonify({'error': f'Аккаунт заблокирован до {ban_end.strftime("%d.%m.%Y %H:%M")}'}), 403
            except (ValueError, TypeError): pass

        if check_password_hash(user['password'], password):
            session.permanent = True # Запоминаем пользователя
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['avatar_url'] = user['avatar_url']
            return jsonify({'success': True, 'username': user['username'], 'avatar_url': user['avatar_url']})
            
    return jsonify({'error': 'Неверное имя пользователя или пароль'}), 401

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))

@auth_bp.route('/login/google')
def google_login():
    if not HAS_AUTHLIB:
        return "Ошибка: Библиотека Authlib не установлена на сервере.", 500
    if not oauth:
        return "Ошибка: Вход через Google не настроен на сервере (отсутствуют ключи).", 500
    redirect_uri = url_for('auth.google_authorize', _external=True)
    # Принудительно используем HTTPS, если запрос пришел через защищенное соединение (Render)
    if request.headers.get('X-Forwarded-Proto') == 'https':
        redirect_uri = redirect_uri.replace('http://', 'https://')
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/login/google/callback')
def google_authorize():
    if not HAS_AUTHLIB or not oauth:
        return "Ошибка: Вход через Google не настроен на сервере.", 500
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo')
        if not user_info:
            return "Не удалось получить данные от Google", 400
        
        email = user_info.get('email')
        google_id = user_info.get('sub')
        name = user_info.get('name', email.split('@')[0])
        picture = user_info.get('picture', '')

        with get_db() as conn:
            # Проверяем, есть ли пользователь с таким google_id
            user = conn.execute('SELECT * FROM users WHERE google_id = ?', (google_id,)).fetchone()
            
            # Проверка на бан для Google входа
            if user and user['banned_until']:
                 try:
                    ban_end = datetime.fromisoformat(user['banned_until'])
                    if ban_end > datetime.now():
                        return f"<h1>Доступ запрещен</h1><p>Ваш аккаунт заблокирован до {ban_end.strftime('%d.%m.%Y %H:%M')}</p><a href='/'>На главную</a>", 403
                 except (ValueError, TypeError): pass
            
            if not user:
                session['google_temp_info'] = {
                    'email': email,
                    'google_id': google_id,
                    'picture': picture
                }
                return redirect(url_for('auth.complete_registration_page'))
            
            conn.execute('UPDATE users SET avatar_url = ? WHERE id = ?', (picture, user['id']))
            conn.commit()
            
            session.permanent = True # Запоминаем пользователя
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['avatar_url'] = user['avatar_url']

        return redirect(url_for('main.index'))
    except Exception as e:
        return f"Ошибка авторизации Google: {e}", 500

@auth_bp.route('/complete_registration')
def complete_registration_page():
    if 'google_temp_info' not in session:
        return redirect(url_for('auth.login_page'))
    return render_template('complete_registration.html', email=session['google_temp_info']['email'])

@auth_bp.route('/complete_registration_action', methods=['POST'])
def complete_registration_action():
    if 'google_temp_info' not in session:
        return jsonify({'error': 'Ошибка сессии. Попробуйте войти через Google заново.'}), 400
    
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Заполните все поля'}), 400
        
    google_info = session['google_temp_info']
    
    with get_db() as conn:
        if conn.execute('SELECT 1 FROM users WHERE LOWER(username) = ?', (username.lower(),)).fetchone():
            return jsonify({'error': 'Пользователь с таким именем уже существует'}), 400
            
        if conn.execute('SELECT 1 FROM users WHERE LOWER(email) = ?', (google_info['email'].lower(),)).fetchone():
            return jsonify({'error': 'Пользователь с таким Email уже существует. Попробуйте войти.'}), 400
            
        hashed_pw = generate_password_hash(password)
        
        try:
            cursor = conn.execute('INSERT INTO users (username, password, email, google_id, avatar_url, created_at) VALUES (?, ?, ?, ?, ?, ?)', 
                                  (username, hashed_pw, google_info['email'], google_info['google_id'], google_info['picture'], datetime.now()))
            conn.commit()
            
            session.permanent = True # Запоминаем пользователя
            session['user_id'] = cursor.lastrowid
            session['username'] = username
            session['avatar_url'] = google_info['picture']
            
            session.pop('google_temp_info', None)
            
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': f'Ошибка регистрации: {e}'}), 500

@auth_bp.route('/check_auth')
def check_auth():
    if 'user_id' in session:
        with get_db() as conn:
            user = UserRepository.get_user(session['user_id'])
        is_premium = UserRepository.is_premium(user)
        is_admin = (ADMIN_EMAIL and user and user['email'] == ADMIN_EMAIL)
        return jsonify({'authenticated': True, 'username': session['username'], 'avatar_url': session.get('avatar_url'), 'is_premium': is_premium, 'is_admin': is_admin})
    return jsonify({'authenticated': False})

@auth_bp.route('/login_page')
def login_page():
    return render_template('auth.html', mode='login')

@auth_bp.route('/register_page')
def register_page():
    return render_template('auth.html', mode='register')

@auth_bp.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    
    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if not user:
        return redirect(url_for('auth.logout'))

    is_admin = (ADMIN_EMAIL and user['email'] and str(user['email']).strip().lower() == str(ADMIN_EMAIL).strip().lower())
    is_premium = UserRepository.is_premium(user)
    
    premium_until_date = None
    if is_premium and not is_admin and user['premium_until']:
        try:
            expiry = datetime.fromisoformat(user['premium_until'])
            if expiry > datetime.now():
                premium_until_date = expiry.strftime('%d.%m.%Y')
        except (ValueError, TypeError): pass

    return render_template('profile.html', username=user['username'], avatar_url=user['avatar_url'], email=user['email'], google_id=user['google_id'], is_premium=is_premium, premium_until=premium_until_date, is_admin=is_admin)

@auth_bp.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    data = request.json
    new_avatar = data.get('avatar_url', '').strip()
    
    with get_db() as conn:
        conn.execute('UPDATE users SET avatar_url = ? WHERE id = ?', (new_avatar, session['user_id']))
        conn.commit()
    
    session['avatar_url'] = new_avatar
    return jsonify({'success': True})

@auth_bp.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    user_id = session['user_id']
    
    try:
        with get_db() as conn:
            user_data = conn.execute('SELECT avatar_url FROM users WHERE id = ?', (user_id,)).fetchone()
            if user_data and user_data['avatar_url'] and '/avatars/' in user_data['avatar_url']:
                try:
                    fname = user_data['avatar_url'].split('/')[-1]
                    fpath = os.path.join('avatars', fname)
                    if os.path.exists(fpath): os.remove(fpath)
                except Exception: pass
                
            conn.execute('DELETE FROM history WHERE user_id = ?', (user_id,))
            conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
        session.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': f"Ошибка удаления: {e}"}), 500

@auth_bp.route('/avatars/<filename>')
def uploaded_avatar(filename):
    return send_from_directory(os.path.abspath(AVATAR_FOLDER), filename)

@auth_bp.route('/upload_avatar', methods=['POST'])
def upload_avatar():
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    if 'avatar' not in request.files:
        return jsonify({'error': 'Файл не выбран'}), 400
    
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400
        
    if file:
        # Проверка размера файла (макс. 2 МБ)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > 2 * 1024 * 1024: # 2 МБ
            return jsonify({'error': 'Размер файла превышает 2 МБ'}), 400

        ext = os.path.splitext(file.filename)[1]
        if ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
             return jsonify({'error': 'Разрешены только изображения'}), 400

        header = file.read(512)
        file.seek(0)
        if not (header.startswith(b'\xff\xd8') or header.startswith(b'\x89PNG') or header.startswith(b'GIF8') or header.startswith(b'RIFF') and b'WEBP' in header):
             return jsonify({'error': 'Недопустимый формат файла'}), 400

        try:
            with get_db() as conn:
                old_user = conn.execute('SELECT avatar_url FROM users WHERE id = ?', (session['user_id'],)).fetchone()
                if old_user and old_user['avatar_url'] and '/avatars/' in old_user['avatar_url']:
                    old_filename = old_user['avatar_url'].split('/')[-1]
                    old_path = os.path.join(AVATAR_FOLDER, old_filename)
                    if os.path.exists(old_path): os.remove(old_path)
        except Exception: pass

        filename = f"user_{session['user_id']}_{int(time.time())}{ext}"
        filepath = os.path.join(AVATAR_FOLDER, filename)
        file.save(filepath)
        
        avatar_url = url_for('auth.uploaded_avatar', filename=filename, _external=True)
        
        with get_db() as conn:
            conn.execute('UPDATE users SET avatar_url = ? WHERE id = ?', (avatar_url, session['user_id']))
            conn.commit()
        
        session['avatar_url'] = avatar_url
        return jsonify({'success': True, 'avatar_url': avatar_url})
        
    return jsonify({'error': 'Ошибка загрузки'}), 500
