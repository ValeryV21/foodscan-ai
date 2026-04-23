"""
OCR модул за разпознаване на текст от снимки на хранителни продукти.
Поддържа EasyOCR (препоръчително) и pytesseract (алтернатива).
"""

import re
import io
from PIL import Image, ImageEnhance, ImageFilter

# Опитваме се да импортираме OCR библиотеките
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


def get_ocr_reader():
    """
    Инициализира OCR четец.
    Приоритет: EasyOCR > pytesseract > None
    """
    if EASYOCR_AVAILABLE:
        try:
            reader = easyocr.Reader(['bg', 'en'], gpu=False, verbose=False)
            return reader, "easyocr"
        except Exception as e:
            print(f"EasyOCR грешка: {e}")

    if TESSERACT_AVAILABLE:
        return pytesseract, "tesseract"

    return None, None


def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Подобрява качеството на изображението преди OCR.
    Увеличава контраста и рязкостта за по-добро разпознаване.
    """
    # Конвертираме в RGB ако е нужно
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    # Увеличаваме размера ако е малко (OCR работи по-добре с по-голями изображения)
    min_dimension = 1000
    if image.width < min_dimension or image.height < min_dimension:
        scale = min_dimension / min(image.width, image.height)
        new_w = int(image.width * scale)
        new_h = int(image.height * scale)
        image = image.resize((new_w, new_h), Image.LANCZOS)

    # Повишаваме контраста
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)

    # Повишаваме рязкостта
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2.0)

    return image


def extract_text_from_image(image: Image.Image, reader=None, engine: str = None) -> dict:
    """
    Извлича текст от изображение чрез OCR.

    Returns:
        dict с извлечен текст, метаданни и евентуална грешка
    """
    result = {
        "raw_text": "",
        "confidence": 0.0,
        "engine": engine or "none",
        "success": False,
        "lines": [],
        "error": None,
        "no_ocr_installed": False
    }

    # ---- Няма инсталиран OCR двигател ----
    if reader is None:
        result["success"] = False
        result["no_ocr_installed"] = True
        result["error"] = (
            "Не е намерен OCR двигател. "
            "Инсталирай EasyOCR (`pip install easyocr`) или "
            "pytesseract (`pip install pytesseract` + Tesseract app)."
        )
        return result

    # Предобработка на изображението
    try:
        processed_image = preprocess_image(image)
    except Exception:
        processed_image = image  # Продължаваме с оригинала при грешка

    try:
        if engine == "easyocr":
            import numpy as np
            img_array = np.array(processed_image)
            ocr_results = reader.readtext(img_array)

            texts = []
            confidences = []
            for (bbox, text, conf) in ocr_results:
                if conf > 0.2:  # По-нисък праг за повече резултати
                    texts.append(text.strip())
                    confidences.append(conf)

            raw = '\n'.join(t for t in texts if t)
            result["raw_text"] = raw
            result["lines"] = [t for t in texts if t]
            result["confidence"] = (
                sum(confidences) / len(confidences) if confidences else 0.0
            )
            result["success"] = bool(raw.strip())
            if not result["success"]:
                result["error"] = "OCR не разпозна текст в снимката. Опитай с по-ясна снимка."

        elif engine == "tesseract":
            # Опитваме с различни PSM режими за по-добри резултати
            best_text = ""
            for psm in [6, 3, 11]:
                try:
                    config = f'--oem 3 --psm {psm}'
                    text = reader.image_to_string(processed_image, config=config, lang='eng')
                    if len(text.strip()) > len(best_text.strip()):
                        best_text = text
                except Exception:
                    pass

            result["raw_text"] = best_text
            result["lines"] = [l for l in best_text.split('\n') if l.strip()]
            result["success"] = bool(best_text.strip())
            if not result["success"]:
                result["error"] = "Tesseract не разпозна текст. Опитай с по-ясна снимка."

            # Изчисляваме достоверност
            try:
                data = reader.image_to_data(
                    processed_image, config='--oem 3 --psm 6',
                    output_type=reader.Output.DICT
                )
                confs = [int(c) for c in data['conf'] if str(c) != '-1' and int(c) > 0]
                result["confidence"] = sum(confs) / len(confs) / 100 if confs else 0.0
            except Exception:
                result["confidence"] = 0.5

    except Exception as e:
        result["success"] = False
        result["error"] = f"OCR грешка: {str(e)}"

    return result


def get_ocr_status() -> dict:
    """Връща статус на наличните OCR двигатели."""
    return {
        "easyocr": EASYOCR_AVAILABLE,
        "tesseract": TESSERACT_AVAILABLE,
        "any_available": EASYOCR_AVAILABLE or TESSERACT_AVAILABLE,
        "install_hint": (
            "Инсталирай EasyOCR: pip install easyocr"
            if not EASYOCR_AVAILABLE else ""
        )
    }


def parse_food_label(text: str) -> dict:
    """
    Анализира извлечения текст и структурира данните от хранителния етикет.
    
    Args:
        text: Суров текст от OCR
    
    Returns:
        dict с структурирани данни
    """
    parsed = {
        "product_name": "",
        "ingredients": "",
        "nutrition": {},
        "e_numbers": [],
        "weight": "",
        "brand": ""
    }
    
    text_lines = text.strip().split('\n')
    text_lower = text.lower()
    
    # ---- Намираме съставки ----
    ingredients_patterns = [
        r'(?:съставки|ingredients|состав|zutaten|ingrédients)[:\s]+(.+?)(?:\n\n|\Z)',
        r'(?:съдържа|contains)[:\s]+(.+?)(?:\n\n|\Z)',
    ]
    
    for pattern in ingredients_patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL)
        if match:
            parsed["ingredients"] = match.group(1).strip()[:500]
            break
    
    # ---- Намираме E-числа ----
    e_numbers = re.findall(r'[Ee][-]?\d{3}[a-zA-Z]?', text)
    parsed["e_numbers"] = list(set(e_numbers))
    
    # ---- Намираме тегло/обем ----
    weight_match = re.search(r'(\d+(?:[.,]\d+)?\s*(?:g|ml|kg|л|гр|мл|oz))', text, re.IGNORECASE)
    if weight_match:
        parsed["weight"] = weight_match.group(1)
    
    # ---- Намираме калории ----
    calorie_patterns = [
        r'(?:калории|energy|energie|kcal)[:\s]*(\d+(?:[.,]\d+)?)\s*(?:kcal|кДж)?',
        r'(\d+(?:[.,]\d+)?)\s*kcal',
        r'(\d+(?:[.,]\d+)?)\s*кКал',
    ]
    
    for pattern in calorie_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                parsed["nutrition"]["calories"] = float(match.group(1).replace(',', '.'))
                break
            except ValueError:
                pass
    
    # ---- Мазнини ----
    fat_match = re.search(r'(?:мазнини|total fat|fett|fat)[:\s]*(\d+(?:[.,]\d+)?)\s*g', text, re.IGNORECASE)
    if fat_match:
        try:
            parsed["nutrition"]["fat"] = float(fat_match.group(1).replace(',', '.'))
        except ValueError:
            pass
    
    # ---- Захар ----
    sugar_match = re.search(r'(?:захари|sugars|zucker|sucres)[:\s]*(\d+(?:[.,]\d+)?)\s*g', text, re.IGNORECASE)
    if sugar_match:
        try:
            parsed["nutrition"]["sugars"] = float(sugar_match.group(1).replace(',', '.'))
        except ValueError:
            pass
    
    # ---- Сол/Натрий ----
    salt_match = re.search(r'(?:сол|salt|salz|sel|sodium)[:\s]*(\d+(?:[.,]\d+)?)\s*g', text, re.IGNORECASE)
    if salt_match:
        try:
            parsed["nutrition"]["salt"] = float(salt_match.group(1).replace(',', '.'))
        except ValueError:
            pass
    
    # ---- Протеин ----
    protein_match = re.search(r'(?:протеин|protein|eiweiß)[:\s]*(\d+(?:[.,]\d+)?)\s*g', text, re.IGNORECASE)
    if protein_match:
        try:
            parsed["nutrition"]["protein"] = float(protein_match.group(1).replace(',', '.'))
        except ValueError:
            pass
    
    # ---- Приблизително определяне на продукта ----
    if text_lines:
        # Обикновено първите 2-3 реда съдържат името
        for line in text_lines[:3]:
            if len(line.strip()) > 3 and not any(keyword in line.lower() 
                for keyword in ['съставки', 'ingredients', 'e1', 'e2', 'e3', 'e4', 'e5', 'kcal', 'g ']):
                parsed["product_name"] = line.strip()
                break
    
    return parsed


def _get_demo_ocr_text() -> str:
    """Демонстрационен OCR текст за тестване."""
    return """Lay's Паприка
Картофен чипс с вкус на паприка
NET WT 150g

СЪСТАВКИ: Картофи, слънчогледово масло,
сол, паприка (2%), захар, лимонена киселина (E330),
натриев глутамат (E621), екстракт от паприка.

Хранителна стойност на 100g:
Енергия: 536 kcal / 2241 kJ
Мазнини: 34g
от които наситени: 3.5g
Въглехидрати: 52g
от които захари: 2g
Протеин: 7g
Сол: 1.5g

Да се съхранява на сухо и хладно място.
Произведено от: Lay's Bulgaria ЕООД"""
