"""
Модул за сканиране на баркодове.
Поддържа pyzbar и OpenCV за разчитане на различни видове баркодове.
"""

import io
import requests
from PIL import Image

# Опитваме се да импортираме библиотеките за баркод
try:
    from pyzbar import pyzbar
    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False


def scan_barcode(image: Image.Image) -> dict:
    """
    Сканира баркод от изображение.
    
    Args:
        image: PIL Image обект
    
    Returns:
        dict с данни от баркода
    """
    result = {
        "found": False,
        "barcode": None,
        "barcode_type": None,
        "method": None,
        "raw_data": None
    }
    
    # Метод 1: pyzbar (препоръчително)
    if PYZBAR_AVAILABLE:
        try:
            barcodes = pyzbar.decode(image)
            if barcodes:
                barcode = barcodes[0]
                result["found"] = True
                result["barcode"] = barcode.data.decode('utf-8')
                result["barcode_type"] = barcode.type
                result["method"] = "pyzbar"
                result["raw_data"] = {
                    "rect": barcode.rect,
                    "polygon": str(barcode.polygon)
                }
                return result
        except Exception as e:
            print(f"pyzbar грешка: {e}")
    
    # Метод 2: OpenCV QR детектор
    if OPENCV_AVAILABLE:
        try:
            img_array = np.array(image)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # QR Code
            qr_detector = cv2.QRCodeDetector()
            data, bbox, _ = qr_detector.detectAndDecode(gray)
            
            if data:
                result["found"] = True
                result["barcode"] = data
                result["barcode_type"] = "QR_CODE"
                result["method"] = "opencv"
                return result
        except Exception as e:
            print(f"OpenCV грешка: {e}")
    
    return result


def fetch_openfoodfacts(barcode: str) -> dict | None:
    """
    Извлича данни за продукт от Open Food Facts API.
    
    Args:
        barcode: EAN/UPC баркод
    
    Returns:
        dict с данни за продукта или None
    """
    try:
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        headers = {
            "User-Agent": "FoodAnalyzer/1.0 - Educational App"
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("status") == 1:  # Продуктът е намерен
                product = data.get("product", {})
                
                return {
                    "name": product.get("product_name", "Неизвестно"),
                    "brand": product.get("brands", "Неизвестно"),
                    "ingredients": product.get("ingredients_text", ""),
                    "nutrition": _parse_off_nutrition(product.get("nutriments", {})),
                    "categories": product.get("categories", ""),
                    "image_url": product.get("image_url", ""),
                    "nutriscore": product.get("nutriscore_grade", "").upper(),
                    "ecoscore": product.get("ecoscore_grade", "").upper(),
                    "allergens": product.get("allergens", ""),
                    "source": "Open Food Facts"
                }
    except requests.RequestException:
        pass
    except Exception as e:
        print(f"Open Food Facts грешка: {e}")
    
    return None


def _parse_off_nutrition(nutriments: dict) -> dict:
    """
    Парсира хранителните данни от Open Food Facts формат.
    """
    def safe_float(key):
        val = nutriments.get(key, 0)
        try:
            return float(val)
        except (TypeError, ValueError):
            return 0.0
    
    return {
        "calories": safe_float("energy-kcal_100g"),
        "protein": safe_float("proteins_100g"),
        "carbs": safe_float("carbohydrates_100g"),
        "sugars": safe_float("sugars_100g"),
        "fat": safe_float("fat_100g"),
        "saturated_fat": safe_float("saturated-fat_100g"),
        "salt": safe_float("salt_100g"),
        "fiber": safe_float("fiber_100g"),
        "sodium": safe_float("sodium_100g")
    }


def get_barcode_info() -> dict:
    """
    Връща информация за наличните библиотеки за баркод.
    """
    return {
        "pyzbar": PYZBAR_AVAILABLE,
        "opencv": OPENCV_AVAILABLE,
        "any_available": PYZBAR_AVAILABLE or OPENCV_AVAILABLE
    }


# Демо баркодове за тестване
DEMO_BARCODES = {
    "5900259128095": "Lay's Паприка",
    "4000521004972": "Haribo Goldbären",
    "5449000000996": "Coca-Cola Класик",
    "5449000133328": "Coca-Cola Zero",
    "3017760000000": "Луканка Стара Загора",
    "7613034626844": "Nestlé Fitness",
    "8076800195057": "Barilla Спагети №5",
}
