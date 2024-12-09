import os
import requests
import telebot
import schedule
import time
from dotenv import load_dotenv
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Загрузка переменных окружения из .env файла
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def fetch_crypto_data():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin,ethereum,binancecoin,solana",
            "vs_currencies": "usd",
            "include_24hr_change": "true",
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Ошибка при получении данных о криптовалюте: {e}")
        return None

def fetch_market_data():
    fear_greed_url = "https://api.alternative.me/fng/"
    market_data = requests.get(fear_greed_url).json()["data"][0]

    try:
        fear_greed_index = int(market_data["value"])
        btc_dominance = requests.get("https://api.coingecko.com/api/v3/global").json()["data"]["market_cap_percentage"]["btc"]
        altcoin_dominance = 100 - btc_dominance

        return {
            "fear_greed_index": fear_greed_index,
            "btc_dominance": btc_dominance,
            "altcoin_dominance": altcoin_dominance,
        }
    except Exception as e:
        print(f"Ошибка при получении рыночных данных: {e}")
        return None

def interpret_fear_greed_index(value):
    """
    Интерпретирует индекс страха и жадности кратко.
    """
    if 0 <= value <= 24:
        return "Экстремальный страх"
    elif 25 <= value <= 49:
        return "Страх"
    elif 50 <= value <= 74:
        return "Жадность"
    elif 75 <= value <= 100:
        return "Экстремальная жадность"
    else:
        return "Некорректное значение"

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
    fear_greed = interpret_fear_greed_index(market_data["fear_greed_index"])
    report += f"\n- Индекс страха и жадности: {market_data['fear_greed_index']} ({fear_greed})\n"
    report += f"- Доминация BTC: {market_data['btc_dominance']:.2f}%\n"
    report += f"- Доминация альткоинов: {market_data['altcoin_dominance']:.2f}%"

    return report

def send_daily_update():
    report = create_market_report()
    if report:
        try:
            bot.send_message(CHANNEL_ID, report)
            logging.info("Отчет успешно отправлен в канал.")
        except Exception as e:
            logging.error(f"Ошибка при отправке отчета: {e}")
    else:
        logging.error("Не удалось создать отчет. Данные отсутствуют или некорректны.")

# Настройка расписания на 10:30 по UTC+5
schedule.every().day.at("05:30").do(send_daily_update)  # Утреннее уведомление в 10:30 UTC+5

# Настройка расписания на 18:30 по UTC+5
schedule.every().day.at("13:30").do(send_daily_update)  # Вечернее уведомление в 18:30 UTC+5

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
