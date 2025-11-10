import io
import csv

def generate_csv(data: dict) -> io.StringIO:
    """
    Конвертує словник 'data' з аналітикою Telegram у CSV-рядок.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 1. Заголовок
    writer.writerow(['Параметр', 'Значення'])
    
    # 2. Основні дані
    writer.writerow(['Назва', data.get('name', 'N/A')])
    writer.writerow(['Username', f"@{data.get('username', 'N/A')}" if data.get('username') else 'N/A'])
    writer.writerow(['URL', data.get('url', 'N/A')])
    writer.writerow(['Тип', data.get('type', 'N/A')])
    
    # 3. Метрики (тільки Telegram)
    writer.writerow(['Підписники', data.get('subscribers', 0)])
    writer.writerow(['Сер. перегляди (20 постів)', data.get('avg_views', 0)])

    # 4. Pro-метрики (якщо вони є у словнику)
    if 'er' in data:
        writer.writerow(['--- Pro Метрики (Якість) ---', '---'])
        writer.writerow(['Engagement Rate (ER)', f"{data.get('er', 0):.2f}%"])
        writer.writerow(['Частота постингу (пост/день)', f"{data.get('posts_per_day', 0):.1f}"])
        # --- НОВІ РЯДКИ ---
        writer.writerow(['Коефіцієнт Реакцій (RR)', f"{data.get('reaction_rate', 0):.2f}%"])
        writer.writerow(['Мін. Перегляди (20 постів)', data.get('min_views', 0)])
        writer.writerow(['Макс. Перегляди (20 постів)', data.get('max_views', 0)])

    # 5. Top/Flop пости
    if 'top_posts' in data:
        writer.writerow(['--- Top Пости ---', '---'])
        metric_name = "Перегляди"
        for i, post in enumerate(data.get('top_posts', [])):
            writer.writerow([f"Top {i+1} ({metric_name})", post.get('views', 0)])
            writer.writerow([f"Top {i+1} (Текст)", post.get('text', 'N/A')])
    
    if 'flop_posts' in data:
        writer.writerow(['--- Flop Пости ---', '---'])
        metric_name = "Перегляди"
        for i, post in enumerate(data.get('flop_posts', [])):
            writer.writerow([f"Flop {i+1} ({metric_name})", post.get('views', 0)])
            writer.writerow([f"Flop {i+1} (Текст)", post.get('text', 'N/A')])

    # 6. НОВИЙ БЛОК: Поради
    if 'insights' in data:
        writer.writerow(['--- Pro Поради ---', '---'])
        for i, insight in enumerate(data.get('insights', [])):
            writer.writerow([f"Порада #{i+1} ({insight.get('type')})", insight.get('text', 'N/A')])

    output.seek(0)
    return output