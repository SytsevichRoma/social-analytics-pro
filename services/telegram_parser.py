import os
import asyncio
import uuid
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.errors import ChannelInvalidError, ChannelPrivateError
import time
from datetime import datetime, timezone, timedelta # 1. Додаємо timedelta

# --- Налаштування кешу ---
_cache = {}
_CACHE_TIMEOUT_SECONDS = 300  # 5 хвилин

# --- Завантаження конфігурації ---
API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')
SESSION_STRING = os.environ.get('TELETHON_SESSION_STRING')

if not all([API_ID, API_HASH, SESSION_STRING]):
    print("ПОПЕРЕДЖЕННЯ: Змінні Telegram (API_ID, API_HASH, SESSION_STRING) не налаштовані в .env")

TEMP_AVATAR_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'temp_avatars')
os.makedirs(TEMP_AVATAR_DIR, exist_ok=True)


# --- PRO FUNCTIONS (ОНОВЛЕНО) ---

def _calculate_telegram_pro_metrics(messages, subscribers_count, entity_username):
    """
    Розраховує ER, частоту, Top/Flop, RR,
    ТАКОЖ: Стабільність переглядів ТІЛЬКИ для "зрілих" постів.
    """
    if not messages:
        return 0, 0, 0, [], [], 0, 0, 0 

    total_views = 0
    total_reactions = 0 
    valid_posts = 0
    
    # --- 2. НОВІ СПИСКИ для "зрілих" постів ---
    now = datetime.now(timezone.utc)
    one_day_ago = now - timedelta(days=1)
    mature_view_list = [] # Список переглядів ТІЛЬКИ для постів > 24 год.
    # ----------------------------------------

    for msg in messages:
        if msg.views:
            total_views += msg.views
            valid_posts += 1
            
            # --- 3. НОВА ЛОГІКА ---
            # Додаємо перегляди в список "зрілих",
            # ТІЛЬКИ ЯКЩО пост старший за 24 години
            if msg.date < one_day_ago:
                mature_view_list.append(msg.views)
            # ---------------------
            
            if msg.reactions and msg.reactions.results:
                for reaction in msg.reactions.results:
                    total_reactions += reaction.count
            
    avg_views = total_views / valid_posts if valid_posts > 0 else 0
    avg_reactions = total_reactions / valid_posts if valid_posts > 0 else 0 

    # 1. ER
    er = 0
    if subscribers_count > 0:
        er = (avg_views / subscribers_count) * 100

    # 2. Частота постингу
    posts_per_day = 0
    if len(messages) > 1:
        newest_post_date = messages[0].date
        oldest_post_date = messages[-1].date
        time_diff = newest_post_date - oldest_post_date
        days_diff = time_diff.total_seconds() / (60 * 60 * 24)
        if days_diff < 1:
            days_diff = 1
        posts_per_day = len(messages) / days_diff

    # 3. Top/Flop (тут логіка без змін, вона правильна)
    sorted_posts = sorted(
        [msg for msg in messages if msg.views and msg.message], 
        key=lambda x: x.views, 
        reverse=True
    )
    
    def get_post_link(msg):
        if entity_username:
            return f"https://t.me/{entity_username}/{msg.id}"
        else:
            return f"https://t.me/c/{msg.peer_id.channel_id}/{msg.id}"

    top_posts = []
    for msg in sorted_posts[:3]:
        top_posts.append({
            'text': msg.message.split('\n')[0][:50] + '...',
            'views': msg.views,
            'link': get_post_link(msg)
        })

    flop_posts = []
    for msg in sorted_posts[-3:]:
        flop_posts.append({
            'text': msg.message.split('\n')[0][:50] + '...',
            'views': msg.views,
            'link': get_post_link(msg)
        })

    # 4. Коефіцієнт Реакцій (RR)
    reaction_rate = 0
    if avg_views > 0:
        reaction_rate = (avg_reactions / avg_views) * 100

    # 5. --- 4. ОНОВЛЕНА ЛОГІКА СТАБІЛЬНОСТІ ---
    # Ми рахуємо Min/Max ТІЛЬКИ по "зрілому" списку
    min_views = min(mature_view_list) if mature_view_list else 0
    max_views = max(mature_view_list) if mature_view_list else 0
    # ----------------------------------------

    return avg_views, er, posts_per_day, top_posts, flop_posts, reaction_rate, min_views, max_views


# --- MAIN ASYNC FUNCTION (без змін) ---
async def _internal_get_telegram_data(channel_url: str, is_pro_user: bool):
    if not all([API_ID, API_HASH, SESSION_STRING]):
        raise ValueError("API_ID, API_HASH та TELETHON_SESSION_STRING повинні бути встановлені в .env")

    async with TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH) as client:
        try:
            await client.connect()
            if not await client.is_user_authorized():
                print("ПОМИЛКА: Сесія Telethon не авторизована.")
                return None
                
            entity = await client.get_entity(channel_url)
            
            full_channel_info = await client(GetFullChannelRequest(channel=entity))
            subscribers_count = full_channel_info.full_chat.participants_count
            channel_title = entity.title
            entity_username = getattr(entity, 'username', None)

            avatar_path = None
            try:
                unique_filename = f"{entity.id}_{uuid.uuid4()}.jpg"
                temp_path = os.path.join(TEMP_AVATAR_DIR, unique_filename)
                await client.download_profile_photo(entity, file=temp_path)
                if os.path.exists(temp_path):
                    avatar_path = temp_path
                    print(f"Аватар успішно завантажено у: {avatar_path}")
                else:
                    print(f"Канал {channel_title} не має фото профілю.")
            except Exception as e:
                print(f"Помилка завантаження аватарки: {e}")

            messages = await client.get_messages(entity, limit=20)
            
            (avg_views, er, posts_per_day, 
             top_posts, flop_posts, 
             reaction_rate, min_views, max_views) = _calculate_telegram_pro_metrics(messages, subscribers_count, entity_username)

            data = {
                "name": channel_title,
                "username": entity_username,
                "subscribers": subscribers_count,
                "type": "Telegram Канал",
                "is_private": False,
                "platform": "telegram",
                "url": channel_url,
                "avg_views": int(avg_views),
                "avatar_path": avatar_path 
            }
            
            if is_pro_user:
                data["er"] = er
                data["posts_per_day"] = posts_per_day
                data["top_posts"] = top_posts
                data["flop_posts"] = flop_posts
                data["reaction_rate"] = reaction_rate
                data["min_views"] = min_views
                data["max_views"] = max_views

            return data

        except (ChannelInvalidError, ChannelPrivateError):
            print(f"Помилка: Канал '{channel_url}' не знайдено або він приватний.")
            return None
        except ValueError:
            print(f"Помилка: Неправильний URL каналу '{channel_url}'.")
            return None
        except Exception as e:
            print(f"Загальна помилка Telethon: {e}")
            return None

# --- PUBLIC SYNC WRAPPER (без змін) ---
def get_telegram_data(channel_url: str, is_pro_user: bool, force_fresh: bool = False) -> dict | None:
    now = time.time()
    cache_key = f"{channel_url}_{is_pro_user}"
    
    if not force_fresh and cache_key in _cache:
        timestamp, data = _cache[cache_key]
        if now - timestamp < _CACHE_TIMEOUT_SECONDS:
            if 'avatar_path' in data:
                data['avatar_path'] = None
            print(f"[CACHE] Повертаю дані для {cache_key} (без аватарки)")
            return data
            
    print(f"[API (Force Fresh: {force_fresh})] Роблю запит до Telegram для {cache_key}")
    try:
        data = asyncio.run(_internal_get_telegram_data(channel_url, is_pro_user))
        
        if data:
            _cache[cache_key] = (now, data)
        return data
        
    except Exception as e:
        print(f"Помилка при запуску asyncio.run для Telegram: {e}")
        return None