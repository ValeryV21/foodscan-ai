"""
UI помощни функции и CSS стилове за мобилния интерфейс.
"""

import streamlit as st


# ============ ОСНОВЕН CSS ============
MOBILE_CSS = """
<style>
/* ===== Импортиране на шрифтове ===== */
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap');

/* ===== Основни настройки ===== */
:root {
    --primary: #00B894;
    --primary-dark: #00A381;
    --danger: #FF3B30;
    --warning: #FF9500;
    --success: #34C759;
    --bg: #0A0F1E;
    --bg-card: #111827;
    --bg-card2: #1A2235;
    --text: #F0F4FF;
    --text-muted: #8896B0;
    --border: rgba(255,255,255,0.08);
    --radius: 18px;
    --shadow: 0 8px 32px rgba(0,0,0,0.4);
}

/* ===== Глобален layout ===== */
.stApp {
    background: linear-gradient(135deg, #0A0F1E 0%, #0F172A 50%, #0A0F1E 100%) !important;
    font-family: 'Nunito', sans-serif !important;
}

/* ===== Sidebar ===== */
[data-testid="stSidebar"] {
    background: #0D1426 !important;
    border-right: 1px solid var(--border) !important;
}

/* ===== Хедър ===== */
.app-header {
    background: linear-gradient(135deg, #00B894 0%, #00CEC9 50%, #6C5CE7 100%);
    border-radius: var(--radius);
    padding: 28px 24px;
    margin-bottom: 24px;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0, 184, 148, 0.3);
    position: relative;
    overflow: hidden;
}

.app-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
    animation: pulse-bg 4s ease-in-out infinite;
}

@keyframes pulse-bg {
    0%, 100% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.1); opacity: 1; }
}

.app-header h1 {
    color: white !important;
    font-size: 28px !important;
    font-weight: 900 !important;
    margin: 0 !important;
    text-shadow: 0 2px 10px rgba(0,0,0,0.3);
    letter-spacing: -0.5px;
    position: relative;
    z-index: 1;
}

.app-header p {
    color: rgba(255,255,255,0.85) !important;
    font-size: 14px !important;
    margin: 8px 0 0 0 !important;
    position: relative;
    z-index: 1;
}

/* ===== Карти ===== */
.food-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: var(--shadow);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.food-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(0,0,0,0.5);
}

.food-card-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 16px;
    padding-bottom: 14px;
    border-bottom: 1px solid var(--border);
}

.food-emoji {
    font-size: 48px;
    min-width: 60px;
    text-align: center;
    filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
}

.food-info h2 {
    color: var(--text) !important;
    font-size: 20px !important;
    font-weight: 800 !important;
    margin: 0 0 4px 0 !important;
}

.food-info .brand {
    color: var(--text-muted);
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ===== Скор/Рейтинг ===== */
.health-score-ring {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 24px;
    background: var(--bg-card2);
    border-radius: var(--radius);
    border: 1px solid var(--border);
    margin-bottom: 16px;
}

.score-number {
    font-size: 72px;
    font-weight: 900;
    line-height: 1;
    font-family: 'Space Grotesk', sans-serif;
}

.score-label {
    font-size: 16px;
    font-weight: 700;
    margin-top: 8px;
    text-align: center;
}

.score-sublabel {
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 4px;
}

/* ===== Бар прогрес ===== */
.nutrient-bar {
    margin-bottom: 12px;
}

.nutrient-label {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}

.nutrient-name {
    color: var(--text);
    font-size: 14px;
    font-weight: 600;
}

.nutrient-value {
    color: var(--text-muted);
    font-size: 13px;
}

.progress-track {
    height: 8px;
    background: rgba(255,255,255,0.08);
    border-radius: 4px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.5s ease;
}

/* ===== Добавки ===== */
.additive-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    border-radius: 100px;
    font-size: 13px;
    font-weight: 700;
    margin: 4px;
    border: 1px solid transparent;
}

.additive-badge.high {
    background: rgba(255, 59, 48, 0.15);
    color: #FF6B6B;
    border-color: rgba(255, 59, 48, 0.3);
}

.additive-badge.medium-high {
    background: rgba(255, 107, 53, 0.15);
    color: #FF8C42;
    border-color: rgba(255, 107, 53, 0.3);
}

.additive-badge.medium {
    background: rgba(255, 159, 28, 0.15);
    color: #FFBE0B;
    border-color: rgba(255, 159, 28, 0.3);
}

.additive-badge.low-medium, .additive-badge.low {
    background: rgba(76, 175, 80, 0.15);
    color: #69F0AE;
    border-color: rgba(76, 175, 80, 0.3);
}

/* ===== Здравни рискове ===== */
.risk-card {
    background: var(--bg-card2);
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 10px;
    border-left: 4px solid;
    transition: all 0.2s ease;
}

.risk-card.high { border-color: #FF3B30; }
.risk-card.medium { border-color: #FF9500; }
.risk-card.low { border-color: #34C759; }

.risk-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
}

.risk-title {
    font-size: 15px;
    font-weight: 700;
    color: var(--text);
}

.risk-level {
    font-size: 12px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 100px;
}

.risk-level.high {
    background: rgba(255,59,48,0.2);
    color: #FF6B6B;
}

.risk-level.medium {
    background: rgba(255,149,0,0.2);
    color: #FFB340;
}

.risk-level.low {
    background: rgba(52,199,89,0.2);
    color: #34C759;
}

.risk-text {
    font-size: 13px;
    color: var(--text-muted);
    line-height: 1.5;
}

/* ===== Алтернативи ===== */
.alternative-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(0, 184, 148, 0.12);
    color: #00D4AA;
    border: 1px solid rgba(0, 184, 148, 0.25);
    border-radius: 100px;
    padding: 8px 16px;
    font-size: 14px;
    font-weight: 600;
    margin: 4px;
    transition: all 0.2s ease;
    cursor: default;
}

.alternative-chip:hover {
    background: rgba(0, 184, 148, 0.2);
}

/* ===== История карта ===== */
.history-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 14px;
}

.history-emoji {
    font-size: 32px;
    min-width: 40px;
    text-align: center;
}

.history-info {
    flex: 1;
}

.history-name {
    color: var(--text);
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 4px;
}

.history-meta {
    color: var(--text-muted);
    font-size: 12px;
}

.history-score {
    font-size: 22px;
    font-weight: 900;
    font-family: 'Space Grotesk', sans-serif;
    min-width: 36px;
    text-align: center;
}

/* ===== Бутони ===== */
.stButton > button {
    background: linear-gradient(135deg, #00B894, #00CEC9) !important;
    color: white !important;
    border: none !important;
    border-radius: 100px !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    padding: 14px 28px !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 16px rgba(0, 184, 148, 0.3) !important;
    font-family: 'Nunito', sans-serif !important;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 24px rgba(0, 184, 148, 0.5) !important;
}

/* ===== Tabs ===== */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-card) !important;
    border-radius: 100px !important;
    padding: 4px !important;
    border: 1px solid var(--border) !important;
    gap: 0 !important;
}

.stTabs [data-baseweb="tab"] {
    color: var(--text-muted) !important;
    border-radius: 100px !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    padding: 10px 16px !important;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #00B894, #00CEC9) !important;
    color: white !important;
}

/* ===== Inputs ===== */
.stSelectbox > div > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    color: var(--text) !important;
}

.stFileUploader {
    background: var(--bg-card) !important;
    border: 2px dashed var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 20px !important;
    text-align: center;
    transition: all 0.3s ease;
}

.stFileUploader:hover {
    border-color: var(--primary) !important;
}

/* ===== Expander ===== */
.streamlit-expanderHeader {
    background: var(--bg-card2) !important;
    border-radius: 14px !important;
    color: var(--text) !important;
    font-weight: 700 !important;
}

/* ===== Текст елементи ===== */
h1, h2, h3, h4 {
    color: var(--text) !important;
    font-family: 'Nunito', sans-serif !important;
}

p, label, .stMarkdown {
    color: var(--text-muted) !important;
}

/* ===== Мобилна адаптация ===== */
@media (max-width: 768px) {
    .app-header h1 { font-size: 22px !important; }
    .score-number { font-size: 56px; }
    .food-emoji { font-size: 36px; }
    .food-info h2 { font-size: 17px !important; }
    
    /* По-малки падинги на малки екрани */
    .food-card { padding: 14px; }
    .block-container { padding: 12px !important; }
}

/* ===== Анимации ===== */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.animate-in {
    animation: fadeInUp 0.4s ease forwards;
}

/* ===== Spinner ===== */
.loading-spinner {
    text-align: center;
    padding: 40px;
    color: var(--primary);
}

/* ===== Информационна секция ===== */
.info-section {
    background: rgba(0, 184, 148, 0.08);
    border: 1px solid rgba(0, 184, 148, 0.2);
    border-radius: 14px;
    padding: 16px;
    margin: 12px 0;
}

.info-section p {
    color: var(--text) !important;
    font-size: 14px;
    line-height: 1.6;
    margin: 0;
}

/* ===== Метрики ===== */
.stMetric {
    background: var(--bg-card) !important;
    border-radius: 14px !important;
    padding: 16px !important;
    border: 1px solid var(--border) !important;
}

.stMetric label {
    color: var(--text-muted) !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

.stMetric [data-testid="stMetricValue"] {
    color: var(--text) !important;
    font-weight: 800 !important;
}

/* ===== Divider ===== */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 20px 0 !important;
}

/* ===== Image ===== */
.stImage {
    border-radius: 14px !important;
    overflow: hidden;
}

/* ===== Section titles ===== */
.section-title {
    font-size: 18px;
    font-weight: 800;
    color: var(--text);
    margin: 20px 0 14px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ===== Score indicators ===== */
.score-indicator {
    display: flex;
    gap: 6px;
    margin-top: 12px;
    justify-content: center;
}

.score-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: rgba(255,255,255,0.1);
}

.score-dot.active {
    background: currentColor;
}
</style>
"""


def render_header():
    """Рендира хедъра на приложението."""
    st.markdown("""
    <div class="app-header">
        <h1>🔍 FoodScan AI</h1>
        <p>Анализирай хранителните продукти за секунди</p>
    </div>
    """, unsafe_allow_html=True)


def render_health_score(score: int, label: str, color: str, emoji: str):
    """Рендира визуален индикатор за здравна оценка."""
    st.markdown(f"""
    <div class="health-score-ring animate-in">
        <div class="score-number" style="color: {color}">{score}</div>
        <div class="score-label" style="color: {color}">{emoji} {label}</div>
        <div class="score-sublabel">Скала на вредност: 1 (здравословно) — 10 (много вредно)</div>
        <div class="score-indicator">
            {"".join([
                f'<div class="score-dot {"active" if i <= score else ""}" style="color: {color}; background: {"" if i <= score else "rgba(255,255,255,0.1)"}; background-color: {color if i <= score else "rgba(255,255,255,0.08)"}"></div>'
                for i in range(1, 11)
            ])}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_additive_badge(code: str, name: str, risk_level: str):
    """Рендира бадж за хранителна добавка."""
    st.markdown(f"""
    <span class="additive-badge {risk_level}">
        <span>{code}</span>
        <span style="opacity:0.7">|</span>
        <span>{name}</span>
    </span>
    """, unsafe_allow_html=True)


def render_nutrition_bar(label: str, value: float, unit: str, percentage: float, color: str):
    """Рендира бар за хранителна стойност."""
    st.markdown(f"""
    <div class="nutrient-bar">
        <div class="nutrient-label">
            <span class="nutrient-name">{label}</span>
            <span class="nutrient-value">{value}{unit} ({percentage}% ДД)</span>
        </div>
        <div class="progress-track">
            <div class="progress-fill" style="width: {min(100, percentage)}%; background: {color};"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_risk_card(name: str, emoji: str, level: str, text: str):
    """Рендира карта за здравен риск."""
    level_labels = {
        "high": "⛔ Висок риск",
        "medium": "⚠️ Среден риск",
        "low": "✅ Нисък риск"
    }
    st.markdown(f"""
    <div class="risk-card {level}">
        <div class="risk-header">
            <span style="font-size:22px">{emoji}</span>
            <span class="risk-title">{name}</span>
            <span class="risk-level {level}">{level_labels.get(level, level)}</span>
        </div>
        <div class="risk-text">{text}</div>
    </div>
    """, unsafe_allow_html=True)


def render_history_card(entry: dict):
    """Рендира карта за история."""
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(entry["timestamp"])
        time_str = dt.strftime("%d.%m %H:%M")
    except Exception:
        time_str = "—"
    
    st.markdown(f"""
    <div class="history-card">
        <div class="history-emoji">{entry.get('emoji', '🍽️')}</div>
        <div class="history-info">
            <div class="history-name">{entry['product_name']}</div>
            <div class="history-meta">{entry.get('brand', '')} • {time_str} • {entry.get('additives_count', 0)} добавки</div>
        </div>
        <div class="history-score" style="color: {entry['health_color']}">{entry['health_score']}</div>
    </div>
    """, unsafe_allow_html=True)


def render_alternatives(alternatives: list):
    """Рендира алтернативи за продукта."""
    badges = " ".join([
        f'<span class="alternative-chip">🌿 {alt}</span>'
        for alt in alternatives
    ])
    st.markdown(f'<div style="display:flex; flex-wrap:wrap; gap:4px;">{badges}</div>', unsafe_allow_html=True)


def render_product_header(name: str, brand: str, category: str, emoji: str):
    """Рендира хедъра на продукта."""
    st.markdown(f"""
    <div class="food-card animate-in">
        <div class="food-card-header">
            <div class="food-emoji">{emoji}</div>
            <div class="food-info">
                <h2>{name}</h2>
                <div class="brand">🏷️ {brand} • {category}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_section_title(icon: str, title: str):
    """Рендира заглавие на секция."""
    st.markdown(f"""
    <div class="section-title">
        <span>{icon}</span>
        <span>{title}</span>
    </div>
    """, unsafe_allow_html=True)


def get_nutriscore_color(grade: str) -> str:
    """Връща цвят за Nutri-Score."""
    colors = {
        "A": "#038141",
        "B": "#85BB2F",
        "C": "#FECB02",
        "D": "#EE8100",
        "E": "#E63E11",
    }
    return colors.get(grade.upper(), "#888")
