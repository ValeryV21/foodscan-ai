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
    "E330": {"code": "E330", "name": "Лимонена киселина", "category": "Консервант/Регулатор", "risk_level": "low", "risk_score": 1, "description": "Естествена или синтетична киселина.", "health_risks": ["Ерозия на зъбите (в големи количества)"], "banned_in": [], "alternatives": "Пресен лимонов сок", "found_in": ["Напитки", "Сладкиши"]},
    "E102": {"code": "E102", "name": "Тартразин", "category": "Оцветител", "risk_level": "high", "risk_score": 8, "description": "Синтетичен жълт оцветител.", "health_risks": ["Алергии", "Хиперактивност при деца"], "banned_in": ["Норвегия", "Австрия"], "alternatives": "Естествени оцветители", "found_in": ["Безалкохолни напитки", "Сладки"]},
    "E250": {"code": "E250", "name": "Натриев нитрит", "category": "Консервант", "risk_level": "high", "risk_score": 9, "description": "Консервант в месни продукти.", "health_risks": ["Канцерогенен риск", "Сърдечно-съдови проблеми"], "banned_in": [], "alternatives": "Натурална консервация", "found_in": ["Колбаси", "Бекон", "Наденици"]},
    "E211": {"code": "E211", "name": "Натриев бензоат", "category": "Консервант", "risk_level": "medium", "risk_score": 5, "description": "Консервант в напитки и сосове.", "health_risks": ["Алергии", "Хиперактивност"], "banned_in": [], "alternatives": "Витамин C", "found_in": ["Газирани напитки", "Сосове", "Маринати"]},
    "E320": {"code": "E320", "name": "Бутилхидроксианизол (BHA)", "category": "Антиоксидант", "risk_level": "medium-high", "risk_score": 7, "description": "Синтетичен антиоксидант.", "health_risks": ["Потенциален канцероген"], "banned_in": ["Япония"], "alternatives": "Витамин E", "found_in": ["Чипс", "Бисквити", "Маргарин"]},
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
def render_header():
    st.markdown("<h1 style='text-align: center; color: #00b894;'>🔍 FoodScan AI</h1>", unsafe_allow_html=True)

def render_section_title(icon, title):
    st.markdown(f"### {icon} {title}")

def get_nutriscore_color(score):
    return {"A": "#038141", "B": "#85BB2F", "C": "#FECB02", "D": "#EE8100", "E": "#E63E11"}.get(score.upper(), "#888")

def render_health_score(score, label, color, emoji):
    st.markdown(
        f"<div class='food-card' style='text-align:center; border-top: 4px solid {color};'>"
        f"<h2 style='color:{color}; margin:0;'>{score}/10 {emoji}</h2>"
        f"<p style='margin:0; font-weight:bold;'>{label}</p></div>",
        unsafe_allow_html=True
    )

def render_risk_card(name, emoji, lvl, desc):
    color = RISK_COLORS.get(lvl, "#888")
    st.markdown(
        f"<div style='padding: 10px; border-left: 4px solid {color}; background: rgba(255,255,255,0.05); margin-bottom:8px;'>"
        f"<strong>{emoji} {name}</strong>: {desc}</div>",
        unsafe_allow_html=True
    )

def render_nutrition_bar(nut, val, unit, pct, col):
    st.progress(min(pct / 100, 1.0), text=f"{nut}: {val}{unit}")

def render_product_header(name, brand, cat, emoji):
    st.markdown(f"<h2>{emoji} {name}</h2><p style='color:#888;'>{brand} | {cat}</p>", unsafe_allow_html=True)

def render_history_card(e):
    st.markdown(f"**{e['product']['name']}** - Оценка: {e['analysis']['health_score']['score']}/10")

def render_alternatives(alts):
    for a in alts:
        st.markdown(f"- 🌿 {a}")

def render_ocr_result_with_highlights(text, found_additives):
    for a in found_additives:
        color = "#FF3B30" if a["risk_level"] in ["high", "medium-high"] else "#34C759"
        text = text.replace(
            a["code"],
            f"<span style='background-color:{color}; padding:2px; border-radius:3px; color:white;'>{a['code']}</span>"
        )
    return text

# ════════════════════════════════════════════════════════════════════════
# 4. SCANNER & OCR MODULES
# ════════════════════════════════════════════════════════════════════════
def get_ocr_status():
    try:
        import easyocr
        return {"easyocr": True, "any_available": True}
    except ImportError:
        return {"easyocr": False, "any_available": True}  # Claude fallback

def get_barcode_info():
    try:
        import pyzbar
        return {"pyzbar": True, "opencv": True}
    except ImportError:
        return {"pyzbar": False, "opencv": False}

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
    except ImportError:
        pass
    return {"found": False}

def extract_text_easyocr(image, reader):
    if reader is None:
        return {"success": False, "error": "EasyOCR не е инсталиран."}
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
    except Exception:
        pass
    return None

def get_product_by_barcode(bc):
    return MOCK_PRODUCTS.get(bc)

def get_demo_products():
    return [
        {"name": "Coca-Cola", "brand": "Кока-Кола", "emoji": "🥤", "barcode": "5449000000996"},
        {"name": "Kinder Bueno", "brand": "Ferrero", "emoji": "🍫", "barcode": "8000500167104"},
    ]

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
    if not found_additives:
        return {"label": "Безопасно", "color": "#34C759"}
    max_risk = max([a["risk_score"] for a in found_additives])
    if max_risk >= 7:
        return {"label": "Висок риск", "color": "#FF3B30"}
    if max_risk >= 4:
        return {"label": "Умерен риск", "color": "#FF9500"}
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
    if nut.get("calories"):
        na.append({"nutrient": "Калории", "value": nut["calories"], "unit": "kcal", "percentage_daily": min(100, nut["calories"] / 20), "color": "blue"})
    if nut.get("fat"):
        na.append({"nutrient": "Мазнини", "value": nut["fat"], "unit": "g", "percentage_daily": min(100, nut["fat"] / 0.7), "color": "orange"})
    if nut.get("sugars"):
        na.append({"nutrient": "Захари", "value": nut["sugars"], "unit": "g", "percentage_daily": min(100, nut["sugars"] / 0.5), "color": "red"})
    if nut.get("salt"):
        na.append({"nutrient": "Сол", "value": nut["salt"], "unit": "g", "percentage_daily": min(100, nut["salt"] / 0.06), "color": "purple"})

    return {
        "product": product_data,
        "health_score": {
            "score": score,
            "label": "Добра" if score >= 7 else "Средна" if score >= 4 else "Лоша",
            "color": color,
            "emoji": "🌟",
            "breakdown": []
        },
        "additives": {"count": len(found), "found": found, "risk": risk},
        "nutrition_analysis": na
    }

def initialize_history(state):
    state.setdefault("history", [])

def add_to_history(state, p, a):
    state["history"].insert(0, {"product": p, "analysis": a})

def get_history(state):
    return state.get("history", [])

def clear_history(state):
    state["history"] = []

def get_history_stats(state):
    h = state.get("history", [])
    if not h:
        return {}
    scores = [item["analysis"]["health_score"]["score"] for item in h]
    return {
        "total_scanned": len(h),
        "avg_health_score": round(sum(scores) / len(scores), 1),
        "high_risk_count": sum(1 for s in scores if s < 5)
    }

def export_history_json(state):
    return json.dumps(state.get("history", []), ensure_ascii=False, indent=2)

# ════════════════════════════════════════════════════════════════════════
# 6. MAIN APPLICATION STATE & RUNNER
# ════════════════════════════════════════════════════════════════════════
st.markdown(MOBILE_CSS, unsafe_allow_html=True)
initialize_history(st.session_state)

for key, val in [
    ("current_analysis", None),
    ("ocr_reader", None),
    ("ocr_engine", None),
    ("ai_analysis", None),
    ("manual_barcode", ""),
]:
    if key not in st.session_state:
        st.session_state[key] = val

def load_reader():
    if st.session_state.ocr_reader is None:
        r, e = get_ocr_reader()
        st.session_state.ocr_reader = r
        st.session_state.ocr_engine = e
    return st.session_state.ocr_reader, st.session_state.ocr_engine

def run_analysis(product_data, source="db"):
    product_data["source"] = source
    analysis = analyze_product(product_data, product_data.get("ingredients", ""))
    st.session_state.current_analysis = analysis
    st.session_state.ai_analysis = None
    add_to_history(st.session_state, product_data, analysis)
    return analysis

def build_product_from_ocr(ocr_result, image_note="📷"):
    parsed = parse_food_label(ocr_result["raw_text"])
    return {
        "name": parsed.get("product_name") or "Продукт от снимка",
        "brand": "OCR Сканиране",
        "category": "OCR Сканиране",
        "image_emoji": image_note,
        "ingredients": parsed.get("ingredients") or ocr_result["raw_text"],
        "nutrition": {},
        "health_risks": {"obesity": "medium", "diabetes": "medium", "heart": "medium", "blood_pressure": "medium"},
        "alternatives": ["Прясна храна", "Домашно приготвена храна"],
    }

def show_ocr_panel(ocr_result):
    if not ocr_result.get("success") or not ocr_result.get("raw_text", "").strip():
        return
    found = find_additives_in_text(ocr_result["raw_text"])
    highlighted = render_ocr_result_with_highlights(ocr_result["raw_text"], found)
    with st.expander(f"📄 Разпознат текст ({ocr_result.get('confidence', 0):.0%} точност)", expanded=True):
        st.markdown(f'<div class="ocr-box">{highlighted}</div>', unsafe_allow_html=True)
        if found:
            st.markdown(f"🔴 Маркирани **{len(found)}** вредни добавки: " + ", ".join(f"`{a['code']}`" for a in found))
        else:
            st.markdown("✅ Не са намерени вредни E-числа в текста.")

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
    st.markdown("---")
    st.markdown("### 📖 Как да използвам?")
    st.markdown(
        "1. Избери метод за сканиране\n"
        "2. Качи снимка или въведи баркод\n"
        "3. Виж резултатите в таб **Резултати**\n"
        "4. Провери историята в таб **История**"
    )

tab_scan, tab_results, tab_history, tab_edata = st.tabs(["📷 Сканиране", "📊 Резултати", "📋 История", "🧪 Е-та"])

# ─── TAB: СКАНИРАНЕ ───────────────────────────────────────────────────
with tab_scan:
    method = st.radio(
        "Метод",
        ["📦 Демо продукт", "🖼️ Качи снимка", "📷 Камера", "🔢 Въведи баркод"],
        label_visibility="collapsed"
    )
    st.markdown("---")

    # ── Демо продукт ──
    if method == "📦 Демо продукт":
        opts = {f"{p['emoji']} {p['name']}": p["barcode"] for p in get_demo_products()}
        sel = st.selectbox("Избери продукт:", list(opts.keys()))
        if st.button("🔍 Анализирай", key="demo_btn"):
            bc = opts[sel]
            with st.spinner("Зареждаме данни..."):
                p = fetch_openfoodfacts(bc)
            if p:
                p["barcode"] = bc
                run_analysis(p, "demo")
                st.success(f"✅ {p['name']} анализиран! Виж таб **Резултати**")
            else:
                st.error("❌ Не можахме да намерим продукта. Опитай друг.")

    # ── Качи снимка ──
    elif method == "🖼️ Качи снимка":
        uploaded = st.file_uploader("Качи снимка на етикета", type=["jpg", "jpeg", "png", "webp"])
        if uploaded:
            image = Image.open(uploaded)
            st.image(image, caption="Качена снимка", width=300)

            with st.spinner("🔍 Търсим баркод..."):
                bc_res = scan_barcode(image)

            if bc_res["found"]:
                st.success(f"✅ Намерен баркод: `{bc_res['barcode']}`")
                with st.spinner("Зареждаме данни от OpenFoodFacts..."):
                    p = fetch_openfoodfacts(bc_res["barcode"])
                if p:
                    p["barcode"] = bc_res["barcode"]
                    run_analysis(p, "barcode_scan")
                    st.success("✅ Продуктът е анализиран! Виж таб **Резултати**")
                else:
                    st.warning("⚠️ Баркодът е намерен, но продуктът не е в базата данни.")
            else:
                st.info("📄 Баркод не е намерен. Опитваме OCR разпознаване на текст...")
                reader, engine = load_reader()
                if engine == "easyocr":
                    with st.spinner("🔤 Разпознаваме текст с EasyOCR..."):
                        ocr_result = extract_text_easyocr(image, reader)
                else:
                    ocr_result = extract_text_claude_vision(image)

                if ocr_result.get("success"):
                    show_ocr_panel(ocr_result)
                    product_data = build_product_from_ocr(ocr_result)
                    run_analysis(product_data, "ocr")
                    st.success("✅ Анализът е готов! Виж таб **Резултати**")
                else:
                    st.error(f"❌ OCR грешка: {ocr_result.get('error', 'Неизвестна грешка')}")
                    st.info("💡 Инсталирай EasyOCR: `pip install easyocr`")

    # ── Камера ──
    elif method == "📷 Камера":
        st.info("📷 Използвай камерата за снимка на етикета")
        camera_img = st.camera_input("Снимай етикета")
        if camera_img:
            image = Image.open(camera_img)

            with st.spinner("🔍 Обработваме снимката..."):
                bc_res = scan_barcode(image)

            if bc_res["found"]:
                st.success(f"✅ Намерен баркод: `{bc_res['barcode']}`")
                with st.spinner("Зареждаме данни..."):
                    p = fetch_openfoodfacts(bc_res["barcode"])
                if p:
                    p["barcode"] = bc_res["barcode"]
                    run_analysis(p, "camera_scan")
                    st.success("✅ Продуктът е анализиран! Виж таб **Резултати**")
                else:
                    st.warning("⚠️ Продуктът не е намерен в базата данни.")
            else:
                reader, engine = load_reader()
                if engine == "easyocr":
                    with st.spinner("🔤 OCR разпознаване..."):
                        ocr_result = extract_text_easyocr(image, reader)
                    if ocr_result.get("success"):
                        show_ocr_panel(ocr_result)
                        product_data = build_product_from_ocr(ocr_result, "📷")
                        run_analysis(product_data, "ocr_camera")
                        st.success("✅ Анализът е готов! Виж таб **Резултати**")
                    else:
                        st.error("❌ Не можахме да разпознаем текст от снимката.")
                else:
                    st.warning("⚠️ EasyOCR не е инсталиран. Инсталирай го: `pip install easyocr`")

    # ── Въведи баркод ──
    elif method == "🔢 Въведи баркод":
        st.markdown("**Въведи баркод ръчно:**")
        barcode_input = st.text_input(
            "Баркод (EAN-13):",
            value=st.session_state.manual_barcode,
            placeholder="напр. 5449000000996",
            key="barcode_text_input"
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Търси", key="search_barcode_btn"):
                if barcode_input.strip():
                    st.session_state.manual_barcode = barcode_input.strip()
                    with st.spinner("Зареждаме данни..."):
                        p = fetch_openfoodfacts(barcode_input.strip())
                    if p:
                        p["barcode"] = barcode_input.strip()
                        run_analysis(p, "manual")
                        st.success(f"✅ **{p['name']}** намерен! Виж таб **Резултати**")
                    else:
                        st.error("❌ Продуктът не е намерен в OpenFoodFacts.")
                else:
                    st.warning("⚠️ Моля въведи баркод.")
        with col2:
            if st.button("🗑️ Изчисти", key="clear_barcode_btn"):
                st.session_state.manual_barcode = ""
                st.rerun()

        st.markdown("---")
        st.markdown("**Демо баркодове за тест:**")
        for bc, name in DEMO_BARCODES.items():
            if st.button(f"📦 {name} ({bc})", key=f"demo_{bc}"):
                with st.spinner(f"Зареждаме {name}..."):
                    p = fetch_openfoodfacts(bc)
                if p:
                    p["barcode"] = bc
                    run_analysis(p, "demo_barcode")
                    st.success(f"✅ {name} анализиран! Виж таб **Резултати**")
                else:
                    st.error("❌ Грешка при зареждане.")

# ─── TAB: РЕЗУЛТАТИ ───────────────────────────────────────────────────
with tab_results:
    analysis = st.session_state.current_analysis

    if analysis is None:
        st.markdown(
            "<div class='info-box'>ℹ️ Все още няма анализ. Използвай таб <strong>📷 Сканиране</strong>, за да сканираш продукт.</div>",
            unsafe_allow_html=True
        )
    else:
        product = analysis["product"]
        hs = analysis["health_score"]
        additives = analysis["additives"]
        nutrition = analysis["nutrition_analysis"]

        # Заглавие на продукта
        render_product_header(
            product.get("name", "Неизвестен"),
            product.get("brand", ""),
            product.get("category", ""),
            product.get("image_emoji", "🍽️")
        )

        # Здравна оценка
        render_section_title("💯", "Здравна оценка")
        render_health_score(hs["score"], hs["label"], hs["color"], hs["emoji"])

        # NutriScore
        nutriscore = product.get("nutriscore", "u")
        if nutriscore and nutriscore != "u":
            ns_color = get_nutriscore_color(nutriscore)
            st.markdown(
                f"<div style='text-align:center; margin-bottom:16px;'>"
                f"<span style='background:{ns_color}; color:white; padding:8px 20px; border-radius:8px; font-size:1.4em; font-weight:bold;'>"
                f"NutriScore: {nutriscore.upper()}</span></div>",
                unsafe_allow_html=True
            )

        # Хранителни стойности
        if nutrition:
            render_section_title("🥗", "Хранителни стойности (на 100г)")
            for item in nutrition:
                render_nutrition_bar(item["nutrient"], item["value"], item["unit"], item["percentage_daily"], item["color"])

        # Здравни рискове
        render_section_title("🏥", "Здравни рискове")
        health_risks = product.get("health_risks", {})
        cols = st.columns(2)
        for i, (key, info) in enumerate(HEALTH_RISK_INFO.items()):
            lvl = health_risks.get(key, "low")
            color = RISK_COLORS.get(lvl, "#34C759")
            desc = info.get(lvl, "")
            with cols[i % 2]:
                st.markdown(
                    f"<div style='text-align:center; padding:10px; border-radius:8px; border: 2px solid {color}; margin-bottom:8px;'>"
                    f"<div style='font-size:1.5em;'>{info['emoji']}</div>"
                    f"<strong>{info['name']}</strong><br>"
                    f"<span style='color:{color}; font-size:0.85em;'>{desc}</span></div>",
                    unsafe_allow_html=True
                )

        # Добавки
        render_section_title("🧪", f"Добавки ({additives['count']} намерени)")
        if additives["found"]:
            for a in additives["found"]:
                lvl = a["risk_level"]
                label = RISK_LABELS.get(lvl, lvl)
                color = RISK_COLORS.get(lvl, "#888")
                with st.expander(f"{label} — {a['code']} {a['name']}"):
                    st.markdown(f"**Категория:** {a['category']}")
                    st.markdown(f"**Описание:** {a['description']}")
                    if a.get("health_risks"):
                        st.markdown("**Рискове за здравето:** " + ", ".join(a["health_risks"]))
                    if a.get("banned_in"):
                        st.markdown("**Забранен в:** " + ", ".join(a["banned_in"]))
                    if a.get("alternatives"):
                        st.markdown(f"**Алтернативи:** {a['alternatives']}")
        else:
            st.success("✅ Не са намерени вредни добавки!")

        # Съставки
        ingredients = product.get("ingredients", "")
        if ingredients:
            with st.expander("📋 Пълен списък съставки"):
                st.write(ingredients)

        # Алтернативи
        alts = product.get("alternatives", [])
        if alts:
            render_section_title("🌿", "По-здравословни алтернативи")
            render_alternatives(alts)

        # AI анализ
        render_section_title("🤖", "AI Анализ")
        if st.button("🔬 Генерирай AI анализ", key="ai_btn"):
            with st.spinner("AI анализира продукта..."):
                ai_text = get_ai_analysis(product)
                st.session_state.ai_analysis = ai_text
        if st.session_state.ai_analysis:
            st.info(st.session_state.ai_analysis)

# ─── TAB: ИСТОРИЯ ────────────────────────────────────────────────────
with tab_history:
    render_section_title("📋", "История на сканиранията")
    history = get_history(st.session_state)
    stats = get_history_stats(st.session_state)

    if not history:
        st.markdown(
            "<div class='info-box'>📭 Историята е празна. Сканирай продукт, за да започнеш.</div>",
            unsafe_allow_html=True
        )
    else:
        # Статистики
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📦 Сканирани", stats.get("total_scanned", 0))
        with col2:
            st.metric("⭐ Средна оценка", stats.get("avg_health_score", 0))
        with col3:
            st.metric("⛔ Рискови", stats.get("high_risk_count", 0))

        st.markdown("---")

        for i, entry in enumerate(history):
            score = entry["analysis"]["health_score"]["score"]
            color = entry["analysis"]["health_score"]["color"]
            name = entry["product"].get("name", "Неизвестен")
            brand = entry["product"].get("brand", "")
            source = entry["product"].get("source", "")
            with st.expander(f"{'🍽️'} {name} — {score}/10"):
                st.markdown(f"**Марка:** {brand}")
                st.markdown(f"**Оценка:** <span style='color:{color}; font-weight:bold;'>{score}/10</span>", unsafe_allow_html=True)
                st.markdown(f"**Източник:** {source}")
                additives_count = entry["analysis"]["additives"]["count"]
                st.markdown(f"**Добавки:** {additives_count}")
                if st.button(f"📊 Зареди резултати", key=f"load_hist_{i}"):
                    st.session_state.current_analysis = entry["analysis"]
                    st.info("✅ Резултатите са заредени в таб **Резултати**")

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Изчисти история", key="clear_hist_btn"):
                clear_history(st.session_state)
                st.rerun()
        with col2:
            json_data = export_history_json(st.session_state)
            st.download_button(
                "💾 Експортирай JSON",
                data=json_data,
                file_name="foodscan_history.json",
                mime="application/json",
                key="export_btn"
            )

# ─── TAB: Е-ТА ───────────────────────────────────────────────────────
with tab_edata:
    render_section_title("🧪", "База данни с Е-добавки")

    search_query = st.text_input("🔍 Търси добавка (код или име):", placeholder="напр. E621 или глутамат")

    filtered = {}
    if search_query:
        q = search_query.lower()
        filtered = {
            code: data for code, data in HARMFUL_ADDITIVES.items()
            if q in code.lower() or q in data["name"].lower() or q in data["category"].lower()
        }
        if not filtered:
            st.warning("⚠️ Няма намерени добавки за това търсене.")
    else:
        filtered = HARMFUL_ADDITIVES

    # Филтър по риск
    risk_filter = st.multiselect(
        "Филтър по ниво на риск:",
        options=["high", "medium-high", "medium", "low-medium", "low"],
        format_func=lambda x: RISK_LABELS.get(x, x),
        default=[]
    )
    if risk_filter:
        filtered = {code: data for code, data in filtered.items() if data["risk_level"] in risk_filter}

    st.markdown(f"**Показани:** {len(filtered)} добавки")
    st.markdown("---")

    for code, data in filtered.items():
        lvl = data["risk_level"]
        label = RISK_LABELS.get(lvl, lvl)
        color = RISK_COLORS.get(lvl, "#888")
        with st.expander(f"{label} — **{code}** {data['name']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Категория:** {data['category']}")
                st.markdown(f"**Описание:** {data['description']}")
                if data.get("health_risks"):
                    st.markdown("**Здравни рискове:**")
                    for r in data["health_risks"]:
                        st.markdown(f"  - ⚠️ {r}")
            with col2:
                if data.get("found_in"):
                    st.markdown("**Среща се в:**")
                    for f in data["found_in"]:
                        st.markdown(f"  - 🍕 {f}")
                if data.get("banned_in"):
                    st.markdown("**Забранен в:** " + ", ".join(data["banned_in"]))
                if data.get("alternatives"):
                    st.markdown(f"**Алтернативи:** 🌿 {data['alternatives']}")

    st.markdown("---")
    st.markdown(
        "<div class='info-box'>ℹ️ Тази база данни е образователна. "
        "Консултирайте се с лекар или диетолог за медицински съвети.</div>",
        unsafe_allow_html=True
    )
