from flask import Blueprint, render_template, session, jsonify
from models import UserRepository

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
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

@main_bp.route('/premium')
def premium_page():
    is_premium = False
    if 'user_id' in session:
        user = UserRepository.get_user(session['user_id'])
        is_premium = UserRepository.is_premium(user)
    return render_template('premium.html', is_premium=is_premium)

@main_bp.route('/about')
def about():
    return render_template('info.html', title='О нас', content='Video Downloader — это современный сервис для быстрого скачивания видео и аудио.<br><br>Мы поддерживаем высокое качество (до 4K) и удобные форматы.', icon='info-circle-fill')

@main_bp.route('/privacy')
def privacy():
    return render_template('info.html', title='Конфиденциальность', content='Мы ценим вашу приватность.<br><br>Наш сайт использует файлы cookie только для сохранения ваших настроек (например, темы оформления).<br>Мы не передаем ваши данные третьим лицам.', icon='shield-lock-fill')

@main_bp.route('/terms')
def terms():
    return render_template('info.html', title='Условия использования', content='Используя этот сервис, вы соглашаетесь скачивать видео только для личного ознакомления.<br><br><b>Строго запрещено скачивать контент с возрастным ограничением (18+).</b><br><br>Запрещено скачивать контент, защищенный авторским правом, без разрешения владельца.<br>Мы не несем ответственности за использование скачанных материалов.', icon='file-earmark-text-fill')

@main_bp.route('/get_limit_status')
def get_limit_status():
    if 'user_id' not in session:
        return jsonify({'count': 0, 'limit': 5, 'reached': False})
    
    user = UserRepository.get_user(session['user_id'])
    is_premium = UserRepository.is_premium(user)
    
    if is_premium:
        return jsonify({'count': 0, 'limit': '∞', 'reached': False})
        
    count = UserRepository.check_daily_limit(session['user_id'])
    return jsonify({'count': count, 'limit': 5, 'reached': count >= 5})
