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
    market_cap_url = "https://api.coingecko.com/api/v3/global"

    try:
        fear_greed = requests.get(fear_greed_url).json()["data"][0]
        market_data = requests.get(market_cap_url).json()["data"]

        fear_greed_index = int(fear_greed["value"])
        fear_greed_text = "Жадность" if fear_greed_index >= 50 else "Страх"
        market_cap = market_data["total_market_cap"]["usd"]
        market_cap_change_24h = market_data["market_cap_change_percentage_24h_usd"]
        btc_dominance = market_data["market_cap_percentage"]["btc"]
        altcoin_dominance = 100 - btc_dominance

        return {
            "fear_greed_index": fear_greed_index,
            "fear_greed_text": fear_greed_text,
            "market_cap": market_cap,
            "market_cap_change_24h": market_cap_change_24h,
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

    report = "📊 Утреннее состояние рынка\n\n"
    
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
    report += f"\n- Капитализация рынка ≈ ${market_data['market_cap']:,.0f} ({market_data['market_cap_change_24h']:+.2f}%)\n"
    report += f"- Индекс страха и жадности: {market_data['fear_greed_index']} ({market_data['fear_greed_text']})\n"
    report += f"- Доминация BTC: {market_data['btc_dominance']:.2f}%\n"
    report += f"- Доминация альткоинов: {market_data['altcoin_dominance']:.2f}%"

    return report

def send_daily_update():
    report = create_market_report()
    bot.send_message(CHANNEL_ID, report)

# Настройка расписания
schedule.every().day.at("21:00").do(send_daily_update)  # Зимнее время (UTC-8)

@bot.message_handler(commands=['start'])
def handle_start(message):
    send_daily_update()
    bot.reply_to(message, "Бот запущен! Оповещения будут приходить каждый день по расписанию.")

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(60)
