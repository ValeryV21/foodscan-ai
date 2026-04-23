"""
Модул за анализ на хранителни продукти.
Изчислява здравна оценка, анализира съставки и дава препоръки.
"""

import re
from data.harmful_additives import HARMFUL_ADDITIVES, find_additives_in_text, get_overall_risk_score


def calculate_health_score(product_data: dict) -> dict:
    """
    Изчислява здравна оценка на продукта от 1 до 10.
    (1 = много здравословно, 10 = много вредно)
    
    Алгоритъм:
    - Калории на 100g (0-2т)
    - Захар (0-2т)
    - Наситени мазнини (0-2т)
    - Сол (0-1т)
    - Вредни добавки (0-3т)
    """
    score = 0
    breakdown = []
    nutrition = product_data.get("nutrition", {})
    
    # ---- Калории ----
    calories = nutrition.get("calories", 0)
    if calories > 500:
        score += 2
        breakdown.append({"factor": "Калории", "points": 2, "note": f"{calories} kcal/100g - много високи"})
    elif calories > 350:
        score += 1
        breakdown.append({"factor": "Калории", "points": 1, "note": f"{calories} kcal/100g - високи"})
    elif calories > 0:
        breakdown.append({"factor": "Калории", "points": 0, "note": f"{calories} kcal/100g - умерени"})
    
    # ---- Захар ----
    sugars = nutrition.get("sugars", 0)
    if sugars > 20:
        score += 2
        breakdown.append({"factor": "Захар", "points": 2, "note": f"{sugars}g/100g - много висока"})
    elif sugars > 10:
        score += 1
        breakdown.append({"factor": "Захар", "points": 1, "note": f"{sugars}g/100g - висока"})
    elif sugars > 0:
        breakdown.append({"factor": "Захар", "points": 0, "note": f"{sugars}g/100g - умерена"})
    
    # ---- Наситени мазнини ----
    sat_fat = nutrition.get("saturated_fat", 0)
    if sat_fat > 10:
        score += 2
        breakdown.append({"factor": "Наситени мазнини", "points": 2, "note": f"{sat_fat}g/100g - много високи"})
    elif sat_fat > 5:
        score += 1
        breakdown.append({"factor": "Наситени мазнини", "points": 1, "note": f"{sat_fat}g/100g - високи"})
    elif sat_fat > 0:
        breakdown.append({"factor": "Наситени мазнини", "points": 0, "note": f"{sat_fat}g/100g - умерени"})
    
    # ---- Сол ----
    salt = nutrition.get("salt", 0)
    if salt > 2.5:
        score += 1
        breakdown.append({"factor": "Сол", "points": 1, "note": f"{salt}g/100g - много висока"})
    elif salt > 1.5:
        score += 0.5
        breakdown.append({"factor": "Сол", "points": 0.5, "note": f"{salt}g/100g - висока"})
    
    # ---- Вредни добавки ----
    additives = product_data.get("found_additives", [])
    if additives:
        high_risk = [a for a in additives if a.get("risk_level") in ["high", "medium-high"]]
        additive_score = min(3, len(high_risk) * 1.5 + len(additives) * 0.5)
        score += additive_score
        breakdown.append({
            "factor": "Вредни добавки",
            "points": additive_score,
            "note": f"{len(additives)} добавки, {len(high_risk)} с висок риск"
        })
    
    # ---- Фибри (положителен ефект) ----
    fiber = nutrition.get("fiber", 0)
    if fiber > 6:
        score -= 0.5
        breakdown.append({"factor": "Фибри (бонус)", "points": -0.5, "note": f"{fiber}g/100g - много добро"})
    elif fiber > 3:
        score -= 0.25
        breakdown.append({"factor": "Фибри (бонус)", "points": -0.25, "note": f"{fiber}g/100g - добро"})
    
    # Ограничаваме скалата 1-10
    final_score = max(1, min(10, round(score + 1)))
    
    return {
        "score": final_score,
        "breakdown": breakdown,
        "label": _score_to_label(final_score),
        "color": _score_to_color(final_score),
        "emoji": _score_to_emoji(final_score)
    }


def _score_to_label(score: int) -> str:
    if score <= 2: return "Много здравословен"
    if score <= 4: return "Здравословен"
    if score <= 6: return "Умерено вреден"
    if score <= 8: return "Вреден"
    return "Много вреден"


def _score_to_color(score: int) -> str:
    if score <= 2: return "#00C853"
    if score <= 4: return "#64DD17"
    if score <= 6: return "#FFAB00"
    if score <= 8: return "#FF6D00"
    return "#D50000"


def _score_to_emoji(score: int) -> str:
    if score <= 2: return "🥦"
    if score <= 4: return "🍎"
    if score <= 6: return "⚠️"
    if score <= 8: return "🔴"
    return "☠️"


def analyze_product(product_data: dict, ocr_text: str = "") -> dict:
    """
    Пълен анализ на продукта.
    
    Args:
        product_data: Данни за продукта (от база данни или парсиране)
        ocr_text: Суров OCR текст (ако е наличен)
    
    Returns:
        dict с пълен анализ
    """
    # Намираме вредни добавки
    ingredients_text = product_data.get("ingredients", "") + " " + ocr_text
    found_additives = find_additives_in_text(ingredients_text)
    product_data["found_additives"] = found_additives
    
    # Изчисляваме здравна оценка
    health_score = calculate_health_score(product_data)
    
    # Обща оценка на добавките
    additives_risk = get_overall_risk_score(found_additives)
    
    # Анализ на хранителните стойности
    nutrition_analysis = analyze_nutrition(product_data.get("nutrition", {}))
    
    return {
        "product": product_data,
        "health_score": health_score,
        "additives": {
            "found": found_additives,
            "risk": additives_risk,
            "count": len(found_additives)
        },
        "nutrition_analysis": nutrition_analysis,
        "health_risks": product_data.get("health_risks", {}),
        "alternatives": product_data.get("alternatives", [])
    }


def analyze_nutrition(nutrition: dict) -> list:
    """
    Анализира хранителните стойности и дава оценки.
    """
    analysis = []
    
    nutrients = [
        {
            "key": "calories",
            "label": "Калории",
            "unit": "kcal",
            "thresholds": [(100, "low"), (250, "medium"), (400, "high"), (float('inf'), "very_high")],
            "descriptions": {
                "low": "✅ Ниски калории",
                "medium": "🟡 Умерени калории",
                "high": "🟠 Високи калории",
                "very_high": "🔴 Много високи калории"
            }
        },
        {
            "key": "sugars",
            "label": "Захари",
            "unit": "g",
            "thresholds": [(5, "low"), (12, "medium"), (20, "high"), (float('inf'), "very_high")],
            "descriptions": {
                "low": "✅ Ниско съдържание на захар",
                "medium": "🟡 Умерено съдържание на захар",
                "high": "🟠 Високо съдържание на захар",
                "very_high": "🔴 Много високо съдържание на захар"
            }
        },
        {
            "key": "fat",
            "label": "Мазнини",
            "unit": "g",
            "thresholds": [(3, "low"), (10, "medium"), (20, "high"), (float('inf'), "very_high")],
            "descriptions": {
                "low": "✅ Ниско съдържание на мазнини",
                "medium": "🟡 Умерено съдържание на мазнини",
                "high": "🟠 Високо съдържание на мазнини",
                "very_high": "🔴 Много високо съдържание на мазнини"
            }
        },
        {
            "key": "salt",
            "label": "Сол",
            "unit": "g",
            "thresholds": [(0.3, "low"), (0.75, "medium"), (1.5, "high"), (float('inf'), "very_high")],
            "descriptions": {
                "low": "✅ Ниско съдържание на сол",
                "medium": "🟡 Умерено съдържание на сол",
                "high": "🟠 Високо съдържание на сол",
                "very_high": "🔴 Много високо съдържание на сол"
            }
        },
        {
            "key": "protein",
            "label": "Протеин",
            "unit": "g",
            "thresholds": [(5, "low"), (10, "medium"), (20, "high"), (float('inf'), "very_high")],
            "descriptions": {
                "low": "🟡 Ниско съдържание на протеин",
                "medium": "✅ Умерено съдържание на протеин",
                "high": "✅ Добро съдържание на протеин",
                "very_high": "✅ Много добро съдържание на протеин"
            },
            "inverted": True  # Повече = по-добре
        },
        {
            "key": "fiber",
            "label": "Фибри",
            "unit": "g",
            "thresholds": [(1.5, "low"), (3, "medium"), (6, "high"), (float('inf'), "very_high")],
            "descriptions": {
                "low": "🟠 Ниско съдържание на фибри",
                "medium": "🟡 Умерено съдържание на фибри",
                "high": "✅ Добро съдържание на фибри",
                "very_high": "✅ Много добро съдържание на фибри"
            },
            "inverted": True
        }
    ]
    
    for nutrient in nutrients:
        value = nutrition.get(nutrient["key"], None)
        if value is None:
            continue
        
        # Намираме ниво
        level = "low"
        for threshold, lvl in nutrient["thresholds"]:
            if value <= threshold:
                level = lvl
                break
        
        # Цвят според нивото (обратен за протеин/фибри)
        is_inverted = nutrient.get("inverted", False)
        color_map = {
            "low": "#00C853" if is_inverted else "#4CAF50",
            "medium": "#FFAB00",
            "high": "#FF6D00" if not is_inverted else "#00C853",
            "very_high": "#D50000" if not is_inverted else "#00C853"
        }
        
        analysis.append({
            "nutrient": nutrient["label"],
            "value": value,
            "unit": nutrient["unit"],
            "level": level,
            "description": nutrient["descriptions"].get(level, ""),
            "color": color_map.get(level, "#FFAB00"),
            "percentage_daily": _calc_daily_percentage(nutrient["key"], value)
        })
    
    return analysis


def _calc_daily_percentage(nutrient_key: str, value: float) -> float:
    """Изчислява процент от дневната препоръчителна доза (базирано на 100g)."""
    daily_values = {
        "calories": 2000,
        "fat": 70,
        "saturated_fat": 20,
        "carbs": 260,
        "sugars": 90,
        "protein": 50,
        "salt": 6,
        "fiber": 25,
        "sodium": 2.4
    }
    
    daily = daily_values.get(nutrient_key)
    if daily and daily > 0:
        return min(100, round((value / daily) * 100, 1))
    return 0


def estimate_calories_from_text(text: str) -> float | None:
    """
    Оценява калориите ако не са намерени директно.
    Използва макронутриентите: протеин=4kcal, въглехидрати=4kcal, мазнини=9kcal
    """
    nutrition = {}
    
    # Опитваме се да намерим макронутриенти
    patterns = {
        "protein": r'протеин[^0-9]*(\d+(?:[.,]\d+)?)',
        "carbs": r'въглехидрат[^0-9]*(\d+(?:[.,]\d+)?)',
        "fat": r'мазнин[^0-9]*(\d+(?:[.,]\d+)?)',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                nutrition[key] = float(match.group(1).replace(',', '.'))
            except ValueError:
                pass
    
    if len(nutrition) >= 2:
        calories = (
            nutrition.get("protein", 0) * 4 +
            nutrition.get("carbs", 0) * 4 +
            nutrition.get("fat", 0) * 9
        )
        return round(calories, 1)
    
    return None
