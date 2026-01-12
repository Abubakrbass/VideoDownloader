import os
import shutil
import smtplib
import threading
import time
import yt_dlp
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import hashlib
from flask import url_for
from markupsafe import escape
from extensions import socketio, task_manager, get_db
from models import UserRepository
import logging

logger = logging.getLogger(__name__)

SMTP_EMAIL = os.getenv('SMTP_EMAIL', "").strip()
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', "").replace(' ', '')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', "").strip()
FREEKASSA_MERCHANT_ID = os.getenv('FREEKASSA_MERCHANT_ID')
FREEKASSA_SECRET_1 = os.getenv('FREEKASSA_SECRET_1')
FREEKASSA_SECRET_2 = os.getenv('FREEKASSA_SECRET_2')

class EmailService:
    """Сервис для отправки уведомлений и писем."""
    @staticmethod
    def send_feedback(text, contact):
        try:
            logo_path = os.path.join('static', 'logo.png')
            logo_data = None
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    logo_data = f.read()

            # Экранируем ввод для защиты от XSS/Injection в письмах
            safe_text = escape(text).replace('\n', '<br>')
            safe_contact = escape(contact)

            # 1. Письмо АДМИНИСТРАТОРУ
            msg_root = MIMEMultipart('related')
            msg_root['Subject'] = "Новое сообщение с сайта Video Downloader"
            msg_root['From'] = SMTP_EMAIL
            msg_root['To'] = ADMIN_EMAIL

            msg_alternative = MIMEMultipart('alternative')
            msg_root.attach(msg_alternative)
            
            text_body = f"Сообщение от пользователя:\n{text}\n\nКонтакт для связи: {contact}"
            msg_alternative.attach(MIMEText(text_body, 'plain', 'utf-8'))

            html_body = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <img src="cid:logo_image" alt="Logo" style="width: 60px;">
                    <h2 style="color: #212529;">Новое сообщение</h2>
                </div>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6;">
                    {safe_text}
                </div>
                <p style="margin-top: 20px;"><b>От кого:</b> {safe_contact}</p>
                <div style="text-align: center; margin-top: 30px;">
                    <a href="mailto:{safe_contact}?subject=Re: Ваш вопрос" style="background: #0d6efd; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Ответить</a>
                </div>
            </div>
            """
            msg_alternative.attach(MIMEText(html_body, 'html', 'utf-8'))

            if logo_data:
                img = MIMEImage(logo_data)
                img.add_header('Content-ID', '<logo_image>')
                msg_root.attach(img)
            
            # 2. Письмо ПОЛЬЗОВАТЕЛЮ (Автоответ)
            reply_root = MIMEMultipart('related')
            reply_root['Subject'] = "Мы получили ваше сообщение | Video Downloader"
            reply_root['From'] = SMTP_EMAIL
            reply_root['To'] = contact

            reply_alternative = MIMEMultipart('alternative')
            reply_root.attach(reply_alternative)
            
            reply_html = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; color: #333; text-align: center;">
                <img src="cid:logo_image" alt="Logo" style="width: 80px; margin-bottom: 20px;">
                <h2 style="color: #212529;">Спасибо за обращение!</h2>
                <p>Мы получили ваше сообщение и ответим в течение 24 часов.</p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
                <a href="{url_for('main.index', _external=True)}" style="color: #0d6efd; text-decoration: none;">Вернуться на сайт</a>
            </div>
            """
            reply_alternative.attach(MIMEText(reply_html, 'html', 'utf-8'))

            if logo_data:
                img = MIMEImage(logo_data)
                img.add_header('Content-ID', '<logo_image>')
                reply_root.attach(img)
            
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(SMTP_EMAIL, SMTP_PASSWORD)
                server.send_message(msg_root)
                server.send_message(reply_root)
                
            return True
        except Exception as e:
            logger.error(f"Email error: {e}")
            raise e

class PaymentService:
    """Сервис для работы с платежами."""
    @staticmethod
    def generate_signature(merchant_id, amount, secret, currency, order_id):
        sign_str = f"{merchant_id}:{amount}:{secret}:{currency}:{order_id}"
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest()

    @staticmethod
    def validate_signature(merchant_id, amount, secret, order_id, received_sign):
        # SECURITY: MD5 - требование FreeKassa. 
        sign_str = f"{merchant_id}:{amount}:{secret}:{order_id}"
        my_sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
        return my_sign == received_sign

    @staticmethod
    def get_amount_and_currency(req_currency):
        if req_currency == 'USD':
            return "2.99", "USD"
        return "199", "RUB"

    @staticmethod
    def validate_amount(amount):
        try:
            val = float(amount)
            # Разрешаем 199 RUB или 2.99 USD (с учетом погрешности float)
            return (198 <= val <= 200) or (2.9 <= val <= 3.1)
        except ValueError:
            return False

class DownloadService:
    """Сервис для скачивания видео и обработки."""
    
    def get_video_info(self, url):
        ydl_opts = {
            'quiet': True,
            'cachedir': False,
            'extract_flat': 'in_playlist',
        }
        # Прокси можно добавить здесь, если нужно
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception:
            if 'extractor_args' in ydl_opts: del ydl_opts['extractor_args']
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

    def calculate_sizes(self, info, is_premium=False):
        formats = info.get('formats', [])
        duration = info.get('duration')
        
        # Находим максимальное доступное разрешение видео
        max_height = 0
        for f in formats:
            h = f.get('height')
            if h:
                try: max_height = max(max_height, int(h))
                except: pass

        try: duration = float(duration) if duration else 0
        except: duration = 0
        
        def get_size(f):
            size = f.get('filesize') or f.get('filesize_approx')
            if size: return size
            if duration:
                tbr = f.get('tbr')
                if tbr: return int(tbr * 1000 / 8 * duration)
                # Если нет общего битрейта, пробуем сложить видео + аудио
                vbr = f.get('vbr')
                abr = f.get('abr')
                if vbr:
                    return int((vbr + (abr or 0)) * 1000 / 8 * duration)
            return 0

        audio_size = 0
        for f in formats:
            if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                audio_size = max(audio_size, get_size(f))
        
        def calc_total_size(height):
            best_premerged = 0
            for f in formats:
                h = f.get('height', 0) or 0
                try: h = int(h)
                except: h = 0
                if abs(h - height) < 20 and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    best_premerged = max(best_premerged, get_size(f))
            
            if best_premerged > 0: return best_premerged

            v_size_only = 0
            for f in formats:
                h = f.get('height', 0) or 0
                try: h = int(h)
                except: h = 0
                if abs(h - height) < 20 and f.get('vcodec') != 'none' and f.get('acodec') == 'none':
                    v_size_only = max(v_size_only, get_size(f))
            
            return v_size_only + audio_size if v_size_only > 0 else 0

        def fmt_size(bytes_val):
            if not bytes_val: return "?"
            return f"{bytes_val / (1024 * 1024):.1f} MB"

        crown = '👑 ' if not is_premium else ''
        sizes = {}
        sizes['best'] = crown + fmt_size(calc_total_size(max_height) or calc_total_size(1080))
        sizes['1080'] = crown + fmt_size(calc_total_size(1080))
        sizes['720'] = fmt_size(calc_total_size(720))
        sizes['audio'] = fmt_size(audio_size)
        return sizes

    def background_download(self, task_id, url, quality, user_id, ratelimit, limit_height, sleep_interval):
        try:
            task_manager.update_task(task_id, status='downloading', progress=0)
            
            def progress_hook(d):
                if d['status'] == 'downloading':
                    p = d.get('_percent_str', '0%').replace('%','')
                    task_manager.update_task(task_id, progress=p, message=d.get('_eta_str', ''))
                elif d['status'] == 'finished':
                    task_manager.update_task(task_id, status='processing', progress='100')
            
            # Явно ищем FFmpeg в системе
            ffmpeg_path = shutil.which('ffmpeg') or shutil.which('ffmpeg.exe')

            ydl_opts = {
                'outtmpl': f'downloads/{task_id}_%(title)s.%(ext)s',
                'progress_hooks': [progress_hook],
                'quiet': True,
                'merge_output_format': 'mp4', # Принудительно склеивать в MP4 (лучшая совместимость)
            }
            
            # Если нашли FFmpeg, указываем путь к нему (критично для Render/Windows)
            if ffmpeg_path:
                ydl_opts['ffmpeg_location'] = ffmpeg_path

            # Оптимизация для Premium (ускорение)
            if not ratelimit:
                ydl_opts['concurrent_fragment_downloads'] = 5  # Скачивать 5 фрагментов одновременно
                ydl_opts['buffersize'] = 1024 * 1024  # Увеличенный буфер

            if ratelimit:
                ydl_opts['ratelimit'] = ratelimit
            
            if sleep_interval:
                ydl_opts['sleep_interval'] = sleep_interval

            # Приоритет аудио m4a (AAC) для лучшей совместимости с MP4
            audio_q = 'bestaudio[ext=m4a]/bestaudio'

            # Логика выбора формата
            if quality == 'audio':
                ydl_opts['format'] = 'bestaudio/best'
            else:
                if limit_height:
                    # Пытаемся скачать видео+аудио, если не выйдет - лучший одиночный файл
                    ydl_opts['format'] = f'bestvideo[height<={limit_height}]+{audio_q}/best[height<={limit_height}]/best'
                elif quality == '1080':
                    ydl_opts['format'] = f'bestvideo[height<=1080]+{audio_q}/best[height<=1080]/best'
                elif quality == '720':
                    ydl_opts['format'] = f'bestvideo[height<=720]+{audio_q}/best[height<=720]/best'
                else:
                    ydl_opts['format'] = f'bestvideo+{audio_q}/best'
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
            
            task_manager.update_task(task_id, status='finished', filename=filename, download_name=os.path.basename(filename))
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            task_manager.update_task(task_id, status='error', error=str(e))

download_service = DownloadService()
