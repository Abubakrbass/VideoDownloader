#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы скачивания видео
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services import download_service

# Используем универсальное видео для тестирования
test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

print(f"🔍 Тестируем: {test_url}")
print("=" * 60)

try:
    print("⏳ Получаем информацию о видео...")
    info = download_service.get_video_info(test_url)
    
    print("✅ Успешно!")
    print(f"   Название: {info.get('title', 'N/A')}")
    print(f"   Канал: {info.get('uploader', 'N/A')}")
    print(f"   Длительность: {info.get('duration', 'N/A')} сек")
    print(f"   Количество просмотров: {info.get('view_count', 'N/A')}")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    error_str = str(e).lower()
    if 'not a bot' in error_str or 'sign in' in error_str:
        print("\n⚠️  YouTube требует аутентификацию!")
        print("\n✅ Решение: Обновите cookies.txt")
        print("   1. Прочитайте файл COOKIES_SETUP.md")
        print("   2. Установите расширение 'Get cookies.txt'")
        print("   3. Экспортируйте cookies с youtube.com")
        print("   4. Сохраните как cookies.txt в текущую папку")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ Тест пройден! Скачивание видео должно работать.")
