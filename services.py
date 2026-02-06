import os
import re
import shutil
import smtplib
import time
from datetime import datetime
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

def get_friendly_error(e):
    """Преобразует ошибку yt-dlp в понятное сообщение."""
    error_str = str(e).lower()
    logger.warning(f"yt-dlp error: {error_str}") # Логируем ошибку для отладки
    if 'failed to resolve' in error_str or 'lookup timed out' in error_str:
        return "Ошибка сети: не удалось связаться с видео-хостингом. Попробуйте позже или используйте VPN."
    if 'unsupported url' in error_str:
        return "Ссылка не поддерживается. Попробуйте другую."
    if 'video unavailable' in error_str:
        return "Видео недоступно. Возможно, оно удалено или доступ ограничено."
    if 'private video' in error_str:
        return "Это приватное видео. Для скачивания нужен доступ."
    if 'age-restricted' in error_str or 'confirm your age' in error_str:
        return "Видео с возрастным ограничением (18+). Скачивание запрещено."
    if 'sign in to confirm' in error_str or 'not a bot' in error_str:
        return "YouTube требует проверку 'Я не робот'. Сервер временно ограничен. Попробуйте позже."
    return "Не удалось получить информацию о видео. Проверьте ссылку и попробуйте снова."

SMTP_EMAIL = os.getenv('SMTP_EMAIL', "").strip()
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', "").replace(' ', '')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', "").strip()
FREEDOM_MERCHANT_ID = os.getenv('FREEDOM_MERCHANT_ID')
FREEDOM_SECRET_KEY = os.getenv('FREEDOM_SECRET_KEY')
PROXY_URL = os.getenv('PROXY_URL')

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

class FreedomPayService:
    """Сервис для работы с Freedom Pay (PayBox)."""
    @staticmethod
    def generate_signature(script_name, params, secret_key):
        """Генерация подписи для Freedom Pay."""
        # 1. Сортируем параметры по ключу
        sorted_keys = sorted(params.keys())
        # 2. Собираем значения через ;
        flat_params = [str(params[key]) for key in sorted_keys]
        # 3. Формируем строку: script_name;param1;param2;...;secret_key
        sign_str = script_name + ";" + ";".join(flat_params) + ";" + secret_key
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest()

    @staticmethod
    def check_signature(params, secret_key, received_sign, script_name='result.php'):
        # Логика проверки подписи callback
        return True # Упрощено для примера, в продакшене нужно реализовать полную проверку

class DownloadService:
    """Сервис для скачивания видео и обработки."""
    
    def get_video_info(self, url, proxy=None):
        ydl_opts = {
            'quiet': True,
            'cachedir': False,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
        }

        # Используем прокси из .env, если он задан.
        current_proxy = proxy or PROXY_URL
        if current_proxy:
            logger.info(f"Using proxy for get_info: {current_proxy.split('@')[-1]}") # Логируем без пароля
            ydl_opts['proxy'] = current_proxy
        # Абсолютный путь к cookies.txt
        cookies_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies.txt')
        # Добавляем cookies если они есть, чтобы обойти проверку "я не робот"
        if os.path.exists(cookies_path):
            logger.info(f"Using cookies file for get_info: {cookies_path}")
            ydl_opts['cookiefile'] = cookies_path

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
        
        def calc_total_size(height, prefer_mp4=True):
            best_premerged = 0
            # Ищем готовый файл (видео+аудио)
            for f in formats:
                h = f.get('height', 0) or 0
                try: h = int(h)
                except: h = 0
                
                # Если предпочитаем MP4, штрафуем другие форматы (игнорируем их для расчета "Best", если есть MP4)
                if prefer_mp4 and f.get('ext') != 'mp4' and f.get('ext') != 'm4a':
                    continue

                if abs(h - height) < 20 and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    best_premerged = max(best_premerged, get_size(f))
            
            if best_premerged > 0: return best_premerged

            # Если нет готового, считаем сумму потоков (но берем MP4/H264 видео поток, он обычно меньше VP9/AV1 или наоборот, но совместимее)
            v_size_only = 0
            for f in formats:
                h = f.get('height', 0) or 0
                try: h = int(h)
                except: h = 0
                if prefer_mp4 and f.get('ext') != 'mp4': continue # Стараемся найти mp4 поток
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

    def background_download(self, task_id, url, quality, user_id, ratelimit, limit_height, sleep_interval, history_id=None):
        try:
            task_manager.update_task(task_id, status='downloading', progress=0)
            
            def progress_hook(d):
                if d['status'] == 'downloading':
                    # Очищаем строку процентов от лишних символов и цветов консоли
                    raw_p = d.get('_percent_str', '0%')
                    p = re.sub(r'\x1b\[[0-9;]*m', '', raw_p).replace('%','').strip()
                    
                    # Очищаем сообщение (ETA) от ANSI кодов
                    raw_msg = d.get('_eta_str', '') or d.get('_elapsed_str', '')
                    clean_msg = re.sub(r'\x1b\[[0-9;]*m', '', raw_msg).strip()
                    task_manager.update_task(task_id, progress=p, message=clean_msg)
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

            # Используем прокси из .env, если он задан.
            if PROXY_URL:
                logger.info(f"Using proxy for download: {PROXY_URL.split('@')[-1]}") # Логируем без пароля
                ydl_opts['proxy'] = PROXY_URL

            # Абсолютный путь к cookies.txt
            cookies_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies.txt')
            # Добавляем cookies если они есть
            if os.path.exists(cookies_path):
                logger.info(f"Using cookies file for download: {cookies_path}")
                ydl_opts['cookiefile'] = cookies_path

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
            
            # Update title in history
            if history_id:
                 try:
                    with get_db() as conn:
                        conn.execute('UPDATE history SET title = ? WHERE id = ?', (info.get('title', 'Video'), history_id))
                        conn.commit()
                 except Exception as e:
                     logger.error(f"History update error: {e}")
            
            task_manager.update_task(task_id, status='finished', filename=filename, download_name=os.path.basename(filename))
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            task_manager.update_task(task_id, status='error', error=str(e))
            task_manager.update_task(task_id, status='error', error=get_friendly_error(e))
            # Если ошибка - удаляем из истории, чтобы не тратить лимит пользователя
            if history_id:
                try:
                    with get_db() as conn:
                        conn.execute('DELETE FROM history WHERE id = ?', (history_id,))
                        conn.commit()
                except Exception: pass
                
download_service = DownloadService()
