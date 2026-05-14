"""
База данни с вредни хранителни добавки (Е-та) — 30+ записа
"""
import re

HARMFUL_ADDITIVES = {
    # ── ОЦВЕТИТЕЛИ ──────────────────────────────────────────────────────
    "E102":  {"name":"Тартразин","category":"Оцветител","risk_level":"high","risk_score":8,
               "description":"Синтетичен жълт оцветител от катран.",
               "health_risks":["Хиперактивност при деца","Алергии","Астма","Уртикария"],
               "banned_in":["Норвегия","Австрия"],"found_in":["Газирани напитки","Бонбони","Чипс"],
               "alternatives":"Куркума (E100), натурален бета-каротин"},
    "E110":  {"name":"Залез жълто FCF","category":"Оцветител","risk_level":"high","risk_score":7,
               "description":"Синтетичен оранжев оцветител.",
               "health_risks":["Хиперактивност","Алергии","Гадене"],
               "banned_in":["Норвегия","Финландия"],"found_in":["Портокалови напитки","Желе"],
               "alternatives":"Натурален бета-каротин"},
    "E120":  {"name":"Кошенил / Кармин","category":"Оцветител","risk_level":"medium-high","risk_score":6,
               "description":"Червен оцветител от насекоми — неподходящ за вегани.",
               "health_risks":["Тежки алергии","Анафилактичен шок","Астма"],
               "banned_in":[],"found_in":["Кисело мляко","Сокове","Бонбони"],
               "alternatives":"Сок от цвекло, антоцианини"},
    "E122":  {"name":"Азорубин","category":"Оцветител","risk_level":"high","risk_score":7,
               "description":"Червен синтетичен оцветител.",
               "health_risks":["Алергии","Хиперактивност","Астма"],
               "banned_in":["САЩ","Япония"],"found_in":["Бонбони","Мармалади"],
               "alternatives":"Сок от цвекло"},
    "E123":  {"name":"Амарант","category":"Оцветител","risk_level":"high","risk_score":9,
               "description":"Забранен в много страни заради канцерогенност.",
               "health_risks":["Потенциално канцерогенен","Алергии","Тератогенност"],
               "banned_in":["САЩ","Русия","Норвегия"],"found_in":["Хайвер"],
               "alternatives":"Сок от цвекло"},
    "E124":  {"name":"Понсо 4R","category":"Оцветител","risk_level":"high","risk_score":7,
               "description":"Синтетичен червен оцветител.",
               "health_risks":["Хиперактивност","Алергии","Потенциална канцерогенност"],
               "banned_in":["САЩ","Норвегия"],"found_in":["Колбаси","Сладолед"],
               "alternatives":"Сок от нар"},
    "E129":  {"name":"Алура червено AC","category":"Оцветител","risk_level":"medium-high","risk_score":6,
               "description":"Широко използван червен оцветител.",
               "health_risks":["Хиперактивност","Алергии","Мигрена"],
               "banned_in":[],"found_in":["Газирани напитки","Сладкиши"],
               "alternatives":"Сок от ягоди"},
    "E131":  {"name":"Патентно синьо V","category":"Оцветител","risk_level":"high","risk_score":7,
               "description":"Синтетичен син оцветител.",
               "health_risks":["Алергии","Анафилактичен шок","Гадене"],
               "banned_in":["САЩ","Австралия"],"found_in":["Сладолед"],
               "alternatives":"Спирулина"},
    "E150d": {"name":"Карамел IV (сулфитно-амониев)","category":"Оцветител","risk_level":"medium-high","risk_score":6,
               "description":"Произвежда се с амониеви и сулфитни съединения. Съдържа 4-MEI.",
               "health_risks":["Потенциален канцероген (4-MEI)","Намалява левкоцити","Алергии"],
               "banned_in":[],"found_in":["Кола напитки","Соев сос","Бира"],
               "alternatives":"Натурален карамел E150a"},
    "E160a": {"name":"Бета-каротин","category":"Оцветител","risk_level":"low-medium","risk_score":2,
               "description":"Жълто-оранжев оцветител. Като цяло безопасен.",
               "health_risks":["Високите дози при пушачи → риск от рак на белия дроб"],
               "banned_in":[],"found_in":["Маргарин","Сирена","Сладолед"],
               "alternatives":"Натурален бета-каротин от моркови"},
    "E163":  {"name":"Антоцианини","category":"Оцветител","risk_level":"low","risk_score":1,
               "description":"Натурален лилав/червен оцветител от плодове.",
               "health_risks":["Много редки алергии"],
               "banned_in":[],"found_in":["Сокове","Конфитюри"],
               "alternatives":"Самият е натурална алтернатива"},
    # ── КОНСЕРВАНТИ ─────────────────────────────────────────────────────
    "E211":  {"name":"Натриев бензоат","category":"Консервант","risk_level":"medium-high","risk_score":6,
               "description":"С витамин C образува бензен (канцероген).",
               "health_risks":["Образува бензен с вит.C","Хиперактивност","Астма"],
               "banned_in":[],"found_in":["Газирани напитки","Кетчуп","Майонеза"],
               "alternatives":"Витамин E, розмаринов екстракт"},
    "E220":  {"name":"Серен диоксид","category":"Консервант","risk_level":"medium","risk_score":5,
               "description":"Опасен за астматици.",
               "health_risks":["Астматични пристъпи","Главоболие","Разрушава B1"],
               "banned_in":[],"found_in":["Вино","Сушени плодове","Бира"],
               "alternatives":"Аскорбинова киселина"},
    "E249":  {"name":"Калиев нитрит","category":"Консервант","risk_level":"high","risk_score":8,
               "description":"Образува нитрозамини — силни канцерогени.",
               "health_risks":["Нитрозамини (канцерогени)","Метхемоглобинемия"],
               "banned_in":[],"found_in":["Колбаси","Бекон"],
               "alternatives":"Целина, натурални нитрати"},
    "E250":  {"name":"Натриев нитрит","category":"Консервант","risk_level":"high","risk_score":8,
               "description":"Канцероген при висока температура.",
               "health_risks":["Рак на дебелото черво","Нитрозамини","Главоболие"],
               "banned_in":[],"found_in":["Наденица","Бекон","Шунка"],
               "alternatives":"Ферментирали зеленчуци"},
    "E251":  {"name":"Натриев нитрат","category":"Консервант","risk_level":"medium-high","risk_score":7,
               "description":"Превръща се в нитрит в тялото.",
               "health_risks":["→ нитрити в тялото","Нитрозамини","Риск за деца"],
               "banned_in":[],"found_in":["Сушени меса","Пушена риба"],
               "alternatives":"Аскорбинова киселина"},
    # ── УСИЛВАТЕЛИ НА ВКУС ──────────────────────────────────────────────
    "E621":  {"name":"Мононатриев глутамат (MSG)","category":"Усилвател на вкус","risk_level":"medium-high","risk_score":6,
               "description":"Спорен усилвател — 'Китайски ресторант синдром'.",
               "health_risks":["Главоболие","Изпотяване","Гадене","Хиперактивност"],
               "banned_in":[],"found_in":["Чипс","Бързо хранене","Супени кубчета"],
               "alternatives":"Дрожди, пармезан, доматена паста"},
    "E622":  {"name":"Монокалиев глутамат","category":"Усилвател на вкус","risk_level":"medium","risk_score":5,
               "description":"Аналог на MSG.",
               "health_risks":["Главоболие","Алергии","Гадене"],
               "banned_in":[],"found_in":["Подправки","Чипс"],
               "alternatives":"Натурални подправки"},
    # ── ПОДСЛАДИТЕЛИ ────────────────────────────────────────────────────
    "E950":  {"name":"Ацесулфам К","category":"Подсладител","risk_level":"medium","risk_score":5,
               "description":"Синтетичен подсладител — нарушава чревната микробиота.",
               "health_risks":["Нарушава микробиота","Инсулинов отговор"],
               "banned_in":[],"found_in":["Диетични продукти","Напитки без захар"],
               "alternatives":"Стевия, монк фрут"},
    "E951":  {"name":"Аспартам","category":"Подсладител","risk_level":"medium-high","risk_score":7,
               "description":"Класифициран като 'вероятно канцерогенен' от СЗО (2023).",
               "health_risks":["Вероятно канцерогенен (IARC 2B)","Мигрена","Противопоказан при ФКУ"],
               "banned_in":[],"found_in":["Диетични напитки","Дъвки","Йогурт"],
               "alternatives":"Стевия (E960), еритритол"},
    "E952":  {"name":"Цикламова киселина","category":"Подсладител","risk_level":"high","risk_score":8,
               "description":"Забранен в много страни.",
               "health_risks":["Потенциално канцерогенен","Нарушава микробиота"],
               "banned_in":["САЩ","Великобритания"],"found_in":["Диетични напитки"],
               "alternatives":"Стевия"},
    # ── АНТИОКСИДАНТИ ───────────────────────────────────────────────────
    "E300":  {"name":"Аскорбинова киселина (Вит. C)","category":"Антиоксидант","risk_level":"low","risk_score":1,
               "description":"Витамин C — естествен антиоксидант. Безопасен.",
               "health_risks":["Диария при много висока доза"],
               "banned_in":[],"found_in":["Колбаси","Сокове"],
               "alternatives":"Натурален витамин C"},
    "E320":  {"name":"Бутилхидроксианизол (BHA)","category":"Антиоксидант","risk_level":"high","risk_score":8,
               "description":"Потенциален карциноген (IARC 2B).",
               "health_risks":["Потенциално канцерогенен","Ендокринен дисраптор","Алергии"],
               "banned_in":["Япония"],"found_in":["Чипс","Бисквити"],
               "alternatives":"Витамин E, розмаринов екстракт"},
    "E321":  {"name":"Бутилхидрокситолуен (BHT)","category":"Антиоксидант","risk_level":"medium-high","risk_score":6,
               "description":"Синтетичен антиоксидант.",
               "health_risks":["Потенциален канцероген","Ендокринни ефекти"],
               "banned_in":[],"found_in":["Зърнени закуски","Жвакчета"],
               "alternatives":"Витамин E"},
    # ── РЕГУЛАТОРИ НА КИСЕЛИННОСТ ────────────────────────────────────────
    "E330":  {"name":"Лимонена киселина","category":"Регулатор на киселинност","risk_level":"low-medium","risk_score":2,
               "description":"Естествена киселина — разяжда зъбния емайл.",
               "health_risks":["Разяжда зъбен емайл","Стомашни проблеми"],
               "banned_in":[],"found_in":["Газирани напитки","Чипс","Конфитюри"],
               "alternatives":"Натурален лимонов сок"},
    "E338":  {"name":"Фосфорна киселина","category":"Регулатор на киселинност","risk_level":"medium-high","risk_score":6,
               "description":"Разяжда зъбния емайл и нарушава калций-фосфорния баланс.",
               "health_risks":["Разяжда зъбен емайл","Нарушава усвояването на калций","Остеопороза"],
               "banned_in":[],"found_in":["Кола напитки","Газирани напитки"],
               "alternatives":"Лимонена киселина, вода"},
    # ── ЕМУЛГАТОРИ / СТАБИЛИЗАТОРИ ────────────────────────────────────────
    "E407":  {"name":"Карагенан","category":"Сгъстител","risk_level":"medium","risk_score":5,
               "description":"Може да причини чревно възпаление.",
               "health_risks":["Чревно възпаление","Синдром на раздразненото черво"],
               "banned_in":[],"found_in":["Млечни продукти","Готови меса"],
               "alternatives":"Гуар гума (E412)"},
    "E450":  {"name":"Дифосфати","category":"Регулатор на киселинност","risk_level":"medium","risk_score":5,
               "description":"Нарушава калций-фосфорния баланс.",
               "health_risks":["Нарушава усвояването на калций","Остеопороза","Бъбречни проблеми"],
               "banned_in":[],"found_in":["Преработени меса","Топени сирена"],
               "alternatives":"Лимонена киселина"},
    "E471":  {"name":"Моно- и диглицериди","category":"Емулгатор","risk_level":"medium","risk_score":4,
               "description":"Може да съдържа транс-мазнини.",
               "health_risks":["Потенциални транс-мазнини","Сърдечно-съдови рискове"],
               "banned_in":[],"found_in":["Маргарин","Хляб","Сладолед"],
               "alternatives":"Лецитин от слънчоглед"},
    "E476":  {"name":"PGPR","category":"Емулгатор","risk_level":"low-medium","risk_score":3,
               "description":"Замества какаово масло в шоколада.",
               "health_risks":["Слабо изследван","Потенциални алергии"],
               "banned_in":[],"found_in":["Шоколад"],
               "alternatives":"Истинско какаово масло"},
}

RISK_COLORS = {
    "high":        "#FF3B30",
    "medium-high": "#FF6B35",
    "medium":      "#FF9F1C",
    "low-medium":  "#FFBE0B",
    "low":         "#4CAF50",
}
RISK_LABELS = {
    "high":        "⛔ Много вреден",
    "medium-high": "🔴 Вреден",
    "medium":      "🟡 Умерено вреден",
    "low-medium":  "🟢 Ниска опасност",
    "low":         "✅ Безопасен",
}


def find_additives_in_text(text: str) -> list:
    """
    Открива E-числа в текст.
    Поддържа: E621, (E621), E-621, e621, E 621, E160a, E150d и др.
    """
    if not text:
        return []
    # Премахваме скоби и нормализираме към горен регистър
    normalized = re.sub(r'[()]', ' ', text.upper())
    found = []
    for code, data in HARMFUL_ADDITIVES.items():
        # Разделяме на числова и буквена (суфикс) части
        m = re.match(r'E(\d+)([A-Z]?)', code.upper())
        if not m:
            continue
        digits, suffix = m.group(1), m.group(2)
        # Строим pattern: E + незадължително тире/интервал + числа + суфикс
        if suffix:
            pattern = rf'\bE[-\s]?{digits}{suffix}\b'
        else:
            # Без суфикс — уверяваме се, че след числата няма буква (за да не мачне E160 към E160a)
            pattern = rf'\bE[-\s]?{digits}(?![A-Z0-9])'
        if re.search(pattern, normalized):
            found.append({"code": code, **data})
    return found


def get_overall_risk_score(additives: list) -> dict:
    if not additives:
        return {"score": 0, "label": "✅ Без известни вредни добавки", "color": "#4CAF50"}
    max_s = max(a["risk_score"] for a in additives)
    avg_s = sum(a["risk_score"] for a in additives) / len(additives)
    combined = max_s * 0.6 + avg_s * 0.4
    if combined >= 7:
        return {"score": combined, "label": "⛔ Много вредни добавки", "color": "#FF3B30"}
    elif combined >= 5:
        return {"score": combined, "label": "🔴 Вредни добавки",      "color": "#FF6B35"}
    elif combined >= 3:
        return {"score": combined, "label": "🟡 Умерено вредни",       "color": "#FF9F1C"}
    return {"score": combined, "label": "🟢 Ниско рискови",           "color": "#4CAF50"}
