from flask_mail import Mail, Message
from flask import render_template, url_for, current_app

# Створюємо інстанс Mail
mail = Mail()

def init_app_mail(app):
    """Ініціалізує Flask-Mail"""
    mail.init_app(app)
    print("Flask-Mail успішно ініціалізовано.")

def send_password_reset_email(user):
    """
    Генерує токен, створює лист і відправляє його.
    """
    # 1. Отримуємо токен (з нашої моделі User)
    token = user.get_reset_token()
    
    # 2. Створюємо URL для посилання у листі
    # _external=True генерує повний URL (з https://... з .env)
    reset_url = url_for('reset_password', token=token, _external=True)
    
    # 3. Створюємо тіло листа, рендерячи HTML-шаблон
    email_html = render_template(
        'email/reset_password.html', 
        user=user, 
        reset_url=reset_url
    )
    
    # 4. Створюємо об'єкт листа
    msg = Message(
        subject="[Social Analytics Pro] Інструкції зі скидання пароля",
        sender=("Social Analytics Pro", current_app.config['MAIL_DEFAULT_SENDER']),
        recipients=[user.email],
        html=email_html
    )
    
    # 5. Відправляємо
    mail.send(msg)
    print(f"Лист для скидання пароля надіслано на {user.email}")