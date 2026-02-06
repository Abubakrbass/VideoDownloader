#!/usr/bin/env python3
"""
Скрипт для экспорта YouTube cookies.
Использует встроенный браузер yt-dlp или расширение браузера.

ИНСТРУКЦИИ:
1. Установите расширение "Get cookies.txt" в браузер:
   - Chrome: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbmealblebaccac8827d961f
   - Edge: https://microsoftedge.microsoft.com/addons/detail/get-cookiestxt-locally/nifmhegehaecjomjdbalbccgbjfdnlbp
   - Opera: https://addons.opera.com/extensions/details/get-cookiestxt-locally/

2. Откройте https://www.youtube.com и убедитесь что вы залогинены
3. Нажмите на расширение "Get cookies.txt" и выберите Export
4. Сохраните файл как cookies.txt в текущую директорию
5. Запустите этот скрипт
"""

import os
import sys

def check_cookies():
    """Проверяет наличие файла cookies.txt"""
    if os.path.exists('cookies.txt'):
        with open('cookies.txt', 'r') as f:
            lines = f.readlines()
            # Пропускаем комментарии
            cookie_lines = [l for l in lines if not l.startswith('#')]
            if len(cookie_lines) > 5:
                print("✅ Файл cookies.txt найден и содержит cookies")
                print(f"   Количество cookies: {len(cookie_lines)}")
                return True
    return False

if __name__ == '__main__':
    print(__doc__)
    
    if not check_cookies():
        print("\n⚠️  Файл cookies.txt не найден или пуст")
        print("\nШаги:")
        print("1. Перейдите на https://www.youtube.com")
        print("2. Убедитесь что вы залогинены в YouTube")
        print("3. Установите расширение 'Get cookies.txt'")
        print("4. Нажмите на значок расширения")
        print("5. Выберите 'Export'")
        print("6. Сохраните как cookies.txt в текущую папку")
        sys.exit(1)
    else:
        print("\n✅ Все готово! Cookies успешно экспортированы.")
        print("\nТеперь запустите:")
        print("  git add cookies.txt")
        print("  git commit -m 'Update YouTube cookies'")
        print("  git push")
