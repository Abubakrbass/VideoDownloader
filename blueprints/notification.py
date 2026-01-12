from flask import Blueprint, request, jsonify, session
from extensions import get_db, socketio

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/check_notifications')
def check_notifications():
    last_id = request.args.get('last_id', 0, type=int)
    
    with get_db() as conn:
        notifs = []
        if last_id > 0:
            if 'user_id' in session:
                notifs = conn.execute('SELECT * FROM notifications WHERE id > ? AND (user_id IS NULL OR user_id = ?)', (last_id, session['user_id'])).fetchall()
            else:
                notifs = conn.execute('SELECT * FROM notifications WHERE id > ? AND user_id IS NULL', (last_id,)).fetchall()
        
        unread_count = 0
        if 'user_id' in session:
            user = conn.execute('SELECT last_read_notif_id FROM users WHERE id = ?', (session['user_id'],)).fetchone()
            last_read = user['last_read_notif_id'] if user and user['last_read_notif_id'] else 0
            
            unread_count = conn.execute('''
                SELECT COUNT(*) FROM notifications 
                WHERE id > ?
                AND (user_id IS NULL OR user_id = ?)
                AND id NOT IN (SELECT notification_id FROM hidden_notifications WHERE user_id = ?)
            ''', (last_read, session['user_id'], session['user_id'])).fetchone()[0]

        if last_id == 0:
            cur = conn.execute('SELECT MAX(id) FROM notifications')
            row = cur.fetchone()
            max_id = row[0] if row and row[0] else 0
            return jsonify({'notifications': [], 'last_id': max_id, 'unread_count': unread_count})
    
    result = [{'id': row['id'], 'message': row['message']} for row in notifs]
    new_last_id = result[-1]['id'] if result else last_id
    
    return jsonify({'notifications': result, 'last_id': new_last_id, 'unread_count': unread_count})

@notification_bp.route('/notification_history')
def notification_history():
    if 'user_id' not in session: return jsonify([])
    with get_db() as conn:
        query = '''
            SELECT * FROM notifications
            WHERE (user_id IS NULL OR user_id = ?)
            AND id NOT IN (SELECT notification_id FROM hidden_notifications WHERE user_id = ?)
            ORDER BY created_at DESC LIMIT 20
        '''
        notifs = conn.execute(query, (session['user_id'], session['user_id'])).fetchall()
    return jsonify([{'id': row['id'], 'message': row['message'], 'date': row['created_at']} for row in notifs])

@notification_bp.route('/mark_notifications_read', methods=['POST'])
def mark_notifications_read():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    with get_db() as conn:
        res = conn.execute('SELECT MAX(id) FROM notifications').fetchone()
        max_id = res[0] if res and res[0] else 0
        
        conn.execute('UPDATE users SET last_read_notif_id = ? WHERE id = ?', (max_id, session['user_id']))
        conn.commit()
    return jsonify({'success': True})

@notification_bp.route('/hide_notification', methods=['POST'])
def hide_notification():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    notif_id = request.json.get('id')
    with get_db() as conn:
        conn.execute('INSERT INTO hidden_notifications (user_id, notification_id) VALUES (?, ?)', (session['user_id'], notif_id))
        conn.commit()
    return jsonify({'success': True})

@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        from flask_socketio import join_room
        join_room(f"user_{session['user_id']}")
