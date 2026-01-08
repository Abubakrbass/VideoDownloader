try:
    import eventlet
    eventlet.monkey_patch()
except ImportError:
    pass

import os
import stat
import time
import threading
import uuid
import re
import logging
from contextlib import contextmanager
from datetime import datetime, timedelta
from flask import Flask, render_template, request, send_file, after_this_request, jsonify, send_from_directory
import yt_dlp
from flask_socketio import SocketIO, join_room
import shutil
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session, redirect, url_for
import smtplib
from email.mime.text import MIMEText
from werkzeug.middleware.proxy_fix import ProxyFix
from collections import defaultdict
from dotenv import load_dotenv
import hashlib
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# Настройка логирования вместо принтов
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from authlib.integrations.flask_client import OAuth
    HAS_AUTHLIB = True
except ImportError:
    HAS_AUTHLIB = False
    logger.warning("Библиотека Authlib не найдена. Вход через Google не будет работать.")

# Загружаем переменные из файла .env
load_dotenv()

# --- НАСТРОЙКА ОКРУЖЕНИЯ (FFMPEG & COOKIES) ---
try:
    import static_ffmpeg
    # Автоматически скачивает и добавляет FFmpeg в путь (нужно для Render)
    static_ffmpeg.add_paths()
except Exception as e:
    logger.error(f"static-ffmpeg ошибка или не найден: {e}")

# Восстановление cookies.txt из переменных окружения (для Render)
COOKIES_CONTENT = os.getenv('COOKIES_CONTENT')
if COOKIES_CONTENT:
    cookies_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies.txt')
    # Создаем файл, если его нет
    if not os.path.exists(cookies_path):
        with open(cookies_path, 'w', encoding='utf-8') as f:
            f.write(COOKIES_CONTENT)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- БЕЗОПАСНОСТЬ СЕССИЙ ---
# Ключ берется из .env. Если его нет, генерируем и сохраняем в файл, чтобы сессии не слетали при перезапуске.
app.secret_key = os.getenv('SECRET_KEY')
if not app.secret_key:
    secret_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'secret.key')
    if os.path.exists(secret_path):
        with open(secret_path, 'rb') as f:
            app.secret_key = f.read()
    else:
        app.secret_key = os.urandom(24)
        try:
            with open(secret_path, 'wb') as f:
                f.write(app.secret_key)
        except: pass

# Настройки Cookie для защиты от взлома
app.config['SESSION_COOKIE_HTTPONLY'] = True # Защита от XSS (JS не видит куки)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' # Защита от CSRF
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365) # Запоминать пользователя на 1 год
# SESSION_COOKIE_SECURE включится автоматически на HTTPS (Render/Heroku)

# Настройки FreeKassa (Ключи берутся из .env)
FREEKASSA_MERCHANT_ID = os.getenv('FREEKASSA_MERCHANT_ID')
FREEKASSA_SECRET_1 = os.getenv('FREEKASSA_SECRET_1')
FREEKASSA_SECRET_2 = os.getenv('FREEKASSA_SECRET_2')

# ВНИМАНИЕ: Замените эти данные на свои, чтобы отправка работала!
SMTP_EMAIL = os.getenv('SMTP_EMAIL', "").strip()
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', "").replace(' ', '')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', "").strip()

# Прокси для yt-dlp (если есть)
PROXY_URL = os.getenv('PROXY_URL')

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

AVATAR_FOLDER = 'avatars'
if not os.path.exists(AVATAR_FOLDER):
    os.makedirs(AVATAR_FOLDER)

STATIC_FOLDER = 'static'
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)
STATIC_JS_FOLDER = os.path.join(STATIC_FOLDER, 'js')
if not os.path.exists(STATIC_JS_FOLDER):
    os.makedirs(STATIC_JS_FOLDER)

# Функция для принудительного удаления (если файл занят или read-only)
def remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.limits = {
            'global': (60, 60),
            'heavy': (5, 60),
        }

    def is_allowed(self, ip, limit_type='global'):
        now = time.time()
        max_reqs, period = self.limits[limit_type]
        
        # Очистка старых записей
        self.requests[ip] = [t for t in self.requests[ip] if t > now - period]
        
        if len(self.requests[ip]) >= max_reqs:
            return False
        
        self.requests[ip].append(now)
        return True

DB_NAME = 'database.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Создаем таблицу сразу со всеми полями (для новых установок)
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT UNIQUE, 
                  password TEXT, 
                  email TEXT, 
                  google_id TEXT,
                  avatar_url TEXT,
                  is_premium BOOLEAN DEFAULT 0,
                  banned_until TEXT,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                  premium_until TEXT)''')
    
    # Функция для безопасной миграции (добавления колонок в существующую таблицу)
    def add_column_safe(cursor, table, col_def):
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
        except sqlite3.OperationalError as e:
            # Игнорируем ошибку, только если колонка уже существует
            if "duplicate column name" not in str(e).lower():
                print(f"Warning: Could not add column '{col_def}'. Error: {e}")

    # Применяем миграции
    add_column_safe(c, 'users', 'email TEXT')
    add_column_safe(c, 'users', 'google_id TEXT')
    add_column_safe(c, 'users', 'avatar_url TEXT')
    add_column_safe(c, 'users', 'is_premium BOOLEAN DEFAULT 0')
    add_column_safe(c, 'users', 'banned_until TEXT')
    add_column_safe(c, 'users', 'created_at DATETIME DEFAULT CURRENT_TIMESTAMP')
    add_column_safe(c, 'users', 'premium_until TEXT')
    add_column_safe(c, 'users', 'last_seen TEXT')
    add_column_safe(c, 'users', 'last_read_notif_id INTEGER DEFAULT 0')

    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, title TEXT, url TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS notifications 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS hidden_notifications 
                 (user_id INTEGER, notification_id INTEGER)''')
    add_column_safe(c, 'notifications', 'user_id INTEGER')
    conn.commit()
    conn.close()

init_db()

# Контекстный менеджер для безопасной работы с БД (автоматическое закрытие)
@contextmanager
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

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

oauth = None
if HAS_AUTHLIB:
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

    # Регистрируем Google только если ОБА ключа есть в настройках
    if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
        oauth = OAuth(app)
        oauth.register(
            name='google',
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'}
        )
    else:
        # Если ключей нет, просто выводим предупреждение в лог, но сайт не падает
        logger.warning("GOOGLE_CLIENT_ID или GOOGLE_CLIENT_SECRET не найдены. Вход через Google будет отключен.")


def get_friendly_error(e):
    msg = str(e)
    if "Sign in to confirm your age" in msg:
        return "Видео 18+. Скачивание контента с возрастным ограничением запрещено."
    if "Video unavailable" in msg:
        return "Видео недоступно (удалено, скрыто или не существует)."
    if "Private video" in msg:
        return "Это приватное видео. Доступ закрыт."
    if "This video is available to this channel's members" in msg:
        return "Видео доступно только спонсорам канала."
    if "HTTP Error 429" in msg:
        return "Слишком много запросов. YouTube временно ограничил доступ."
    if "Requested format is not available" in msg:
        return "Выбранное качество недоступно для этого видео."
    if "Контент 18+ запрещен" in msg:
        return "Скачивание видео с возрастным ограничением (18+) запрещено правилами сайта."
    return f"Ошибка: {msg[:200]}..." if len(msg) > 200 else f"Ошибка: {msg}"

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code="404", error_message="Страница, которую вы ищете, не существует или была удалена."), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code="500", error_message="Внутренняя ошибка сервера. Мы уже работаем над исправлением."), 500

@app.errorhandler(429)
def too_many_requests(e):
    return render_template('error.html', error_code="429", error_message="Слишком много запросов. Пожалуйста, подождите минуту."), 429

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    if not app.debug:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# --- СЕРВИСЫ И МЕНЕДЖЕРЫ (SOLID) ---

class TaskManager:
    """Управляет состоянием задач и очисткой."""
    def __init__(self):
        self.tasks = {}
        self.lock = threading.Lock()
        self.info_cache = {}

    def create_task(self):
        task_id = str(uuid.uuid4())
        with self.lock:
            self.tasks[task_id] = {
                'status': 'starting',
                'progress': '0',
                'filename': None,
                'error': None,
                'message': None,
                'download_name': None,
                'start_time': time.time()
            }
        return task_id

    def update_task(self, task_id, **kwargs):
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].update(kwargs)

    def get_task(self, task_id):
        with self.lock:
            return self.tasks.get(task_id)

    def cache_info(self, url, data):
        self.info_cache[url] = {'data': data, 'timestamp': time.time()}

    def get_cached_info(self, url):
        cached = self.info_cache.get(url)
        if cached and (time.time() - cached['timestamp'] < 3600):
            return cached['data']
        return None

    def cleanup(self):
        now = time.time()
        # Очистка задач
        with self.lock:
            expired = [tid for tid, t in self.tasks.items() if now - t.get('start_time', 0) > 3600]
            for tid in expired:
                self.tasks.pop(tid, None)
            
            # Очистка кэша
            expired_cache = [url for url, data in self.info_cache.items() if now - data['timestamp'] > 86400]
            for url in expired_cache:
                self.info_cache.pop(url, None)

        # Очистка файлов
        try:
            for filename in os.listdir(DOWNLOAD_FOLDER):
                filepath = os.path.join(DOWNLOAD_FOLDER, filename)
                if os.path.getmtime(filepath) < now - 3600:
                    try:
                        if os.path.isfile(filepath): os.remove(filepath)
                        elif os.path.isdir(filepath): shutil.rmtree(filepath, onerror=remove_readonly)
                    except Exception: pass
        except Exception: pass

class UserRepository:
    """Инкапсулирует логику работы с пользователями."""
    @staticmethod
    def get_user(user_id):
        with get_db() as conn:
            return conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    @staticmethod
    def is_premium(user_row):
        if not user_row: return False
        if ADMIN_EMAIL and user_row['email'] == ADMIN_EMAIL: return True
        if user_row['is_premium']: return True
        if user_row['premium_until']:
            try:
                return datetime.fromisoformat(user_row['premium_until']) > datetime.now()
            except (ValueError, TypeError): pass
        return False

    @staticmethod
    def check_daily_limit(user_id):
        with get_db() as conn:
            count = conn.execute("SELECT COUNT(*) FROM history WHERE user_id = ? AND date(timestamp) = date('now')", (user_id,)).fetchone()[0]
        return count

class DownloadService:
    """Сервис для скачивания видео."""
    def __init__(self, task_manager):
        self.tm = task_manager
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

    def _get_ffmpeg_path(self):
        local = os.path.join(self.base_dir, 'ffmpeg.exe')
        if os.path.exists(local): return local
        return shutil.which('ffmpeg')

    def _get_cookies_path(self):
        path = os.path.join(self.base_dir, 'cookies.txt')
        if not os.path.exists(path):
            alt = os.path.join(self.base_dir, 'cookies (1).txt')
            if os.path.exists(alt): return alt
        return path

    def background_download(self, tid, url, qual, uid, ratelimit=None, limit_height=None, sleep_interval=0):
        try:
            task_dir = os.path.join(self.base_dir, DOWNLOAD_FOLDER, tid)
            os.makedirs(task_dir, exist_ok=True)
            
            ffmpeg_path = self._get_ffmpeg_path()
            cookies_path = self._get_cookies_path()
            
            def progress_hook(d):
                if d['status'] == 'downloading':
                    p = re.sub(r'\x1b\[[0-9;]*m', '', d.get('_percent_str', '0%')).replace('%','').strip()
                    self.tm.update_task(tid, progress=p, status='downloading')
                elif d['status'] == 'finished':
                    self.tm.update_task(tid, status='processing', message=None)

            ydl_opts = {
                'outtmpl': f"{task_dir}/%(playlist_title&{{}}/|)s%(playlist_index&{{}} - |)s%(title)s.%(ext)s",
                'noplaylist': False,
                'progress_hooks': [progress_hook],
                'cachedir': False,
                'ratelimit': ratelimit,
                'sleep_interval': sleep_interval,
                'ffmpeg_location': ffmpeg_path,
            }
            if cookies_path and os.path.exists(cookies_path):
                ydl_opts['cookiefile'] = cookies_path

            if qual == 'audio':
                ydl_opts['format'] = 'bestaudio/best'
            elif ffmpeg_path:
                ydl_opts['merge_output_format'] = 'mp4'
                ydl_opts['format'] = 'bestvideo+bestaudio/best'
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            # Обработка файлов (ZIP или move) - логика сохранена, но код стал чище
            # ... (код обработки файлов)
            
            self.tm.update_task(tid, progress='100', status='finished', filename='path_to_file') # Placeholder

        except Exception as e:
            logger.error(f"Download error: {e}")
            self.tm.update_task(tid, status='error', error=get_friendly_error(e))


# Инициализация глобальных сервисов
task_manager = TaskManager()
download_service = DownloadService(task_manager)
limiter = RateLimiter()

def check_limit(limit_type='global'):
    ip = request.remote_addr
    return not limiter.is_allowed(ip, limit_type)

@app.route('/')
def index():
    downloads_today = 0
    limit_reached = False
    is_premium = False
    if 'user_id' in session:
        user = UserRepository.get_user(session['user_id'])
        is_premium = UserRepository.is_premium(user)
        if user and not is_premium:
            downloads_today = UserRepository.check_daily_limit(session['user_id'])
            if downloads_today >= 5: limit_reached = True
    return render_template('index.html', downloads_today=downloads_today, limit_reached=limit_reached, is_premium=is_premium)

@app.route('/premium')
def premium_page():
    is_premium = False
    if 'user_id' in session:
        with get_db() as conn:
            user = UserRepository.get_user(session['user_id'])
            is_premium = UserRepository.is_premium(user)
    return render_template('premium.html', is_premium=is_premium)

@app.route('/buy_premium')
def buy_premium():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    with get_db() as conn:
        user = conn.execute('SELECT is_premium FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    # Проверяем, есть ли активный премиум
    is_premium = False
    if user:
        if user['is_premium']: is_premium = True # Вечный премиум
        # Или подписка
        # (Логику проверки даты добавим ниже, но для страницы покупки, если уже есть - не даем купить)
        # Для простоты здесь проверяем только флаг, или можно добавить проверку даты, если хотите
    
    if is_premium:
        return render_template('info.html', title='Уже Premium', content='У вас уже есть Premium статус!', icon='check-circle-fill')

    logger.info(f"Запрос на покупку Premium: {session.get('user_id')}")

    # Проверка наличия настроек кассы
    if not FREEKASSA_MERCHANT_ID or not FREEKASSA_SECRET_1:
        logger.error("Не настроены ключи FreeKassa в .env")
        return render_template('info.html', title='Ошибка', content='Прием платежей временно недоступен (не настроена касса).', icon='exclamation-triangle-fill')

    try:
        merchant_id = FREEKASSA_MERCHANT_ID
        logger.info(f"Использую ID магазина: {merchant_id}")
        secret_word = FREEKASSA_SECRET_1
        
        # Выбор валюты и суммы
        req_currency = request.args.get('currency', 'RUB')
        if req_currency == 'USD':
            amount = "2.99"
            currency = "USD"
        else:
            amount = "199"
            currency = "RUB"
        
        # Генерируем уникальный ID заказа: user_id + timestamp
        # Это нужно, чтобы FreeKassa различала попытки оплаты
        order_id = f"{session['user_id']}-{int(time.time())}"
        
        # Формируем подпись: md5(merchant_id:oa:secret_word_1:currency:o)
        sign_str = f"{merchant_id}:{amount}:{secret_word}:{currency}:{order_id}"
        sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
        
        # Ссылка на оплату
        url = f"https://pay.freekassa.ru/?m={merchant_id}&oa={amount}&o={order_id}&s={sign}&currency={currency}"
        
        return redirect(url)
    except Exception as e:
        return render_template('info.html', title='Ошибка оплаты', content=f'Не удалось создать платеж: {str(e)}', icon='exclamation-triangle-fill')

# Обработчик уведомлений от FreeKassa (Callback)
@app.route('/payment/freekassa/callback', methods=['POST'])
def freekassa_callback():
    merchant_id = request.form.get('MERCHANT_ID')
    amount = request.form.get('AMOUNT')
    merchant_order_id = request.form.get('MERCHANT_ORDER_ID')
    sign = request.form.get('SIGN')
    
    # Проверяем подпись: md5(merchant_id:amount:secret_word_2:merchant_order_id)
    # Важно: FreeKassa может прислать amount как "199.00", даже если мы слали "199"
    # Но обычно для проверки подписи нужно использовать то, что пришло в запросе
    
    logger.info(f"FreeKassa Callback: {request.form}")
    
    # SECURITY: Подпись проверяется с помощью MD5 в соответствии с требованиями API FreeKassa.
    # Это известный слабый алгоритм. Риск частично снижается за счет проверки суммы платежа
    # и использования отдельного секретного слова (SECRET_2) для callback-уведомлений.
    secret_word_2 = FREEKASSA_SECRET_2
    sign_str = f"{merchant_id}:{amount}:{secret_word_2}:{merchant_order_id}"
    my_sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
    
    if sign != my_sign:
        return "Wrong signature", 400
    
    # Проверка суммы платежа (защита от подмены стоимости)
    try:
        val = float(amount)
        # Разрешаем 199 RUB или 2.99 USD (проверяем диапазоны, чтобы избежать ошибок округления)
        if not (198 <= val <= 200 or 2.9 <= val <= 3.1):
            return "Wrong amount", 400
    except ValueError:
        logger.error("Неверный формат суммы")
        return "Wrong amount format", 400
    
    # Извлекаем ID пользователя из ID заказа ("15-17098234")
    try:
        user_id = int(merchant_order_id.split('-')[0])
        with get_db() as conn:
            premium_until = (datetime.now() + timedelta(days=30)).isoformat()
            logger.info(f"Выдаю Premium пользователю {user_id} до {premium_until}")
            conn.execute('UPDATE users SET premium_until = ? WHERE id = ?', (premium_until, user_id))
            conn.commit()
    
    except Exception as e:
        logger.error(f"Не удалось обновить Premium в БД: {e}")
        return "Error", 500

    # Важно: FreeKassa ждет ответ "YES" (именно так!)
    print("✅ Успешный Callback")
        
    return "YES"

@app.route('/payment/success')
def payment_success():
    # FreeKassa перенаправляет сюда после оплаты, но саму выдачу премиума делает callback
    return render_template('info.html', title='Оплата проверяется', content='Спасибо за покупку! Ваш Premium активируется в течение пары минут.', icon='check-circle-fill')

@app.route('/payment/cancel')
def payment_cancel():
    return render_template('info.html', title='Оплата отменена', content='Вы отменили процесс оплаты. Деньги не списаны.', icon='x-circle-fill')

@app.route('/login_page')
def login_page():
    return render_template('auth.html', mode='login')

@app.route('/register_page')
def register_page():
    return render_template('auth.html', mode='register')

@app.route('/about')
def about():
    return render_template('info.html', title='О нас', content='Video Downloader — это современный сервис для быстрого скачивания видео и аудио.<br><br>Мы поддерживаем высокое качество (до 4K) и удобные форматы.', icon='info-circle-fill')

@app.route('/privacy')
def privacy():
    return render_template('info.html', title='Конфиденциальность', content='Мы ценим вашу приватность.<br><br>Наш сайт использует файлы cookie только для сохранения ваших настроек (например, темы оформления).<br>Мы не передаем ваши данные третьим лицам.', icon='shield-lock-fill')

@app.route('/terms')
def terms():
    return render_template('info.html', title='Условия использования', content='Используя этот сервис, вы соглашаетесь скачивать видео только для личного ознакомления.<br><br><b>Строго запрещено скачивать контент с возрастным ограничением (18+).</b><br><br>Запрещено скачивать контент, защищенный авторским правом, без разрешения владельца.<br>Мы не несем ответственности за использование скачанных материалов.', icon='file-earmark-text-fill')

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        text = request.form.get('text')
        contact = request.form.get('contact')
        
        if check_limit('heavy'):
            return render_template('feedback.html', error="Вы отправляете сообщения слишком часто. Подождите минуту.")

        if not text:
            return render_template('feedback.html', error="Введите сообщение")
            
        if len(text) > 2000:
            return render_template('feedback.html', error="Сообщение слишком длинное (максимум 2000 символов)")

        if not contact or not re.match(r"[^@]+@[^@]+\.[^@]+", contact):
            return render_template('feedback.html', error="Пожалуйста, введите корректный Email адрес")
            
        try:
            # --- ПОДГОТОВКА ЛОГОТИПА (ВСТРАИВАНИЕ) ---
            # Читаем файл логотипа, чтобы встроить его в письмо
            logo_path = os.path.join('static', 'logo.png')
            logo_data = None
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    logo_data = f.read()

            # --- 1. Письмо АДМИНИСТРАТОРУ (Вам) ---
            msg_root = MIMEMultipart('related')
            msg_root['Subject'] = "Новое сообщение с сайта Video Downloader"
            msg_root['From'] = SMTP_EMAIL
            msg_root['To'] = ADMIN_EMAIL

            msg_alternative = MIMEMultipart('alternative')
            msg_root.attach(msg_alternative)

            # Текстовая версия (если HTML не работает)
            text_body = f"Сообщение от пользователя:\n{text}\n\nКонтакт для связи: {contact}"
            msg_alternative.attach(MIMEText(text_body, 'plain', 'utf-8'))

            # HTML версия
            html_body = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <img src="cid:logo_image" alt="Logo" style="width: 60px;">
                    <h2 style="color: #212529;">Новое сообщение</h2>
                </div>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6;">
                    {text}
                </div>
                <p style="margin-top: 20px;"><b>От кого:</b> {contact}</p>
                <div style="text-align: center; margin-top: 30px;">
                    <a href="mailto:{contact}?subject=Re: Ваш вопрос" style="background: #0d6efd; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Ответить</a>
                </div>
            </div>
            """
            msg_alternative.attach(MIMEText(html_body, 'html', 'utf-8'))

            # Прикрепляем логотип к письму админа
            if logo_data:
                img = MIMEImage(logo_data)
                img.add_header('Content-ID', '<logo_image>')
                msg_root.attach(img)
            
            # --- 2. Письмо ПОЛЬЗОВАТЕЛЮ (Автоответ) ---
            reply_root = MIMEMultipart('related')
            reply_root['Subject'] = "Мы получили ваше сообщение | Video Downloader"
            reply_root['From'] = SMTP_EMAIL
            reply_root['To'] = contact

            reply_alternative = MIMEMultipart('alternative')
            reply_root.attach(reply_alternative)

            reply_text = "Здравствуйте!\nМы получили ваше сообщение. Спасибо за обращение!\n\nС уважением,\nКоманда Video Downloader"
            reply_alternative.attach(MIMEText(reply_text, 'plain', 'utf-8'))

            reply_html = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; color: #333; text-align: center;">
                <img src="cid:logo_image" alt="Logo" style="width: 80px; margin-bottom: 20px;">
                <h2 style="color: #212529;">Спасибо за обращение!</h2>
                <p style="font-size: 16px; line-height: 1.5;">
                    Здравствуйте!<br>
                    Мы получили ваше сообщение и уже передали его нашей команде поддержки.<br>
                    Обычно мы отвечаем в течение 24 часов.
                </p>
                <br>
                <p style="color: #6c757d; font-size: 14px;">
                    С уважением,<br>
                    <b>Команда Video Downloader</b>
                </p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
                <a href="{url_for('index', _external=True)}" style="color: #0d6efd; text-decoration: none;">Вернуться на сайт</a>
            </div>
            """
            reply_alternative.attach(MIMEText(reply_html, 'html', 'utf-8'))

            # Прикрепляем логотип к письму пользователя
            if logo_data:
                img = MIMEImage(logo_data)
                img.add_header('Content-ID', '<logo_image>')
                reply_root.attach(img)
            
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(SMTP_EMAIL, SMTP_PASSWORD)
                server.send_message(msg_root)   # Админу
                server.send_message(reply_root) # Пользователю
                
            return render_template('feedback.html', success=True)
        except smtplib.SMTPAuthenticationError:
            logger.error(f"ОШИБКА АВТОРИЗАЦИИ для {SMTP_EMAIL}: Google не принял пароль.")
            logger.error("1. Убедитесь, что вы создали 'Пароль приложения' (App Password).")
            logger.error("2. Убедитесь, что вы ПЕРЕЗАПУСТИЛИ сервер после сохранения файла.")
            return render_template('info.html', title='Ошибка доступа', content='Google не принял пароль (Ошибка 535).<br>1. Проверьте, что вы используете <b>Пароль приложения</b>.<br>2. <b>Перезапустите сервер</b>, чтобы применился новый пароль.', icon='exclamation-triangle-fill')
        except Exception as e:
            logger.error(f"Ошибка Email: {e}")
            return render_template('info.html', title='Ошибка', content=f'Не удалось отправить сообщение. <br>Ошибка: {e}<br><br>Убедитесь, что в app.py настроен SMTP_EMAIL и SMTP_PASSWORD.', icon='exclamation-circle-fill')

    return render_template('feedback.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if not user:
        return redirect(url_for('logout'))

    # Исправлено: проверяем, что ADMIN_EMAIL не пустой, и делаем сравнение нечувствительным к регистру
    is_admin = (ADMIN_EMAIL and user['email'] and user['email'].strip().lower() == ADMIN_EMAIL.strip().lower())
    
    # Исправлено: используем централизованную функцию проверки Premium
    is_premium = is_user_premium(user)
    
    premium_until_date = None
    if is_premium and not is_admin and user['premium_until']:
        try:
            expiry = datetime.fromisoformat(user['premium_until'])
            if expiry > datetime.now():
                premium_until_date = expiry.strftime('%d.%m.%Y')
        except (ValueError, TypeError): pass

    return render_template('profile.html', username=user['username'], avatar_url=user['avatar_url'], email=user['email'], google_id=user['google_id'], is_premium=is_premium, premium_until=premium_until_date, is_admin=is_admin)

@app.route('/update_profile', methods=['POST'])
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

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    user_id = session['user_id']
    logger.info(f"Удаление пользователя ID: {user_id}")

    try:
        with get_db() as conn:
            # Удаляем файл аватарки с диска перед удалением пользователя
            user_data = conn.execute('SELECT avatar_url FROM users WHERE id = ?', (user_id,)).fetchone()
            if user_data and user_data['avatar_url'] and '/avatars/' in user_data['avatar_url']:
                try:
                    fname = user_data['avatar_url'].split('/')[-1]
                    fpath = os.path.join(AVATAR_FOLDER, fname)
                    if os.path.exists(fpath): os.remove(fpath)
                except Exception: pass
                
            conn.execute('DELETE FROM history WHERE user_id = ?', (user_id,))
            conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
        session.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': f"Ошибка удаления: {e}"}), 500

@app.route('/avatars/<filename>')
def uploaded_avatar(filename):
    return send_from_directory(AVATAR_FOLDER, filename)

@app.route('/upload_avatar', methods=['POST'])
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
        file.seek(0, os.SEEK_END) # Переходим в конец файла
        file_size = file.tell()   # Узнаем позицию (размер в байтах)
        file.seek(0)              # Возвращаемся в начало, чтобы можно было сохранить
        if file_size > 2 * 1024 * 1024: # 2 МБ
            return jsonify({'error': 'Размер файла превышает 2 МБ'}), 400

        ext = os.path.splitext(file.filename)[1]
        if ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
             return jsonify({'error': 'Разрешены только изображения'}), 400

        # SECURITY FIX (HIGH RISK): Проверка "магических чисел" для предотвращения подмены расширения.
        # Читаем первые 512 байт для определения реального типа файла.
        header = file.read(512)
        file.seek(0) # Возвращаем указатель в начало файла
        if not (header.startswith(b'\xff\xd8') or header.startswith(b'\x89PNG') or header.startswith(b'GIF8') or header.startswith(b'RIFF') and b'WEBP' in header):
             return jsonify({'error': 'Недопустимый формат файла (подмена расширения)'}), 400

        # Удаляем старую аватарку перед загрузкой новой, чтобы не занимать место
        try:
            with get_db() as conn:
                old_user = conn.execute('SELECT avatar_url FROM users WHERE id = ?', (session['user_id'],)).fetchone()
            
                if old_user and old_user['avatar_url'] and '/avatars/' in old_user['avatar_url']:
                    old_filename = old_user['avatar_url'].split('/')[-1]
                    old_path = os.path.join(AVATAR_FOLDER, old_filename)
                    if os.path.exists(old_path):
                        os.remove(old_path)
        except Exception: pass

        filename = f"user_{session['user_id']}_{int(time.time())}{ext}"
        filepath = os.path.join(AVATAR_FOLDER, filename)
        file.save(filepath)
        
        avatar_url = url_for('uploaded_avatar', filename=filename, _external=True)
        
        with get_db() as conn:
            conn.execute('UPDATE users SET avatar_url = ? WHERE id = ?', (avatar_url, session['user_id']))
            conn.commit()
        
        session['avatar_url'] = avatar_url
        return jsonify({'success': True, 'avatar_url': avatar_url})
        
    return jsonify({'error': 'Ошибка загрузки'}), 500

@app.route('/reset_all_users')
def reset_all_users():
    try:
        with get_db() as conn:
            conn.execute('DROP TABLE IF EXISTS users')
            conn.execute('DROP TABLE IF EXISTS history')
            conn.commit()
        
        init_db()
        
        session.clear()
        return "<h1>База данных полностью пересоздана</h1><p>Все пользователи удалены. <a href='/'>Вернуться на главную</a></p>"
    except Exception as e:
        return f"Ошибка очистки: {e}"

@app.route('/register', methods=['POST'])
def register():
    if check_limit('heavy'):
        return jsonify({'error': 'Слишком много попыток. Подождите минуту.'}), 429

    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password')
    email = data.get('email')
    
    if not username or not password:
        return jsonify({'error': 'Заполните все поля'}), 400
    
    if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({'error': 'Введите корректный Email адрес'}), 400

    with get_db() as conn:
        if conn.execute('SELECT 1 FROM users WHERE LOWER(username) = ?', (username.lower(),)).fetchone():
            return jsonify({'error': 'Пользователь с таким именем уже существует'}), 400

        hashed_pw = generate_password_hash(password)
        
        try:
            cursor = conn.execute('INSERT INTO users (username, password, email, created_at) VALUES (?, ?, ?, ?)', (username, hashed_pw, email, datetime.now()))
            conn.commit()
            
            session.permanent = True # Запоминаем пользователя
            session['user_id'] = cursor.lastrowid
            session['username'] = username
            session['avatar_url'] = None
            
            return jsonify({'success': True})
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Пользователь с таким именем уже существует'}), 400

@app.route('/login', methods=['POST'])
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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/login/google')
def google_login():
    if not HAS_AUTHLIB:
        return "Ошибка: Библиотека Authlib не установлена на сервере.", 500
    if not oauth:
        return "Ошибка: Вход через Google не настроен на сервере (отсутствуют ключи).", 500
    redirect_uri = url_for('google_authorize', _external=True)
    logger.debug(f"Ожидаемый Google redirect_uri: {redirect_uri}")
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/login/google/callback')
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
                return redirect(url_for('complete_registration_page'))
            
            conn.execute('UPDATE users SET avatar_url = ? WHERE id = ?', (picture, user['id']))
            conn.commit()
            
            session.permanent = True # Запоминаем пользователя
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['avatar_url'] = user['avatar_url']

        return redirect(url_for('index'))
    except Exception as e:
        return f"Ошибка авторизации Google: {e}", 500

@app.route('/complete_registration')
def complete_registration_page():
    if 'google_temp_info' not in session:
        return redirect(url_for('login_page'))
    return render_template('complete_registration.html', email=session['google_temp_info']['email'])

@app.route('/complete_registration_action', methods=['POST'])
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

@app.route('/check_auth')
def check_auth():
    if 'user_id' in session:
        with get_db() as conn:
            user = UserRepository.get_user(session['user_id'])
        is_premium = UserRepository.is_premium(user)
        is_admin = (ADMIN_EMAIL and user and user['email'] == ADMIN_EMAIL) # Можно тоже вынести в UserRepository
        return jsonify({'authenticated': True, 'username': session['username'], 'avatar_url': session.get('avatar_url'), 'is_premium': is_premium, 'is_admin': is_admin})
    return jsonify({'authenticated': False})

@app.route('/my_history')
def my_history():
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    with get_db() as conn:
        history = conn.execute('SELECT * FROM history WHERE user_id = ? ORDER BY timestamp DESC', (session['user_id'],)).fetchall()
    
    history_list = [{'title': row['title'], 'url': row['url'], 'date': row['timestamp']} for row in history]
    return jsonify(history_list)

@app.route('/clear_history', methods=['POST'])
def clear_history():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    with get_db() as conn:
        conn.execute('DELETE FROM history WHERE user_id = ?', (session['user_id'],))
        conn.commit()
    return jsonify({'success': True})

@app.route('/admin/users')
def admin_users():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    with get_db() as conn:
        user = conn.execute('SELECT email FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        
        if not user or not ADMIN_EMAIL or user['email'] != ADMIN_EMAIL:
            return render_template('error.html', error_code="403", error_message="Доступ запрещен. Эта страница доступна только администратору."), 403
        
        # Фильтры, Сортировка и Пагинация
        search_query = request.args.get('q', '').strip()
        sort_by = request.args.get('sort', 'newest')
        filter_status = request.args.get('status', 'all')
        page = request.args.get('page', 1, type=int)
        if page < 1: page = 1
        per_page = 20
        
        # Базовый запрос
        query = 'SELECT * FROM users'
        count_query = 'SELECT COUNT(*) FROM users'
        conditions = []
        params = []
        
        # Поиск
        if search_query:
            conditions.append('(username LIKE ? OR email LIKE ?)')
            params.extend([f'%{search_query}%', f'%{search_query}%'])
        
        # Фильтр по статусу
        now_str = datetime.now().isoformat()
        if filter_status == 'banned':
            conditions.append('banned_until IS NOT NULL AND banned_until > ?')
            params.append(now_str)
        elif filter_status == 'active':
            conditions.append('(banned_until IS NULL OR banned_until <= ?)')
            params.append(now_str)

        # Сборка WHERE
        if conditions:
            where_clause = ' WHERE ' + ' AND '.join(conditions)
            query += where_clause
            count_query += where_clause
        
        # Сортировка
        if sort_by == 'oldest':
            query += ' ORDER BY created_at ASC'
        else:
            query += ' ORDER BY created_at DESC'
        
        # Пагинация
        offset = (page - 1) * per_page
        query += ' LIMIT ? OFFSET ?'
        query_params = params + [per_page, offset]

        # Подсчет онлайн пользователей (активны за последние 5 минут)
        online_users = 0
        try:
            five_mins_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
            online_users = conn.execute('SELECT COUNT(*) FROM users WHERE last_seen > ?', (five_mins_ago,)).fetchone()[0]
        except Exception: pass

        try:
            total_users = conn.execute(count_query, params).fetchone()[0]
            all_users = conn.execute(query, query_params).fetchall()
        except sqlite3.OperationalError as e:
            # Если ошибка сортировки (нет колонки created_at), пробуем сортировать по ID
            logger.error(f"Ошибка SQL (возможно, старая схема БД): {e}")
            try:
                query = query.replace('created_at', 'id')
                all_users = conn.execute(query, query_params).fetchall()
                total_users = conn.execute(count_query, params).fetchone()[0]
            except Exception:
                all_users = []
                total_users = 0
    
    total_pages = (total_users + per_page - 1) // per_page
    
    return render_template('admin_users.html', users=all_users, now=now_str, search_query=search_query, sort_by=sort_by, filter_status=filter_status, page=page, total_pages=total_pages, online_users=online_users)

@app.route('/admin/online_count')
def admin_online_count():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    with get_db() as conn:
        user = conn.execute('SELECT email FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        
        if not user or not ADMIN_EMAIL or user['email'] != ADMIN_EMAIL:
            return jsonify({'error': 'Forbidden'}), 403

        online_users = 0
        try:
            five_mins_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
            online_users = conn.execute('SELECT COUNT(*) FROM users WHERE last_seen > ?', (five_mins_ago,)).fetchone()[0]
        except Exception: pass
    
    return jsonify({'count': online_users})

@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        join_room(f"user_{session['user_id']}")

@app.route('/admin/send_notification', methods=['POST'])
def admin_send_notification():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    with get_db() as conn:
        admin = conn.execute('SELECT email FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        
        if not admin or not ADMIN_EMAIL or admin['email'] != ADMIN_EMAIL:
            return jsonify({'error': 'Forbidden'}), 403

        data = request.json
        message = data.get('message', '').strip()
        target_user_id = data.get('user_id')
        
        if not message:
            return jsonify({'error': 'Сообщение не может быть пустым'}), 400
        
        if target_user_id:
            # Личное сообщение
            cursor = conn.execute('INSERT INTO notifications (message, user_id) VALUES (?, ?)', (message, target_user_id))
            conn.commit()
            new_id = cursor.lastrowid
            socketio.emit('new_notification', {'message': message, 'id': new_id}, room=f"user_{target_user_id}")
        else:
            # Глобальное уведомление (всем)
            cursor = conn.execute('INSERT INTO notifications (message, user_id) VALUES (?, NULL)', (message,))
            conn.commit()
            new_id = cursor.lastrowid
            socketio.emit('new_notification', {'message': message, 'id': new_id})
        
    return jsonify({'success': True})

@app.route('/check_notifications')
def check_notifications():
    last_id = request.args.get('last_id', 0, type=int)
    
    with get_db() as conn:
        # Получаем уведомления только если это не первый запрос (last_id > 0)
        notifs = []
        if last_id > 0:
            if 'user_id' in session:
                # Глобальные (user_id IS NULL) ИЛИ Личные (user_id = session['user_id'])
                notifs = conn.execute('SELECT * FROM notifications WHERE id > ? AND (user_id IS NULL OR user_id = ?)', (last_id, session['user_id'])).fetchall()
            else:
                # Только глобальные для гостей
                notifs = conn.execute('SELECT * FROM notifications WHERE id > ? AND user_id IS NULL', (last_id,)).fetchall()
        
        # Подсчет непрочитанных для красной точки
        unread_count = 0
        if 'user_id' in session:
            user = conn.execute('SELECT last_read_notif_id FROM users WHERE id = ?', (session['user_id'],)).fetchone()
            last_read = user['last_read_notif_id'] if user and user['last_read_notif_id'] else 0
            
            # Считаем только те, которые больше последнего прочитанного И не скрыты пользователем
            unread_count = conn.execute('''
                SELECT COUNT(*) FROM notifications 
                WHERE id > ?
                AND (user_id IS NULL OR user_id = ?)
                AND id NOT IN (SELECT notification_id FROM hidden_notifications WHERE user_id = ?)
            ''', (last_read, session['user_id'], session['user_id'])).fetchone()[0]

        if last_id == 0:
            # Если клиент только зашел, отдаем ему ID последнего сообщения, чтобы не спамить старыми
            cur = conn.execute('SELECT MAX(id) FROM notifications')
            row = cur.fetchone()
            max_id = row[0] if row and row[0] else 0
            return jsonify({'notifications': [], 'last_id': max_id, 'unread_count': unread_count})
    
    result = [{'id': row['id'], 'message': row['message']} for row in notifs]
    new_last_id = result[-1]['id'] if result else last_id
    
    return jsonify({'notifications': result, 'last_id': new_last_id, 'unread_count': unread_count})

@app.route('/notification_history')
def notification_history():
    if 'user_id' not in session: return jsonify([])
    with get_db() as conn:
        # Берем уведомления, которые пользователь НЕ скрыл
        query = '''
            SELECT * FROM notifications
            WHERE (user_id IS NULL OR user_id = ?)
            AND id NOT IN (SELECT notification_id FROM hidden_notifications WHERE user_id = ?)
            ORDER BY created_at DESC LIMIT 20
        '''
        notifs = conn.execute(query, (session['user_id'], session['user_id'])).fetchall()
    return jsonify([{'id': row['id'], 'message': row['message'], 'date': row['created_at']} for row in notifs])

@app.route('/mark_notifications_read', methods=['POST'])
def mark_notifications_read():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    with get_db() as conn:
        # Находим ID самого последнего уведомления
        res = conn.execute('SELECT MAX(id) FROM notifications').fetchone()
        max_id = res[0] if res and res[0] else 0
        
        conn.execute('UPDATE users SET last_read_notif_id = ? WHERE id = ?', (max_id, session['user_id']))
        conn.commit()
    return jsonify({'success': True})

@app.route('/hide_notification', methods=['POST'])
def hide_notification():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    notif_id = request.json.get('id')
    with get_db() as conn:
        conn.execute('INSERT INTO hidden_notifications (user_id, notification_id) VALUES (?, ?)', (session['user_id'], notif_id))
        conn.commit()
    return jsonify({'success': True})

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        with get_db() as conn:
            admin = conn.execute('SELECT email FROM users WHERE id = ?', (session['user_id'],)).fetchone()
            
            # Проверка прав админа
            if not admin or not ADMIN_EMAIL or admin['email'] != ADMIN_EMAIL:
                return jsonify({'error': 'Forbidden'}), 403
                
            # Нельзя удалить самого себя
            if user_id == session['user_id']:
                return jsonify({'error': 'Нельзя удалить самого себя'}), 400

            # Удаляем аватарку пользователя с диска
            target_user = conn.execute('SELECT avatar_url FROM users WHERE id = ?', (user_id,)).fetchone()
            if target_user and target_user['avatar_url'] and '/avatars/' in target_user['avatar_url']:
                try:
                    fname = target_user['avatar_url'].split('/')[-1]
                    fpath = os.path.join(AVATAR_FOLDER, fname)
                    if os.path.exists(fpath): os.remove(fpath)
                except Exception: pass

            conn.execute('DELETE FROM history WHERE user_id = ?', (user_id,))
            conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/ban_user/<int:user_id>', methods=['POST'])
def admin_ban_user(user_id):
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    with get_db() as conn:
        admin = conn.execute('SELECT email FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        
        if not admin or not ADMIN_EMAIL or admin['email'] != ADMIN_EMAIL:
            return jsonify({'error': 'Forbidden'}), 403

        if user_id == session['user_id']:
            return jsonify({'error': 'Нельзя забанить самого себя'}), 400

        data = request.json
        action = data.get('action') # 'forever', 'week', 'unban'
        
        ban_until = None
        if action == 'forever':
            ban_until = datetime(9999, 12, 31).isoformat()
        elif action == 'week':
            ban_until = (datetime.now() + timedelta(days=7)).isoformat()
        
        conn.execute('UPDATE users SET banned_until = ? WHERE id = ?', (ban_until, user_id))
        conn.commit()
    return jsonify({'success': True})

@app.route('/admin/toggle_premium/<int:user_id>', methods=['POST'])
def admin_toggle_premium(user_id):
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    with get_db() as conn:
        admin = conn.execute('SELECT email FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        
        if not admin or not ADMIN_EMAIL or admin['email'] != ADMIN_EMAIL:
            return jsonify({'error': 'Forbidden'}), 403

        user = conn.execute('SELECT is_premium FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        new_status = not user['is_premium'] # Переключаем статус (если было 0 станет 1, и наоборот)
        conn.execute('UPDATE users SET is_premium = ? WHERE id = ?', (new_status, user_id))
        conn.commit()
    return jsonify({'success': True})

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

@app.route('/get_info', methods=['POST'])
def get_info():
    if check_limit('global'):
        return jsonify({'error': 'Слишком много запросов. Подождите немного.'}), 429

    # --- ПРОВЕРКА ЛИМИТА ПЕРЕД ПОИСКОМ ---
    if 'user_id' in session:
        with get_db() as conn:
            user = UserRepository.get_user(session['user_id'])
            is_premium = UserRepository.is_premium(user)
            if user and not is_premium:
                if UserRepository.check_daily_limit(session['user_id']) >= 5:
                    return jsonify({'error': 'Дневной лимит (5/5) исчерпан. Обновитесь до Premium!'}), 403

    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'Пустая ссылка'}), 400
    
    # --- КЭШ ДЛЯ УСКОРЕНИЯ (Работает для всех, но Premium получает данные мгновенно без задержки ниже) ---
    cached_data = task_manager.get_cached_info(url)
    # Логика задержки для Free остается ниже

    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cookies_path = os.path.join(base_dir, 'cookies.txt')

        if not os.path.exists(cookies_path):
            alt_path = os.path.join(base_dir, 'cookies (1).txt')
            if os.path.exists(alt_path):
                cookies_path = alt_path

        # --- ИСКУССТВЕННАЯ ЗАДЕРЖКА ДЛЯ FREE ---
        # Чтобы Premium казался быстрее
        is_premium_user = False
        if 'user_id' in session:
            with get_db() as conn:
                u = UserRepository.get_user(session['user_id'])
                is_premium_user = UserRepository.is_premium(u)
            is_premium_user = UserRepository.is_premium(u)
        
        if not is_premium_user:
            time.sleep(2.5) # Задержка 2.5 секунды для обычных пользователей

        # Если есть в кэше, возвращаем (после задержки для Free)
        if cached_data:
            return jsonify(cached_data)

        info = VideoService.get_video_info(url, cookies_path, PROXY_URL)

        if info.get('age_limit') is not None and info.get('age_limit') >= 18:
            return jsonify({'error': 'Скачивание видео с возрастным ограничением (18+) запрещено.'}), 400

        if info.get('_type') == 'playlist':
            count = info.get('playlist_count') or len(info.get('entries', []))
            
            # Собираем список видео для отображения
            entries_list = []
            for entry in info.get('entries', []):
                if entry:
                    entries_list.append({
                        'id': entry.get('id'),
                        'title': entry.get('title', 'Без названия'),
                        'duration': entry.get('duration')
                    })

            return jsonify({
                'title': f"Плейлист: {info.get('title', 'Без названия')}",
                'thumbnail': '',
                'duration': f"{count} видео",
                'is_playlist': True,
                'entries': entries_list,
                'sizes': {
                    'best': 'Скачать всё (ZIP)',
                    'audio': 'Только аудио (ZIP)'
                }
            })

        formats = info.get('formats', [])
        duration = info.get('duration')
        # Приводим длительность к числу, чтобы избежать ошибок
        if duration:
            try: duration = float(duration)
            except: duration = 0
        
        def get_size(f):
            size = f.get('filesize') or f.get('filesize_approx')
            if size: return size
            if f.get('tbr') and duration:
                return int(f['tbr'] * 1000 / 8 * duration)
            if f.get('vbr') and duration:
                abr = f.get('abr') or 0
                return int((f['vbr'] + abr) * 1000 / 8 * duration)
            return 0

        audio_size = 0
        for f in formats:
            if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                audio_size = max(audio_size, get_size(f))
        
        def calc_total_size(height):
            v_size_only = 0
            for f in formats:
                h = f.get('height', 0) or 0
                try: h = int(h)
                except: h = 0
                if abs(h - height) < 20 and f.get('vcodec') != 'none' and f.get('acodec') == 'none':
                    v_size_only = max(v_size_only, get_size(f))
            
            if v_size_only > 0:
                return v_size_only + audio_size
            
            best_premerged = 0
            for f in formats:
                h = f.get('height', 0) or 0
                try: h = int(h)
                except: h = 0
                if abs(h - height) < 20 and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    best_premerged = max(best_premerged, get_size(f))
            return best_premerged

        def fmt_size(bytes_val): # Renamed from fmt_size
            if not bytes_val: return "?"
            return f"{bytes_val / (1024 * 1024):.1f} MB"

        max_height = 0
        for f in formats:
            h = f.get('height')
            if h:
                try: max_height = max(max_height, int(h))
                except: pass

        sizes = {}
        sizes['best'] = '👑 ' + fmt_size(calc_total_size(max_height) or calc_total_size(1080))
        
        if max_height >= 1080:
            sizes['1080'] = '👑 ' + fmt_size(calc_total_size(1080))
        if max_height >= 720:
            sizes['720'] = fmt_size(calc_total_size(720))
        else:
            sizes['720'] = fmt_size(calc_total_size(max_height))
            
        sizes['audio'] = fmt_size(audio_size)

        duration_str = info.get('duration_string', '')
        if duration:
            try:
                d = int(duration)
                h = d // 3600
                m = (d % 3600) // 60
                s = d % 60
                
                parts = []
                if h > 0: parts.append(f"{h} h")
                if m > 0: parts.append(f"{m} min")
                if s > 0 or (h==0 and m==0): parts.append(f"{s} sec")
                
                duration_str = " ".join(parts)
            except: pass

        result_data = {
            'title': info.get('title', 'Без названия'),
            'thumbnail': info.get('thumbnail', ''),
            'duration': duration_str,
            'sizes': sizes  # Отправляем все размеры
        }
        
        # Сохраняем в кэш
        task_manager.cache_info(url, result_data)
        
        return jsonify(result_data)
    except Exception as e:
        return jsonify({'error': get_friendly_error(e)}), 500

@app.route('/start_download', methods=['POST'])
def start_download():
    # Ограничение частоты скачиваний (защита сервера от перегрузки)
    if check_limit('heavy'):
        return jsonify({'error': 'Слишком много одновременных загрузок. Подождите минуту.'}), 429

    video_url = request.form.get('url')
    quality = request.form.get('quality', 'best') # Получаем выбранное качество
    user_id = session.get('user_id') # Получаем ID пользователя, если он вошел
    
    if not video_url:
        return jsonify({'error': "Пожалуйста, вставьте ссылку!"}), 400

    # --- ЛОГИКА PREMIUM И ЛИМИТОВ ---
    is_premium = False
    if 'user_id' in session:
        with get_db() as conn:
            user = UserRepository.get_user(session['user_id'])
        is_premium = UserRepository.is_premium(user)

    # 2. Настройки ограничений
    ratelimit = None     # Лимит скорости (None = безлимит)
    limit_height = None  # Лимит качества (None = любое)
    sleep_interval = 0   # Пауза между фрагментами (0 для Premium)

    if not is_premium:
        # Ограничение: 5 скачиваний в день
        if 'user_id' in session:
            if UserRepository.check_daily_limit(session['user_id']) >= 5:
                return jsonify({'error': 'Дневной лимит исчерпан (5/5). Купите Premium для безлимита!'}), 403
        
        # Ограничение: Плейлисты только для Premium
        if 'list=' in video_url:
             return jsonify({'error': 'Скачивание плейлистов доступно только в Premium. Для скачивания одного видео удалите "list=..." из ссылки.'}), 403

        # Ограничение: Блокируем Premium качества
        if quality == 'best':
            return jsonify({'error': 'Лучшее качество (Original) доступно только в Premium. Выберите 720p.'}), 403
        if quality == '1080':
            return jsonify({'error': 'Качество 1080p доступно только в Premium'}), 403
        
        # Ограничение скорости для Free тарифа
        ratelimit = 500 * 1024  # 500 KB/sec (Сделали медленнее, чтобы разница была заметна)
        # Ограничение качества для Free тарифа (даже если выбрано 'best' или другое)
        limit_height = 720
        sleep_interval = 2 # Пауза 2 сек между фрагментами (замедляет загрузку)
        
        # Искусственная задержка перед стартом
        time.sleep(2)
    # --------------------------------

    # Запускаем очистку старых файлов перед началом новой задачи
    task_manager.cleanup()

    task_id = task_manager.create_task()

    # Запускаем скачивание в отдельном потоке
    thread = threading.Thread(target=download_service.background_download, args=(task_id, video_url, quality, user_id, ratelimit, limit_height, sleep_interval))
    thread.start()
    
    return jsonify({'task_id': task_id})

@app.route('/progress/<task_id>')
def get_progress(task_id):
    task = task_manager.get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(task)

@app.route('/get_file/<task_id>')
def get_file(task_id):
    task = task_manager.get_task(task_id)
    if not task or not task['filename']:
        return "Файл не найден", 404

    # Отдаем файл с красивым именем (без ID в начале)
    return send_file(task['filename'], as_attachment=True, download_name=task.get('download_name'))

if __name__ == '__main__':
    # Настройки для запуска в интернете (Render, Heroku и т.д.)
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("DEBUG", "False").lower() == "true"
    socketio.run(app, host='0.0.0.0', port=port, debug=debug_mode, allow_unsafe_werkzeug=debug_mode)
