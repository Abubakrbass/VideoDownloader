try:
    # --- НАСТРОЙКА ОКРУЖЕНИЯ (FFMPEG) ---
    # Запускаем ДО eventlet, чтобы избежать ошибки "blocking functions from mainloop" при скачивании
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception as e:
    print(f"static-ffmpeg ошибка или не найден: {e}")

try:
    import eventlet
    import os
    # На Windows eventlet ломает DNS (requests), поэтому патчим только на Linux (Render)
    if os.name != 'nt':
        eventlet.monkey_patch()
except ImportError:
    pass

import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

# Импорт расширений из extensions.py
from extensions import (
    get_db, init_db, limiter, check_limit, task_manager,
    socketio, oauth, HAS_AUTHLIB, ADMIN_EMAIL, csrf
)
from models import UserRepository

# Импорт блюпринтов
from blueprints.auth import auth_bp
from blueprints.main import main_bp
from blueprints.payment import payment_bp
from blueprints.feedback import feedback_bp
from blueprints.download import download_bp
from blueprints.history import history_bp
from blueprints.notification import notification_bp
from blueprints.admin import admin_bp

# Настройка логирования вместо принтов
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Загружаем переменные из файла .env
load_dotenv()

# Восстановление cookies.txt из переменных окружения (для Render)
COOKIES_CONTENT = os.getenv('COOKIES_CONTENT')
if COOKIES_CONTENT:
    cookies_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies.txt')
    # Всегда перезаписываем файл, чтобы использовать актуальные куки из ENV
    with open(cookies_path, 'w', encoding='utf-8') as f:
        f.write(COOKIES_CONTENT)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(feedback_bp)
app.register_blueprint(download_bp)
app.register_blueprint(history_bp)
app.register_blueprint(notification_bp)
app.register_blueprint(admin_bp)

socketio.init_app(app)

# Включаем CSRF защиту
csrf.init_app(app)

# --- БЕЗОПАСНОСТЬ СЕССИЙ ---
# Ключ берется из .env. Если его нет, генерируем и сохраняем в файл, чтобы сессии не слетали при перезапуске.
app.secret_key = os.getenv('SECRET_KEY', 'fallback_fixed_secret_key_for_render_12345')

# Настройки Cookie для защиты от взлома
app.config['SESSION_COOKIE_HTTPONLY'] = True # Защита от XSS (JS не видит куки)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' # Защита от CSRF
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365) # Запоминать пользователя на 1 год
# SESSION_COOKIE_SECURE включится автоматически на HTTPS (Render/Heroku)

# --- Проверка бана перед КАЖДЫМ запросом ---
@app.before_request
def check_ban_status():
    if 'user_id' in session:
        # Не проверяем статику (картинки, стили), чтобы не грузить базу
        if request.endpoint and 'static' in request.endpoint:
            return

        user = None
        with get_db() as conn:
            # Обновляем время последней активности
            try:
                conn.execute('UPDATE users SET last_seen = ? WHERE id = ?', (datetime.now().isoformat(), session['user_id']))
                conn.commit()
            except Exception: pass
            user = conn.execute('SELECT banned_until FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        
        if user and user['banned_until']:
            try:
                ban_end = datetime.fromisoformat(user['banned_until'])
                if ban_end > datetime.now():
                    session.clear() # Выкидываем пользователя из сессии
                    return render_template('error.html', error_code="403", error_message=f"Ваш аккаунт заблокирован до {ban_end.strftime('%d.%m.%Y %H:%M')}"), 403
            except (ValueError, TypeError): pass

# --- Context Processor (Глобальные переменные для шаблонов) ---
@app.context_processor
def inject_global_vars():
    is_premium = False
    if 'user_id' in session:
        # Используем UserRepository для проверки
        user = UserRepository.get_user(session['user_id'])
        is_premium = UserRepository.is_premium(user)
    return dict(is_premium=is_premium)

if HAS_AUTHLIB and oauth:
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

    # Регистрируем Google только если ОБА ключа есть в настройках
    if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
        oauth.register(
            name='google',
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'}
        )
        oauth.init_app(app)
    else:
        # Если ключей нет, просто выводим предупреждение в лог, но сайт не падает
        logger.warning("GOOGLE_CLIENT_ID или GOOGLE_CLIENT_SECRET не найдены. Вход через Google будет отключен.")


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code="404", error_message="Страница, которую вы ищете, не существует или была удалена."), 404

@app.errorhandler(500)
def internal_server_error(e):
    # Если ошибка произошла при AJAX запросе (поиск, скачивание), возвращаем JSON
    if request.path.startswith('/get_info') or request.path.startswith('/start_download') or request.path.startswith('/progress'):
        return jsonify({'error': 'Внутренняя ошибка сервера (500). Попробуйте позже.'}), 500
    return render_template('error.html', error_code="500", error_message="Внутренняя ошибка сервера. Мы уже работаем над исправлением."), 500

@app.errorhandler(429)
def too_many_requests(e):
    if request.path.startswith('/get_info') or request.path.startswith('/start_download'):
        return jsonify({'error': 'Слишком много запросов. Подождите минуту.'}), 429
    return render_template('error.html', error_code="429", error_message="Слишком много запросов. Пожалуйста, подождите минуту."), 429

@app.after_request
def add_security_headers(response):
    # Заголовки безопасности
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    if not app.debug:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Маршруты для PWA (чтобы браузер видел manifest и sw в корне)
@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

@app.route('/sw.js')
def service_worker():
    return app.send_static_file('sw.js')

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

if __name__ == '__main__':
    # Настройки для запуска в интернете (Render, Heroku и т.д.)
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("DEBUG", "False").lower() == "true"
    socketio.run(app, host='0.0.0.0', port=port, debug=debug_mode, allow_unsafe_werkzeug=debug_mode)
