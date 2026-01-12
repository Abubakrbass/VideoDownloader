from flask import Blueprint, jsonify, session
from extensions import get_db

history_bp = Blueprint('history', __name__)

@history_bp.route('/my_history')
def my_history():
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    with get_db() as conn:
        history = conn.execute('SELECT * FROM history WHERE user_id = ? ORDER BY timestamp DESC', (session['user_id'],)).fetchall()
    
    history_list = [{'title': row['title'], 'url': row['url'], 'date': row['timestamp']} for row in history]
    return jsonify(history_list)

@history_bp.route('/clear_history', methods=['POST'])
def clear_history():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    with get_db() as conn:
        conn.execute('DELETE FROM history WHERE user_id = ?', (session['user_id'],))
        conn.commit()
    return jsonify({'success': True})
