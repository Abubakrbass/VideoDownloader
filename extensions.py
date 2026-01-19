import os
import time
import threading
import uuid
import logging
import sqlite3
import shutil
import stat
try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None
from collections import defaultdict
from contextlib import contextmanager
from flask import request
from flask_socketio import SocketIO
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect

load_dotenv()

# Logger configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment Variables
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', "").strip()

# Folders
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

AVATAR_FOLDER = 'avatars'
if not os.path.exists(AVATAR_FOLDER):
    os.makedirs(AVATAR_FOLDER)

STATIC_FOLDER = 'static'
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)


# SocketIO
socketio = SocketIO(cors_allowed_origins="*")
csrf = CSRFProtect()

# OAuth
oauth = None
HAS_AUTHLIB = False
try:
    from authlib.integrations.flask_client import OAuth
    HAS_AUTHLIB = True
    oauth = OAuth()
except ImportError:
    pass

# Database Logic
def get_db_connection():
    db_url = os.environ.get('DATABASE_URL')
    if db_url and psycopg2:
        return psycopg2.connect(db_url)
    else:
        return sqlite3.connect('database.db')

@contextmanager
def get_db():
    conn = get_db_connection()
    if psycopg2 and isinstance(conn, psycopg2.extensions.connection):
        cursor_factory = psycopg2.extras.DictCursor
        conn.cursor_factory = cursor_factory
    else:
        conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id SERIAL PRIMARY KEY, 
                  username TEXT UNIQUE, 
                  password TEXT, 
                  email TEXT, 
                  google_id TEXT,
                  avatar_url TEXT,
                  is_premium BOOLEAN DEFAULT FALSE,
                  banned_until TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  premium_until TEXT)''')
    
    def add_column_safe(cursor, table, col_def):
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
        except (sqlite3.OperationalError, psycopg2.errors.DuplicateColumn):
            pass

    add_column_safe(c, 'users', 'email TEXT')
    add_column_safe(c, 'users', 'google_id TEXT')
    add_column_safe(c, 'users', 'avatar_url TEXT')
    add_column_safe(c, 'users', 'is_premium BOOLEAN DEFAULT FALSE')
    add_column_safe(c, 'users', 'banned_until TEXT')
    add_column_safe(c, 'users', 'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    add_column_safe(c, 'users', 'premium_until TEXT')
    add_column_safe(c, 'users', 'last_seen TEXT')
    add_column_safe(c, 'users', 'last_read_notif_id INTEGER DEFAULT 0')

    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (id SERIAL PRIMARY KEY, user_id INTEGER, title TEXT, url TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS notifications 
                 (id SERIAL PRIMARY KEY, message TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS hidden_notifications 
                 (user_id INTEGER, notification_id INTEGER)''')
    add_column_safe(c, 'notifications', 'user_id INTEGER')
    conn.commit()
    conn.close()

# Rate Limiter
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
        self.requests[ip] = [t for t in self.requests[ip] if t > now - period]
        if len(self.requests[ip]) >= max_reqs:
            return False
        self.requests[ip].append(now)
        return True

limiter = RateLimiter()

def check_limit(limit_type='global'):
    ip = request.remote_addr
    return not limiter.is_allowed(ip, limit_type)

# Функция для принудительного удаления (если файл занят или read-only)
def remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)

# Task Manager
class TaskManager:
    def __init__(self):
        self.tasks = {}
        self.info_cache = {}
        self.lock = threading.Lock()
        threading.Thread(target=self._cleanup_loop, daemon=True).start()

    def create_task(self):
        with self.lock:
            tid = str(uuid.uuid4())
            self.tasks[tid] = {'status': 'starting', 'progress': '0', 'start_time': time.time()}
            return tid

    def get_task(self, tid):
        with self.lock:
            return self.tasks.get(tid)

    def update_task(self, tid, **kwargs):
        with self.lock:
            if tid in self.tasks:
                self.tasks[tid].update(kwargs)

    def get_cached_info(self, url):
        with self.lock:
            cache = self.info_cache.get(url)
            if cache:
                # Кэш валиден 1 час
                if time.time() - cache['timestamp'] < 3600:
                    return cache['data']
                else:
                    del self.info_cache[url]
            return None

    def cache_info(self, url, data):
        with self.lock:
            self.info_cache[url] = {'data': data, 'timestamp': time.time()}

    def cleanup(self):
        with self.lock:
            current_time = time.time()
            old_tasks = [tid for tid, task in self.tasks.items() if current_time - task['start_time'] > 3600]
            for tid in old_tasks:
                del self.tasks[tid]
            
            # Очистка старого кэша
            old_cache = [url for url, cache in self.info_cache.items() if current_time - cache['timestamp'] > 3600]
            for url in old_cache:
                del self.info_cache[url]
        
        # Очистка файлов
        try:
            for filename in os.listdir(DOWNLOAD_FOLDER):
                filepath = os.path.join(DOWNLOAD_FOLDER, filename)
                if os.path.getmtime(filepath) < current_time - 3600:
                    try:
                        if os.path.isfile(filepath): os.remove(filepath)
                        elif os.path.isdir(filepath): shutil.rmtree(filepath, onerror=remove_readonly)
                    except Exception: pass
        except Exception: pass

    def _cleanup_loop(self):
        while True:
            self.cleanup()
            time.sleep(600)

task_manager = TaskManager()
init_db()