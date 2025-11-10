import os
from urllib.parse import urlparse # Імпортуємо urlparse

# --- Утиліти парсингу ---

def detect_platform(url: str) -> str:
    """
    Визначає платформу. Тепер ТІЛЬКИ Telegram.
    """
    try:
        # 1. Очищуємо від випадкових пробілів
        url = url.strip() 
        
        # 2. Якщо користувач не ввів http:// або https://, додаємо https://
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
            
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()

        if 't.me' in domain or 'telegram.me' in domain:
            return 'telegram'
        
        # Якщо це не Telegram, це 'unknown'
        return 'unknown'
    except Exception:
        return 'unknown'

# --- extract_instagram_username() ВИДАЛЕНО ---