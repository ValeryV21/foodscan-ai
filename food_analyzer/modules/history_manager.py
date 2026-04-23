"""
Модул за управление на историята на сканирани продукти.
Използва Streamlit session_state за временно съхранение.
"""

from datetime import datetime
import json


def initialize_history(session_state):
    """Инициализира историята ако не съществува."""
    if "scan_history" not in session_state:
        session_state.scan_history = []


def add_to_history(session_state, product_data: dict, analysis: dict):
    """
    Добавя продукт към историята.
    
    Args:
        session_state: Streamlit session state
        product_data: Данни за продукта
        analysis: Резултати от анализа
    """
    initialize_history(session_state)
    
    history_entry = {
        "timestamp": datetime.now().isoformat(),
        "product_name": product_data.get("name", "Неизвестен продукт"),
        "brand": product_data.get("brand", ""),
        "category": product_data.get("category", ""),
        "emoji": product_data.get("image_emoji", "🍽️"),
        "health_score": analysis["health_score"]["score"],
        "health_label": analysis["health_score"]["label"],
        "health_color": analysis["health_score"]["color"],
        "calories": product_data.get("nutrition", {}).get("calories", 0),
        "additives_count": analysis["additives"]["count"],
        "barcode": product_data.get("barcode", ""),
        "source": product_data.get("source", "unknown")
    }
    
    # Избягваме дублирани записи (последен scan)
    if (session_state.scan_history and 
        session_state.scan_history[0]["product_name"] == history_entry["product_name"] and
        session_state.scan_history[0]["barcode"] == history_entry["barcode"]):
        session_state.scan_history[0] = history_entry
    else:
        # Добавяме в началото (най-новото е отгоре)
        session_state.scan_history.insert(0, history_entry)
    
    # Пазим максимум 20 записа
    session_state.scan_history = session_state.scan_history[:20]


def get_history(session_state) -> list:
    """Връща историята на сканиране."""
    initialize_history(session_state)
    return session_state.scan_history


def clear_history(session_state):
    """Изчиства историята."""
    session_state.scan_history = []


def get_history_stats(session_state) -> dict:
    """Изчислява статистики от историята."""
    history = get_history(session_state)
    
    if not history:
        return {}
    
    scores = [h["health_score"] for h in history]
    
    return {
        "total_scanned": len(history),
        "avg_health_score": round(sum(scores) / len(scores), 1),
        "worst_product": max(history, key=lambda x: x["health_score"])["product_name"],
        "best_product": min(history, key=lambda x: x["health_score"])["product_name"],
        "high_risk_count": sum(1 for h in history if h["health_score"] >= 7)
    }


def export_history_json(session_state) -> str:
    """Експортира историята като JSON."""
    history = get_history(session_state)
    return json.dumps(history, ensure_ascii=False, indent=2)
