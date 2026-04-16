"""
🔍 FoodScan AI - Анализатор на хранителни продукти
====================================================
Мобилно приложение за анализ на хранителни продукти чрез:
- OCR разпознаване на текст от етикети
- Баркод сканиране
- Анализ на вредни добавки (E-та)
- Здравни рискове и алтернативи

Технологии: Python + Streamlit + EasyOCR + pyzbar
Автор: FoodScan AI Team
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from PIL import Image
import io
import json
import requests

# ============ Конфигурация на страницата ============
st.set_page_config(
    page_title="FoodScan AI",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": "FoodScan AI - Анализирай хранителни продукти за секунди!"
    }
)

# ============ Импортиране на вътрешни модули ============
from utils.ui_helpers import (
    MOBILE_CSS, render_header, render_health_score,
    render_additive_badge, render_nutrition_bar, render_risk_card,
    render_history_card, render_alternatives, render_product_header,
    render_section_title, get_nutriscore_color
)
from data.harmful_additives import (
    HARMFUL_ADDITIVES, find_additives_in_text,
    get_overall_risk_score, RISK_COLORS, RISK_LABELS
)
from data.product_database import (
    MOCK_PRODUCTS, HEALTH_RISK_INFO, get_product_by_barcode, get_demo_products
)
from modules.barcode_scanner import scan_barcode, fetch_openfoodfacts, DEMO_BARCODES, get_barcode_info
from modules.ocr_scanner import get_ocr_reader, extract_text_from_image, parse_food_label
from modules.product_analyzer import analyze_product, calculate_health_score
from modules.history_manager import (
    initialize_history, add_to_history, get_history,
    clear_history, get_history_stats, export_history_json
)

# ============ CSS Инжектиране ============
st.markdown(MOBILE_CSS, unsafe_allow_html=True)

# ============ Инициализация на сесията ============
initialize_history(st.session_state)

if "current_analysis" not in st.session_state:
    st.session_state.current_analysis = None

if "ocr_reader" not in st.session_state:
    st.session_state.ocr_reader = None
    st.session_state.ocr_engine = None


def load_ocr_reader():
    """Зарежда OCR четеца (с кеширане в сесията)."""
    if st.session_state.ocr_reader is None:
        reader, engine = get_ocr_reader()
        st.session_state.ocr_reader = reader
        st.session_state.ocr_engine = engine
    return st.session_state.ocr_reader, st.session_state.ocr_engine


def analyze_from_product_data(product_data: dict, source: str = "database"):
    """
    Анализира продукт от речник с данни.
    Добавя source и задейства пълен анализ.
    """
    product_data["source"] = source
    
    # Пълен анализ
    analysis = analyze_product(product_data, product_data.get("ingredients", ""))
    
    # Запазваме в сесията
    st.session_state.current_analysis = analysis
    
    # Добавяме в историята
    add_to_history(st.session_state, product_data, analysis)
    
    return analysis


def get_ai_analysis(product_data: dict) -> str:
    """
    Получава AI анализ чрез Anthropic API.
    """
    try:
        product_name = product_data.get("name", "Неизвестен продукт")
        ingredients = product_data.get("ingredients", "")
        nutrition = product_data.get("nutrition", {})
        
        prompt = f"""Анализирай следния хранителен продукт и дай кратко, ясно мнение на български:

Продукт: {product_name}
Съставки: {ingredients}
Калории/100g: {nutrition.get('calories', 'неизвестно')}
Мазнини/100g: {nutrition.get('fat', 'неизвестно')}g
Захари/100g: {nutrition.get('sugars', 'неизвестно')}g

Дай:
1. 🎯 Обща оценка (1-2 изречения)
2. ⚠️ Главни опасения (макс 3 точки)
3. 💡 Практични съвети (макс 2 точки)

Бъди конкретен, честен и полезен. Не повтаряй излишно информацията."""

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json"},
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["content"][0]["text"]
        else:
            return "⚠️ AI анализът не е наличен в момента."
            
    except Exception as e:
        return f"⚠️ Грешка при AI анализ: {str(e)[:100]}"


# ============================================================
# ГЛАВНА НАВИГАЦИЯ
# ============================================================

render_header()

# Основни табове
tab_scan, tab_results, tab_history, tab_additives = st.tabs([
    "📷 Сканиране",
    "📊 Резултати",
    "📋 История",
    "🧪 E-та"
])


# ============================================================
# ТАБ 1: СКАНИРАНЕ
# ============================================================
with tab_scan:
    st.markdown("### Как искаш да добавиш продукт?")
    
    scan_method = st.radio(
        "Метод на сканиране",
        ["📦 Демо продукт", "🖼️ Качи снимка", "📷 Камера", "🔢 Въведи баркод"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # ---- ДЕМО ПРОДУКТ ----
    if scan_method == "📦 Демо продукт":
        st.markdown("""
        <div class="info-section">
            <p>🎯 <strong>Избери продукт от нашата демо база данни</strong> за да видиш как работи анализът без нужда от камера или баркод скенер.</p>
        </div>
        """, unsafe_allow_html=True)
        
        demo_products = get_demo_products()
        product_options = {f"{p['emoji']} {p['name']} ({p['brand']})": p["barcode"] 
                         for p in demo_products}
        
        selected = st.selectbox(
            "Избери продукт:",
            list(product_options.keys())
        )
        
        if st.button("🔍 Анализирай продукта", key="demo_analyze"):
            barcode = product_options[selected]
            product_data = get_product_by_barcode(barcode)
            
            if product_data:
                with st.spinner("⚡ Анализираме продукта..."):
                    product_data["barcode"] = barcode
                    analysis = analyze_from_product_data(product_data, "demo")
                
                st.success(f"✅ {product_data['name']} е анализиран успешно!")
                st.info("📊 Виж резултатите в таб **'Резултати'**")
    
    # ---- КАЧИ СНИМКА ----
    elif scan_method == "🖼️ Качи снимка":
        st.markdown("""
        <div class="info-section">
            <p>📸 <strong>Качи снимка на хранителния етикет</strong> — OCR ще разпознае текста и ще намери съставките, E-та и хранителните стойности.</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Качи снимка на етикет",
            type=["jpg", "jpeg", "png", "webp"],
            help="Подкрепени формати: JPG, PNG, WebP. Максимум 10MB."
        )
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.image(image, caption="Качена снимка", use_container_width=True)
            with col2:
                st.metric("Резолюция", f"{image.width}×{image.height}")
                st.metric("Формат", image.format or "JPG")
            
            # Проверяваме за баркод
            with st.spinner("🔍 Търсим баркод..."):
                barcode_result = scan_barcode(image)
            
            if barcode_result["found"]:
                st.success(f"✅ Намерен баркод: **{barcode_result['barcode']}**")
                
                # Търсим в демо базата
                product_data = get_product_by_barcode(barcode_result["barcode"])
                
                if not product_data:
                    # Търсим в Open Food Facts
                    with st.spinner("🌐 Търсим в Open Food Facts..."):
                        product_data = fetch_openfoodfacts(barcode_result["barcode"])
                
                if product_data:
                    product_data["barcode"] = barcode_result["barcode"]
                    if "image_emoji" not in product_data:
                        product_data["image_emoji"] = "🏷️"
                    
                    with st.spinner("⚡ Анализираме..."):
                        analysis = analyze_from_product_data(product_data, "barcode_scan")
                    
                    st.success("✅ Готово! Виж таб **'Резултати'**")
                else:
                    st.warning("⚠️ Продуктът не е намерен в базата данни.")
            else:
                st.info("ℹ️ Баркод не е намерен — извършваме OCR анализ на текста...")
            
            if st.button("🔤 Анализирай с OCR", key="ocr_analyze"):
                with st.spinner("🤖 OCR разпознаване на текст..."):
                    reader, engine = load_ocr_reader()
                    ocr_result = extract_text_from_image(image, reader, engine)
                
                if ocr_result["success"]:
                    st.success(f"✅ Разпознат текст (двигател: {ocr_result['engine']}, точност: {ocr_result['confidence']:.0%})")
                    
                    with st.expander("📄 Разпознат текст"):
                        st.text(ocr_result["raw_text"])
                    
                    # Парсираме хранителния етикет
                    parsed = parse_food_label(ocr_result["raw_text"])
                    
                    # Изграждаме product_data от OCR
                    product_data = {
                        "name": parsed.get("product_name") or "Разпознат продукт",
                        "brand": parsed.get("brand") or "Неизвестна марка",
                        "category": "OCR Сканиране",
                        "image_emoji": "📷",
                        "ingredients": parsed.get("ingredients", ocr_result["raw_text"]),
                        "nutrition": parsed.get("nutrition", {}),
                        "health_risks": {
                            "obesity": "medium",
                            "diabetes": "medium",
                            "heart": "medium",
                            "blood_pressure": "medium"
                        },
                        "alternatives": ["Прясна храна", "Домашно приготвена храна"]
                    }
                    
                    with st.spinner("⚡ Анализираме продукта..."):
                        analysis = analyze_from_product_data(product_data, "ocr")
                    
                    st.success("✅ Анализът е готов! Виж таб **'Резултати'**")
                else:
                    st.error("❌ Неуспешно OCR разпознаване.")
    
    # ---- КАМЕРА ----
    elif scan_method == "📷 Камера":
        st.markdown("""
        <div class="info-section">
            <p>📱 <strong>Снимай директно с камерата</strong> на устройството си — перфектно за мобилни устройства.</p>
        </div>
        """, unsafe_allow_html=True)
        
        camera_image = st.camera_input("Насочи камерата към етикета или баркода")
        
        if camera_image:
            image = Image.open(camera_image)
            
            # Проверяваме за баркод
            with st.spinner("🔍 Търсим баркод..."):
                barcode_result = scan_barcode(image)
            
            if barcode_result["found"]:
                st.success(f"✅ Намерен баркод: **{barcode_result['barcode']}**")
                
                product_data = get_product_by_barcode(barcode_result["barcode"])
                if not product_data:
                    with st.spinner("🌐 Търсим онлайн..."):
                        product_data = fetch_openfoodfacts(barcode_result["barcode"])
                
                if product_data:
                    product_data["barcode"] = barcode_result["barcode"]
                    product_data.setdefault("image_emoji", "📷")
                    
                    with st.spinner("⚡ Анализираме..."):
                        analysis = analyze_from_product_data(product_data, "camera_barcode")
                    st.success("✅ Готово! Виж таб **'Резултати'**")
                else:
                    st.warning("⚠️ Продуктът не е намерен.")
            else:
                st.info("ℹ️ Извършваме OCR анализ...")
                
                with st.spinner("🤖 OCR разпознаване..."):
                    reader, engine = load_ocr_reader()
                    ocr_result = extract_text_from_image(image, reader, engine)
                
                if ocr_result["success"]:
                    parsed = parse_food_label(ocr_result["raw_text"])
                    product_data = {
                        "name": parsed.get("product_name") or "Сниман продукт",
                        "brand": "",
                        "category": "Камера скан",
                        "image_emoji": "📷",
                        "ingredients": parsed.get("ingredients", ocr_result["raw_text"]),
                        "nutrition": parsed.get("nutrition", {}),
                        "health_risks": {"obesity": "medium", "diabetes": "medium", "heart": "medium", "blood_pressure": "medium"},
                        "alternatives": ["Прясна храна"]
                    }
                    
                    with st.spinner("⚡ Анализираме..."):
                        analysis = analyze_from_product_data(product_data, "camera_ocr")
                    st.success("✅ Готово! Виж таб **'Резултати'**")
    
    # ---- РЪЧЕН БАРКОД ----
    elif scan_method == "🔢 Въведи баркод":
        st.markdown("""
        <div class="info-section">
            <p>⌨️ <strong>Въведи баркода ръчно</strong> — търсим в демо базата и Open Food Facts.</p>
        </div>
        """, unsafe_allow_html=True)
        
        barcode_input = st.text_input(
            "Въведи баркода (EAN-13, EAN-8, UPC-A):",
            placeholder="Напр: 5449000000996",
            max_chars=20
        )
        
        st.markdown("**Демо баркодове за тестване:**")
        demo_cols = st.columns(2)
        for i, (bc, name) in enumerate(DEMO_BARCODES.items()):
            with demo_cols[i % 2]:
                if st.button(f"`{bc}`\n{name}", key=f"demo_bc_{bc}"):
                    barcode_input = bc
                    st.session_state.manual_barcode = bc
        
        actual_barcode = barcode_input or st.session_state.get("manual_barcode", "")
        
        if actual_barcode and st.button("🔍 Търси продукт", key="manual_search"):
            with st.spinner(f"🔍 Търсим {actual_barcode}..."):
                product_data = get_product_by_barcode(actual_barcode)
                
                if not product_data:
                    st.info("ℹ️ Не е намерен локално — търсим в Open Food Facts...")
                    product_data = fetch_openfoodfacts(actual_barcode)
            
            if product_data:
                product_data["barcode"] = actual_barcode
                product_data.setdefault("image_emoji", "🏷️")
                
                analysis = analyze_from_product_data(product_data, "manual_barcode")
                st.success(f"✅ Намерен: **{product_data['name']}**! Виж таб **'Резултати'**")
            else:
                st.error(f"❌ Продукт с баркод **{actual_barcode}** не е намерен.")
                st.info("💡 Опитай с демо баркод: `5449000000996` (Coca-Cola)")


# ============================================================
# ТАБ 2: РЕЗУЛТАТИ
# ============================================================
with tab_results:
    if st.session_state.current_analysis is None:
        st.markdown("""
        <div style="text-align:center; padding: 60px 20px; color: #8896B0;">
            <div style="font-size: 64px; margin-bottom: 16px;">🔍</div>
            <h3 style="color: #8896B0 !important;">Все още няма анализиран продукт</h3>
            <p>Отиди в таб <strong style="color: #00B894;">Сканиране</strong> и избери или сканирай продукт</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        analysis = st.session_state.current_analysis
        product = analysis["product"]
        health_score = analysis["health_score"]
        additives_data = analysis["additives"]
        nutrition_analysis = analysis["nutrition_analysis"]
        
        # ---- ХЕДЪР НА ПРОДУКТА ----
        render_product_header(
            product.get("name", "Неизвестен продукт"),
            product.get("brand", ""),
            product.get("category", ""),
            product.get("image_emoji", "🍽️")
        )
        
        # ---- ЗДРАВНА ОЦЕНКА ----
        render_section_title("🏥", "Здравна оценка")
        render_health_score(
            health_score["score"],
            health_score["label"],
            health_score["color"],
            health_score["emoji"]
        )
        
        # ---- МЕТРИКИ ----
        col1, col2, col3 = st.columns(3)
        
        nutrition = product.get("nutrition", {})
        with col1:
            calories = nutrition.get("calories", 0)
            st.metric("🔥 Калории", f"{calories:.0f} kcal", help="на 100g")
        with col2:
            fat = nutrition.get("fat", 0)
            st.metric("🫧 Мазнини", f"{fat:.1f}g", help="на 100g")
        with col3:
            sugars = nutrition.get("sugars", 0)
            st.metric("🍬 Захари", f"{sugars:.1f}g", help="на 100g")
        
        st.markdown("---")
        
        # ---- ХРАНИТЕЛНИ СТОЙНОСТИ ----
        render_section_title("📈", "Хранителни стойности (на 100g)")
        
        for item in nutrition_analysis:
            render_nutrition_bar(
                item["nutrient"],
                item["value"],
                item["unit"],
                item["percentage_daily"],
                item["color"]
            )
        
        if not nutrition_analysis:
            st.info("ℹ️ Хранителните стойности не са налични за този продукт.")
        
        st.markdown("---")
        
        # ---- ВРЕДНИ ДОБАВКИ ----
        render_section_title("🧪", f"Хранителни добавки ({additives_data['count']} намерени)")
        
        found_additives = additives_data["found"]
        
        if found_additives:
            # Обща оценка на добавките
            risk = additives_data["risk"]
            st.markdown(f"""
            <div class="food-card" style="border-left: 4px solid {risk['color']}; margin-bottom: 16px;">
                <div style="font-size: 16px; font-weight: 700; color: {risk['color']};">{risk['label']}</div>
                <div style="font-size: 13px; color: #8896B0; margin-top: 4px;">{len(found_additives)} добавки открити в съставките</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Бадж за всяка добавка
            st.markdown('<div style="display:flex; flex-wrap:wrap; gap:6px; margin-bottom:16px;">', unsafe_allow_html=True)
            for additive in found_additives:
                render_additive_badge(
                    additive["code"],
                    additive["name"],
                    additive["risk_level"]
                )
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Детайли за всяка добавка
            for additive in found_additives:
                risk_color = RISK_COLORS.get(additive["risk_level"], "#888")
                risk_label = RISK_LABELS.get(additive["risk_level"], "")
                
                with st.expander(f"📋 {additive['code']} — {additive['name']} {risk_label}"):
                    st.markdown(f"""
                    <div style="padding: 8px 0;">
                        <div style="color: #8896B0; font-size: 13px; margin-bottom: 12px;">
                            📂 <strong>Категория:</strong> {additive['category']}
                        </div>
                        <div style="color: #F0F4FF; font-size: 14px; margin-bottom: 12px; line-height: 1.5;">
                            ℹ️ {additive['description']}
                        </div>
                        <div style="margin-bottom: 10px;">
                            <div style="color: {risk_color}; font-weight: 700; font-size: 14px; margin-bottom: 8px;">
                                ⚠️ Здравни рискове:
                            </div>
                            {"".join([f'<div style="color: #8896B0; font-size: 13px; padding: 3px 0;">• {risk}</div>' for risk in additive['health_risks']])}
                        </div>
                        {"<div style='color: #8896B0; font-size: 13px; margin-top: 10px;'>🚫 <strong>Забранен в:</strong> " + ", ".join(additive['banned_in']) + "</div>" if additive.get('banned_in') else ""}
                        {"<div style='color: #00D4AA; font-size: 13px; margin-top: 8px;'>🌿 <strong>Алтернативи:</strong> " + additive.get('alternatives', '') + "</div>" if additive.get('alternatives') else ""}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="food-card" style="border-left: 4px solid #00C853; text-align: center; padding: 24px;">
                <div style="font-size: 36px; margin-bottom: 8px;">✅</div>
                <div style="color: #00C853; font-weight: 700; font-size: 16px;">Без известни вредни добавки</div>
                <div style="color: #8896B0; font-size: 13px; margin-top: 4px;">Не са намерени E-та с висок риск в съставките</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ---- ЗДРАВНИ РИСКОВЕ ----
        render_section_title("❤️", "Здравни рискове")
        
        health_risks = product.get("health_risks", {})
        
        for risk_key, risk_info in HEALTH_RISK_INFO.items():
            level = health_risks.get(risk_key, "low")
            description = risk_info.get(level, "Няма информация.")
            
            render_risk_card(
                risk_info["name"],
                risk_info["emoji"],
                level,
                description
            )
        
        st.markdown("---")
        
        # ---- АЛТЕРНАТИВИ ----
        alternatives = product.get("alternatives", [])
        if alternatives:
            render_section_title("🌿", "По-здравословни алтернативи")
            
            st.markdown("""
            <div class="info-section">
                <p>💡 Вместо <strong>{}</strong>, опитай:</p>
            </div>
            """.format(product.get("name", "този продукт")), unsafe_allow_html=True)
            
            render_alternatives(alternatives)
        
        st.markdown("---")
        
        # ---- СЪСТАВКИ ----
        ingredients = product.get("ingredients", "")
        if ingredients:
            with st.expander("📄 Пълен списък със съставки"):
                # Маркираме E-числата в текста
                st.markdown(f"""
                <div style="font-size: 13px; color: #8896B0; line-height: 1.8; padding: 8px 0;">
                    {ingredients}
                </div>
                """, unsafe_allow_html=True)
        
        # ---- AI АНАЛИЗ (бутон) ----
        st.markdown("---")
        render_section_title("🤖", "AI Дълбок анализ")
        
        if "ai_analysis" not in st.session_state:
            st.session_state.ai_analysis = None
        
        if st.button("✨ Получи AI анализ", key="ai_btn"):
            with st.spinner("🤖 Claude анализира продукта..."):
                ai_text = get_ai_analysis(product)
                st.session_state.ai_analysis = ai_text
        
        if st.session_state.ai_analysis:
            st.markdown(f"""
            <div class="food-card" style="border-left: 4px solid #6C5CE7;">
                <div style="color: #F0F4FF; font-size: 14px; line-height: 1.7; white-space: pre-line;">
                    {st.session_state.ai_analysis}
                </div>
                <div style="color: #8896B0; font-size: 11px; margin-top: 12px;">
                    🤖 Анализиран от Claude AI
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # ---- ОЦЕНКА НА РАЗБИВКАТА ----
        breakdown = health_score.get("breakdown", [])
        if breakdown:
            with st.expander("📊 Как е изчислена оценката?"):
                for item in breakdown:
                    pts = item["points"]
                    color = "#FF3B30" if pts > 1 else "#FF9500" if pts > 0 else "#34C759"
                    icon = "🔴" if pts > 1 else "🟡" if pts > 0 else "🟢"
                    st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; align-items:center; 
                               padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                        <span style="color: #F0F4FF; font-size: 13px;">{icon} {item['factor']}</span>
                        <span style="color: {color}; font-weight: 700; font-size: 14px;">+{pts:.1f}т | {item['note']}</span>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Nutri-Score ако е наличен
        nutriscore = product.get("nutriscore", "")
        if nutriscore and nutriscore in "ABCDE":
            color = get_nutriscore_color(nutriscore)
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:12px; margin-top:16px; padding: 12px 16px;
                       background: rgba(255,255,255,0.04); border-radius: 14px; border: 1px solid rgba(255,255,255,0.08);">
                <div style="background: {color}; color: white; font-weight: 900; font-size: 24px;
                           width: 48px; height: 48px; display:flex; align-items:center; justify-content:center;
                           border-radius: 12px;">{nutriscore}</div>
                <div>
                    <div style="color: #F0F4FF; font-weight: 700;">Nutri-Score</div>
                    <div style="color: #8896B0; font-size: 13px;">Официална европейска оценка</div>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ============================================================
# ТАБ 3: ИСТОРИЯ
# ============================================================
with tab_history:
    history = get_history(st.session_state)
    stats = get_history_stats(st.session_state)
    
    if not history:
        st.markdown("""
        <div style="text-align:center; padding: 60px 20px; color: #8896B0;">
            <div style="font-size: 64px; margin-bottom: 16px;">📋</div>
            <h3 style="color: #8896B0 !important;">Историята е празна</h3>
            <p>Сканирай продукти и те ще се появят тук</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Статистики
        render_section_title("📊", "Твоята статистика")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Сканирани", stats.get("total_scanned", 0), help="Общо сканирани продукти")
        with col2:
            avg = stats.get("avg_health_score", 0)
            st.metric("Средна оценка", f"{avg}/10", help="Средна оценка на вредност")
        with col3:
            st.metric("Рискови", stats.get("high_risk_count", 0), help="Продукти с оценка ≥ 7")
        
        if stats.get("worst_product"):
            st.markdown(f"""
            <div class="info-section" style="border-color: rgba(255,59,48,0.3); background: rgba(255,59,48,0.08);">
                <p>⛔ <strong>Най-вреден скениран продукт:</strong> {stats['worst_product']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        if stats.get("best_product"):
            st.markdown(f"""
            <div class="info-section">
                <p>✅ <strong>Най-здравословен:</strong> {stats['best_product']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        render_section_title("📋", f"Последно сканирани ({len(history)})")
        
        for entry in history:
            render_history_card(entry)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Изчисти историята"):
                clear_history(st.session_state)
                st.rerun()
        with col2:
            json_data = export_history_json(st.session_state)
            st.download_button(
                "📥 Изтегли JSON",
                json_data,
                "scan_history.json",
                "application/json"
            )


# ============================================================
# ТАБ 4: РЕЧНИК НА E-ТА
# ============================================================
with tab_additives:
    st.markdown("### 🧪 Пълен речник на Е-добавките")
    st.markdown("""
    <div class="info-section">
        <p>📚 Изчерпателна база данни с <strong>{} вредни добавки</strong> — оцветители, консерванти, усилватели на вкус и подсладители.</p>
    </div>
    """.format(len(HARMFUL_ADDITIVES)), unsafe_allow_html=True)
    
    # Филтри
    col1, col2 = st.columns(2)
    with col1:
        categories = list(set(a["category"] for a in HARMFUL_ADDITIVES.values()))
        selected_category = st.selectbox("📂 Категория", ["Всички"] + sorted(categories))
    with col2:
        risk_levels = ["Всички", "high", "medium-high", "medium", "low-medium", "low"]
        risk_labels_ui = {
            "Всички": "Всички",
            "high": "⛔ Много вредни",
            "medium-high": "🔴 Вредни",
            "medium": "🟡 Умерено вредни",
            "low-medium": "🟢 Ниска опасност",
            "low": "✅ Безопасни"
        }
        selected_risk = st.selectbox("⚠️ Ниво на риск", 
                                      list(risk_labels_ui.keys()),
                                      format_func=lambda x: risk_labels_ui[x])
    
    search_term = st.text_input("🔍 Търси по E-номер или наименование:", placeholder="Напр: E621, аспартам...")
    
    st.markdown("---")
    
    # Показваме добавките
    shown = 0
    for code, data in HARMFUL_ADDITIVES.items():
        # Прилагаме филтри
        if selected_category != "Всички" and data["category"] != selected_category:
            continue
        if selected_risk != "Всички" and data["risk_level"] != selected_risk:
            continue
        if search_term and search_term.lower() not in code.lower() and search_term.lower() not in data["name"].lower():
            continue
        
        shown += 1
        risk_color = RISK_COLORS.get(data["risk_level"], "#888")
        risk_label = RISK_LABELS.get(data["risk_level"], "")
        
        with st.expander(f"{risk_label} **{code}** — {data['name']} ({data['category']})"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"""
                <div style="padding: 4px 0;">
                    <p style="color: #F0F4FF; font-size: 14px; line-height: 1.6; margin-bottom: 12px;">
                        ℹ️ {data['description']}
                    </p>
                    <div style="margin-bottom: 12px;">
                        <strong style="color: {risk_color}; font-size: 13px;">⚠️ Здравни рискове:</strong>
                        {"".join([f'<div style="color: #8896B0; font-size: 13px; padding: 2px 0; padding-left: 16px;">• {r}</div>' for r in data['health_risks']])}
                    </div>
                    {"<div style='margin-bottom: 8px;'><strong style='color: #FF6B6B; font-size: 13px;'>🚫 Забранен в:</strong> <span style='color: #8896B0; font-size: 13px;'>" + ", ".join(data['banned_in']) + "</span></div>" if data.get('banned_in') else ""}
                    {"<div><strong style='color: #00D4AA; font-size: 13px;'>🌿 Алтернативи:</strong> <span style='color: #8896B0; font-size: 13px;'>" + data.get('alternatives', '') + "</span></div>" if data.get('alternatives') else ""}
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style="text-align: center; padding: 16px; background: rgba(255,255,255,0.04); 
                           border-radius: 14px; border: 1px solid {risk_color}33;">
                    <div style="font-size: 36px; font-weight: 900; color: {risk_color}; font-family: 'Space Grotesk';">
                        {data['risk_score']}
                    </div>
                    <div style="font-size: 11px; color: #8896B0; margin-top: 4px;">Риск скор /10</div>
                    <div style="margin-top: 12px;">
                        {"".join([
                            f'<div style="width: 10px; height: 10px; border-radius: 50%; margin: 4px auto; background: {"" if i > data["risk_score"] else risk_color}; background-color: {risk_color if i <= data["risk_score"] else "rgba(255,255,255,0.08)"}"></div>'
                            for i in range(10, 0, -1)
                        ])}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if data.get("found_in"):
                    st.markdown(f"""
                    <div style="margin-top: 12px; padding: 12px; background: rgba(255,255,255,0.03); border-radius: 12px;">
                        <div style="color: #8896B0; font-size: 11px; font-weight: 700; text-transform: uppercase; 
                                   letter-spacing: 0.5px; margin-bottom: 8px;">Среща се в:</div>
                        {"".join([f'<div style="color: #8896B0; font-size: 12px; padding: 2px 0;">• {f}</div>' for f in data['found_in'][:4]])}
                    </div>
                    """, unsafe_allow_html=True)
    
    if shown == 0:
        st.info("ℹ️ Няма намерени добавки с тези критерии.")
    else:
        st.markdown(f"""
        <div style="text-align: center; color: #8896B0; font-size: 13px; padding: 16px; margin-top: 8px;">
            Показани {shown} от {len(HARMFUL_ADDITIVES)} добавки
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #8896B0; font-size: 12px; padding: 16px 0;">
    <div style="margin-bottom: 8px;">
        🔍 <strong style="color: #00B894;">FoodScan AI</strong> — Анализатор на хранителни продукти
    </div>
    <div>
        Данните са за информационни цели. Консултирайте се с диетолог за персонализирани съвети.
    </div>
    <div style="margin-top: 8px;">
        🌐 Данни: Open Food Facts • 🤖 AI: Claude by Anthropic • 📊 E-та: EU Food Additives Database
    </div>
</div>
""", unsafe_allow_html=True)
