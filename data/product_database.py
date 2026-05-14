"""База данни с демо продукти."""

MOCK_PRODUCTS = {
    "5900259128095": {
        "name":"Lay's Паприка","brand":"Lay's","category":"Чипс","image_emoji":"🥔",
        "ingredients":"Картофи, слънчогледово масло, сол, паприка (2%), захар, лимонена киселина (E330), натриев глутамат (E621), екстракт от паприка.",
        "nutrition":{"calories":536,"protein":7.0,"carbs":52.0,"sugars":2.0,"fat":34.0,"saturated_fat":3.5,"salt":1.5,"fiber":4.4},
        "allergens":[],"alternatives":["Печени ядки","Оризови гризини","Печен нахут"],
        "health_risks":{"obesity":"high","diabetes":"medium","heart":"high","blood_pressure":"high"}},
    "4000521004972": {
        "name":"Haribo Goldbären","brand":"Haribo","category":"Бонбони","image_emoji":"🐻",
        "ingredients":"Захарен сироп, захар, желатин, декстроза, аромат, лимонена киселина (E330), концентрирани сокове, оцветители: E120, E160a, E163.",
        "nutrition":{"calories":343,"protein":6.9,"carbs":77.0,"sugars":46.0,"fat":0.5,"saturated_fat":0.2,"salt":0.04,"fiber":0.2},
        "allergens":[],"alternatives":["Пресни плодове","Сушени плодове без захар"],
        "health_risks":{"obesity":"high","diabetes":"high","heart":"medium","blood_pressure":"low"}},
    "5449000000996": {
        "name":"Coca-Cola Класик","brand":"Coca-Cola","category":"Газирани напитки","image_emoji":"🥤",
        "ingredients":"Вода, захарен сироп от глюкоза-фруктоза, захар, CO2, оцветител (E150d), фосфорна киселина (E338), натурален аромат, кофеин.",
        "nutrition":{"calories":42,"protein":0,"carbs":10.6,"sugars":10.6,"fat":0,"saturated_fat":0,"salt":0.01,"fiber":0},
        "allergens":[],"alternatives":["Минерална вода с лимон","Домашна лимонада без захар"],
        "health_risks":{"obesity":"high","diabetes":"high","heart":"medium","blood_pressure":"medium"}},
    "5449000133328": {
        "name":"Coca-Cola Zero","brand":"Coca-Cola","category":"Напитки без захар","image_emoji":"🥤",
        "ingredients":"Вода, CO2, оцветител (E150d), фосфорна киселина (E338), подсладители: аспартам (E951), ацесулфам К (E950), натурален аромат, кофеин.",
        "nutrition":{"calories":0.4,"protein":0,"carbs":0.1,"sugars":0,"fat":0,"saturated_fat":0,"salt":0.04,"fiber":0},
        "allergens":[],"alternatives":["Минерална вода","Чай без захар"],
        "health_risks":{"obesity":"low","diabetes":"medium","heart":"low","blood_pressure":"low"}},
    "3017760000000": {
        "name":"Луканка Стара Загора","brand":"Месокомбинат","category":"Колбаси","image_emoji":"🥩",
        "ingredients":"Свинско месо 60%, телешко 20%, сланина, сол, подправки, нишесте, натриев нитрит (E250), натриев нитрат (E251), аскорбинова киселина (E300), чесън, черен пипер.",
        "nutrition":{"calories":420,"protein":25.0,"carbs":2.0,"sugars":0.5,"fat":35.0,"saturated_fat":14.0,"salt":3.5,"fiber":0},
        "allergens":["Глутен"],"alternatives":["Домашно месо","Пуешко без нитрити"],
        "health_risks":{"obesity":"medium","diabetes":"low","heart":"high","blood_pressure":"high"}},
    "7613034626844": {
        "name":"Nestlé Fitness","brand":"Nestlé","category":"Зърнени закуски","image_emoji":"🥣",
        "ingredients":"Пълнозърнеста пшеница 62%, захар, малцов екстракт, сол, витамини B.",
        "nutrition":{"calories":373,"protein":10.0,"carbs":75.0,"sugars":13.0,"fat":2.8,"saturated_fat":0.5,"salt":0.8,"fiber":9.0},
        "allergens":["Глутен"],"alternatives":["Натурални овесени ядки","Мюсли без захар"],
        "health_risks":{"obesity":"low","diabetes":"medium","heart":"low","blood_pressure":"low"}},
    "8076800195057": {
        "name":"Barilla Спагети №5","brand":"Barilla","category":"Тестени изделия","image_emoji":"🍝",
        "ingredients":"Твърда пшеница (семолина).",
        "nutrition":{"calories":353,"protein":13.0,"carbs":70.0,"sugars":3.5,"fat":1.5,"saturated_fat":0.3,"salt":0.0,"fiber":3.0},
        "allergens":["Глутен"],"alternatives":["Спагети от нахут","Киноа","Пълнозърнести макарони"],
        "health_risks":{"obesity":"low","diabetes":"medium","heart":"low","blood_pressure":"low"}},
}

HEALTH_RISK_INFO = {
    "obesity":{"name":"Затлъстяване","emoji":"⚖️",
               "high":"Много висока калорийност/мазнини — риск от затлъстяване.",
               "medium":"Умерен риск. Препоръчва се ограничена консумация.",
               "low":"Нисък риск при нормална консумация."},
    "diabetes":{"name":"Диабет тип 2","emoji":"🩸",
                "high":"Много захар/прости въглехидрати — бързо вдига кръвната захар.",
                "medium":"Умерен гликемичен индекс. Внимание при предиабет.",
                "low":"Нисък гликемичен ефект."},
    "heart":{"name":"Сърдечни заболявания","emoji":"❤️",
             "high":"Наситени мазнини/трансмазнини → повишен LDL холестерол.",
             "medium":"Умерено влияние върху сърдечно-съдовото здраве.",
             "low":"Минимален риск за сърцето."},
    "blood_pressure":{"name":"Високо кръвно","emoji":"📊",
                      "high":"Много сол — значително повишава кръвното налягане.",
                      "medium":"Умерен натрий. Внимание при хипертония.",
                      "low":"Ниско съдържание на натрий."},
}


def get_product_by_barcode(barcode: str) -> dict | None:
    return MOCK_PRODUCTS.get(barcode)

def get_demo_products() -> list:
    return [{"barcode":k,"name":v["name"],"brand":v["brand"],"emoji":v["image_emoji"]}
            for k, v in MOCK_PRODUCTS.items()]
