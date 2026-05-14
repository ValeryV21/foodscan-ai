"""
Модул за анализ на хранителни продукти.
Scoring v2 — калибриран алгоритъм.
"""

import re
from data.harmful_additives import HARMFUL_ADDITIVES, find_additives_in_text, get_overall_risk_score


def calculate_health_score(product_data: dict) -> dict:
    """Изчислява здравна оценка 1–10 (1=здравословно, 10=много вредно)."""
    score, breakdown = 0.0, []
    n = product_data.get("nutrition", {})

    def add(factor, pts, note):
        nonlocal score
        score += pts
        breakdown.append({"factor": factor, "points": pts, "note": note})

    # Захар (0-3)
    s = float(n.get("sugars", 0) or 0)
    if   s > 30:  add("🍬 Захари", 3.0, f"{s}g — изключително висока")
    elif s > 15:  add("🍬 Захари", 2.0, f"{s}g — много висока")
    elif s > 7:   add("🍬 Захари", 1.0, f"{s}g — висока")
    elif s > 2:   add("🍬 Захари", 0.5, f"{s}g — умерена")
    else:         add("🍬 Захари", 0.0, f"{s}g — ниска ✅")

    # Наситени мазнини (0-2)
    sf = float(n.get("saturated_fat", 0) or 0)
    if   sf > 10: add("🫧 Наситени мазнини", 2.0, f"{sf}g — много високи")
    elif sf > 5:  add("🫧 Наситени мазнини", 1.0, f"{sf}g — високи")
    elif sf > 2:  add("🫧 Наситени мазнини", 0.5, f"{sf}g — умерени")
    else:         add("🫧 Наситени мазнини", 0.0, f"{sf}g — ниски ✅")

    # Калории (0-2)
    c = float(n.get("calories", 0) or 0)
    if   c > 450: add("🔥 Калории", 2.0, f"{c} kcal — много високи")
    elif c > 300: add("🔥 Калории", 1.5, f"{c} kcal — високи")
    elif c > 150: add("🔥 Калории", 1.0, f"{c} kcal — умерени")
    elif c > 50:  add("🔥 Калории", 0.5, f"{c} kcal — ниски")
    else:         add("🔥 Калории", 0.0, f"{c} kcal — много ниски ✅")

    # Сол (0-2)
    sa = float(n.get("salt", 0) or 0)
    if   sa > 2.0: add("🧂 Сол", 2.0, f"{sa}g — много висока")
    elif sa > 1.0: add("🧂 Сол", 1.0, f"{sa}g — висока")
    elif sa > 0.3: add("🧂 Сол", 0.5, f"{sa}g — умерена")
    else:          add("🧂 Сол", 0.0, f"{sa}g — ниска ✅")

    # Добавки (0-3)
    additives = product_data.get("found_additives", [])
    if additives:
        max_r = max(a.get("risk_score", 5) for a in additives)
        avg_r = sum(a.get("risk_score", 5) for a in additives) / len(additives)
        high  = [a for a in additives if a.get("risk_level") in ("high","medium-high")]
        pts   = min(3.0, (max_r/10)*2.0 + len(additives)*0.2 + (avg_r/10)*0.5)
        add("🧪 Добавки", round(pts,2), f"{len(additives)} добавки, {len(high)} с висок риск (макс. риск: {max_r}/10)")

    # Бонуси
    pr = float(n.get("protein", 0) or 0)
    if pr > 10:
        add("💪 Протеин (бонус)", -0.5, f"{pr}g — добро")
    fi = float(n.get("fiber", 0) or 0)
    if   fi > 6: add("🌾 Фибри (бонус)", -0.5,  f"{fi}g — много добро")
    elif fi > 3: add("🌾 Фибри (бонус)", -0.25, f"{fi}g — добро")

    final = max(1, min(10, round(score + 1)))
    return {"score": final, "breakdown": breakdown,
            "label": _label(final), "color": _color(final), "emoji": _emoji(final)}


def _label(s):
    if s <= 2: return "Много здравословен"
    if s <= 4: return "Здравословен"
    if s <= 5: return "Умерено вреден"
    if s <= 7: return "Вреден"
    return "Много вреден"

def _color(s):
    if s <= 2: return "#00C853"
    if s <= 4: return "#64DD17"
    if s <= 5: return "#FFAB00"
    if s <= 7: return "#FF6D00"
    return "#D50000"

def _emoji(s):
    if s <= 2: return "🥦"
    if s <= 4: return "🍎"
    if s <= 5: return "⚠️"
    if s <= 7: return "🔴"
    return "☠️"


def analyze_product(product_data: dict, ocr_text: str = "") -> dict:
    ingredients_text = (product_data.get("ingredients","") + " " + ocr_text).strip()
    found_additives  = find_additives_in_text(ingredients_text)
    product_data["found_additives"] = found_additives
    health_score     = calculate_health_score(product_data)
    additives_risk   = get_overall_risk_score(found_additives)
    nutrition_items  = analyze_nutrition(product_data.get("nutrition", {}))
    return {
        "product":           product_data,
        "health_score":      health_score,
        "additives":         {"found": found_additives, "risk": additives_risk, "count": len(found_additives)},
        "nutrition_analysis": nutrition_items,
        "health_risks":       product_data.get("health_risks", {}),
        "alternatives":       product_data.get("alternatives", []),
    }


def analyze_nutrition(nutrition: dict) -> list:
    rows = [
        ("calories","Калории","kcal", [(80,"low"),(200,"medium"),(400,"high"),(9999,"very_high")],
         {"low":"✅ Ниски","medium":"🟡 Умерени","high":"🟠 Високи","very_high":"🔴 Много високи"}, False),
        ("sugars","Захари","g", [(2,"low"),(7,"medium"),(15,"high"),(9999,"very_high")],
         {"low":"✅ Ниски","medium":"🟡 Умерени","high":"🟠 Високи","very_high":"🔴 Много високи"}, False),
        ("fat","Мазнини","g", [(3,"low"),(10,"medium"),(20,"high"),(9999,"very_high")],
         {"low":"✅ Ниски","medium":"🟡 Умерени","high":"🟠 Високи","very_high":"🔴 Много високи"}, False),
        ("salt","Сол","g", [(0.3,"low"),(0.75,"medium"),(1.5,"high"),(9999,"very_high")],
         {"low":"✅ Ниска","medium":"🟡 Умерена","high":"🟠 Висока","very_high":"🔴 Много висока"}, False),
        ("protein","Протеин","g", [(5,"low"),(10,"medium"),(20,"high"),(9999,"very_high")],
         {"low":"🟠 Нисък","medium":"🟡 Умерен","high":"✅ Добър","very_high":"✅ Много добър"}, True),
        ("fiber","Фибри","g", [(1.5,"low"),(3,"medium"),(6,"high"),(9999,"very_high")],
         {"low":"🟠 Ниски","medium":"🟡 Умерени","high":"✅ Добри","very_high":"✅ Много добри"}, True),
    ]
    daily = {"calories":2000,"fat":70,"sugars":90,"protein":50,"salt":6,"fiber":25}
    result = []
    for key, label, unit, thresholds, descs, inv in rows:
        val = nutrition.get(key)
        if val is None: continue
        val = float(val)
        lvl = next((l for t, l in thresholds if val <= t), "very_high")
        colors = {"low":"#4CAF50","medium":"#FFAB00",
                  "high":"#00C853" if inv else "#FF6D00",
                  "very_high":"#00C853" if inv else "#D50000"}
        pct = min(999, round((val / daily[key]) * 100, 1)) if key in daily else 0
        result.append({"nutrient":label,"value":val,"unit":unit,"level":lvl,
                        "description":descs.get(lvl,""),"color":colors[lvl],"percentage_daily":pct})
    return result
