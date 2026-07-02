import json
import os
import requests
from datetime import datetime
import pytz

FLAG_FILE = 'sent_today.flag'

def get_session():
    session = requests.Session()
    session.timeout = 10
    return session

def is_already_sent(tashkent_date_str):
    """Читает флаг из репозитория"""
    if not os.path.exists(FLAG_FILE):
        return False
    
    try:
        with open(FLAG_FILE, 'r') as f:
            saved_date = f.read().strip()
        return saved_date == tashkent_date_str
    except Exception:
        return False

def mark_as_sent(tashkent_date_str):
    """Записывает дату в локальный файл (потом закоммитится в YAML)"""
    with open(FLAG_FILE, 'w') as f:
        f.write(tashkent_date_str)
    print(f"💾 Создан/обновлен файл статуса: {tashkent_date_str}")

def get_today_birthdays():
    tz_tashkent = pytz.timezone('Asia/Tashkent')
    now_tashkent = datetime.now(tz_tashkent)
    
    current_day = now_tashkent.day
    current_month = now_tashkent.month
    date_str = now_tashkent.strftime('%Y-%m-%d')
    
    print(f"🕰️ Время в Ташкенте: {now_tashkent.strftime('%Y-%m-%d %H:%M:%S')}")

    # Проверка дублей через Git-файл
    if is_already_sent(date_str):
        print("✅ Поздравления уже были отправлены сегодня. Пропускаем.")
        return None, None

    with open('birthdays.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    birthdays = [p for p in data['birthdays'] 
                 if p['day'] == current_day and p['month'] == current_month]
    
    return birthdays, date_str

def format_mention(person):
    if person.get('username'):
        return f"@{person['username'].lstrip('@')}"
    return person['display_name']

def send_telegram_message(birthdays_list, date_str):
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('CHAT_ID')
    
    if not birthdays_list:
        print("ℹ️ Сегодня нет именинников")
        # Всё равно ставим метку, чтобы не проверять повторно
        mark_as_sent(date_str)
        return
    
    mentions = [format_mention(p) for p in birthdays_list]
    
    if len(mentions) == 1:
        msg = f"🎉 Сегодня день рождения у {mentions[0]}! Поздравляем! 🎂"
    elif len(mentions) == 2:
        msg = f"🎉 Дни рождения у {mentions[0]} и {mentions[1]}! Поздравляем! "
    else:
        names = ", ".join(mentions[:-1]) + f" и {mentions[-1]}"
        msg = f" Дни рождения у: {names}! Поздравляем! 🎂"
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': msg, 'parse_mode': 'HTML'}
    
    try:
        response = get_session().post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Сообщение отправлено!")
            mark_as_sent(date_str) # Ставим метку только после успеха
        else:
            print(f"❌ Ошибка Telegram API: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка сети: {e}")

if __name__ == '__main__':
    try:
        birthdays, date_str = get_today_birthdays()
        if birthdays is not None:
            send_telegram_message(birthdays, date_str)
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")