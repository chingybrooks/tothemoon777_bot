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
    print("Запрос к API CoinGecko для получения данных о криптовалютах...")
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,ethereum,binancecoin,solana",  # Указываем нужные монеты
        "vs_currencies": "usd",
        "include_24hr_change": "true",
    }
    try:
        response = requests.get(url, params=params)
        print(f"Ответ от API: {response.text}")
        return response.json()
    except Exception as e:
        print(f"Ошибка при запросе данных о криптовалютах: {e}")
        return None

def fetch_market_data():
    print("Запрос к API для получения рыночных данных...")
    fear_greed_url = "https://api.alternative.me/fng/"
    market_cap_url = "https://api.coingecko.com/api/v3/global"

    try:
        fear_greed = requests.get(fear_greed_url).json()["data"][0]
        market_data = requests.get(market_cap_url).json()["data"]

        fear_greed_index = int(fear_greed["value"])
        fear_greed_text = "Жадность" if fear_greed_index >= 50 else "Страх"
        market_cap = market_data["total_market_cap"]["usd"]
        btc_dominance = market_data["market_cap_percentage"]["btc"]

        return {
            "fear_greed_index": fear_greed_index,
            "fear_greed_text": fear_greed_text,
            "market_cap": market_cap,
            "btc_dominance": btc_dominance,
        }
    except Exception as e:
        print(f"Ошибка при получении рыночных данных: {e}")
        return None

def create_market_report():
    print("Создание отчета...")
    crypto_data = fetch_crypto_data()
    market_data = fetch_market_data()

    if not crypto_data or not market_data:
        print("Не удалось получить данные для отчета.")
        return "Не удалось получить данные для отчета."

    report = "📊 Утреннее состояние рынка\n\n"
    
    # Добавляем информацию по каждой криптовалюте
    for coin, data in crypto_data.items():
        name = coin.upper()
        price = data["usd"]
        change = data["usd_24h_change"]
        report += f"- {name}: ${price:,.2f} ({change:+.2f}%)\n"
    
    # Добавляем информацию о рынке
    report += f"\n- Капитализация рынка ≈ ${market_data['market_cap']:,.0f}\n"
    report += f"- Индекс страха и жадности: {market_data['fear_greed_index']} ({market_data['fear_greed_text']})\n"
    report += f"- Доминация BTC: {market_data['btc_dominance']:.2f}%"

    print("Отчет готов.")
    return report

def send_daily_update():
    print("Отправка ежедневного обновления...")
    report = create_market_report()
    if report:
        bot.send_message(CHANNEL_ID, report)
        print("Сообщение отправлено в канал.")
    else:
        print("Не удалось отправить сообщение, отчет пустой.")

# Настройка расписания для отправки оповещений в зависимости от времени года
# Зимнее время (UTC-8)
schedule.every().day.at("21:00").do(send_daily_update)  # Запуск в 21:00 предыдущего дня

# Летнее время (UTC-7) - раскомментируйте при необходимости
# schedule.every().day.at("22:00").do(send_daily_update)  # Запуск в 22:00 предыдущего дня

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    print("Команда /start получена")  # Отладочное сообщение
    # Немедленно отправить первое сообщение
    send_daily_update()
    bot.reply_to(message, "Бот запущен! Оповещения будут приходить каждый день по расписанию.")

if __name__ == "__main__":
    print("Бот запущен")  # Отладочное сообщение
    # Запуск бота и периодическая проверка задач
    while True:
        schedule.run_pending()  # Проверка задач по расписанию
        time.sleep(60)  # Проверка каждую минуту
