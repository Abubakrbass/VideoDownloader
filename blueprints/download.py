from flask import Blueprint, request, jsonify, session, send_file
from extensions import check_limit, task_manager, get_db
from services import download_service, PROXY_URL
from models import UserRepository
import os
import threading
from datetime import datetime

download_bp = Blueprint('download', __name__)

@download_bp.route('/get_info', methods=['POST'])
def get_info():
    try:
        is_premium = False
        if 'user_id' in session:
            # Проверка лимита только если пользователь вошел
            user = UserRepository.get_user(session['user_id'])
            is_premium = UserRepository.is_premium(user)
            if user and not is_premium:
                if UserRepository.check_daily_limit(session['user_id']) >= 5:
                    return jsonify({'error': 'Дневной лимит (5/5) исчерпан. Обновитесь до Premium!'}), 403

        # Проверяем лимит запросов только для обычных пользователей
        if not is_premium and check_limit('global'):
            return jsonify({'error': 'Слишком много запросов. Подождите немного.'}), 429

        url = request.form.get('url')
        if not url:
            return jsonify({'error': 'Пустая ссылка'}), 400
        
        cached_data = task_manager.get_cached_info(url)
        if cached_data:
            return jsonify(cached_data)

        info = download_service.get_video_info(url, proxy=PROXY_URL)
            
        if info.get('age_limit') is not None and info.get('age_limit') >= 18:
            return jsonify({'error': 'Скачивание видео с возрастным ограничением (18+) запрещено.'}), 400

        if info.get('_type') == 'playlist':
            count = info.get('playlist_count') or len(info.get('entries', []))
            
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

        sizes = download_service.calculate_sizes(info)

        duration = info.get('duration')
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
            'sizes': sizes
        }
        
        task_manager.cache_info(url, result_data)
        
        return jsonify(result_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@download_bp.route('/start_download', methods=['POST'])
def start_download():
    if check_limit('heavy'):
        return jsonify({'error': 'Слишком много одновременных загрузок. Подождите минуту.'}), 429

    video_url = request.form.get('url')
    quality = request.form.get('quality', 'best')
    user_id = session.get('user_id')
    
    if not video_url:
        return jsonify({'error': "Пожалуйста, вставьте ссылку!"}), 400

    is_premium = False
    if 'user_id' in session:
        with get_db() as conn:
            user = UserRepository.get_user(session['user_id'])
        is_premium = UserRepository.is_premium(user)

    ratelimit = None
    limit_height = None
    sleep_interval = 0

    if not is_premium:
        if 'user_id' not in session:
            return jsonify({'error': 'Для скачивания войдите в аккаунт (лимит 5 видео в день).'}), 401
            
        if UserRepository.check_daily_limit(session['user_id']) >= 5:
            return jsonify({'error': 'Дневной лимит исчерпан (5/5). Купите Premium для безлимита!'}), 403
        
        if 'list=' in video_url:
             return jsonify({'error': 'Скачивание плейлистов доступно только в Premium. Для скачивания одного видео удалите "list=..." из ссылки.'}), 403

        if quality == 'best':
            return jsonify({'error': 'Лучшее качество (Original) доступно только в Premium. Выберите 720p.'}), 403
        if quality == '1080':
            return jsonify({'error': 'Качество 1080p доступно только в Premium'}), 403
        
        ratelimit = 500 * 1024
        limit_height = 720
        sleep_interval = 2
        
    task_manager.cleanup()

    task_id = task_manager.create_task()

    # Фикс лимита: Записываем в историю СРАЗУ в основном потоке
    history_id = None
    if user_id:
        try:
            with get_db() as conn:
                # Используем стандартный формат даты SQL, чтобы проверка лимита работала корректно
                cur = conn.execute('INSERT INTO history (user_id, title, url, timestamp) VALUES (?, ?, ?, ?)', 
                             (user_id, 'Скачивание...', video_url, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                conn.commit()
                history_id = cur.lastrowid
        except Exception as e:
            print(f"History save error: {e}")

    # Запускаем скачивание в отдельном потоке, чтобы не блокировать интерфейс
    thread = threading.Thread(target=download_service.background_download, args=(task_id, video_url, quality, user_id, ratelimit, limit_height, sleep_interval, history_id))
    thread.start()
    
    return jsonify({'task_id': task_id})

@download_bp.route('/progress/<task_id>')
def get_progress(task_id):
    task = task_manager.get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(task)

@download_bp.route('/get_file/<task_id>')
def get_file(task_id):
    task = task_manager.get_task(task_id)
    if not task or not task['filename']:
        return "Файл не найден (задача истекла или не существует)", 404

    try:
        if not os.path.exists(task['filename']):
            return "Файл физически отсутствует на сервере (возможно, был удален)", 404

        return send_file(task['filename'], as_attachment=True, download_name=task.get('download_name'))
    except Exception as e:
        return f"Ошибка отправки файла: {e}", 500
