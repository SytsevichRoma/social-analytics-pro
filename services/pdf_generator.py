import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, Image
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont

# --- Налаштування Шрифтів ---
PDF_FONT_NAME = 'Helvetica' 
PDF_FONT_NAME_CYRILLIC = 'DejaVuSans'
PDF_FONT_BOLD = 'Helvetica-Bold'
PDF_FONT_CYRILLIC_BOLD = 'DejaVuSans-Bold' 

COLOR_BACKGROUND = colors.HexColor("#111827") 
COLOR_CARD = colors.HexColor("#1F2937") 
COLOR_WHITE = colors.HexColor("#FFFFFF")
COLOR_GRAY = colors.HexColor("#9CA3AF")
COLOR_BLUE = colors.HexColor("#3B82F6")
COLOR_GREEN = colors.HexColor("#16A34A")
COLOR_RED = colors.HexColor("#DC2626")
COLOR_YELLOW = colors.HexColor("#EAB308") # Для 'suggestion'

try:
    font_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'DejaVuSans.ttf')
    if os.path.exists(font_path):
         registerFont(TTFont(PDF_FONT_NAME_CYRILLIC, font_path))
         PDF_FONT_NAME = PDF_FONT_NAME_CYRILLIC
         print("Шрифт DejaVuSans.ttf успішно завантажено для PDF.")
    else:
        print(f"ПОПЕРЕДЖЕННЯ: Шрифт DejaVuSans.ttf не знайдено у '{font_path}'.")

    font_path_bold = os.path.join(os.path.dirname(__file__), '..', 'static', 'DejaVuSans-Bold.ttf')
    if os.path.exists(font_path_bold):
        registerFont(TTFont(PDF_FONT_CYRILLIC_BOLD, font_path_bold))
        PDF_FONT_BOLD = PDF_FONT_CYRILLIC_BOLD
        print("Шрифт DejaVuSans-Bold.ttf успішно завантажено.")
    else:
        print("ПОПЕРЕДЖЕННЯ: 'DejaVuSans-Bold.ttf' не знайдено.")
        PDF_FONT_BOLD = PDF_FONT_NAME 
except Exception as e:
    print(f"ПОПЕРЕДЖЕННЯ: Не вдалося завантажити шрифт для PDF: {e}")

# --- Глобальні Стилі ---
def get_pdf_styles():
    """Створює наші кастомні стилі для PDF"""
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='Base', fontName=PDF_FONT_NAME, fontSize=10, 
        leading=14, textColor=COLOR_GRAY
    ))
    styles.add(ParagraphStyle(
        name='Base_White', parent=styles['Base'], textColor=COLOR_WHITE
    ))
    styles.add(ParagraphStyle(
        name='H1_White', parent=styles['Base'], fontName=PDF_FONT_BOLD, 
        fontSize=16, alignment=TA_LEFT, textColor=COLOR_WHITE, spaceAfter=0, leading=20
    ))
    styles.add(ParagraphStyle(
        name='H1_Sub', parent=styles['Base'], fontName=PDF_FONT_NAME, 
        fontSize=11, alignment=TA_LEFT, textColor=COLOR_GRAY, spaceAfter=16
    ))
    styles.add(ParagraphStyle(
        name='H2_White', parent=styles['Base'], fontName=PDF_FONT_BOLD, 
        fontSize=14, textColor=COLOR_WHITE, spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name='Card_Title_Small', parent=styles['Base'], fontSize=9, 
        textColor=COLOR_GRAY, alignment=TA_LEFT, spaceAfter=2
    ))
    styles.add(ParagraphStyle(
        name='Card_Value_Big', parent=styles['Base'], fontName=PDF_FONT_BOLD, 
        fontSize=26, textColor=COLOR_WHITE, alignment=TA_LEFT, leading=30
    ))
    styles.add(ParagraphStyle(
        name='Card_Value_Pro_ER', parent=styles['Card_Value_Big'], fontSize=20, 
        textColor=COLOR_WHITE, alignment=TA_LEFT
    ))
    styles.add(ParagraphStyle(
        name='Card_Value_Pro_Sub', parent=styles['Base'], fontSize=10, 
        alignment=TA_LEFT # Змінено на TA_LEFT
    ))
    styles.add(ParagraphStyle(
        name='TopPostTitle', parent=styles['Base'], fontName=PDF_FONT_BOLD, 
        fontSize=11, textColor=COLOR_GREEN, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name='FlopPostTitle', parent=styles['TopPostTitle'], textColor=COLOR_RED
    ))
    styles.add(ParagraphStyle(
        name='PostText', parent=styles['Base'], fontSize=10, 
        textColor=COLOR_WHITE, spaceAfter=2
    ))
    styles.add(ParagraphStyle(
        name='PostMetric', parent=styles['Base'], fontSize=9, 
        textColor=COLOR_GRAY, spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        name='Footer', parent=styles['Base'], fontSize=8, 
        alignment=TA_CENTER, textColor=COLOR_GRAY
    ))
    
    # --- НОВІ СТИЛІ ДЛЯ ПОРАД ---
    styles.add(ParagraphStyle(
        name='Insight_Positive', parent=styles['Base'], textColor=COLOR_GREEN,
    ))
    styles.add(ParagraphStyle(
        name='Insight_Warning', parent=styles['Base'], textColor=COLOR_RED,
    ))
    styles.add(ParagraphStyle(
        name='Insight_Suggestion', parent=styles['Base'], textColor=COLOR_YELLOW,
    ))

    return styles

styles = get_pdf_styles() # Отримуємо стилі один раз

def _on_page(canvas, doc):
    """Малює темний фон та футер на КОЖНІЙ сторінці"""
    canvas.saveState()
    width, height = doc.pagesize
    canvas.setFillColor(COLOR_BACKGROUND)
    canvas.rect(0, 0, width, height, fill=1, stroke=0)
    footer_text = f"© {datetime.now().year} Social Analytics Pro | Звіт згенеровано {datetime.now().strftime('%Y-%m-%d')}"
    p_footer = Paragraph(footer_text, styles['Footer'])
    w, h = p_footer.wrapOn(canvas, doc.width, doc.bottomMargin)
    p_footer.drawOn(canvas, doc.leftMargin, h) 
    page_num = canvas.getPageNumber()
    page_text = f"Сторінка {page_num}"
    canvas.setFont(PDF_FONT_NAME, 8)
    canvas.setFillColor(COLOR_GRAY)
    canvas.drawRightString(doc.width + doc.leftMargin, doc.bottomMargin, page_text)
    canvas.restoreState()

def _create_metric_card(data: dict):
    p_title = Paragraph('ПІДПИСНИКИ:', styles['Card_Title_Small'])
    p_value = Paragraph(f"{data.get('subscribers', 0):,}", styles['Card_Value_Big'])
    p_title2 = Paragraph('СЕР. ПЕРЕГЛЯДИ (20 ПОСТІВ):', styles['Card_Title_Small'])
    p_value2 = Paragraph(f"{data.get('avg_views', 0):,}", styles['Card_Value_Big'])
    table_data = [[p_title, p_title2], [p_value, p_value2]]
    table = Table(table_data, colWidths=[2.5*inch, 3.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), COLOR_CARD),
        ('PADDING', (0,0), (-1,-1), 12),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]), 
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    return table

def _create_pro_metrics_card(data: dict):
    """Створює 'Картку' для Pro Метрик (з новими Red Flags)"""
    p_title = Paragraph('🚀 PRO АНАЛІТИКА (ЯКІСТЬ АУДИТОРІЇ)', styles['H2_White'])
    
    # ER (великий, зліва)
    p_er_title = Paragraph('Engagement Rate (ER):', styles['Card_Title_Small'])
    p_er_value = Paragraph(f"{data.get('er', 0):.2f}%", styles['Card_Value_Pro_ER'])
    er_block = [p_er_title, p_er_value]
    
    # --- НОВІ МЕТРИКИ (справа) ---
    p_rr_title = Paragraph('Коефіцієнт Реакцій (RR):', styles['Card_Title_Small'])
    p_rr_value = Paragraph(f"{data.get('reaction_rate', 0):.2f}%", styles['Card_Value_Pro_Sub'])
    
    p_spread_title = Paragraph('Розкид переглядів (Min/Max):', styles['Card_Title_Small'])
    p_spread_value = Paragraph(f"{data.get('min_views', 0):,} / {data.get('max_views', 0):,}", styles['Card_Value_Pro_Sub'])
    
    p_posts_title = Paragraph('Частота постингу:', styles['Card_Title_Small'])
    p_posts_value = Paragraph(f"~ {data.get('posts_per_day', 0):.1f} пост/день", styles['Card_Value_Pro_Sub'])
    
    # Збираємо правий блок
    sub_metrics_block = [
        p_rr_title, p_rr_value, 
        Spacer(1, 8),
        p_spread_title, p_spread_value,
        Spacer(1, 8),
        p_posts_title, p_posts_value
    ]
    
    # Розміщуємо ER зліва, а 3 інші метрики справа
    data_row = [
        [er_block, sub_metrics_block]
    ]
    
    inner_table = Table(data_row, colWidths=[3*inch, 3*inch])
    inner_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    
    full_card_data = [[p_title], [inner_table]]
    table = Table(full_card_data, colWidths=[6*inch]) 
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), COLOR_CARD),
        ('PADDING', (0,0), (-1,-1), 12),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    return table

def _create_content_card(data: dict, platform: str, usable_width: float):
    metric_name = "переглядів"
    metric_key = "views"
    
    top_posts_content = [Paragraph('📈 Top 3 Пости', styles['TopPostTitle'])]
    top_posts = data.get('top_posts', [])
    if top_posts:
        for post in top_posts:
            p_text = Paragraph(post.get('text', 'N/A'), styles['PostText'])
            p_metric = Paragraph(f"{post.get(metric_key, 0):,} {metric_name}", styles['PostMetric'])
            top_posts_content.extend([p_text, p_metric])
    else:
        top_posts_content.append(Paragraph("Немає даних.", styles['Base']))

    flop_posts_content = [Paragraph('📉 Flop 3 Пости', styles['FlopPostTitle'])]
    flop_posts = data.get('flop_posts', [])
    if flop_posts:
         for post in flop_posts:
            p_text = Paragraph(post.get('text', 'N/A'), styles['PostText'])
            p_metric = Paragraph(f"{post.get(metric_key, 0):,} {metric_name}", styles['PostMetric'])
            flop_posts_content.extend([p_text, p_metric])
    else:
        flop_posts_content.append(Paragraph("Немає даних.", styles['Base']))

    data_table = [[top_posts_content, flop_posts_content]]
    col_width = (usable_width / 2.0) - (5 * mm) 
    table = Table(data_table, colWidths=[col_width, col_width])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), COLOR_CARD),
        ('PADDING', (0,0), (-1,-1), 12),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    return table

def _create_history_card(history: list, platform: str):
    p_title = Paragraph("📈 Історія Зростання (Останні 7 днів)", styles['H2_White'])
    table_data = [
        [
            Paragraph("Дата", styles['PostText']), 
            Paragraph("Підписники", styles['PostText']), 
            Paragraph("ER (%)", styles['PostText'])
        ]
    ]
    for entry in history:
        metric = entry.subscribers
        table_data.append([
            Paragraph(entry.date.strftime('%Y-%m-%d'), styles['Base']),
            Paragraph(f"{metric:,}", styles['Base']),
            Paragraph(f"{entry.er:.2f}%", styles['Base'])
        ])
    inner_table = Table(table_data, colWidths=[2*inch, 2*inch, 2*inch])
    inner_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, COLOR_GRAY), 
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#374151")), 
    ]))
    full_card_data = [[p_title], [inner_table]]
    table = Table(full_card_data, colWidths=[6*inch]) 
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), COLOR_CARD),
        ('PADDING', (0,0), (-1,-1), 12),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    return table

# --- НОВА КАРТКА ДЛЯ ПОРАД ---
def _create_insights_card(insights: list):
    """Створює 'Картку' для Pro Порад"""
    
    p_title = Paragraph("💡 Pro Поради & \"Red Flags\"", styles['H2_White'])
    
    content = [p_title]
    
    if not insights:
        content.append(Paragraph("Аналіз не виявив значних проблем або переваг.", styles['Base']))
    else:
        for insight in insights:
            # Вибираємо стиль (колір)
            if insight['type'] == 'positive':
                style = styles['Insight_Positive']
                icon = '✅'
            elif insight['type'] == 'warning':
                style = styles['Insight_Warning']
                icon = '🚨'
            else: # suggestion
                style = styles['Insight_Suggestion']
                icon = '💡'
                
            p_text = Paragraph(f"{icon} {insight['text']}", style)
            content.append(p_text)
            content.append(Spacer(1, 4)) # Маленький відступ

    table = Table([ [content] ], colWidths=[6*inch]) 
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), COLOR_CARD),
        ('PADDING', (0,0), (-1,-1), 12),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    return table


# --- ГОЛОВНА ФУНКЦІЯ ГЕНЕРАЦІЇ ---

def generate_pdf_report(data: dict, platform: str, history: list = None, avatar_path: str = None) -> io.BytesIO:
    """
    Генерує PDF-звіт, з аватаркою, порадами та стилем з фото.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        leftMargin=inch/2,
        rightMargin=inch/2,
        topMargin=inch/2,
        bottomMargin=inch/2
    )
    
    Story = []
    
    # --- 1. Шапка з Аватаркою ---
    name = data.get('name', 'N/A').upper()
    username = data.get('username', 'N/A')
    
    p_title = Paragraph(name, styles['H1_White'])
    p_subtitle = Paragraph(f"@{username} - {data.get('type', 'Telegram Канал')}", styles['H1_Sub'])
    text_content = [p_title, p_subtitle]

    header_content = []
    col_widths = []

    if avatar_path and os.path.exists(avatar_path):
        try:
            avatar_img = Image(avatar_path, width=0.8*inch, height=0.8*inch)
            avatar_img.mask = 'auto' 
            header_content = [[avatar_img, text_content]]
            col_widths = [0.9*inch, 5.1*inch] 
        except Exception as e:
            print(f"Помилка обробки аватарки: {e}")
            header_content = [text_content]
            col_widths = [6*inch]
    else:
        header_content = [text_content]
        col_widths = [6*inch]

    header_table = Table(header_content, colWidths=col_widths)
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (0,0), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    
    Story.append(header_table)
    
    
    if data.get('is_private'):
        Story.append(Paragraph("🔒 Акаунт приватний. Аналітика недоступна.", styles['Base_White']))
    else:
        # --- 2. Картка Базових Метрик ---
        Story.append(_create_metric_card(data))
        Story.append(Spacer(1, 0.15 * inch))
        
        # --- 3. Картка Pro Метрик ---
        Story.append(_create_pro_metrics_card(data))
        Story.append(Spacer(1, 0.15 * inch))
        
        # --- 4. НОВА КАРТКА: PRO ПОРАДИ ---
        if data.get('insights'):
            Story.append(_create_insights_card(data['insights']))
            Story.append(Spacer(1, 0.15 * inch))

        # --- 5. Картка Історії (якщо є) ---
        if history:
            Story.append(_create_history_card(history, platform))
            Story.append(Spacer(1, 0.15 * inch))

        # --- 6. Картка Аналізу Контенту ---
        Story.append(_create_content_card(data, platform, doc.width))

    # Збираємо PDF
    doc.build(Story, onFirstPage=_on_page, onLaterPages=_on_page)
    
    buffer.seek(0)
    return buffer