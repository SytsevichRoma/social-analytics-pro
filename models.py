import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import date, datetime, timedelta, timezone
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app 

db = SQLAlchemy()

def init_app_db(app):
    """Ініціалізує та створює таблиці БД"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print("База даних 'project.db' успішно ініціалізована (з Дашбордом).")

# Модель користувача
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    
    is_pro = db.Column(db.Boolean, default=False)
    expiry_date = db.Column(db.Date, nullable=True)
    
    analysis_count = db.Column(db.Integer, default=0)
    last_analysis_date = db.Column(db.Date, default=date(2000, 1, 1))
    
    # --- НОВИЙ ЗВ'ЯЗОК ---
    # Дозволяє нам писати current_user.tracked_accounts
    tracked_accounts = db.relationship('TrackedAccount', backref='owner', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<User {self.email} (Pro: {self.is_pro})>'

    def check_pro_status(self):
        """Перевіряє, чи не закінчився Pro-статус."""
        if self.is_pro:
            if self.expiry_date and self.expiry_date < date.today():
                self.is_pro = False
                db.session.commit()
                print(f"Pro-статус для {self.email} закінчився.")
        return self.is_pro

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=expires_sec)
            user_id = data.get('user_id')
        except Exception as e:
            print(f"Помилка верифікації токена: {e}")
            return None
        return User.query.get(user_id)

# --- НОВА ТАБЛИЦЯ ---
class TrackedAccount(db.Model):
    """
    Акаунт, який користувач додав у свій "Дашборд" для відстеження.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    platform = db.Column(db.String(20), nullable=False) # 'telegram' or 'instagram'
    username = db.Column(db.String(100), nullable=False)
    account_name = db.Column(db.String(255)) # Повна назва
    url = db.Column(db.String(255), nullable=False) # Посилання
    
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime(2000, 1, 1))
    
    # --- НОВИЙ ЗВ'ЯЗОК ---
    # Дозволяє нам писати account.history
    history = db.relationship('AnalyticsHistory', backref='account', lazy=True, cascade="all, delete-orphan")
    
    # Створюємо індекс, щоб user_id + username були унікальними
    __table_args__ = (db.UniqueConstraint('user_id', 'username', 'platform', name='_user_account_uc'),)

    def __repr__(self):
        return f'<TrackedAccount {self.username} (Owner: {self.user_id})>'

    def get_recent_history(self, days=7):
        """Отримує історію за останні N днів"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return AnalyticsHistory.query.filter(
            AnalyticsHistory.tracked_account_id == self.id,
            AnalyticsHistory.date >= cutoff_date
        ).order_by(AnalyticsHistory.date.asc()).all()
        
    def get_latest_data(self):
        """Отримує останній запис історії"""
        return AnalyticsHistory.query.filter_by(tracked_account_id=self.id).order_by(AnalyticsHistory.date.desc()).first()

# --- НОВА ТАБЛИЦЯ ---
class AnalyticsHistory(db.Model):
    """
    Знімок аналітики (запис у часі) для відстежуваного акаунта.
    """
    id = db.Column(db.Integer, primary_key=True)
    tracked_account_id = db.Column(db.Integer, db.ForeignKey('tracked_account.id'), nullable=False)
    
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Метрики
    followers = db.Column(db.Integer) # Для Insta
    subscribers = db.Column(db.Integer) # Для TG
    er = db.Column(db.Float)
    
    # ... тут можна додати avg_views, posts_per_day тощо, якщо потрібно

    def __repr__(self):
        return f'<History {self.account.username} on {self.date.strftime("%Y-%m-%d")}>'