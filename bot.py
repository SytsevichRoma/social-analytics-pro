import os
import sys
import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode


print("STARTED BOT PID:", os.getpid())

# 1. Завантажуємо .env (так само, як у app.py)
load_dotenv()

# 2. Отримуємо токен бота ТА URL нашого веб-додатка
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEB_APP_URL = os.environ.get("BASE_URL")

# ✅ Додаємо діагностику, яку ти просив
print("BOT_TOKEN LENGTH:", len(BOT_TOKEN) if BOT_TOKEN else "NONE")
print("WEB_APP_URL:", WEB_APP_URL)

# 3. Перевірка ключів
if not BOT_TOKEN:
    logging.critical("ПОМИЛКА: BOT_TOKEN не знайдено у .env! Бот не може запуститися.")
    sys.exit()
if not WEB_APP_URL:
    logging.critical("ПОМИЛКА: BASE_URL (ваша ngrok-адреса) не знайдено у .env! Бот не знатиме, що відкривати.")
    sys.exit()

# Ініціалізуємо Бота та Диспетчер
dp = Dispatcher()
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    """
    Цей хендлер викликається, коли користувач надсилає /start
    """

    web_app = types.WebAppInfo(url=WEB_APP_URL)

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="🚀 Відкрити Аналізатор", 
                    web_app=web_app
                )
            ]
        ]
    )

    await message.answer(
        f"Вітаю, {message.from_user.full_name}!\n\n"
        "Це бот для аналітики Telegram-каналів.\n\n"
        "Натисніть кнопку нижче, щоб запустити Pro-аналізатор:",
        reply_markup=keyboard
    )


async def main() -> None:
    """Запускає бота"""
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    print("Запускаємо Telegram-бота...")
    asyncio.run(main())
