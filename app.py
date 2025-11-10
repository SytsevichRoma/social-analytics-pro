# 1. Завантажуємо змінні оточення
from dotenv import load_dotenv
load_dotenv() 

# 2. Інші імпорти
import os
import uuid
from datetime import datetime, date, timedelta, timezone
from flask import Flask, render_template, request, redirect, url_for, session, make_response, abort, flash, Response, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

# 3. Локальні імпорти
from utils import detect_platform 
from services.telegram_parser import get_telegram_data
from services.billing import create_fondy_checkout_url
from services.pdf_generator import generate_pdf_report
from services.export_service import generate_csv
from services.email_service import init_app_mail, send_password_reset_email
from services.insights_generator import generate_pro_insights
from models import db, User, TrackedAccount, AnalyticsHistory, init_app_db
from forms import LoginForm, RegistrationForm, CompareForm, RequestPasswordResetForm, ResetPasswordForm
from sqlalchemy.exc import IntegrityError 


app = Flask(__name__)
app.secret_key = os.environ.get('APP_SECRET_KEY', os.urandom(24))

# --- *** ВИПРАВЛЕННЯ: ПРАВИЛЬНЕ ПІДКЛЮЧЕННЯ ДО БАЗИ *** ---
# Спроба отримати URL бази з середовища (на Render він буде, локально - ні)
database_url = os.environ.get('DATABASE_URL')

# Якщо ми на Render, і URL починається з 'postgres://', 
# виправляємо його на 'postgresql://' (вимога нової бібліотеки)
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Використовуємо знайдену базу АБО створюємо локальний файл sqlite, якщо бази немає
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///project.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
init_app_db(app)
# --- *** КІНЕЦЬ ВИПРАВЛЕННЯ *** ---


# --- НАЛАШТУВАННЯ FLASK-MAIL ---
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')
init_app_mail(app)

# --- НАЛАШТУВАННЯ FLASK-LOGIN ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 
login_manager.login_message = 'Будь ласка, увійдіть, щоб отримати доступ до цієї сторінки.'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- КОНТЕКСТНИЙ ПРОЦЕСОР ---
@app.context_processor
def inject_global_vars():
    is_pro_status = False
    if current_user.is_authenticated:
        is_pro_status = current_user.check_pro_status() 
    return {
        'current_year': datetime.now().year,
        'is_pro': is_pro_status
    }

# --- ДОПОМІЖНІ ФУНКЦІЇ (без змін) ---
def get_base_url():
    return os.environ.get('BASE_URL', request.url_root.rstrip('/'))

def check_rate_limit(user):
    today = date.today()
    if user.last_analysis_date != today:
        user.analysis_count = 0
        user.last_analysis_date = today
    return user.analysis_count >= 3

# --- РОУТИ АВТЕНТИФІКАЦІЇ (без змін) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=True)
            flash('Ви успішно увійшли!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Неправильний email або пароль.', 'danger')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(email=form.email.data, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Ваш акаунт успішно створено! Тепер ви можете увійти.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Ви вийшли з акаунта.', 'info')
    return redirect(url_for('index'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated: return redirect(url_for('index'))
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            try:
                send_password_reset_email(user)
                flash('Інструкції зі скидання пароля надіслано на ваш e-mail.', 'info')
                return redirect(url_for('login'))
            except Exception as e:
                print(f"ПОМИЛКА ВІДПРАВКИ E-MAIL: {e}")
                flash('Не вдалося надіслати лист. Перевірте налаштування MAIL у .env', 'danger')
                return redirect(url_for('forgot_password'))
        else:
            flash('Акаунт з таким e-mail не знайдено.', 'warning')
    return render_template('forgot_password.html', form=form)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated: return redirect(url_for('index'))
    user = User.verify_reset_token(token)
    if not user:
        flash('Час дії посилання вичерпано або воно некоректне.', 'warning')
        return redirect(url_for('forgot_password'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user.password_hash = hashed_password
        db.session.commit()
        flash('Ваш пароль успішно оновлено! Тепер ви можете увійти.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form, token=token)

# --- ОСНОВНІ РОУТИ ДОДАТКУ ---

@app.route('/')
def index():
    error = session.pop('analysis_error', None)
    last_url = session.pop('analysis_url', None)
    remaining = 3
    if current_user.is_authenticated:
        limit_count = current_user.analysis_count if current_user.last_analysis_date == date.today() else 0
        remaining = 3 - limit_count
    else:
        today = str(date.today())
        if session.get('last_analysis_date') != today:
            session['analysis_count'] = 0
            session['last_analysis_date'] = today
        limit_count = session.get('analysis_count', 0)
        remaining = 3 - limit_count
    return render_template('index.html', error=error, last_url=last_url, remaining=remaining)

@app.route('/analyze', methods=['POST'])
def analyze():
    url = request.form.get('social_url')
    is_pro = current_user.is_authenticated and current_user.check_pro_status()
    session.pop('analysis_result', None)
    session.pop('analysis_error', None)
    session.pop('analysis_url', None)

    if not is_pro:
        is_limit_reached = False
        if current_user.is_authenticated:
            if check_rate_limit(current_user): is_limit_reached = True
        else:
            today = str(date.today())
            if session.get('last_analysis_date') != today:
                session['analysis_count'] = 0
                session['last_analysis_date'] = today
            if session.get('analysis_count', 0) >= 3: is_limit_reached = True
        if is_limit_reached:
            session['analysis_error'] = "Ви вичерпали ліміт (3 аналізи на день). Увійдіть або оновіть до Pro."
            return redirect(url_for('index')) 
    
    if not url:
        session['analysis_error'] = "Будь ласка, введіть URL."
        return redirect(url_for('index'))

    platform = detect_platform(url)
    data = None
    error = None

    try:
        if platform == 'telegram':
            data = get_telegram_data(url, is_pro_user=is_pro)
            if not data: error = "Не вдалося отримати дані з Telegram."
        else:
            error = "Непідтримуване посилання. Введіть URL Telegram-каналу (t.me/...)."
    except Exception as e:
        print(f"Сталася помилка при обробці {url}: {e}")
        error = f"Сталася внутрішня помилка: {e}"

    if error:
        session['analysis_error'] = error
        session['analysis_url'] = url
        return redirect(url_for('index'))

    if not is_pro:
        if current_user.is_authenticated:
            current_user.analysis_count += 1
            current_user.last_analysis_date = date.today()
            db.session.commit()
        else:
            session['analysis_count'] = (session.get('analysis_count', 0) + 1)
            session['last_analysis_date'] = str(date.today())

    if is_pro and data:
        insights = generate_pro_insights(data)
        data['insights'] = insights

    session['analysis_result'] = data
    session['analysis_url'] = url
    session['last_analysis'] = data 
    session['last_platform'] = platform 

    return redirect(url_for('show_result'))


@app.route('/result')
def show_result():
    data = session.get('analysis_result')
    url = session.get('analysis_url')
    if not data:
        return redirect(url_for('index'))
    
    platform = data.get('platform', 'unknown')
    return render_template('result.html', data=data, platform=platform, url=url)

@app.route('/export-csv')
@login_required
def export_csv():
    if not current_user.is_pro:
        flash('Експорт в CSV доступний лише для Pro-акаунтів.', 'warning')
        return redirect(url_for('index'))
    data = session.get('last_analysis')
    if not data:
        flash('Немає даних для експорту. Будь ласка, проведіть аналіз.', 'info')
        return redirect(url_for('index'))
    try:
        csv_buffer = generate_csv(data)
        filename = f"{data.get('platform', 'report')}_{data.get('username', 'analytics')}.csv"
        return Response(
            csv_buffer,
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        print(f"Помилка генерації CSV: {e}")
        flash('Сталася помилка при створенні CSV файлу.', 'danger')
        return redirect(url_for('show_result'))

@app.route('/compare')
@login_required
def compare_page():
    if not current_user.is_pro:
        flash('Порівняння акаунтів доступне лише для Pro-користувачів.', 'warning')
        return redirect(url_for('upgrade_page'))
    form = CompareForm()
    return render_template('compare.html', form=form)

@app.route('/compare-analyze', methods=['POST'])
@login_required
def compare_analyze():
    if not current_user.is_pro: abort(403)
    form = CompareForm()
    session.pop('compare_data1', None)
    session.pop('compare_data2', None)
    session.pop('compare_error', None)
    
    if form.validate_on_submit():
        url1 = form.url1.data
        url2 = form.url2.data
        platform1 = detect_platform(url1)
        platform2 = detect_platform(url2)

        if platform1 != 'telegram' or platform2 != 'telegram':
            flash('Наразі підтримується лише порівняння Telegram-каналів.', 'danger')
            return redirect(url_for('compare_page'))
        
        try:
            is_pro = current_user.is_pro
            data1 = get_telegram_data(url1, is_pro_user=is_pro)
            data2 = get_telegram_data(url2, is_pro_user=is_pro)

            if not data1 or not data2:
                flash('Не вдалося отримати дані для одного з акаунтів.', 'danger')
                return redirect(url_for('compare_page'))
            
            if is_pro:
                data1['insights'] = generate_pro_insights(data1)
                data2['insights'] = generate_pro_insights(data2)

            session['compare_data1'] = data1
            session['compare_data2'] = data2
            return redirect(url_for('compare_result_page'))
        except Exception as e:
            print(f"Помилка порівняння: {e}")
            flash('Сталася внутрішня помилка під час аналізу.', 'danger')
            return redirect(url_for('compare_page'))
    
    return render_template('compare.html', form=form)


@app.route('/compare-result')
@login_required
def compare_result_page():
    if not current_user.is_pro: return redirect(url_for('upgrade_page'))
    data1 = session.get('compare_data1')
    data2 = session.get('compare_data2')
    if not data1 or not data2:
        flash('Немає даних для порівняння. Будь ласка, спробуйте ще раз.', 'info')
        return redirect(url_for('compare_page'))
    
    platform = data1.get('platform', 'unknown')
    return render_template('compare_result.html', data1=data1, data2=data2, platform=platform)

@app.route('/download-pdf')
@login_required 
def download_pdf_report():
    if not current_user.is_pro:
        flash('Доступ до PDF-звітів є лише у Pro-акаунтів.', 'warning')
        return redirect(url_for('upgrade_page'))

    url = session.get('analysis_url')
    platform = session.get('last_platform')
    
    if not url or not platform:
        flash('Немає даних для звіту. Будь ласка, проведіть аналіз.', 'info')
        return redirect(url_for('index'))

    print(f"Запускаємо 'свіжий' аналіз для PDF-звіту для {url}...")
    try:
        if platform == 'telegram':
            data = get_telegram_data(url, is_pro_user=True, force_fresh=True) 
        else:
            data = None 

        if not data:
            flash('Не вдалося отримати свіжі дані для PDF-звіту.', 'danger')
            return redirect(url_for('show_result'))
        
        if current_user.is_pro:
            data['insights'] = generate_pro_insights(data)

    except Exception as e:
        print(f"Помилка під час 'свіжого' аналізу для PDF: {e}")
        flash('Сталася помилка під час оновлення даних для звіту.', 'danger')
        return redirect(url_for('show_result'))
    
    avatar_path = data.get('avatar_path')
    history = None

    try:
        tracked_acc = TrackedAccount.query.filter_by(
            user_id=current_user.id,
            platform=platform,
            username=data.get('username')
        ).first()
        
        if tracked_acc:
            history = tracked_acc.get_recent_history(days=7)
            
        pdf_buffer = generate_pdf_report(data, platform, history=history, avatar_path=avatar_path) 
        
        filename_name = data.get('username', data.get('name', 'report')).replace(" ", "_")
        filename = f"{platform}_{filename_name}_report.pdf"

        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        return response
    
    except Exception as e:
        print(f"Помилка генерації PDF: {e}")
        flash(f"Помилка генерації PDF: {e}", "danger")
        return redirect(url_for('index'))
    
    finally:
        if avatar_path and os.path.exists(avatar_path):
            try:
                os.remove(avatar_path)
                print(f"Тимчасову аватарку {avatar_path} видалено.")
            except Exception as e:
                print(f"Помилка видалення аватарки {avatar_path}: {e}")

# --- РОУТИ ДАШБОРДА ---
@app.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_pro:
        flash('Дашборд доступний лише для Pro-користувачів.', 'warning')
        return redirect(url_for('upgrade_page'))

    tracked_accounts = sorted(current_user.tracked_accounts, key=lambda x: x.date_added, reverse=True)
    return render_template('dashboard.html', 
                           accounts=tracked_accounts, 
                           datetime=datetime, 
                           timedelta=timedelta)

@app.route('/dashboard/refresh/<int:account_id>', methods=['POST'])
@login_required
def refresh_account(account_id):
    if not current_user.is_pro:
        abort(403)
    
    acc = TrackedAccount.query.get(account_id)
    if not acc or acc.user_id != current_user.id:
        flash('Акаунт не знайдено.', 'danger')
        return redirect(url_for('dashboard'))
    
    if acc.platform != 'telegram':
        flash('Оновлення наразі доступне лише для Telegram.', 'warning')
        return redirect(url_for('dashboard'))

    try:
        print(f"Примусове оновлення для {acc.username}...")
        data = get_telegram_data(acc.url, is_pro_user=True, force_fresh=True)
        
        if data and not data.get('is_private'):
            new_history_entry = AnalyticsHistory(
                tracked_account_id=acc.id,
                subscribers=data.get('subscribers'),
                er=data.get('er', 0)
            )
            db.session.add(new_history_entry)
            acc.last_updated = datetime.utcnow()
            db.session.commit()
            flash(f'Дані для @{acc.username} успішно оновлено.', 'success')
        else:
            flash(f'Не вдалося оновити дані для @{acc.username}.', 'warning')
    
    except Exception as e:
        print(f"Критична помилка оновлення {acc.username}: {e}")
        db.session.rollback()
        flash('Сталася помилка під час оновлення.', 'danger')

    return redirect(url_for('dashboard'))

@app.route('/track-account', methods=['POST'])
@login_required
def track_account():
    if not current_user.is_pro: abort(403)
    
    platform = request.form.get('platform')
    username = request.form.get('username')
    account_name = request.form.get('account_name')
    url = request.form.get('url')
    
    if platform != 'telegram':
        flash('Наразі відстеження доступне лише для Telegram-каналів.', 'danger')
        return redirect(url_for('show_result'))
    
    if not all([platform, username, account_name, url]):
        flash('Не вдалося отримати дані акаунта для відстеження.', 'danger')
        return redirect(url_for('index'))
        
    try:
        new_tracked_account = TrackedAccount(
            user_id=current_user.id,
            platform=platform,
            username=username,
            account_name=account_name,
            url=url,
            last_updated=datetime.utcnow()
        )
        db.session.add(new_tracked_account)
        db.session.commit() 
        
        data = session.get('last_analysis')
        if data and data.get('username') == username:
            if 'insights' not in data:
                 data['insights'] = generate_pro_insights(data)

            first_history_entry = AnalyticsHistory(
                tracked_account_id=new_tracked_account.id,
                subscribers=data.get('subscribers'),
                er=data.get('er', 0)
            )
            db.session.add(first_history_entry)
            db.session.commit()
        
        flash(f'Канал @{username} успішно додано у ваш Дашборд!', 'success')
        return redirect(url_for('dashboard'))
        
    except IntegrityError:
        db.session.rollback()
        flash(f'Ви вже відстежуєте канал @{username}.', 'info')
        return redirect(url_for('dashboard'))
    except Exception as e:
        db.session.rollback()
        print(f"Помилка при додаванні акаунта: {e}")
        flash('Сталася помилка при додаванні акаунта.', 'danger')
        return redirect(url_for('show_result'))


@app.route('/untrack-account/<int:account_id>', methods=['POST'])
@login_required
def untrack_account(account_id):
    if not current_user.is_pro: abort(403)
    account_to_delete = TrackedAccount.query.get(account_id)
    if account_to_delete and account_to_delete.user_id == current_user.id:
        try:
            db.session.delete(account_to_delete)
            db.session.commit()
            flash(f'Акаунт @{account_to_delete.username} видалено з Дашборда.', 'success')
        except Exception as e:
            db.session.rollback()
            print(f"Помилка видалення: {e}")
            flash('Сталася помилка при видаленні.', 'danger')
    else:
        flash('Акаунт не знайдено або у вас немає прав.', 'danger')
    return redirect(url_for('dashboard'))


@app.route('/dashboard/view/<int:account_id>')
@login_required
def dashboard_view_account(account_id):
    if not current_user.is_pro:
        return redirect(url_for('upgrade_page'))
    account = TrackedAccount.query.get(account_id)
    if not account or account.user_id != current_user.id:
        flash('Акаунт не знайдено.', 'danger')
        return redirect(url_for('dashboard'))
    history = account.get_recent_history(days=30)
    return render_template('dashboard_view.html', account=account, history=history)


@app.route('/api/get-chart-data/<int:account_id>')
@login_required
def get_chart_data(account_id):
    if not current_user.is_pro: abort(403)
    account = TrackedAccount.query.get(account_id)
    if not account or account.user_id != current_user.id:
        abort(404)
    history = account.get_recent_history(days=30)
    labels = [h.date.strftime('%Y-%m-%d') for h in history]
    values = [h.subscribers for h in history]
    return jsonify({ 'labels': labels, 'values': values })

# --- РОУТИ МОНЕТИЗАЦІЇ (Fondy) (без змін) ---
@app.route('/upgrade')
@login_required 
def upgrade_page():
    return render_template('upgrade.html')

@app.route('/create-fondy-checkout', methods=['POST'])
@login_required 
def create_fondy_checkout():
    user_id = current_user.id 
    base_url = get_base_url()
    order_id = f"pro_{user_id}_{uuid.uuid4()}"
    session['pending_order_id'] = order_id
    try:
        checkout_url = create_fondy_checkout_url(
            order_id=order_id,
            amount_cents=10000,
            currency='UAH',
            description=f"Pro підписка на 1 рік (User ID: {user_id})",
            base_url=base_url
        )
        return redirect(checkout_url)
    except Exception as e:
        print(f"Помилка створення сесії Fondy: {e}")
        return abort(500, f"Помилка підключення до платіжної системи. {e}")

@app.route('/fondy-webhook', methods=['POST'])
def fondy_webhook():
    try:
        data = request.json
        if not data:
            print("Webhook: Отримано порожній запит")
            return "Empty request", 400
        print(f"Webhook: Отримано дані: {data}")
        if data.get('order_status') == 'approved':
            order_id = data.get('order_id')
            parts = order_id.split('_')
            if len(parts) >= 2 and parts[0] == 'pro':
                user_id = parts[1]
                with app.app_context():
                    user_to_upgrade = User.query.get(user_id)
                    if user_to_upgrade and not user_to_upgrade.is_pro:
                        expiry_date = date.today() + timedelta(days=365) 
                        user_to_upgrade.is_pro = True
                        user_to_upgrade.expiry_date = expiry_date
                        db.session.commit()
                        print(f"Webhook: Успішно активовано Pro для User ID: {user_id}")
                    else:
                        print(f"Webhook: Користувач {user_id} не знайдений або вже Pro.")
            else:
                 print(f"Webhook: Отримано невідомий формат order_id: {order_id}")
        return 'OK', 200
    except Exception as e:
        print(f"Помилка обробки Webhook: {e}")
        return 'Error', 500

@app.route('/success', methods=['GET', 'POST'])
def success():
    session.pop('pending_order_id', None) 
    return render_template('success_pending.html')

@app.route('/fondy-failure')
def fondy_failure():
    return render_template('fondy_failure.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)