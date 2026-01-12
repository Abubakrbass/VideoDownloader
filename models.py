from extensions import get_db, ADMIN_EMAIL
from datetime import datetime

class UserRepository:
    """Инкапсулирует логику работы с пользователями."""
    @staticmethod
    def get_user(user_id):
        with get_db() as conn:
            return conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    @staticmethod
    def is_premium(user_row):
        if not user_row: return False
        # Безопасная проверка email админа
        user_email = user_row['email'] or ''
        if ADMIN_EMAIL and user_email.strip().lower() == ADMIN_EMAIL.strip().lower(): return True
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
