"""Баркод сканиране — pyzbar → OpenCV."""
import re, requests
from PIL import Image

try:
    from pyzbar import pyzbar
    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False

try:
    import cv2, numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False


def scan_barcode(image: Image.Image) -> dict:
    result = {"found":False,"barcode":None,"barcode_type":None,"method":None}

    if PYZBAR_AVAILABLE:
        try:
            codes = pyzbar.decode(image) or pyzbar.decode(image.convert("L"))
            if codes:
                bc = codes[0]
                result.update(found=True, barcode=bc.data.decode().strip(),
                              barcode_type=bc.type, method="pyzbar")
                return result
        except Exception as e:
            print("pyzbar:", e)

    if OPENCV_AVAILABLE:
        try:
            arr  = np.array(image.convert("RGB"))
            gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
            # QR
            qr = cv2.QRCodeDetector()
            data, *_ = qr.detectAndDecode(gray)
            if data:
                result.update(found=True, barcode=data.strip(), barcode_type="QR_CODE", method="opencv_qr")
                return result
            # BarcodeDetector (opencv 4.8+)
            try:
                bd = cv2.barcode.BarcodeDetector()
                ok, decoded, types, _ = bd.detectAndDecodeWithType(gray)
                if ok:
                    for d, t in zip(decoded, types):
                        if d:
                            result.update(found=True, barcode=d.strip(), barcode_type=t, method="opencv_bd")
                            return result
            except Exception:
                pass
        except Exception as e:
            print("OpenCV:", e)

    return result


def fetch_openfoodfacts(barcode: str) -> dict | None:
    barcode = re.sub(r'\D', '', barcode)
    if not barcode:
        return None
    try:
        r = requests.get(
            f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json",
            headers={"User-Agent":"FoodScanAI/2.0"}, timeout=8)
        if r.status_code != 200: return None
        d = r.json()
        if d.get("status") != 1: return None
        p = d["product"]
        nm = p.get("nutriments", {})
        def g(k): 
            v = nm.get(k, 0)
            try: return float(v) if v else 0.0
            except: return 0.0
        nutrition = {
            "calories":g("energy-kcal_100g"),"protein":g("proteins_100g"),
            "carbs":g("carbohydrates_100g"),"sugars":g("sugars_100g"),
            "fat":g("fat_100g"),"saturated_fat":g("saturated-fat_100g"),
            "salt":g("salt_100g"),"fiber":g("fiber_100g"),
        }
        if not nutrition["calories"] and (nutrition["protein"] or nutrition["fat"]):
            nutrition["calories"] = round(nutrition["protein"]*4+nutrition["carbs"]*4+nutrition["fat"]*9,1)
        return {
            "name": p.get("product_name_bg") or p.get("product_name_en") or p.get("product_name","Неизвестен"),
            "brand": p.get("brands",""),"category": p.get("categories",""),
            "image_emoji":"🏷️","ingredients": p.get("ingredients_text_bg") or p.get("ingredients_text",""),
            "nutrition": nutrition, "allergens": p.get("allergens_tags",[]),
            "nutriscore": p.get("nutriscore_grade","").upper(),
            "image_url": p.get("image_url",""), "source":"Open Food Facts",
            "alternatives":[], "health_risks":{"obesity":"medium","diabetes":"medium","heart":"medium","blood_pressure":"medium"},
        }
    except Exception as e:
        print("OFF:", e)
    return None


def get_barcode_info() -> dict:
    return {"pyzbar":PYZBAR_AVAILABLE,"opencv":OPENCV_AVAILABLE,"any_available":PYZBAR_AVAILABLE or OPENCV_AVAILABLE}


DEMO_BARCODES = {
    "5900259128095":"Lay's Паприка","4000521004972":"Haribo Goldbären",
    "5449000000996":"Coca-Cola Класик","5449000133328":"Coca-Cola Zero",
    "3017760000000":"Луканка Стара Загора","7613034626844":"Nestlé Fitness",
    "8076800195057":"Barilla Спагети №5",
}
