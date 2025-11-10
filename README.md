# Social Analytics Pro (MVP)

Веб-додаток на Flask для аналітики Telegram та Instagram з Freemium-моделлю на базі Stripe.

## Функціонал

* **Аналітика**: Отримує базові дані (підписники, перегляди) з Telegram та Instagram.
* **Freemium**: 3 безкоштовні аналізи на день (відстежується через сесії).
* **Pro-тариф**:
    * Безлімітні запити.
    * Завантаження PDF-звітів (згенерованих через `reportlab`).
* **Оплата**: Інтеграція зі Stripe Checkout (підписки або одноразовий платіж).
* **База даних**: SQLite (`users.db`) для зберігання Pro-статусів.

## Як запустити локально

1.  **Створіть оточення:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # (для Windows: venv\Scripts\activate)
    ```

2.  **Встановіть залежності:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Налаштуйте `.env`:**
    * Скопіюйте `.env.example` у новий файл `.env`.
    * `cp .env.example .env`
    * **ОБОВ'ЯЗКОВО** заповніть *усі* поля:
        * `APP_SECRET_KEY`: Згенеруйте випадковий ключ.
        * `BASE_URL`: Встановіть `http://127.0.0.1:5000`.
        * `TELEGRAM_...`: Дотримуйтесь інструкцій в `.env.example` для генерації `TELETHON_SESSION_STRING`.
* `INSTA_SESSION_ID`: Дотримуйтесь інструкцій для отримання `sessionid` з браузера.
        * `STRIPE_...`: Отримайте тестові ключі та `STRIPE_PRICE_ID` з вашого кабінету Stripe.

4.  **(Для PDF)** Щоб кирилиця працювала у PDF:
    * Знайдіть та завантажте шрифт `DejaVuSans.ttf`.
    * Покладіть його у `project/static/DejaVuSans.ttf`.
    * (Якщо ви не зробите цього, кирилиця у PDF не буде відображатись, але додаток працюватиме).

5.  **Запустіть додаток:**
    ```bash
    flask run
    ```
    Або:
    ```bash
    python app.py
    ```

6.  Відкрийте `http://127.0.0.1:5000` у вашому браузері.

## Тестування оплати

1.  Перейдіть на `/upgrade`.
2.  Натисніть кнопку оплати.
3.  На сторінці Stripe використовуйте одну з [тестових карток Stripe](https://stripe.com/docs/testing#testing-cards) (напр., `4242 4242 4242 4242`).
4.  Після успішної оплати вас поверне на `/success`, і ваш `user_id` (з сесії) буде збережено в `database/users.db`. Ви отримаєте Pro-статус.
