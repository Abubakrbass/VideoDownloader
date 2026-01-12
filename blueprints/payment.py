from flask import Blueprint, request, redirect, url_for, render_template, session
from services import PaymentService, FREEKASSA_MERCHANT_ID, FREEKASSA_SECRET_1, FREEKASSA_SECRET_2
from extensions import get_db, csrf
from models import UserRepository
import time
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

payment_bp = Blueprint('payment', __name__, url_prefix='/payment')

@payment_bp.route('/buy_premium')
def buy_premium():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    
    with get_db() as conn:
        user = conn.execute('SELECT is_premium, email FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    is_premium = False
    if user:
        if user['is_premium']: is_premium = True
    
    if is_premium:
        return render_template('info.html', title='Уже Premium', content='У вас уже есть Premium статус!', icon='check-circle-fill')

    if not FREEKASSA_MERCHANT_ID or not FREEKASSA_SECRET_1:
        logger.error("Не настроены ключи FreeKassa в .env")
        return render_template('info.html', title='Ошибка', content='Прием платежей временно недоступен (не настроена касса).', icon='exclamation-triangle-fill')

    try:
        merchant_id = FREEKASSA_MERCHANT_ID
        secret_word = FREEKASSA_SECRET_1
        amount, currency = PaymentService.get_amount_and_currency(request.args.get('currency', 'RUB'))
        
        order_id = f"{session['user_id']}-{int(time.time())}"
        
        sign = PaymentService.generate_signature(merchant_id, amount, secret_word, currency, order_id)
        
        user_email = user['email'] if user and user['email'] else ''
        
        url = f"https://pay.freekassa.ru/?m={merchant_id}&oa={amount}&o={order_id}&s={sign}&currency={currency}&em={user_email}&lang=ru"
        
        return redirect(url)
    except Exception as e:
        return render_template('info.html', title='Ошибка оплаты', content=f'Не удалось создать платеж: {str(e)}', icon='exclamation-triangle-fill')

@payment_bp.route('/freekassa/callback', methods=['POST'])
@csrf.exempt 
def freekassa_callback():
    merchant_id = request.form.get('MERCHANT_ID')
    amount = request.form.get('AMOUNT')
    merchant_order_id = request.form.get('MERCHANT_ORDER_ID')
    sign = request.form.get('SIGN')
    
    if not PaymentService.validate_signature(merchant_id, amount, FREEKASSA_SECRET_2, merchant_order_id, sign):
        return "Wrong signature", 400
    
    if not PaymentService.validate_amount(amount):
        return "Wrong amount format", 400
    
    try:
        user_id = int(merchant_order_id.split('-')[0])
        with get_db() as conn:
            # Проверяем текущую подписку, чтобы продлить её, а не перезаписать
            user = conn.execute('SELECT premium_until FROM users WHERE id = ?', (user_id,)).fetchone()
            current_until = None
            if user and user['premium_until']:
                try:
                    current_until = datetime.fromisoformat(user['premium_until'])
                except: pass
            
            now = datetime.now()
            start_date = current_until if (current_until and current_until > now) else now
            premium_until = (start_date + timedelta(days=30)).isoformat()
            
            conn.execute('UPDATE users SET premium_until = ? WHERE id = ?', (premium_until, user_id))
            conn.commit()
    
    except Exception as e:
        logger.error(f"Не удалось обновить Premium в БД: {e}")
        return "Error", 500
        
    return "YES"

@payment_bp.route('/success')
def payment_success():
    return render_template('info.html', title='Оплата проверяется', content='Спасибо за покупку! Ваш Premium активируется в течение пары минут.', icon='check-circle-fill')

@payment_bp.route('/cancel')
def payment_cancel():
    return render_template('info.html', title='Оплата отменена', content='Вы отменили процесс оплаты. Деньги не списаны.', icon='x-circle-fill')
