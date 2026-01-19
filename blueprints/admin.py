from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from extensions import get_db, ADMIN_EMAIL, socketio, AVATAR_FOLDER
from datetime import datetime, timedelta
import sqlite3
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
def before_request():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    
    with get_db() as conn:
        user = conn.execute('SELECT email FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        
        if not user or not ADMIN_EMAIL or user['email'] != ADMIN_EMAIL:
            return render_template('error.html', error_code="403", error_message="Доступ запрещен. Эта страница доступна только администратору."), 403

@admin_bp.route('/users')
def users():
    # Фильтры, Сортировка и Пагинация
    search_query = request.args.get('q', '').strip()
    sort_by = request.args.get('sort', 'newest')
    filter_status = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    if page < 1: page = 1
    per_page = 20
    
    with get_db() as conn:
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
            try:
                query = query.replace('created_at', 'id')
                all_users = conn.execute(query, query_params).fetchall()
                total_users = conn.execute(count_query, params).fetchone()[0]
            except Exception:
                all_users = []
                total_users = 0
    
    total_pages = (total_users + per_page - 1) // per_page
    
    return render_template('admin_users.html', users=all_users, now=now_str, search_query=search_query, sort_by=sort_by, filter_status=filter_status, page=page, total_pages=total_pages, online_users=online_users)

@admin_bp.route('/online_count')
def online_count():
    with get_db() as conn:
        online_users = 0
        try:
            five_mins_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
            online_users = conn.execute('SELECT COUNT(*) FROM users WHERE last_seen > ?', (five_mins_ago,)).fetchone()[0]
        except Exception: pass
    
    return jsonify({'count': online_users})

@admin_bp.route('/stats')
def stats():
    with get_db() as conn:
        # Статистика по дням (последние 30 дней)
        # Используем substr для извлечения даты YYYY-MM-DD из timestamp
        query = '''
            SELECT substr(timestamp, 1, 10) as day, COUNT(*) as count 
            FROM history 
            WHERE timestamp IS NOT NULL
            GROUP BY day 
            ORDER BY day DESC 
            LIMIT 30
        '''
        stats_data = [dict(row) for row in conn.execute(query).fetchall()]
        
        # Преобразуем для графика (нужен порядок по возрастанию даты)
        chart_data = sorted(stats_data, key=lambda x: x['day']) if stats_data else []
        
        # Общее количество скачиваний
        total_downloads = conn.execute('SELECT COUNT(*) FROM history').fetchone()[0]
        
        # Топ 10 популярных видео (по URL)
        top_videos = conn.execute('''
            SELECT title, url, COUNT(*) as count 
            FROM history 
            GROUP BY url 
            ORDER BY count DESC 
            LIMIT 10
        ''').fetchall()
        
    return render_template('admin_stats.html', stats=stats_data, chart_data=chart_data, total_downloads=total_downloads, top_videos=top_videos)

@admin_bp.route('/send_notification', methods=['POST'])
def send_notification():
    data = request.json
    message = data.get('message', '').strip()
    target_user_id = data.get('user_id')
    
    if not message:
        return jsonify({'error': 'Сообщение не может быть пустым'}), 400
    
    with get_db() as conn:
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

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if user_id == session['user_id']:
        return jsonify({'error': 'Нельзя удалить самого себя'}), 400

    with get_db() as conn:
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

@admin_bp.route('/ban_user/<int:user_id>', methods=['POST'])
def ban_user(user_id):
    if user_id == session['user_id']:
        return jsonify({'error': 'Нельзя забанить самого себя'}), 400

    data = request.json
    action = data.get('action') # 'forever', 'week', 'unban'
    
    ban_until = None
    if action == 'forever':
        ban_until = datetime(9999, 12, 31).isoformat()
    elif action == 'week':
        ban_until = (datetime.now() + timedelta(days=7)).isoformat()
    
    with get_db() as conn:
        conn.execute('UPDATE users SET banned_until = ? WHERE id = ?', (ban_until, user_id))
        conn.commit()
    return jsonify({'success': True})

@admin_bp.route('/toggle_premium/<int:user_id>', methods=['POST'])
def toggle_premium(user_id):
    with get_db() as conn:
        user = conn.execute('SELECT is_premium FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        new_status = not user['is_premium']
        conn.execute('UPDATE users SET is_premium = ? WHERE id = ?', (new_status, user_id))
        conn.commit()
    return jsonify({'success': True})
