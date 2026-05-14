"""
OCR модул — EasyOCR (основен) с NumPy предобработка и Claude Vision резервен вариант.
"""

import re
import io
import base64
import requests
from PIL import Image, ImageEnhance, ImageFilter

try:
    import numpy as np
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# Глобален reader — зареждаме веднъж
_reader_cache = None


def get_ocr_reader():
    """Инициализира и кешира EasyOCR reader (bg + en)."""
    global _reader_cache
    if not EASYOCR_AVAILABLE:
        return None, None
    if _reader_cache is None:
        try:
            _reader_cache = easyocr.Reader(
                ['bg', 'en'],
                gpu=False,
                verbose=False,
                model_storage_directory=None,   # default ~/.EasyOCR/
            )
        except Exception as e:
            print(f"EasyOCR init грешка: {e}")
            return None, None
    return _reader_cache, "easyocr"


def get_ocr_status() -> dict:
    return {
        "easyocr":     EASYOCR_AVAILABLE,
        "tesseract":   TESSERACT_AVAILABLE,
        "any_available": EASYOCR_AVAILABLE or TESSERACT_AVAILABLE,
    }


# ── NumPy предобработка ────────────────────────────────────────────────
def preprocess_for_ocr(image: Image.Image) -> "np.ndarray":
    """
    Предобработва изображение с NumPy за по-добър OCR.
    Стъпки: resize → grayscale → contrast → sharpen → adaptive threshold.
    """
    import numpy as np

    # 1. Преоразмеряване — OCR работи по-добре с >= 1200px по ширина
    w, h = image.size
    if w < 1200:
        scale = 1200 / w
        image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    # 2. Конвертиране в RGB
    img_rgb = image.convert("RGB")
    arr = np.array(img_rgb, dtype=np.float32)

    # 3. Нормализация и подобряване на контраста (NumPy)
    arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-6) * 255
    arr = arr.clip(0, 255).astype(np.uint8)

    # 4. Sharpen kernel (NumPy convolution)
    from numpy.lib.stride_tricks import as_strided
    kernel = np.array([
        [ 0, -0.5,  0],
        [-0.5,  3, -0.5],
        [ 0, -0.5,  0],
    ], dtype=np.float32)
    # Прилагаме по всеки канал поотделно
    sharpened = np.zeros_like(arr, dtype=np.float32)
    for c in range(3):
        ch = arr[:, :, c].astype(np.float32)
        # Padding
        pad = np.pad(ch, 1, mode='edge')
        # Ръчна 2D конволюция (3×3)
        out = np.zeros_like(ch)
        for i in range(3):
            for j in range(3):
                out += kernel[i, j] * pad[i:i+ch.shape[0], j:j+ch.shape[1]]
        sharpened[:, :, c] = out
    sharpened = sharpened.clip(0, 255).astype(np.uint8)

    return sharpened   # numpy array (H, W, 3) — EasyOCR приема директно


def extract_text_easyocr(image: Image.Image, reader) -> dict:
    """Разпознава текст с EasyOCR + NumPy предобработка."""
    import numpy as np

    try:
        arr = preprocess_for_ocr(image)
    except Exception:
        arr = np.array(image.convert("RGB"))

    try:
        results = reader.readtext(arr, detail=1, paragraph=False)
    except Exception as e:
        return {"success": False, "error": f"EasyOCR грешка: {e}",
                "raw_text": "", "lines": [], "confidence": 0.0, "engine": "easyocr"}

    lines, confs = [], []
    for (bbox, text, conf) in results:
        text = text.strip()
        if conf > 0.15 and text:
            lines.append({"text": text, "confidence": conf})
            confs.append(conf)

    raw = "\n".join(l["text"] for l in lines)
    avg_conf = sum(confs) / len(confs) if confs else 0.0

    return {
        "success": bool(raw.strip()),
        "error": None if raw.strip() else "Не е разпознат текст. Опитай с по-ясна снимка.",
        "raw_text": raw,
        "lines": lines,
        "confidence": avg_conf,
        "engine": "easyocr",
    }


def extract_text_claude_vision(image: Image.Image) -> dict:
    """
    Claude Vision като резервен OCR — изпраща изображението към Anthropic API.
    Работи само в Streamlit artifact (API key се инжектира автоматично).
    """
    try:
        buf = io.BytesIO()
        image.convert("RGB").save(buf, format="JPEG", quality=90)
        b64 = base64.b64encode(buf.getvalue()).decode()

        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json"},
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1000,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image",
                         "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
                        {"type": "text",
                         "text": (
                             "Ти си OCR система. Прочети ЦЕЛИЯ текст от тази снимка на хранителен етикет. "
                             "Върни само суровия текст, без обяснения или форматиране. "
                             "Включи всичко: съставки, хранителни стойности, E-числа, тегло, марка."
                         )}
                    ]
                }],
            },
            timeout=20,
        )

        if resp.status_code == 200:
            text = resp.json()["content"][0]["text"].strip()
            lines = [{"text": l, "confidence": 0.9} for l in text.split("\n") if l.strip()]
            return {
                "success": bool(text),
                "error": None,
                "raw_text": text,
                "lines": lines,
                "confidence": 0.90,
                "engine": "claude_vision",
            }
        else:
            return {"success": False, "error": f"Claude Vision API грешка: {resp.status_code}",
                    "raw_text": "", "lines": [], "confidence": 0.0, "engine": "claude_vision"}

    except Exception as e:
        return {"success": False, "error": f"Claude Vision грешка: {e}",
                "raw_text": "", "lines": [], "confidence": 0.0, "engine": "claude_vision"}


def extract_text_from_image(image: Image.Image, reader=None, engine: str = None) -> dict:
    """
    Главна функция: пробва EasyOCR → Claude Vision → грешка.
    """
    # ── EasyOCR ────────────────────────────────────────────
    if engine == "easyocr" and reader is not None:
        result = extract_text_easyocr(image, reader)
        if result["success"]:
            return result
        # Ако EasyOCR не успя — пробваме Claude Vision
        cv = extract_text_claude_vision(image)
        if cv["success"]:
            return cv
        return result  # Връщаме оригиналната EasyOCR грешка

    # ── Claude Vision (директно, ако няма reader) ──────────
    if reader is None:
        return extract_text_claude_vision(image)

    return {"success": False,
            "error": "Не е намерен OCR двигател. Инсталирай EasyOCR: pip install easyocr",
            "no_ocr_installed": True,
            "raw_text": "", "lines": [], "confidence": 0.0, "engine": "none"}


# ── Парсиране на хранителен етикет ────────────────────────────────────
def parse_food_label(text: str) -> dict:
    """Извлича структурирани данни от OCR текст."""
    parsed = {"product_name": "", "ingredients": "", "nutrition": {}, "e_numbers": [], "weight": ""}
    if not text:
        return parsed

    text_up = text.upper()
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Съставки
    for kw in ["INGREDIENTS", "СЪСТАВКИ", "СОСТАВ", "ZUTATEN", "INGRÉDIENTS", "INGREDIËNTEN"]:
        idx = text_up.find(kw)
        if idx != -1:
            rest = text[idx + len(kw):].lstrip(": \n")
            # Вземаме до следващ двоен нов ред или 500 символа
            end = rest.find("\n\n")
            parsed["ingredients"] = rest[:end].strip() if end != -1 else rest[:500].strip()
            break

    # E-числа
    parsed["e_numbers"] = list(set(re.findall(r'[Ee][-]?\d{3}[a-zA-Z]?', text)))

    # Тегло/обем — намираме ВСИЧКИ и вземаме НАЙ-ГОЛЯМОТО (NET WT)
    weight_matches = re.findall(r'(\d+(?:[.,]\d+)?)\s*(g|ml|kg|г\b|мл|гр|л\b|oz)\b', text, re.I)
    if weight_matches:
        def to_g(val, unit):
            v = float(val.replace(',','.'))
            return v * 1000 if unit.lower() in ('kg','кг') else v * 28.35 if unit.lower() == 'oz' else v
        best = max(weight_matches, key=lambda m: to_g(m[0], m[1]))
        parsed["weight"] = f"{best[0]}{best[1]}"

    # Хранителни стойности
    def find_num(patterns):
        for p in patterns:
            m = re.search(p, text, re.I | re.MULTILINE)
            if m:
                try:
                    return float(m.group(1).replace(",", "."))
                except:
                    pass
        return None

    # Калории — kcal трябва да е СЛЕД числото или с keyword преди
    parsed["nutrition"]["calories"] = find_num([
        r'(?:energy|калории|енергия|energie)[^\d]{0,25}?(\d{2,4}(?:[.,]\d+)?)\s*(?:kcal|кКал)',
        r'(\d{2,4}(?:[.,]\d+)?)\s*(?:kcal|кКал)',
        r'(?:energy|калории|енергия)[^\d]{0,10}?(\d{2,4}(?:[.,]\d+)?)',
    ])
    parsed["nutrition"]["fat"]     = find_num([
        r'(?:мазнини|total fat|fat(?! acids?)|fett)[^\d]{0,10}(\d+(?:[.,]\d+)?)\s*g'])
    parsed["nutrition"]["sugars"]  = find_num([
        r'(?:захари|of which sugars?|sugars?|zucker)[^\d]{0,10}(\d+(?:[.,]\d+)?)\s*g'])
    parsed["nutrition"]["salt"]    = find_num([
        r'(?:^|\b)(?:сол|salt|salz|sel)[^\d]{0,10}(\d+(?:[.,]\d+)?)\s*g'])
    parsed["nutrition"]["protein"] = find_num([
        r'(?:протеин|proteins?|eiweiß)[^\d]{0,10}(\d+(?:[.,]\d+)?)\s*g'])
    parsed["nutrition"]["fiber"]   = find_num([
        r'(?:фибри|dietary fibre|fibre|fiber|ballaststoffe)[^\d]{0,10}(\d+(?:[.,]\d+)?)\s*g'])
    # Почистваме None стойности
    parsed["nutrition"] = {k: v for k, v in parsed["nutrition"].items() if v is not None}

    # Ако все още нямаме калории — изчисляваме от макро
    if "calories" not in parsed["nutrition"]:
        p_ = parsed["nutrition"].get("protein", 0)
        c_ = parsed["nutrition"].get("carbs",   0)
        f_ = parsed["nutrition"].get("fat",     0)
        if p_ or f_:
            parsed["nutrition"]["calories"] = round(p_*4 + c_*4 + f_*9, 1)

    # Продуктово наименование (първи осмислен ред)
    skip_kw = {"ingredients","съставки","energy","kcal","fat","sugar","protein","salt","e1","e2","e3","e4","e5"}
    for line in lines[:4]:
        if len(line) > 3 and not any(kw in line.lower() for kw in skip_kw):
            parsed["product_name"] = line
            break

    return parsed
