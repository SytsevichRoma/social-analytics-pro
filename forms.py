from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, URL
from models import User # Імпортуємо нашу нову модель User

class RegistrationForm(FlaskForm):
    """Форма для реєстрації нового користувача"""
    email = StringField('Email', 
                        validators=[DataRequired(), Email(message="Некоректний email.")])
    
    password = PasswordField('Пароль', 
                             validators=[DataRequired(), Length(min=6, message="Пароль має бути не менше 6 символів.")])
    
    confirm_password = PasswordField('Підтвердіть Пароль', 
                                     validators=[DataRequired(), EqualTo('password', message="Паролі не співпадають.")])
    
    submit = SubmitField('Зареєструватися')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Цей email вже зареєстрований. Будь ласка, увійдіть.')

class LoginForm(FlaskForm):
    """Форма для входу"""
    email = StringField('Email', 
                        validators=[DataRequired(), Email()])
    
    password = PasswordField('Пароль', 
                             validators=[DataRequired()])
    
    submit = SubmitField('Увійти')

class CompareForm(FlaskForm):
    """Форма для сторінки порівняння"""
    url1 = StringField('Посилання #1', 
                       validators=[DataRequired(), URL(message="Некоректне посилання.")])
    
    url2 = StringField('Посилання #2', 
                       validators=[DataRequired(), URL(message="Некоректне посилання.")])

    submit = SubmitField('Порівняти')
    
# --- НОВІ ФОРМИ (яких у вас бракувало) ---

class RequestPasswordResetForm(FlaskForm):
    """Форма запиту на скидання пароля (ввід email)"""
    email = StringField('Email', 
                        validators=[DataRequired(), Email()])
    
    submit = SubmitField('Надіслати посилання')

    def validate_email(self, email):
        """Перевіряємо, чи існує такий користувач"""
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('Акаунт з таким e-mail не знайдено. Будь ласка, перевірте.')

class ResetPasswordForm(FlaskForm):
    """Форма встановлення нового пароля"""
    password = PasswordField('Новий Пароль', 
                             validators=[DataRequired(), Length(min=6, message="Пароль має бути не менше 6 символів.")])
    
    confirm_password = PasswordField('Підтвердіть Новий Пароль', 
                                     validators=[DataRequired(), EqualTo('password', message="Паролі не співпадають.")])
    
    submit = SubmitField('Оновити Пароль')