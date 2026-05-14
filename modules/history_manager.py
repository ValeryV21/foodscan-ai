"""История на сканирани продукти."""
import json
from datetime import datetime

def initialize_history(ss):
    if "scan_history" not in ss: ss.scan_history = []

def add_to_history(ss, product_data: dict, analysis: dict):
    initialize_history(ss)
    entry = {
        "timestamp":      datetime.now().isoformat(),
        "product_name":   product_data.get("name","?"),
        "brand":          product_data.get("brand",""),
        "emoji":          product_data.get("image_emoji","🍽️"),
        "health_score":   analysis["health_score"]["score"],
        "health_label":   analysis["health_score"]["label"],
        "health_color":   analysis["health_score"]["color"],
        "calories":       product_data.get("nutrition",{}).get("calories",0),
        "additives_count":analysis["additives"]["count"],
        "barcode":        product_data.get("barcode",""),
    }
    if ss.scan_history and ss.scan_history[0]["product_name"] == entry["product_name"]:
        ss.scan_history[0] = entry
    else:
        ss.scan_history.insert(0, entry)
    ss.scan_history = ss.scan_history[:20]

def get_history(ss):
    initialize_history(ss); return ss.scan_history

def clear_history(ss):
    ss.scan_history = []

def get_history_stats(ss) -> dict:
    h = get_history(ss)
    if not h: return {}
    scores = [x["health_score"] for x in h]
    return {
        "total_scanned":  len(h),
        "avg_health_score": round(sum(scores)/len(scores),1),
        "worst_product":  max(h, key=lambda x:x["health_score"])["product_name"],
        "best_product":   min(h, key=lambda x:x["health_score"])["product_name"],
        "high_risk_count":sum(1 for x in h if x["health_score"]>=7),
    }

def export_history_json(ss) -> str:
    return json.dumps(get_history(ss), ensure_ascii=False, indent=2)
