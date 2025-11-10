import os
import sys
import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# 1. Завантажуємо .env (так само, як у app.py)
load_dotenv()

# 2. Отримуємо токен бота ТА URL нашого веб-додатка
BOT_TOKEN = os.environ.get("BOT_TOKEN")
# BASE_URL - це наша ngrok-адреса
WEB_APP_URL = os.environ.get("BASE_URL")

# 3. Перевірка ключів
if not BOT_TOKEN:
    logging.critical("ПОМИЛКА: BOT_TOKEN не знайдено у .env! Бот не може запуститися.")
    sys.exit()
if not WEB_APP_URL:
    logging.critical("ПОМИЛКА: BASE_URL (ваша ngrok-адреса) не знайдено у .env! Бот не знатиме, що відкривати.")
    sys.exit()

# Ініціалізуємо Бота та Диспетчер
# DefaultBotProperties потрібен для коректної роботи з ParseMode
dp = Dispatcher()
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    """
    Цей хендлер викликається, коли користувач надсилає /start
    """
    
    # 1. Створюємо "чарівний" об'єкт WebAppInfo
    # Він каже Telegram: "Відкрий цей URL всередині додатка"
    web_app = types.WebAppInfo(url=WEB_APP_URL)

    # 2. Створюємо клавіатуру з кнопкою, яка містить наш web_app
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="🚀 Відкрити Аналізатор", web_app=web_app)
            ]
        ]
    )
    
    # 3. Відправляємо привітання та кнопку
    await message.answer(
        f"Вітаю, {message.from_user.full_name}!\n\n"
        "Це бот для аналітики Telegram-каналів.\n\n"
        "Натисніть кнопку нижче, щоб запустити Pro-аналізатор:",
        reply_markup=keyboard
    )

async def main() -> None:
    """Запускає бота"""
    # Видаляємо старі вебхуки (про всяк випадок)
    await bot.delete_webhook(drop_pending_updates=True)
    # Запускаємо бота в режимі "polling" (постійне опитування)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    print("Запускаємо Telegram-бота...")
    asyncio.run(main())