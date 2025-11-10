from telethon.sync import TelegramClient
from telethon.sessions import StringSession

# Ваші ключі вже тут:
API_ID = 22928146
API_HASH = "2e7c8c1ac601ecae1ba0293d434bb086"

print("Запускаємо генератор сесії Telethon...")
print("Вам потрібно буде ввести ваш номер телефону та код, який прийде в Telegram.\n")

with TelegramClient(StringSession(), int(API_ID), API_HASH) as client:
    print("\nВаша сесія Telethon (скопіюйте цей довгий рядок нижче):\n")
    print(client.session.save())