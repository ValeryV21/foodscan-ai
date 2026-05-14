"""
🔍 FoodScan AI v3
=================
EasyOCR + NumPy предобработка + Claude Vision резервен вариант.
Показва разпознатия текст с маркирани E-числа в реално време.
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from PIL import Image
import io, json, base64, requests

st.set_page_config(page_title="FoodScan AI", page_icon="🔍", layout="centered",
                   initial_sidebar_state="collapsed")

from utils.ui_helpers import (
    MOBILE_CSS, render_header, render_health_score, render_nutrition_bar,
    render_risk_card, render_history_card, render_alternatives,
    render_product_header, render_section_title, get_nutriscore_color,
    render_ocr_result_with_highlights,
)
from data.harmful_additives import (
    HARMFUL_ADDITIVES, find_additives_in_text, get_overall_risk_score,
    RISK_COLORS, RISK_LABELS,
)
from data.product_database import (
    MOCK_PRODUCTS, HEALTH_RISK_INFO, get_product_by_barcode, get_demo_products,
)
from modules.barcode_scanner  import scan_barcode, fetch_openfoodfacts, DEMO_BARCODES, get_barcode_info
from modules.ocr_scanner      import (
    get_ocr_reader, get_ocr_status, extract_text_from_image,
    extract_text_easyocr, extract_text_claude_vision, parse_food_label,
)
from modules.product_analyzer import analyze_product
from modules.history_manager  import (
    initialize_history, add_to_history, get_history,
    clear_history, get_history_stats, export_history_json,
)

st.markdown(MOBILE_CSS, unsafe_allow_html=True)
initialize_history(st.session_state)

# ── Session state defaults ──────────────────────────────────────────────
for key, val in [("current_analysis", None), ("ocr_reader", None),
                 ("ocr_engine", None), ("ai_analysis", None),
                 ("manual_barcode", "")]:
    if key not in st.session_state:
        st.session_state[key] = val


# ── Helpers ─────────────────────────────────────────────────────────────
def load_reader():
    if st.session_state.ocr_reader is None:
        r, e = get_ocr_reader()
        st.session_state.ocr_reader = r
        st.session_state.ocr_engine = e
    return st.session_state.ocr_reader, st.session_state.ocr_engine


def run_analysis(product_data: dict, source: str = "db") -> dict:
    """Пълен анализ + запис в историята."""
    product_data["source"] = source
    analysis = analyze_product(product_data, product_data.get("ingredients",""))
    st.session_state.current_analysis = analysis
    st.session_state.ai_analysis = None          # нулираме AI анализа при нов продукт
    add_to_history(st.session_state, product_data, analysis)
    return analysis


def build_product_from_ocr(ocr_result: dict, image_note: str = "📷") -> dict:
    """Изгражда product_data речник от OCR резултат."""
    parsed = parse_food_label(ocr_result["raw_text"])
    return {
        "name":        parsed.get("product_name") or "Продукт от снимка",
        "brand":       parsed.get("brand",""),
        "category":    "OCR Сканиране",
        "image_emoji": image_note,
        "ingredients": parsed.get("ingredients") or ocr_result["raw_text"],
        "nutrition":   {k:v for k,v in parsed.get("nutrition",{}).items() if v},
        "health_risks":{"obesity":"medium","diabetes":"medium","heart":"medium","blood_pressure":"medium"},
        "alternatives":["Прясна храна","Домашно приготвена храна"],
    }


def show_ocr_panel(ocr_result: dict):
    """Показва OCR резултат с маркирани E-числа."""
    if not ocr_result.get("success") or not ocr_result.get("raw_text","").strip():
        return
    # Намираме добавки в текста
    found = find_additives_in_text(ocr_result["raw_text"])
    highlighted = render_ocr_result_with_highlights(ocr_result["raw_text"], found)

    conf_pct = f"{ocr_result.get('confidence',0):.0%}"
    engine   = ocr_result.get("engine","?")
    engine_label = {"easyocr":"EasyOCR 🤖","claude_vision":"Claude Vision 👁️","tesseract":"Tesseract"}.get(engine, engine)

    with st.expander(f"📄 Разпознат текст — {engine_label} ({conf_pct} точност)", expanded=True):
        st.markdown(f'<div class="ocr-box">{highlighted}</div>', unsafe_allow_html=True)
        if found:
            st.markdown(
                f"🔴 Маркирани **{len(found)}** вредни добавки: "
                + ", ".join(f"`{a['code']}`" for a in found),
            )
        else:
            st.markdown("✅ Не са намерени вредни E-числа в текста.")


def get_ai_analysis(product_data: dict) -> str:
    """Claude AI дълбок анализ на продукта."""
    n = product_data.get("nutrition",{})
    prompt = f"""Анализирай следния хранителен продукт и дай кратко, ясно мнение на БЪЛГАРСКИ:

Продукт: {product_data.get("name","?")}
Съставки: {product_data.get("ingredients","—")[:400]}
Калории: {n.get("calories","?")} kcal/100g
Мазнини: {n.get("fat","?")}g  Захари: {n.get("sugars","?")}g  Сол: {n.get("salt","?")}g

Дай:
1. 🎯 Обща оценка (1-2 изречения)
2. ⚠️ Главни опасения (макс 3 точки)  
3. 💡 Практични съвети (макс 2 точки)

Бъди конкретен и честен. НЕ повтаряй информацията от горе."""
    try:
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"Content-Type":"application/json"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":500,
                  "messages":[{"role":"user","content":prompt}]}, timeout=15)
        if r.status_code == 200:
            return r.json()["content"][0]["text"]
        return f"⚠️ API грешка {r.status_code}"
    except Exception as e:
        return f"⚠️ {e}"


# ════════════════════════════════════════════════════════════════════════
# LAYOUT
# ════════════════════════════════════════════════════════════════════════
render_header()

# Статус на OCR и баркод скенери (sidebar)
with st.sidebar:
    st.markdown("### ⚙️ Системен статус")
    ocr_st  = get_ocr_status()
    bc_info = get_barcode_info()
    st.markdown(f"**EasyOCR:** {'✅ Инсталиран' if ocr_st['easyocr'] else '❌ Не е инсталиран'}")
    st.markdown(f"**pyzbar:**  {'✅' if bc_info['pyzbar']  else '❌ Не е инсталиран'}")
    st.markdown(f"**OpenCV:**  {'✅' if bc_info['opencv']  else '❌'}")
    st.markdown("---")
    st.markdown("**Инсталация:**")
    st.code("pip install easyocr numpy\npip install pyzbar\n# Linux: sudo apt install libzbar0", language="bash")
    st.markdown("---")
    st.markdown("### ℹ️ OCR легенда")
    st.markdown('<span style="background:rgba(255,59,48,.25);color:#FF6B6B;border-radius:3px;padding:2px 6px;font-weight:700">E621</span> = вредна добавка', unsafe_allow_html=True)
    st.markdown('<span style="background:rgba(0,184,148,.2);color:#00D4AA;border-radius:3px;padding:2px 6px">E330</span> = E-число (по-нисък риск)', unsafe_allow_html=True)

tab_scan, tab_results, tab_history, tab_edata = st.tabs([
    "📷 Сканиране", "📊 Резултати", "📋 История", "🧪 Е-та"
])


# ════════════════════════════════════════════════════════════════════════
# ТАБ 1 — СКАНИРАНЕ
# ════════════════════════════════════════════════════════════════════════
with tab_scan:
    method = st.radio("Метод", ["📦 Демо продукт","🖼️ Качи снимка","📷 Камера","🔢 Въведи баркод"],
                      label_visibility="collapsed")
    st.markdown("---")

    # ── Демо ────────────────────────────────────────────────────────────
    if method == "📦 Демо продукт":
        st.markdown('<div class="info-box">🎯 Избери продукт за демонстрация на пълния анализ.</div>', unsafe_allow_html=True)
        opts = {f"{p['emoji']} {p['name']} ({p['brand']})": p["barcode"] for p in get_demo_products()}
        sel  = st.selectbox("Избери продукт:", list(opts.keys()))
        if st.button("🔍 Анализирай"):
            bc = opts[sel]
            p  = get_product_by_barcode(bc)
            if p:
                p["barcode"] = bc
                with st.spinner("⚡ Анализираме..."):
                    run_analysis(p, "demo")
                st.success(f"✅ {p['name']} анализиран! Виж таб **Резултати**")

    # ── Качи снимка ─────────────────────────────────────────────────────
    elif method == "🖼️ Качи снимка":
        ocr_ok = ocr_st["any_available"]
        if not ocr_ok:
            st.warning("⚠️ EasyOCR не е инсталиран. OCR разпознаването ще използва **Claude Vision** (изисква интернет).")

        st.markdown('<div class="info-box">📸 Качи снимка на етикет — автоматично търсим баркод, след това можеш да пуснеш OCR.</div>', unsafe_allow_html=True)

        uploaded = st.file_uploader("Качи снимка", type=["jpg","jpeg","png","webp"])

        if uploaded:
            image = Image.open(uploaded)
            c1, c2 = st.columns([3,1])
            with c1: st.image(image, caption="Качена снимка", use_container_width=True)
            with c2:
                st.metric("Ширина",  f"{image.width}px")
                st.metric("Височина",f"{image.height}px")

            # Търсим баркод
            with st.spinner("🔍 Търсим баркод..."):
                bc_res = scan_barcode(image)

            if bc_res["found"]:
                st.success(f"✅ Баркод: **{bc_res['barcode']}** ({bc_res['barcode_type']})")
                p = get_product_by_barcode(bc_res["barcode"])
                if not p:
                    with st.spinner("🌐 Open Food Facts..."):
                        p = fetch_openfoodfacts(bc_res["barcode"])
                if p:
                    p["barcode"] = bc_res["barcode"]
                    p.setdefault("image_emoji","🏷️")
                    with st.spinner("⚡ Анализираме..."): run_analysis(p,"barcode_scan")
                    st.success("✅ Готово! Виж **Резултати**")
                else:
                    st.warning("⚠️ Продуктът не е намерен в базите данни.")
            else:
                st.info("ℹ️ Баркод не е открит — можеш да пуснеш OCR.")

            st.markdown("---")
            st.markdown("#### 🔤 OCR разпознаване на текст")

            engine_choice = st.radio("OCR двигател:", ["🤖 EasyOCR (локален)","👁️ Claude Vision (облачен)"],
                                     disabled=False, horizontal=True)

            if st.button("▶️ Стартирай OCR", key="ocr_btn"):
                with st.spinner("🤖 Разпознаваме текст..."):
                    if "EasyOCR" in engine_choice and ocr_ok:
                        reader, eng = load_reader()
                        ocr_res = extract_text_easyocr(image, reader) if reader else extract_text_claude_vision(image)
                    else:
                        ocr_res = extract_text_claude_vision(image)

                if ocr_res["success"] and ocr_res["raw_text"].strip():
                    show_ocr_panel(ocr_res)
                    p = build_product_from_ocr(ocr_res)
                    with st.spinner("⚡ Анализираме..."): run_analysis(p,"ocr")
                    st.success("✅ Готово! Виж **Резултати**")
                else:
                    err = ocr_res.get("error","Непознат проблем")
                    st.error(f"❌ OCR не успя: {err}")
                    st.markdown("""**Съвети:**
- 📸 Снимай отблизо и перпендикулярно на етикета
- 💡 Осигури добро осветление
- 🔲 Снимката трябва да е рязка""")

    # ── Камера ──────────────────────────────────────────────────────────
    elif method == "📷 Камера":
        st.markdown('<div class="info-box">📱 Снимай директно — идеално за мобилни устройства.</div>', unsafe_allow_html=True)
        cam = st.camera_input("Насочи към етикета или баркода")

        if cam:
            image = Image.open(cam)
            with st.spinner("🔍 Търсим баркод..."):
                bc_res = scan_barcode(image)

            if bc_res["found"]:
                st.success(f"✅ Баркод: **{bc_res['barcode']}**")
                p = get_product_by_barcode(bc_res["barcode"])
                if not p:
                    with st.spinner("🌐 Open Food Facts..."): p = fetch_openfoodfacts(bc_res["barcode"])
                if p:
                    p["barcode"] = bc_res["barcode"]; p.setdefault("image_emoji","📷")
                    with st.spinner("⚡ Анализираме..."): run_analysis(p,"camera_bc")
                    st.success("✅ Готово! Виж **Резултати**")
                else:
                    st.warning("⚠️ Продуктът не е намерен.")
            else:
                st.info("ℹ️ Баркод не е открит — опитваме OCR...")
                engine_ch = st.radio("OCR:", ["🤖 EasyOCR","👁️ Claude Vision"], horizontal=True)
                if st.button("▶️ OCR", key="cam_ocr"):
                    with st.spinner("🤖 Разпознаване..."):
                        if "EasyOCR" in engine_ch and ocr_st["any_available"]:
                            reader, _ = load_reader()
                            ocr_res = extract_text_easyocr(image, reader) if reader else extract_text_claude_vision(image)
                        else:
                            ocr_res = extract_text_claude_vision(image)
                    if ocr_res["success"]:
                        show_ocr_panel(ocr_res)
                        p = build_product_from_ocr(ocr_res,"📷")
                        with st.spinner("⚡ Анализираме..."): run_analysis(p,"camera_ocr")
                        st.success("✅ Готово! Виж **Резултати**")
                    else:
                        st.error(f"❌ {ocr_res.get('error','Грешка')}")

    # ── Ръчен баркод ────────────────────────────────────────────────────
    elif method == "🔢 Въведи баркод":
        st.markdown('<div class="info-box">⌨️ Въведи EAN-13 или UPC-A баркод ръчно.</div>', unsafe_allow_html=True)
        bc_in = st.text_input("Баркод:", placeholder="5449000000996", max_chars=20)

        st.markdown("**Демо баркодове:**")
        cols = st.columns(2)
        for i,(bc,nm) in enumerate(DEMO_BARCODES.items()):
            with cols[i%2]:
                if st.button(f"`{bc}` {nm}", key=f"dbc_{bc}"):
                    st.session_state.manual_barcode = bc

        actual = bc_in or st.session_state.get("manual_barcode","")
        if actual and st.button("🔍 Търси", key="bc_search"):
            with st.spinner(f"🔍 Търсим {actual}..."):
                p = get_product_by_barcode(actual) or fetch_openfoodfacts(actual)
            if p:
                p["barcode"] = actual; p.setdefault("image_emoji","🏷️")
                run_analysis(p,"manual_bc")
                st.success(f"✅ {p['name']}! Виж **Резултати**")
            else:
                st.error(f"❌ Не е намерен продукт с баркод **{actual}**")


# ════════════════════════════════════════════════════════════════════════
# ТАБ 2 — РЕЗУЛТАТИ
# ════════════════════════════════════════════════════════════════════════
with tab_results:
    if not st.session_state.current_analysis:
        st.markdown('<div style="text-align:center;padding:60px 20px;color:#8896B0"><div style="font-size:64px">🔍</div><h3 style="color:#8896B0!important">Все още няма анализ</h3><p>Отиди в <strong style="color:#00B894">Сканиране</strong> и избери продукт</p></div>', unsafe_allow_html=True)
    else:
        A   = st.session_state.current_analysis
        prd = A["product"]
        hs  = A["health_score"]
        ad  = A["additives"]
        na  = A["nutrition_analysis"]

        render_product_header(prd.get("name","?"), prd.get("brand",""),
                              prd.get("category",""), prd.get("image_emoji","🍽️"))

        # Здравна оценка
        render_section_title("🏥","Здравна оценка")
        render_health_score(hs["score"], hs["label"], hs["color"], hs["emoji"])

        # Метрики
        n = prd.get("nutrition",{})
        c1,c2,c3 = st.columns(3)
        with c1: st.metric("🔥 Калории", f'{n.get("calories",0):.0f} kcal')
        with c2: st.metric("🫧 Мазнини",  f'{n.get("fat",0):.1f}g')
        with c3: st.metric("🍬 Захари",   f'{n.get("sugars",0):.1f}g')
        st.markdown("---")

        # Хранителни стойности
        render_section_title("📈","Хранителни стойности (на 100g)")
        for item in na:
            render_nutrition_bar(item["nutrient"], item["value"], item["unit"],
                                 item["percentage_daily"], item["color"])
        if not na:
            st.info("ℹ️ Хранителните стойности не са налични.")
        st.markdown("---")

        # Добавки
        render_section_title("🧪", f"Хранителни добавки ({ad['count']} намерени)")
        found = ad["found"]
        if found:
            risk = ad["risk"]
            st.markdown(f'<div class="food-card" style="border-left:4px solid {risk["color"]}">'
                        f'<div style="font-size:16px;font-weight:700;color:{risk["color"]}">{risk["label"]}</div>'
                        f'<div style="font-size:13px;color:#8896B0;margin-top:4px">{len(found)} добавки в съставките</div>'
                        f'</div>', unsafe_allow_html=True)

            # Бадж за всяка
            badges = "".join(
                f'<span class="abadge {a["risk_level"]}">{a["code"]} | {a["name"]}</span>'
                for a in found
            )
            st.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px">{badges}</div>',
                        unsafe_allow_html=True)

            for a in found:
                rc = RISK_COLORS.get(a["risk_level"],"#888")
                rl = RISK_LABELS.get(a["risk_level"],"")
                with st.expander(f"📋 {a['code']} — {a['name']}  {rl}"):
                    col1, col2 = st.columns([2,1])
                    with col1:
                        st.markdown(f"""
<div style="padding:4px 0">
  <div style="color:#8896B0;font-size:13px;margin-bottom:10px">📂 <b>Категория:</b> {a['category']}</div>
  <div style="color:#F0F4FF;font-size:14px;margin-bottom:12px">ℹ️ {a['description']}</div>
  <div style="color:{rc};font-weight:700;font-size:14px;margin-bottom:6px">⚠️ Здравни рискове:</div>
  {"".join(f'<div style="color:#8896B0;font-size:13px;padding:2px 0 2px 16px">• {r}</div>' for r in a['health_risks'])}
  {"<div style='color:#FF6B6B;font-size:13px;margin-top:8px'>🚫 <b>Забранен в:</b> "+", ".join(a['banned_in'])+"</div>" if a.get('banned_in') else ""}
  {"<div style='color:#00D4AA;font-size:13px;margin-top:6px'>🌿 <b>Алтернативи:</b> "+a.get('alternatives','')+"</div>" if a.get('alternatives') else ""}
</div>""", unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"""
<div style="text-align:center;padding:16px;background:rgba(255,255,255,.04);border-radius:14px;border:1px solid {rc}33">
  <div style="font-size:36px;font-weight:900;color:{rc};font-family:'Space Grotesk'">{a['risk_score']}</div>
  <div style="font-size:11px;color:#8896B0;margin-top:4px">Риск скор /10</div>
</div>""", unsafe_allow_html=True)
                        if a.get("found_in"):
                            fi = "".join(f'<div style="color:#8896B0;font-size:12px;padding:2px 0">• {f}</div>' for f in a["found_in"][:4])
                            st.markdown(f'<div style="margin-top:12px;padding:12px;background:rgba(255,255,255,.03);border-radius:12px"><div style="color:#8896B0;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px">Среща се в:</div>{fi}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="food-card" style="border-left:4px solid #00C853;text-align:center;padding:24px"><div style="font-size:36px">✅</div><div style="color:#00C853;font-weight:700;font-size:16px">Без известни вредни добавки</div></div>', unsafe_allow_html=True)

        # OCR текст (ако е налично)
        if prd.get("source") in ("ocr","camera_ocr"):
            st.markdown("---")
            render_section_title("📄","OCR текст")
            fake_ocr = {"success":True,"raw_text":prd.get("ingredients",""),"confidence":0.85,"engine":"easyocr"}
            show_ocr_panel(fake_ocr)

        st.markdown("---")

        # Здравни рискове
        render_section_title("❤️","Здравни рискове")
        for k, ri in HEALTH_RISK_INFO.items():
            lvl = prd.get("health_risks",{}).get(k,"low")
            render_risk_card(ri["name"], ri["emoji"], lvl, ri.get(lvl,""))

        st.markdown("---")

        # Алтернативи
        alts = prd.get("alternatives",[])
        if alts:
            render_section_title("🌿","По-здравословни алтернативи")
            st.markdown(f'<div class="info-box">💡 Вместо <b>{prd.get("name","")}</b>, опитай:</div>', unsafe_allow_html=True)
            render_alternatives(alts)
            st.markdown("---")

        # Пълни съставки
        ingr = prd.get("ingredients","")
        if ingr:
            with st.expander("📄 Пълен списък съставки"):
                st.markdown(f'<div style="font-size:13px;color:#8896B0;line-height:1.8">{ingr}</div>', unsafe_allow_html=True)

        # Как е изчислена оценката
        breakdown = hs.get("breakdown",[])
        if breakdown:
            with st.expander("📊 Как е изчислена оценката?"):
                for b in breakdown:
                    pts = b["points"]
                    col = "#FF3B30" if pts>1 else "#FF9500" if pts>0 else "#34C759"
                    ico = "🔴" if pts>1 else "🟡" if pts>0 else "🟢"
                    st.markdown(
                        f'<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.05)">'
                        f'<span style="color:#F0F4FF;font-size:13px">{ico} {b["factor"]}</span>'
                        f'<span style="color:{col};font-weight:700;font-size:14px">{b["points"]:+.2f}т | {b["note"]}</span>'
                        f'</div>', unsafe_allow_html=True)

        # Nutri-Score
        ns = prd.get("nutriscore","")
        if ns and ns in "ABCDE":
            nsc = get_nutriscore_color(ns)
            st.markdown(f'<div style="display:flex;align-items:center;gap:12px;margin-top:16px;padding:12px 16px;background:rgba(255,255,255,.04);border-radius:14px;border:1px solid rgba(255,255,255,.08)"><div style="background:{nsc};color:white;font-weight:900;font-size:24px;width:48px;height:48px;display:flex;align-items:center;justify-content:center;border-radius:12px">{ns}</div><div><div style="color:#F0F4FF;font-weight:700">Nutri-Score</div><div style="color:#8896B0;font-size:13px">Официална европейска оценка</div></div></div>', unsafe_allow_html=True)

        # AI анализ
        st.markdown("---")
        render_section_title("🤖","AI Дълбок анализ")
        if st.button("✨ Получи AI анализ", key="ai_btn"):
            with st.spinner("🤖 Claude анализира..."):
                st.session_state.ai_analysis = get_ai_analysis(prd)
        if st.session_state.ai_analysis:
            st.markdown(f'<div class="food-card" style="border-left:4px solid #6C5CE7"><div style="color:#F0F4FF;font-size:14px;line-height:1.7;white-space:pre-line">{st.session_state.ai_analysis}</div><div style="color:#8896B0;font-size:11px;margin-top:12px">🤖 Анализиран от Claude AI</div></div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════
# ТАБ 3 — ИСТОРИЯ
# ════════════════════════════════════════════════════════════════════════
with tab_history:
    history = get_history(st.session_state)
    stats   = get_history_stats(st.session_state)
    if not history:
        st.markdown('<div style="text-align:center;padding:60px 20px;color:#8896B0"><div style="font-size:64px">📋</div><h3 style="color:#8896B0!important">Историята е празна</h3></div>', unsafe_allow_html=True)
    else:
        render_section_title("📊","Твоята статистика")
        c1,c2,c3 = st.columns(3)
        with c1: st.metric("Сканирани", stats.get("total_scanned",0))
        with c2: st.metric("Средна оценка", f'{stats.get("avg_health_score",0)}/10')
        with c3: st.metric("Рискови (≥7)", stats.get("high_risk_count",0))
        if stats.get("worst_product"):
            st.markdown(f'<div class="info-box" style="border-color:rgba(255,59,48,.3);background:rgba(255,59,48,.08)">⛔ <b>Най-вреден:</b> {stats["worst_product"]}</div>', unsafe_allow_html=True)
        if stats.get("best_product"):
            st.markdown(f'<div class="info-box">✅ <b>Най-здравословен:</b> {stats["best_product"]}</div>', unsafe_allow_html=True)
        st.markdown("---")
        render_section_title("📋",f"Последно сканирани ({len(history)})")
        for e in history:
            render_history_card(e)
        st.markdown("---")
        c1,c2 = st.columns(2)
        with c1:
            if st.button("🗑️ Изчисти историята"):
                clear_history(st.session_state); st.rerun()
        with c2:
            st.download_button("📥 Изтегли JSON", export_history_json(st.session_state),
                               "scan_history.json","application/json")


# ════════════════════════════════════════════════════════════════════════
# ТАБ 4 — Е-ТА РЕЧНИК
# ════════════════════════════════════════════════════════════════════════
with tab_edata:
    st.markdown(f"### 🧪 Речник на Е-добавките ({len(HARMFUL_ADDITIVES)} записа)")
    st.markdown(f'<div class="info-box">📚 Изчерпателна база данни — оцветители, консерванти, усилватели на вкус и подсладители.</div>', unsafe_allow_html=True)

    cats = sorted(set(a["category"] for a in HARMFUL_ADDITIVES.values()))
    c1,c2 = st.columns(2)
    with c1: cat_f  = st.selectbox("📂 Категория", ["Всички"]+cats)
    with c2:
        risk_opts = {"Всички":"Всички","high":"⛔ Много вредни","medium-high":"🔴 Вредни",
                     "medium":"🟡 Умерено","low-medium":"🟢 Ниска опасност","low":"✅ Безопасни"}
        risk_f = st.selectbox("⚠️ Риск", list(risk_opts.keys()), format_func=lambda x:risk_opts[x])
    search = st.text_input("🔍 Търси:", placeholder="E621, аспартам…")

    st.markdown("---")
    shown = 0
    for code, data in HARMFUL_ADDITIVES.items():
        if cat_f  != "Всички" and data["category"] != cat_f:   continue
        if risk_f != "Всички" and data["risk_level"] != risk_f: continue
        if search and search.lower() not in code.lower() and search.lower() not in data["name"].lower(): continue
        shown += 1
        rc = RISK_COLORS.get(data["risk_level"],"#888")
        rl = RISK_LABELS.get(data["risk_level"],"")
        with st.expander(f"{rl} **{code}** — {data['name']}"):
            c1,c2 = st.columns([2,1])
            with c1:
                st.markdown(f"""
<div style="padding:4px 0">
  <div style="color:#8896B0;font-size:13px;margin-bottom:10px">📂 {data['category']}</div>
  <div style="color:#F0F4FF;font-size:14px;margin-bottom:12px">ℹ️ {data['description']}</div>
  <b style="color:{rc};font-size:13px">⚠️ Здравни рискове:</b>
  {"".join(f'<div style="color:#8896B0;font-size:13px;padding:2px 0 2px 16px">• {r}</div>' for r in data['health_risks'])}
  {"<div style='color:#FF6B6B;font-size:13px;margin-top:8px'>🚫 <b>Забранен в:</b> "+", ".join(data['banned_in'])+"</div>" if data.get('banned_in') else ""}
  {"<div style='color:#00D4AA;font-size:13px;margin-top:6px'>🌿 <b>Алтернативи:</b> "+data.get('alternatives','')+"</div>" if data.get('alternatives') else ""}
</div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div style="text-align:center;padding:16px;background:rgba(255,255,255,.04);border-radius:14px;border:1px solid {rc}33"><div style="font-size:36px;font-weight:900;color:{rc};font-family:\'Space Grotesk\'">{data["risk_score"]}</div><div style="font-size:11px;color:#8896B0;margin-top:4px">Риск скор /10</div></div>', unsafe_allow_html=True)
                if data.get("found_in"):
                    fi = "".join(f'<div style="color:#8896B0;font-size:12px;padding:2px 0">• {f}</div>' for f in data["found_in"][:4])
                    st.markdown(f'<div style="margin-top:12px;padding:12px;background:rgba(255,255,255,.03);border-radius:12px"><div style="color:#8896B0;font-size:11px;font-weight:700;text-transform:uppercase;margin-bottom:8px">Среща се в:</div>{fi}</div>', unsafe_allow_html=True)

    if shown == 0:
        st.info("ℹ️ Няма намерени добавки.")
    else:
        st.markdown(f'<div style="text-align:center;color:#8896B0;font-size:13px;padding:16px">Показани {shown} от {len(HARMFUL_ADDITIVES)}</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown('<div style="text-align:center;color:#8896B0;font-size:12px;padding:16px 0">🔍 <b style="color:#00B894">FoodScan AI v3</b> — EasyOCR + NumPy + Claude Vision<br>Данните са за информационни цели. Консултирайте се с диетолог.<br>🌐 Open Food Facts • 🤖 Claude AI • 📊 EU Food Additives DB</div>', unsafe_allow_html=True)
