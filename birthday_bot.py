import json
import os
import requests
from datetime import datetime

# Настройки прокси (опционально)
# Можно использовать SOCKS5 или HTTP прокси
PROXY_CONFIG = {
    'use_proxy': False,  # Поменяй на True, если нужен прокси
    'proxy_url': 'socks5://user:password@proxy.example.com:1080',  # Пример SOCKS5
    # 'proxy_url': 'http://user:password@proxy.example.com:8080',  # Пример HTTP
}

# Зеркала API Telegram (если основное заблокировано)
# Обычно работают api.telegram.org, но можно добавить альтернативы
API_BASE_URLS = [
    'https://api.telegram.org',
    'https://api.telegram.org.bak',  # Иногда работает
]

def get_session():
    """Создаёт сессию с настройками прокси"""
    session = requests.Session()
    
    if PROXY_CONFIG['use_proxy']:
        proxies = {
            'http': PROXY_CONFIG['proxy_url'],
            'https': PROXY_CONFIG['proxy_url']
        }
        session.proxies.update(proxies)
    
    # Добавляем таймауты для надёжности
    session.timeout = 10
    
    return session

def get_today_birthdays():
    """Получает список людей, у которых сегодня день рождения"""
    today = datetime.now()
    current_day = today.day
    current_month = today.month
    
    with open('birthdays.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    birthdays_today = []
    for person in data['birthdays']:
        if person['day'] == current_day and person['month'] == current_month:
            birthdays_today.append(person)
    
    return birthdays_today

def format_mention(person):
    """Форматирует упоминание пользователя"""
    if person.get('username'):
        username = person['username'].lstrip('@')
        return f"@{username}"
    else:
        return person['display_name']

def send_telegram_message(birthdays_list):
    """Отправляет сообщение в Telegram с обработкой блокировок"""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('CHAT_ID')
    
    if not birthdays_list:
        print("✅ Сегодня нет дней рождений")
        return
    
    # Формируем список упоминаний
    mentions = [format_mention(person) for person in birthdays_list]
    
    # Формируем сообщение
    if len(mentions) == 1:
        message = f"🎉 Сегодня день рождения у {mentions[0]}! Поздравляем! 🎂🎁"
    elif len(mentions) == 2:
        message = f"🎉 Сегодня дни рождения у {mentions[0]} и {mentions[1]}! Поздравляем! 🎂🎁"
    else:
        names_with_and = ", ".join(mentions[:-1]) + f" и {mentions[-1]}"
        message = f"🎉 Сегодня дни рождения у: {names_with_and}! Поздравляем! 🎂🎁"
    
    # Пробуем отправить через разные URL
    success = False
    session = get_session()
    
    for base_url in API_BASE_URLS:
        url = f"{base_url}/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        try:
            print(f"🔄 Пытаемся отправить через: {base_url}")
            response = session.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                print("✅ Сообщение успешно отправлено!")
                print(f"📝 Текст: {message}")
                success = True
                break
            else:
                print(f"⚠️ Ошибка {response.status_code}: {response.text[:200]}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка подключения к {base_url}: {str(e)[:100]}")
            continue
    
    if not success:
        print("❌ Не удалось отправить сообщение ни через один сервер")
        # Можно добавить fallback: сохранение в лог или отправка уведомления другим способом
        raise Exception("Failed to send Telegram message")

if __name__ == '__main__':
    try:
        birthdays = get_today_birthdays()
        send_telegram_message(birthdays)
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        exit(1)