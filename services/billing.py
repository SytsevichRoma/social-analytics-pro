import os
import time
from cloudipsp import Api, Checkout, Payment

# --- Налаштування Fondy ---
FONDY_MERCHANT_ID = os.environ.get('FONDY_MERCHANT_ID')
FONDY_SECRET_KEY = os.environ.get('FONDY_SECRET_KEY')

if not all([FONDY_MERCHANT_ID, FONDY_SECRET_KEY]):
    print("ПОПЕРЕДЖЕННЯ: FONDY_MERCHANT_ID або FONDY_SECRET_KEY не встановлено в .env")

# Ініціалізуємо API
try:
    fondy_api = Api(merchant_id=int(FONDY_MERCHANT_ID),
                    secret_key=FONDY_SECRET_KEY)
    fondy_checkout = Checkout(api=fondy_api)
except Exception as e:
    print(f"Помилка ініціалізації Fondy API. Перевірте .env: {e}")
    fondy_api = None
    fondy_checkout = None

def create_fondy_checkout_url(order_id: str, amount_cents: int, currency: str, description: str, base_url: str) -> str:
    """
    Створює URL-адресу сторінки оплати Fondy.
    """
    if not fondy_checkout:
        raise ValueError("Fondy API не ініціалізовано. Перевірте .env")

    data = {
        "order_id": order_id,
        "amount": amount_cents, # Ціна в копійках
        "currency": currency,
        "order_desc": description,
        "response_url": f"{base_url}/success", # Куди повернеться клієнт
        "server_callback_url": f"{base_url}/fondy-webhook" # Куди Fondy надішле webhook
    }
    
    try:
        result = fondy_checkout.url(data)
        if result.get('checkout_url'):
            return result['checkout_url']
        else:
            raise Exception(f"Fondy не повернув checkout_url: {result.get('error_message', result)}")
    except Exception as e:
        print(f"Помилка створення Fondy checkout: {e}")
        raise e