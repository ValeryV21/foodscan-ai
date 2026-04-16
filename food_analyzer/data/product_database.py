"""
Примерна база данни с продукти за демонстрация.
Включва популярни продукти с техните съставки и хранителна информация.
"""

MOCK_PRODUCTS = {
    # ===== ЧИПС =====
    "5900259128095": {
        "name": "Lay's Паприка",
        "brand": "Lay's",
        "category": "Чипс/Снаксове",
        "image_emoji": "🥔",
        "ingredients": "Картофи, слънчогледово масло, сол, паприка, захар, лимонена киселина (E330), натриев глутамат (E621), екстракт от паприка",
        "nutrition": {
            "calories": 536,
            "protein": 7.0,
            "carbs": 52.0,
            "sugars": 2.0,
            "fat": 34.0,
            "saturated_fat": 3.5,
            "salt": 1.5,
            "fiber": 4.4
        },
        "allergens": ["Глутен"],
        "health_score": 8,  # 1=здравословно, 10=вредно
        "alternatives": [
            "Печени ядки",
            "Оризови гризини",
            "Печени нахут",
            "Зеленчукови чипс (печен)"
        ],
        "health_risks": {
            "obesity": "high",
            "diabetes": "medium",
            "heart": "high",
            "blood_pressure": "high"
        }
    },
    "4000521004972": {
        "name": "Haribo Goldbären",
        "brand": "Haribo",
        "category": "Бонбони/Желирани",
        "image_emoji": "🐻",
        "ingredients": "Захарен сироп от глюкоза, захар, желатин, декстроза, аромат, лимонена киселина (E330), концентрирани сокове (ябълка, ягода, малина, лимон, портокал, грейпфрут), оцветители: E120, E160a, E163",
        "nutrition": {
            "calories": 343,
            "protein": 6.9,
            "carbs": 77.0,
            "sugars": 46.0,
            "fat": 0.5,
            "saturated_fat": 0.2,
            "salt": 0.04,
            "fiber": 0.2
        },
        "allergens": [],
        "health_score": 7,
        "alternatives": [
            "Пресни плодове",
            "Сушени плодове (без добавена захар)",
            "Натурален желатин с плодов сок"
        ],
        "health_risks": {
            "obesity": "high",
            "diabetes": "high",
            "heart": "medium",
            "blood_pressure": "low"
        }
    },
    # ===== ГАЗИРАНИ НАПИТКИ =====
    "5449000000996": {
        "name": "Coca-Cola Класик",
        "brand": "Coca-Cola",
        "category": "Газирани напитки",
        "image_emoji": "🥤",
        "ingredients": "Вода, захарен сироп от глюкоза-фруктоза, захар, въглероден диоксид, оцветител (E150d карамел IV), фосфорна киселина (E338), натурален аромат, кофеин",
        "nutrition": {
            "calories": 42,
            "protein": 0,
            "carbs": 10.6,
            "sugars": 10.6,
            "fat": 0,
            "saturated_fat": 0,
            "salt": 0.01,
            "fiber": 0
        },
        "allergens": [],
        "health_score": 8,
        "alternatives": [
            "Минерална вода с лимон",
            "Домашна лимонада без захар",
            "Натурален плодов сок (разреден)"
        ],
        "health_risks": {
            "obesity": "high",
            "diabetes": "high",
            "heart": "medium",
            "blood_pressure": "medium"
        }
    },
    "5449000133328": {
        "name": "Coca-Cola Zero",
        "brand": "Coca-Cola",
        "category": "Газирани напитки без захар",
        "image_emoji": "🥤",
        "ingredients": "Вода, въглероден диоксид, оцветител (E150d), фосфорна киселина (E338), подсладители: аспартам (E951), ацесулфам К (E950), натурален аромат, кофеин",
        "nutrition": {
            "calories": 0.4,
            "protein": 0,
            "carbs": 0.1,
            "sugars": 0,
            "fat": 0,
            "saturated_fat": 0,
            "salt": 0.04,
            "fiber": 0
        },
        "allergens": [],
        "health_score": 6,
        "alternatives": [
            "Минерална вода",
            "Чай без захар",
            "Натурална газирана вода"
        ],
        "health_risks": {
            "obesity": "low",
            "diabetes": "medium",
            "heart": "low",
            "blood_pressure": "low"
        }
    },
    # ===== МЕСНИ ПРОДУКТИ =====
    "3017760000000": {
        "name": "Луканка Стара Загора",
        "brand": "Месокомбинат",
        "category": "Колбаси/Месни преработки",
        "image_emoji": "🥩",
        "ingredients": "Свинско месо 60%, телешко 20%, сланина, сол, подправки, нишесте, натриев нитрит (E250), натриев нитрат (E251), аскорбинова киселина (E300), чесън, черен пипер",
        "nutrition": {
            "calories": 420,
            "protein": 25.0,
            "carbs": 2.0,
            "sugars": 0.5,
            "fat": 35.0,
            "saturated_fat": 14.0,
            "salt": 3.5,
            "fiber": 0
        },
        "allergens": ["Глутен"],
        "health_score": 8,
        "alternatives": [
            "Домашно приготвено месо",
            "Пуешко без нитрити",
            "Домашна наденица"
        ],
        "health_risks": {
            "obesity": "medium",
            "diabetes": "low",
            "heart": "high",
            "blood_pressure": "high"
        }
    },
    # ===== ЗДРАВОСЛОВНИ ПРОДУКТИ =====
    "7613034626844": {
        "name": "Nestlé Fitness Оригинал",
        "brand": "Nestlé",
        "category": "Зърнени закуски",
        "image_emoji": "🥣",
        "ingredients": "Пълнозърнеста пшеница 62%, захар, малцов екстракт от ечемик, сол, ниацин, пантотенова киселина, рибофлавин, витамин B6, тиамин, фолиева киселина, витамин B12",
        "nutrition": {
            "calories": 373,
            "protein": 10.0,
            "carbs": 75.0,
            "sugars": 13.0,
            "fat": 2.8,
            "saturated_fat": 0.5,
            "salt": 0.8,
            "fiber": 9.0
        },
        "allergens": ["Глутен"],
        "health_score": 4,
        "alternatives": [
            "Овесени ядки (натурални)",
            "Без захар мюсли",
            "Пълнозърнести ядки"
        ],
        "health_risks": {
            "obesity": "low",
            "diabetes": "medium",
            "heart": "low",
            "blood_pressure": "low"
        }
    },
    "8076800195057": {
        "name": "Barilla Спагети №5",
        "brand": "Barilla",
        "category": "Тестени изделия",
        "image_emoji": "🍝",
        "ingredients": "Твърда пшеница (семолина)",
        "nutrition": {
            "calories": 353,
            "protein": 13.0,
            "carbs": 70.0,
            "sugars": 3.5,
            "fat": 1.5,
            "saturated_fat": 0.3,
            "salt": 0.0,
            "fiber": 3.0
        },
        "allergens": ["Глутен"],
        "health_score": 3,
        "alternatives": [
            "Спагети от нахут",
            "Ориз",
            "Киноа",
            "Пълнозърнести макарони"
        ],
        "health_risks": {
            "obesity": "low",
            "diabetes": "medium",
            "heart": "low",
            "blood_pressure": "low"
        }
    },
}

# Здравни рискове - описания
HEALTH_RISK_INFO = {
    "obesity": {
        "name": "Затлъстяване",
        "emoji": "⚖️",
        "high": "Продуктът е с много висока калорийност и мазнини, редовната консумация повишава риска от затлъстяване значително.",
        "medium": "Умерен риск от затлъстяване. Препоръчва се ограничена консумация.",
        "low": "Нисък риск от затлъстяване при нормална консумация."
    },
    "diabetes": {
        "name": "Диабет тип 2",
        "emoji": "🩸",
        "high": "Съдържа много захар и прости въглехидрати, което бързо повишава кръвната захар. Висок риск при диабетици.",
        "medium": "Умерен гликемичен индекс. Внимание при предиабет и диабет.",
        "low": "Нисък гликемичен ефект. Подходящ при диабет (в умерени количества)."
    },
    "heart": {
        "name": "Сърдечни заболявания",
        "emoji": "❤️",
        "high": "Съдържа наситени мазнини и/или трансмазнини, което повишава LDL холестерола и риска от инфаркт.",
        "medium": "Умерено влияние върху сърдечно-съдовото здраве.",
        "low": "Минимален риск за сърцето."
    },
    "blood_pressure": {
        "name": "Високо кръвно",
        "emoji": "📊",
        "high": "Много високо съдържание на сол/натрий. Редовната консумация значително повишава кръвното налягане.",
        "medium": "Умерено съдържание на натрий. Внимание при хипертония.",
        "low": "Ниско съдържание на натрий. Безопасно при хипертония."
    }
}


def get_product_by_barcode(barcode: str) -> dict | None:
    """Търси продукт по баркод в демо базата данни."""
    return MOCK_PRODUCTS.get(barcode)


def get_demo_products() -> list:
    """Връща списък с демо продукти за тестване."""
    return [
        {"barcode": code, "name": data["name"], "brand": data["brand"], "emoji": data["image_emoji"]}
        for code, data in MOCK_PRODUCTS.items()
    ]
