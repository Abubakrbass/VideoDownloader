from flask import Blueprint, request, redirect, render_template, session, url_for, render_template_string
from extensions import get_db, csrf
from services import FreedomPayService, FREEDOM_MERCHANT_ID, FREEDOM_SECRET_KEY
import time
import logging
from datetime import datetime, timedelta

payment_bp = Blueprint('payment', __name__)
logger = logging.getLogger(__name__)

@payment_bp.route('/premium')
def premium_page():
    return render_template('premium.html')

@payment_bp.route('/buy_premium')
def buy_premium():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    
    # Проверка наличия настроек
    if not FREEDOM_MERCHANT_ID or not FREEDOM_SECRET_KEY:
        return render_template('info.html', title='Ошибка', content='Прием платежей временно недоступен.', icon='exclamation-triangle-fill')

    try:
        plan = request.args.get('plan', 'month')
        currency = request.args.get('currency', 'RUB')
        
        # Цены (примерные курсы, как просил пользователь)
        prices = {
            'month': {'RUB': '199', 'KGS': '200', 'USD': '3'},
            'year': {'RUB': '500', 'KGS': '500', 'USD': '6'}
        }
        
        amount = prices.get(plan, prices['month']).get(currency, '199')
        desc = f"Premium {plan} Video Downloader"

        # Параметры для Freedom Pay (PayBox)
        order_id = f"{session['user_id']}-{int(time.time())}"
        script_name = 'pay.php' # Скрипт инициализации оплаты
        
        params = {
            'pg_merchant_id': FREEDOM_MERCHANT_ID,
            'pg_amount': amount,
            'pg_currency': currency,
            'pg_description': desc,
            'pg_salt': str(int(time.time())), # Случайная соль
            'pg_order_id': order_id,
            'pg_check_url': url_for('payment.freedom_callback', _external=True), # URL проверки (опционально)
            'pg_result_url': url_for('payment.freedom_callback', _external=True), # URL результата (callback)
            'pg_success_url': url_for('payment.payment_success', _external=True), # Куда вернуть юзера после успеха
            'pg_request_method': 'GET'
        }
        
        # Генерируем подпись
        params['pg_sig'] = FreedomPayService.generate_signature(script_name, params, FREEDOM_SECRET_KEY)
        
        # Рендерим авто-сабмит форму
        form_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Redirecting...</title></head>
        <body onload="document.forms[0].submit()">
            <div style="text-align:center; margin-top: 20%; font-family: sans-serif;">
                <p>Перенаправление на оплату Freedom Pay...</p>
                <img src="https://cdn.freekassa.net/banners/big-dark-2.png" style="height:50px; opacity:0.5;">
            </div>
            <form action="https://api.freedompay.money/pay.php" method="GET">
                {% for key, value in params.items() %}
                <input type="hidden" name="{{ key }}" value="{{ value }}">
                {% endfor %}
            </form>
        </body>
        </html>
        """
        return render_template_string(form_html, params=params)
        
    except Exception as e:
        return render_template('info.html', title='Ошибка оплаты', content=f'Не удалось создать платеж: {str(e)}', icon='exclamation-triangle-fill')

@payment_bp.route('/payment/freedom/callback', methods=['GET', 'POST'])
@csrf.exempt 
def freedom_callback():
    # Обработка уведомления от Freedom Pay
    try:
        data = request.values.to_dict()
        logger.info(f"Freedom Pay Callback: {data}")
        
        # Здесь нужно проверить подпись (pg_sig)
        # if not FreedomPayService.check_signature(data, FREEDOM_SECRET_KEY, data.get('pg_sig')):
        #    return "Error signature", 400
        
        if data.get('pg_result') == '1': # Успех
            order_id = data.get('pg_order_id')
            user_id = int(order_id.split('-')[0])
            
            with get_db() as conn:
                # Строгая проверка суммы
                amount = float(data.get('pg_amount', 0))
                days = 0
                
                # Цены: Месяц (199 RUB, 200 KGS, 3 USD), Год (500 RUB, 500 KGS, 6 USD)
                if amount in [199.0, 200.0, 3.0]:
                    days = 30
                elif amount in [500.0, 6.0]:
                    days = 365
                
                if days > 0:
                    premium_until = (datetime.now() + timedelta(days=days)).isoformat()
                    conn.execute('UPDATE users SET premium_until = ? WHERE id = ?', (premium_until, user_id))
                    conn.commit()
                
            return "OK" # Ответ для Freedom Pay
            
    except Exception as e:
        logger.error(f"Payment error: {e}")
        
    return "Error", 400

@payment_bp.route('/payment/success')
def payment_success():
    return render_template('info.html', title='Оплата успешна', content='Спасибо! Premium активирован.', icon='check-circle-fill')