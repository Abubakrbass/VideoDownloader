import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import time
from datetime import datetime, timedelta

# Добавляем путь к приложению, чтобы импортировать модули
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем тестируемые компоненты из app.py
from app import get_friendly_error, RateLimiter, TaskManager, UserRepository, DownloadService

class TestHelperFunctions(unittest.TestCase):
    """Тестирование вспомогательных функций"""
    
    def test_get_friendly_error(self):
        # Тестируем различные ветки условий (Branch Coverage)
        self.assertEqual(get_friendly_error("Sign in to confirm your age"), "Видео 18+. Скачивание контента с возрастным ограничением запрещено.")
        self.assertEqual(get_friendly_error("Video unavailable"), "Видео недоступно (удалено, скрыто или не существует).")
        self.assertEqual(get_friendly_error("HTTP Error 429"), "Слишком много запросов. YouTube временно ограничил доступ.")
        # Тестируем дефолтное поведение
        self.assertEqual(get_friendly_error("Unknown error"), "Ошибка: Unknown error")

class TestRateLimiter(unittest.TestCase):
    """Тестирование логики ограничения частоты запросов"""
    
    def test_is_allowed(self):
        limiter = RateLimiter()
        ip = "127.0.0.1"
        
        # Первый запрос должен быть разрешен
        self.assertTrue(limiter.is_allowed(ip, 'global'))
        
        # Имитируем превышение лимита
        # Лимит 'global' = 60. Добавляем 60 записей вручную.
        limiter.requests[ip] = [time.time()] * 60
        
        # 61-й запрос должен быть отклонен
        self.assertFalse(limiter.is_allowed(ip, 'global'))

class TestTaskManager(unittest.TestCase):
    """Тестирование менеджера задач (State Management)"""
    
    def setUp(self):
        self.tm = TaskManager()

    def test_create_task(self):
        tid = self.tm.create_task()
        self.assertIsNotNone(tid)
        task = self.tm.get_task(tid)
        self.assertEqual(task['status'], 'starting')
        self.assertEqual(task['progress'], '0')

    def test_update_task(self):
        tid = self.tm.create_task()
        self.tm.update_task(tid, status='downloading', progress='50')
        task = self.tm.get_task(tid)
        self.assertEqual(task['status'], 'downloading')
        self.assertEqual(task['progress'], '50')

    def test_cleanup(self):
        # Создаем "старую" задачу
        tid = self.tm.create_task()
        # Имитируем, что задача создана 2 часа назад
        with self.tm.lock:
            self.tm.tasks[tid]['start_time'] = time.time() - 7200
            
        self.tm.cleanup()
        self.assertIsNone(self.tm.get_task(tid))

class TestUserRepository(unittest.TestCase):
    """Тестирование бизнес-логики пользователей"""

    def test_is_premium_admin(self):
        # Мокаем ADMIN_EMAIL в модуле app, чтобы проверить логику админа
        with patch('app.ADMIN_EMAIL', 'admin@test.com'):
            user = {'email': 'admin@test.com', 'is_premium': 0, 'premium_until': None}
            self.assertTrue(UserRepository.is_premium(user))

    def test_is_premium_flag(self):
        # Пользователь с вечным премиумом
        user = {'email': 'user@test.com', 'is_premium': 1, 'premium_until': None}
        self.assertTrue(UserRepository.is_premium(user))

    def test_is_premium_date_valid(self):
        # Пользователь с активной подпиской
        future_date = (datetime.now() + timedelta(days=30)).isoformat()
        user = {'email': 'user@test.com', 'is_premium': 0, 'premium_until': future_date}
        self.assertTrue(UserRepository.is_premium(user))

    def test_is_premium_date_expired(self):
        # Пользователь с истекшей подпиской
        past_date = (datetime.now() - timedelta(days=1)).isoformat()
        user = {'email': 'user@test.com', 'is_premium': 0, 'premium_until': past_date}
        self.assertFalse(UserRepository.is_premium(user))

    def test_is_premium_none_user(self):
        # Неавторизованный пользователь
        self.assertFalse(UserRepository.is_premium(None))

class TestDownloadService(unittest.TestCase):
    """Тестирование сервиса загрузки с моками (без реального скачивания)"""

    @patch('app.yt_dlp.YoutubeDL') # Мокаем библиотеку скачивания
    @patch('os.makedirs')          # Мокаем создание папок
    @patch('os.listdir')           # Мокаем чтение папки
    @patch('shutil.move')          # Мокаем перемещение файла
    @patch('os.remove')            # Мокаем удаление файла
    @patch('shutil.rmtree')        # Мокаем удаление папки
    def test_background_download_success(self, mock_rmtree, mock_remove, mock_move, mock_listdir, mock_makedirs, mock_ydl):
        # Настройка
        tm = TaskManager()
        ds = DownloadService(tm)
        
        # Настраиваем поведение мока yt_dlp
        ydl_instance = mock_ydl.return_value
        ydl_instance.__enter__.return_value = ydl_instance
        ydl_instance.extract_info.return_value = {'title': 'Test Video', '_type': 'video'}
        
        # Имитируем, что файл скачался в папку
        mock_listdir.return_value = ['video.mp4'] 
        
        # Создаем задачу
        tid = tm.create_task()
        
        # Запускаем метод (используем patch для os.path.exists, чтобы пройти проверки путей)
        with patch('os.path.exists', return_value=True): 
            ds.background_download(tid, 'http://test.com', 'best', None)
        
                # Проверяем результат в TaskManager
        task = tm.get_task(tid)
        self.assertEqual(task['status'], 'finished')
        self.assertEqual(task['progress'], '100')
        self.assertEqual(task['download_name'], 'video.mp4')

if __name__ == '__main__':
    unittest.main()
