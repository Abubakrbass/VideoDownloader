from flask import Blueprint, request, render_template
from services import EmailService
from extensions import check_limit
import re
import smtplib

feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route('/feedback', methods=['GET', 'POST'])
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
            EmailService.send_feedback(text, contact)
            return render_template('feedback.html', success=True)
        except smtplib.SMTPAuthenticationError:
            return render_template('info.html', title='Ошибка доступа', content='Google не принял пароль (Ошибка 535).<br>1. Проверьте, что вы используете <b>Пароль приложения</b>.<br>2. <b>Перезапустите сервер</b>, чтобы применился новый пароль.', icon='exclamation-triangle-fill')
        except Exception as e:
            return render_template('info.html', title='Ошибка', content=f'Не удалось отправить сообщение. <br>Ошибка: {e}<br><br>Убедитесь, что в app.py настроен SMTP_EMAIL и SMTP_PASSWORD.', icon='exclamation-circle-fill')

    return render_template('feedback.html')
