import sys, os, io, json, base64, requests, re
import streamlit as st
from PIL import Image
import numpy as np

# ════════════════════════════════════════════════════════════════════════
# 1. PAGE CONFIG (Must be first Streamlit command)
# ════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="FoodScan AI", page_icon="🔍", layout="centered", initial_sidebar_state="collapsed")

# ════════════════════════════════════════════════════════════════════════
# 2. DATA & DATABASES
# ════════════════════════════════════════════════════════════════════════
MOBILE_CSS = """
<style>
    .info-box { background: rgba(0, 184, 148, 0.1); border-left: 4px solid #00b894; padding: 12px; border-radius: 4px; margin-bottom: 16px; }
    .food-card { background: rgba(255, 255, 255, 0.05); padding: 16px; border-radius: 8px; margin-bottom: 16px; }
    .ocr-box { background: #1e1e1e; padding: 12px; border-radius: 8px; font-family: monospace; color: #d4d4d4; }
    .abadge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; margin-bottom: 4px; }
    .abadge.high { background: #FF3B30; color: white; }
    .abadge.medium { background: #FF9500; color: white; }
    .abadge.low { background: #34C759; color: white; }
</style>
"""

HARMFUL_ADDITIVES = {
    "E621": {"code": "E621", "name": "Мононатриев глутамат", "category": "Овкусител", "risk_level": "high", "risk_score": 8, "description": "Подобрител на вкуса.", "health_risks": ["Главоболие", "Затлъстяване"], "banned_in": ["Някои детски храни"], "alternatives": "Естествени подправки", "found_in": ["Чипс", "Снаксове", "Бульони"]},
    "E951": {"code": "E951", "name": "Аспартам", "category": "Подсладител", "risk_level": "medium-high", "risk_score": 7, "description": "Изкуствен подсладител.", "health_risks": ["Неврологични проблеми"], "banned_in": [], "alternatives": "Стевия", "found_in": ["Диетични напитки", "Дъвки"]},
    "E330": {"code": "E330", "name": "Лимонена киселина", "category": "Консервант/Регулатор", "risk_level": "low", "risk_score": 1, "description": "Естествена или синтетична киселина.", "health_risks": ["Ерозия на зъбите (в големи количества)"], "banned_in": [], "alternatives": "Пресен лимонов сок", "found_in": ["Напитки", "Сладкиши"]}
}

RISK_COLORS = {"high": "#FF3B30", "medium-high": "#FF3B30", "medium": "#FF9500", "low-medium": "#34C759", "low": "#34C759"}
RISK_LABELS = {"high": "⛔ Висок риск", "medium-high": "🔴 Повишен риск", "medium": "🟡 Умерен риск", "low-medium": "🟢 Нисък риск", "low": "✅ Безопасен"}
HEALTH_RISK_INFO = {
    "obesity": {"name": "Затлъстяване", "emoji": "⚖️", "high": "Високи калории и захари", "medium": "Умерени нива на мазнини", "low": "Нисък риск"},
    "diabetes": {"name": "Диабет", "emoji": "🩸", "high": "Много добавена захар", "medium": "Средно съдържание на въглехидрати", "low": "Безопасно"},
    "heart": {"name": "Сърце", "emoji": "❤️", "high": "Високи наситени мазнини", "medium": "Умерени мазнини", "low": "Полезно за сърцето"},
    "blood_pressure": {"name": "Кръвно налягане", "emoji": "💓", "high": "Високо съдържание на сол", "medium": "Умерено количество сол", "low": "Ниско съдържание на сол"}
}

DEMO_BARCODES = {"5449000000996": "Coca-Cola Original", "8000500167104": "Kinder Bueno"}
MOCK_PRODUCTS = {}

# ════════════════════════════════════════════════════════════════════════
# 3. HELPER & UI FUNCTIONS
# ════════════════════════════════════════════════════════════════════════
def render_header(): st.markdown("<h1 style='text-align: center; color: #00b894;'>🔍 FoodScan AI</h1>", unsafe_allow_html=True)
def render_section_title(icon, title): st.markdown(f"### {icon} {title}")
def get_nutriscore_color(score): return {"A": "#038141", "B": "#85BB2F", "C": "#FECB02", "D": "#EE8100", "E": "#E63E11"}.get(score.upper(), "#888")
def render_health_score(score, label, color, emoji): st.markdown(f"<div class='food-card' style='text-align:center; border-top: 4px solid {color};'><h2 style='color:{color}; margin:0;'>{score}/10 {emoji}</h2><p style='margin:0; font-weight:bold;'>{label}</p></div>", unsafe_allow_html=True)
def render_risk_card(name, emoji, lvl, desc):
    color = RISK_COLORS.get(lvl, "#888")
    st.markdown(f"<div style='padding: 10px; border-left: 4px solid {color}; background: rgba(255,255,255,0.05); margin-bottom:8px;'><strong>{emoji} {name}</strong>: {desc}</div>", unsafe_allow_html=True)
def render_nutrition_bar(nut, val, unit, pct, col): st.progress(min(pct/100, 1.0), text=f"{nut}: {val}{unit}")
def render_product_header(name, brand, cat, emoji): st.markdown(f"<h2>{emoji} {name}</h2><p style='color:#888;'>{brand} | {cat}</p>", unsafe_allow_html=True)
def render_history_card(e): st.markdown(f"**{e['product']['name']}** - Оценка: {e['analysis']['health_score']['score']}/10")
def render_alternatives(alts):
    for a in alts: st.markdown(f"- 🌿 {a}")
def render_ocr_result_with_highlights(text, found_additives):
    for a in found_additives:
        color = "#FF3B30" if a["risk_level"] in ["high", "medium-high"] else "#34C759"
        text = text.replace(a["code"], f"<span style='background-color:{color}; padding:2px; border-radius:3px; color:white;'>{a['code']}</span>")
    return text

# ════════════════════════════════════════════════════════════════════════
# 4. SCANNER & OCR MODULES
# ════════════════════════════════════════════════════════════════════════
def get_ocr_status():
    try: import easyocr; return {"easyocr": True, "any_available": True}
    except: return {"easyocr": False, "any_available": True} # Claude fallback

def get_barcode_info():
    try: import pyzbar; return {"pyzbar": True, "opencv": True}
    except: return {"pyzbar": False, "opencv": False}

@st.cache_resource
def get_ocr_reader():
    try:
        import easyocr
        return easyocr.Reader(['bg', 'en']), "easyocr"
    except ImportError:
        return None, None

def scan_barcode(image):
    try:
        from pyzbar.pyzbar import decode
        decoded = decode(image)
        if decoded:
            return {"found": True, "barcode": decoded[0].data.decode('utf-8'), "barcode_type": decoded[0].type}
    except ImportError: pass
    return {"found": False}

def extract_text_easyocr(image, reader):
    if reader is None: return {"success": False, "error": "EasyOCR не е инсталиран."}
    res = reader.readtext(np.array(image), detail=0)
    return {"success": True, "raw_text": " ".join(res), "confidence": 0.85, "engine": "easyocr"}

def extract_text_claude_vision(image):
    return {"success": False, "error": "Claude Vision изисква API ключ. Моля инсталирайте EasyOCR."}

def fetch_openfoodfacts(barcode):
    try:
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        res = requests.get(url, timeout=5).json()
        if res.get("status") == 1:
            p = res["product"]
            return {
                "name": p.get("product_name", "Неизвестен продукт"),
                "brand": p.get("brands", "Неизвестна марка"),
                "category": p.get("categories", "Храна").split(",")[0],
                "ingredients": p.get("ingredients_text", ""),
                "nutrition": {
                    "calories": p.get("nutriments", {}).get("energy-kcal_100g", 0),
                    "fat": p.get("nutriments", {}).get("fat_100g", 0),
                    "sugars": p.get("nutriments", {}).get("sugars_100g", 0),
                    "salt": p.get("nutriments", {}).get("salt_100g", 0)
                },
                "nutriscore": p.get("nutriscore_grade", "u"),
                "health_risks": {"obesity": "low", "diabetes": "low", "heart": "low", "blood_pressure": "low"},
                "alternatives": ["Пресни плодове", "Домашно приготвена храна"]
            }
    except: pass
    return None

def get_product_by_barcode(bc): return MOCK_PRODUCTS.get(bc)
def get_demo_products(): return [{"name": "Coca-Cola", "brand": "Кока-Кола", "emoji": "🥤", "barcode": "5449000000996"}]

# ════════════════════════════════════════════════════════════════════════
# 5. ANALYSIS & HISTORY
# ════════════════════════════════════════════════════════════════════════
def find_additives_in_text(text):
    found = []
    for code, data in HARMFUL_ADDITIVES.items():
        if code in text or data["name"].lower() in text.lower():
            found.append(data)
    return found

def get_overall_risk_score(found_additives):
    if not found_additives: return {"label": "Безопасно", "color": "#34C759"}
    max_risk = max([a["risk_score"] for a in found_additives])
    if max_risk >= 7: return {"label": "Висок риск", "color": "#FF3B30"}
    if max_risk >= 4: return {"label": "Умерен риск", "color": "#FF9500"}
    return {"label": "Нисък риск", "color": "#34C759"}

def parse_food_label(text):
    return {"ingredients": text, "product_name": "Продукт от OCR"}

def analyze_product(product_data, ingredients_text):
    found = find_additives_in_text(ingredients_text)
    risk = get_overall_risk_score(found)
    
    score = max(1, 10 - len(found) * 2)
    color = "#34C759" if score >= 7 else "#FF9500" if score >= 4 else "#FF3B30"
    
    na = []
    nut = product_data.get("nutrition", {})
    if "calories" in nut: na.append({"nutrient": "Калории", "value": nut["calories"], "unit": "kcal", "percentage_daily": min(100, nut["calories"]/20), "color": "blue"})
    
    return {
        "product": product_data,
        "health_score": {"score": score, "label": "Добра" if score>=7 else "Средна" if score>=4 else "Лоша", "color": color, "emoji": "🌟", "breakdown": []},
        "additives": {"count": len(found), "found": found, "risk": risk},
        "nutrition_analysis": na
    }

def initialize_history(state): state.setdefault("history", [])
def add_to_history(state, p, a): state["history"].insert(0, {"product": p, "analysis": a})
def get_history(state): return state.get("history", [])
def clear_history(state): state["history"] = []
def get_history_stats(state):
    h = state.get("history", [])
    if not h: return {}
    scores = [item["analysis"]["health_score"]["score"] for item in h]
    return {"total_scanned": len(h), "avg_health_score": round(sum(scores)/len(scores), 1), "high_risk_count": sum(1 for s in scores if s < 5)}
def export_history_json(state): return json.dumps(state.get("history", []), ensure_ascii=False, indent=2)

# ════════════════════════════════════════════════════════════════════════
# 6. MAIN APPLICATION STATE & RUNNER
# ════════════════════════════════════════════════════════════════════════
st.markdown(MOBILE_CSS, unsafe_allow_html=True)
initialize_history(st.session_state)

for key, val in [("current_analysis", None), ("ocr_reader", None), ("ocr_engine", None), ("ai_analysis", None), ("manual_barcode", "")]:
    if key not in st.session_state: st.session_state[key] = val

def load_reader():
    if st.session_state.ocr_reader is None:
        r, e = get_ocr_reader()
        st.session_state.ocr_reader = r
        st.session_state.ocr_engine = e
    return st.session_state.ocr_reader, st.session_state.ocr_engine

def run_analysis(product_data, source="db"):
    product_data["source"] = source
    analysis = analyze_product(product_data, product_data.get("ingredients",""))
    st.session_state.current_analysis = analysis
    st.session_state.ai_analysis = None
    add_to_history(st.session_state, product_data, analysis)
    return analysis

def build_product_from_ocr(ocr_result, image_note="📷"):
    parsed = parse_food_label(ocr_result["raw_text"])
    return {
        "name": parsed.get("product_name") or "Продукт от снимка",
        "category": "OCR Сканиране",
        "image_emoji": image_note,
        "ingredients": parsed.get("ingredients") or ocr_result["raw_text"],
        "nutrition": {},
        "health_risks": {"obesity":"medium","diabetes":"medium","heart":"medium","blood_pressure":"medium"},
        "alternatives": ["Прясна храна", "Домашно приготвена храна"],
    }

def show_ocr_panel(ocr_result):
    if not ocr_result.get("success") or not ocr_result.get("raw_text","").strip(): return
    found = find_additives_in_text(ocr_result["raw_text"])
    highlighted = render_ocr_result_with_highlights(ocr_result["raw_text"], found)
    with st.expander(f"📄 Разпознат текст ({ocr_result.get('confidence',0):.0%} точност)", expanded=True):
        st.markdown(f'<div class="ocr-box">{highlighted}</div>', unsafe_allow_html=True)
        if found: st.markdown(f"🔴 Маркирани **{len(found)}** вредни добавки: " + ", ".join(f"`{a['code']}`" for a in found))
        else: st.markdown("✅ Не са намерени вредни E-числа в текста.")

def get_ai_analysis(product_data):
    return "💡 AI Анализът е симулиран, тъй като изисква валиден API ключ към Claude."

# ════════════════════════════════════════════════════════════════════════
# 7. UI LAYOUT
# ════════════════════════════════════════════════════════════════════════
render_header()

with st.sidebar:
    st.markdown("### ⚙️ Системен статус")
    ocr_st = get_ocr_status()
    bc_info = get_barcode_info()
    st.markdown(f"**EasyOCR:** {'✅' if ocr_st['easyocr'] else '❌'}")
    st.markdown(f"**pyzbar:** {'✅' if bc_info['pyzbar'] else '❌'}")

tab_scan, tab_results, tab_history, tab_edata = st.tabs(["📷 Сканиране", "📊 Резултати", "📋 История", "🧪 Е-та"])

with tab_scan:
    method = st.radio("Метод", ["📦 Демо продукт", "🖼️ Качи снимка", "📷 Камера", "🔢 Въведи баркод"], label_visibility="collapsed")
    st.markdown("---")

    if method == "📦 Демо продукт":
        opts = {f"{p['emoji']} {p['name']}": p["barcode"] for p in get_demo_products()}
        sel = st.selectbox("Избери продукт:", list(opts.keys()))
        if st.button("🔍 Анализирай"):
            bc = opts[sel]
            p = fetch_openfoodfacts(bc)
            if p:
                p["barcode"] = bc
                run_analysis(p, "demo")
                st.success(f"✅ {p['name']} анализиран! Виж таб **Резултати**")

    elif method == "🖼️ Качи снимка":
        uploaded = st.file_uploader("Качи снимка", type=["jpg","jpeg","png","webp"])
        if uploaded:
            image = Image.open(uploaded)
            st.image(image, caption="Качена снимка", width=300)
            with st.spinner("🔍 Търсим баркод..."): bc_res = scan_barcode(image)
            if bc_res["found"]:
                st.success
