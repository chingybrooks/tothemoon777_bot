import os
import requests
import telebot
import schedule
import time
from dotenv import load_dotenv
from datetime import datetime

# Загрузка переменных окружения из .env файла
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def fetch_crypto_data():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,ethereum,binancecoin,solana",  # IDs для нужных монет
        "vs_currencies": "usd",
        "include_24hr_change": "true",
    }
    response = requests.get(url, params=params)
    return response.json()

def fetch_market_data():
    fear_greed_url = "https://api.alternative.me/fng/"
    market_data = requests.get(fear_greed_url).json()["data"][0]

    try:
        fear_greed_index = int(market_data["value"])
        fear_greed_text = "Жадность" if fear_greed_index >= 50 else "Страх"
        btc_dominance = requests.get("https://api.coingecko.com/api/v3/global").json()["data"]["market_cap_percentage"]["btc"]
        altcoin_dominance = 100 - btc_dominance

        return {
            "fear_greed_index": fear_greed_index,
            "fear_greed_text": fear_greed_text,
            "btc_dominance": btc_dominance,
            "altcoin_dominance": altcoin_dominance,
        }
    except Exception as e:
        print(f"Ошибка при получении рыночных данных: {e}")
        return None

def create_market_report():
    crypto_data = fetch_crypto_data()
    market_data = fetch_market_data()

    if not crypto_data or not market_data:
        return "Не удалось получить данные для отчета."

    report = "📊 Текущее состояние рынка\n\n"
    
    # Словарь для замены названий криптовалют на сокращенные версии
    crypto_names = {
        "bitcoin": "BTC",
        "ethereum": "ETH",
        "binancecoin": "BNB",
        "solana": "SOL",
    }

    # Добавляем информацию по каждой криптовалюте
    for coin, data in crypto_data.items():
        name = crypto_names.get(coin, coin.upper())  # Заменяем название
        price = data["usd"]
        change = data["usd_24h_change"]
        report += f"- {name}: ${price:,.2f} ({change:+.2f}%)\n"
    
    # Добавляем информацию о рынке
    report += f"\n- Индекс страха и жадности: {market_data['fear_greed_index']} ({market_data['fear_greed_text']})\n"
    report += f"- Доминация BTC: {market_data['btc_dominance']:.2f}%\n"
    report += f"- Доминация альткоинов: {market_data['altcoin_dominance']:.2f}%"

    return report

def send_daily_update():
    report = create_market_report()
    bot.send_message(CHANNEL_ID, report)

# Утреннее время (UTC+5)
schedule.every().day.at("10:30").do(send_daily_update)  # Отправка в 10:30 по UTC+5

# Вечернее время (UTC+5)
schedule.every().day.at("18:30").do(send_daily_update)  # Отправка в 18:30 по UTC+5

@bot.message_handler(commands=['start'])
def handle_start(message):
    send_daily_update()
    bot.reply_to(message, "Бот запущен! Оповещения будут приходить каждый день по расписанию.")

@bot.message_handler(commands=['update'])
def handle_update(message):
    report = create_market_report()
    bot.reply_to(message, report)

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(60)
