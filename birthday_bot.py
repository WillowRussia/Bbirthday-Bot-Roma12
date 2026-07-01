import json
import os
import requests
from datetime import datetime
import pytz

# Настройки прокси (если нужно)
PROXY_CONFIG = {
    'use_proxy': False,
    'proxy_url': '', 
}

def get_session():
    session = requests.Session()
    if PROXY_CONFIG['use_proxy'] and PROXY_CONFIG['proxy_url']:
        proxies = {
            'http': PROXY_CONFIG['proxy_url'],
            'https': PROXY_CONFIG['proxy_url']
        }
        session.proxies.update(proxies)
    session.timeout = 10
    return session

def get_today_birthdays_tashkent():
    """
    Получает список людей, у которых сегодня день рождения 
    ПО ЧАСОВОМУ ПОЯСУ ТАШКЕНТА (UTC+5)
    """
    # Устанавливаем часовой пояс Ташкента
    tz_tashkent = pytz.timezone('Asia/Tashkent')
    
    # Получаем текущее время в Ташкенте
    now_tashkent = datetime.now(tz_tashkent)
    
    current_day = now_tashkent.day
    current_month = now_tashkent.month
    
    print(f" Текущее время в Ташкенте: {now_tashkent.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Проверяем дни рождения на: {current_day}.{current_month}")

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
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('CHAT_ID')
    
    if not birthdays_list:
        print("✅ Сегодня (по Ташкенту) нет дней рождений")
        return
    
    mentions = [format_mention(person) for person in birthdays_list]
    
    if len(mentions) == 1:
        message = f"🎉 Сегодня день рождения у {mentions[0]}! Поздравляем! 🎂🎁"
    elif len(mentions) == 2:
        message = f" Сегодня дни рождения у {mentions[0]} и {mentions[1]}! Поздравляем! 🎁"
    else:
        names_with_and = ", ".join(mentions[:-1]) + f" и {mentions[-1]}"
        message = f"🎉 Сегодня дни рождения у: {names_with_and}! Поздравляем! 🎁"
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    session = get_session()
    
    try:
        print(f"🔄 Отправка сообщения...")
        response = session.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ Сообщение успешно отправлено!")
        else:
            print(f"❌ Ошибка API Telegram: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка сети: {e}")

if __name__ == '__main__':
    try:
        birthdays = get_today_birthdays_tashkent()
        send_telegram_message(birthdays)
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        exit(1)