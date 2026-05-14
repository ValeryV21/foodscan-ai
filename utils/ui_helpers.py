"""UI помощни функции и CSS стилове."""
import streamlit as st

MOBILE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Space+Grotesk:wght@500;700;900&display=swap');

:root {
  --bg:        #0A0F1E; --bg2: #111827; --bg3: #1A2235;
  --primary:   #00B894; --primary2: #00CEC9;
  --danger:    #FF3B30; --warn: #FF9500; --ok: #34C759;
  --text:      #F0F4FF; --muted: #8896B0;
  --border:    rgba(255,255,255,0.08);
  --r:         18px; --shadow: 0 8px 32px rgba(0,0,0,0.4);
}
.stApp { background: linear-gradient(135deg,#0A0F1E 0%,#0F172A 50%,#0A0F1E 100%) !important; font-family:'Nunito',sans-serif !important; }
[data-testid="stSidebar"]{ background:#0D1426 !important; border-right:1px solid var(--border) !important; }

/* Header */
.app-header{ background:linear-gradient(135deg,#00B894,#00CEC9 50%,#6C5CE7); border-radius:var(--r); padding:28px 24px; margin-bottom:24px; text-align:center; box-shadow:0 8px 32px rgba(0,184,148,.3); }
.app-header h1{ color:white !important; font-size:28px !important; font-weight:900 !important; margin:0 !important; letter-spacing:-.5px; }
.app-header p { color:rgba(255,255,255,.85) !important; font-size:14px !important; margin:8px 0 0 !important; }

/* Cards */
.food-card { background:var(--bg2); border:1px solid var(--border); border-radius:var(--r); padding:20px; margin-bottom:16px; box-shadow:var(--shadow); }
.food-card:hover{ transform:translateY(-2px); box-shadow:0 12px 40px rgba(0,0,0,.5); transition:all .2s; }
.section-title{ font-size:18px; font-weight:800; color:var(--text); margin:20px 0 14px; display:flex; align-items:center; gap:8px; }

/* Score ring */
.score-ring{ display:flex; flex-direction:column; align-items:center; padding:24px; background:var(--bg3); border-radius:var(--r); border:1px solid var(--border); margin-bottom:16px; }
.score-num { font-size:72px; font-weight:900; line-height:1; font-family:'Space Grotesk',sans-serif; }
.score-lbl { font-size:16px; font-weight:700; margin-top:8px; }
.score-sub { font-size:12px; color:var(--muted); margin-top:4px; }
.score-dots{ display:flex; gap:6px; margin-top:12px; justify-content:center; }
.sdot { width:10px; height:10px; border-radius:50%; }

/* Nutrient bars */
.nb { margin-bottom:12px; }
.nb-row { display:flex; justify-content:space-between; margin-bottom:6px; }
.nb-name{ color:var(--text); font-size:14px; font-weight:600; }
.nb-val { color:var(--muted); font-size:13px; }
.nb-track{ height:8px; background:rgba(255,255,255,.08); border-radius:4px; overflow:hidden; }
.nb-fill { height:100%; border-radius:4px; transition:width .5s; }

/* Additive badges */
.abadge { display:inline-flex; align-items:center; gap:8px; padding:8px 14px; border-radius:100px; font-size:13px; font-weight:700; margin:4px; border:1px solid transparent; }
.abadge.high       { background:rgba(255,59,48,.15);  color:#FF6B6B; border-color:rgba(255,59,48,.3); }
.abadge.medium-high{ background:rgba(255,107,53,.15); color:#FF8C42; border-color:rgba(255,107,53,.3); }
.abadge.medium     { background:rgba(255,159,28,.15); color:#FFBE0B; border-color:rgba(255,159,28,.3); }
.abadge.low-medium,.abadge.low{ background:rgba(76,175,80,.15); color:#69F0AE; border-color:rgba(76,175,80,.3); }

/* OCR result highlight */
.ocr-box { background:var(--bg3); border:1px solid var(--border); border-radius:14px; padding:16px; font-family:monospace; font-size:13px; color:var(--text); white-space:pre-wrap; max-height:300px; overflow-y:auto; line-height:1.7; }
.ocr-hit  { background:rgba(255,59,48,.25); color:#FF6B6B; border-radius:3px; padding:1px 3px; font-weight:700; }
.ocr-ok   { background:rgba(0,184,148,.2);  color:#00D4AA; border-radius:3px; padding:1px 3px; }

/* Risk cards */
.rcard { background:var(--bg3); border-radius:14px; padding:16px; margin-bottom:10px; border-left:4px solid; }
.rcard.high{ border-color:#FF3B30; } .rcard.medium{ border-color:#FF9500; } .rcard.low{ border-color:#34C759; }
.rcard-hdr{ display:flex; align-items:center; gap:10px; margin-bottom:8px; }
.rcard-title{ font-size:15px; font-weight:700; color:var(--text); }
.rlvl { font-size:12px; font-weight:600; padding:3px 10px; border-radius:100px; }
.rlvl.high  { background:rgba(255,59,48,.2);  color:#FF6B6B; }
.rlvl.medium{ background:rgba(255,149,0,.2);  color:#FFB340; }
.rlvl.low   { background:rgba(52,199,89,.2);  color:#34C759; }
.rcard-txt  { font-size:13px; color:var(--muted); line-height:1.5; }

/* Alternatives */
.alt-chip { display:inline-flex; align-items:center; gap:6px; background:rgba(0,184,148,.12); color:#00D4AA; border:1px solid rgba(0,184,148,.25); border-radius:100px; padding:8px 16px; font-size:14px; font-weight:600; margin:4px; }

/* History card */
.hcard { background:var(--bg2); border:1px solid var(--border); border-radius:14px; padding:14px 16px; margin-bottom:10px; display:flex; align-items:center; gap:14px; }
.hcard-emoji{ font-size:32px; min-width:40px; text-align:center; }
.hcard-info { flex:1; }
.hcard-name { color:var(--text); font-size:14px; font-weight:700; margin-bottom:4px; }
.hcard-meta { color:var(--muted); font-size:12px; }
.hcard-score{ font-size:22px; font-weight:900; font-family:'Space Grotesk',sans-serif; min-width:36px; text-align:center; }

/* Info box */
.info-box { background:rgba(0,184,148,.08); border:1px solid rgba(0,184,148,.2); border-radius:14px; padding:16px; margin:12px 0; font-size:14px; color:var(--text); line-height:1.6; }

/* Buttons */
.stButton>button { background:linear-gradient(135deg,#00B894,#00CEC9) !important; color:white !important; border:none !important; border-radius:100px !important; font-weight:700 !important; font-size:15px !important; padding:14px 28px !important; width:100% !important; box-shadow:0 4px 16px rgba(0,184,148,.3) !important; font-family:'Nunito',sans-serif !important; }
.stButton>button:hover{ transform:translateY(-1px) !important; box-shadow:0 8px 24px rgba(0,184,148,.5) !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"]{ background:var(--bg2) !important; border-radius:100px !important; padding:4px !important; border:1px solid var(--border) !important; }
.stTabs [data-baseweb="tab"]{ color:var(--muted) !important; border-radius:100px !important; font-weight:700 !important; font-size:13px !important; }
.stTabs [aria-selected="true"]{ background:linear-gradient(135deg,#00B894,#00CEC9) !important; color:white !important; }

/* Misc */
h1,h2,h3,h4{ color:var(--text) !important; font-family:'Nunito',sans-serif !important; }
p,label,.stMarkdown{ color:var(--muted) !important; }
hr{ border:none !important; border-top:1px solid var(--border) !important; margin:20px 0 !important; }
.stMetric{ background:var(--bg2) !important; border-radius:14px !important; padding:16px !important; border:1px solid var(--border) !important; }
.stMetric label{ color:var(--muted) !important; font-size:12px !important; font-weight:700 !important; text-transform:uppercase !important; }
.stMetric [data-testid="stMetricValue"]{ color:var(--text) !important; font-weight:800 !important; }

@media(max-width:768px){
  .app-header h1{font-size:22px !important;} .score-num{font-size:56px;} .block-container{padding:12px !important;}
}
@keyframes fadeInUp{ from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
.animate-in{ animation:fadeInUp .4s ease forwards; }
</style>
"""


def render_header():
    st.markdown('<div class="app-header"><h1>🔍 FoodScan AI</h1><p>Анализирай хранителни продукти за секунди</p></div>', unsafe_allow_html=True)

def render_section_title(icon, title):
    st.markdown(f'<div class="section-title"><span>{icon}</span><span>{title}</span></div>', unsafe_allow_html=True)

def render_health_score(score, label, color, emoji):
    dots = "".join(
        f'<div class="sdot" style="background:{"" if i>score else color};background-color:{color if i<=score else "rgba(255,255,255,0.08)"}"></div>'
        for i in range(1,11)
    )
    st.markdown(f'''
    <div class="score-ring animate-in">
      <div class="score-num" style="color:{color}">{score}</div>
      <div class="score-lbl" style="color:{color}">{emoji} {label}</div>
      <div class="score-sub">Скала на вредност: 1 (здравословно) — 10 (много вредно)</div>
      <div class="score-dots">{dots}</div>
    </div>''', unsafe_allow_html=True)

def render_nutrition_bar(label, value, unit, pct, color):
    st.markdown(f'''
    <div class="nb">
      <div class="nb-row"><span class="nb-name">{label}</span><span class="nb-val">{value}{unit} ({pct}% ДД)</span></div>
      <div class="nb-track"><div class="nb-fill" style="width:{min(100,pct)}%;background:{color}"></div></div>
    </div>''', unsafe_allow_html=True)

def render_risk_card(name, emoji, level, text):
    lvl_label = {"high":"⛔ Висок риск","medium":"⚠️ Среден риск","low":"✅ Нисък риск"}.get(level, level)
    st.markdown(f'''
    <div class="rcard {level}">
      <div class="rcard-hdr"><span style="font-size:22px">{emoji}</span>
        <span class="rcard-title">{name}</span>
        <span class="rlvl {level}">{lvl_label}</span></div>
      <div class="rcard-txt">{text}</div>
    </div>''', unsafe_allow_html=True)

def render_history_card(entry):
    from datetime import datetime
    try:    ts = datetime.fromisoformat(entry["timestamp"]).strftime("%d.%m %H:%M")
    except: ts = "—"
    st.markdown(f'''
    <div class="hcard">
      <div class="hcard-emoji">{entry.get("emoji","🍽️")}</div>
      <div class="hcard-info">
        <div class="hcard-name">{entry["product_name"]}</div>
        <div class="hcard-meta">{entry.get("brand","")} • {ts} • {entry.get("additives_count",0)} добавки</div>
      </div>
      <div class="hcard-score" style="color:{entry["health_color"]}">{entry["health_score"]}</div>
    </div>''', unsafe_allow_html=True)

def render_alternatives(alternatives):
    chips = " ".join(f'<span class="alt-chip">🌿 {a}</span>' for a in alternatives)
    st.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:4px">{chips}</div>', unsafe_allow_html=True)

def render_product_header(name, brand, category, emoji):
    st.markdown(f'''
    <div class="food-card animate-in">
      <div style="display:flex;align-items:center;gap:14px;border-bottom:1px solid rgba(255,255,255,.08);padding-bottom:14px;margin-bottom:4px">
        <div style="font-size:48px;min-width:60px;text-align:center">{emoji}</div>
        <div>
          <h2 style="margin:0 0 4px;font-size:20px;font-weight:800">{name}</h2>
          <div style="color:#8896B0;font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:1px">🏷️ {brand} • {category}</div>
        </div>
      </div>
    </div>''', unsafe_allow_html=True)

def render_ocr_result_with_highlights(raw_text: str, found_additives: list) -> str:
    """
    Рендира OCR текст с маркирани E-числа.
    Червено (ocr-hit) = вредна добавка в базата.
    Жълто (ocr-ok)    = E-число, но не в базата / нисък риск.
    """
    import re, html as html_mod

    known_codes = {a["code"].upper() for a in found_additives}

    def replacer(m):
        raw  = m.group(0)
        # Нормализираме за сравнение: E160a → E160A
        norm = re.sub(r'[-\s]', '', raw.upper())
        if norm in known_codes:
            return f'<span class="ocr-hit" title="Вредна добавка!">{html_mod.escape(raw)}</span>'
        return f'<span class="ocr-ok">{html_mod.escape(raw)}</span>'

    # Намираме всички E-числа (с letter suffix)
    pattern = r'[Ee][-\s]?\d{3}[a-zA-Z]?'

    # Разделяме текста на E-числа и останалото
    parts = re.split(f'({pattern})', raw_text)
    result = ""
    for part in parts:
        if re.fullmatch(pattern, part):
            result += replacer(re.match(pattern, part))
        else:
            result += html_mod.escape(part)
    return result

def get_nutriscore_color(grade):
    return {"A":"#038141","B":"#85BB2F","C":"#FECB02","D":"#EE8100","E":"#E63E11"}.get(grade,"#888")
