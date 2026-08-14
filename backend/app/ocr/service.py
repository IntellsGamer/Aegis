"""OCR text extraction with automatic engine detection.

Supported engines (all open-source):
  * Tesseract  (pytesseract + system binary)          - primary
  * EasyOCR    (pytorch)                               - fallback

If neither is available, a clear error is raised and the API responds with a
helpful 503 so operators can install one of the engines.
"""
from __future__ import annotations

import io
import logging
import os
import shutil
import tempfile
from pathlib import Path

from app.config import settings

logger = logging.getLogger("aegis.ocr")

HAS_PIL = False
try:
    from PIL import Image, ImageEnhance, ImageOps

    HAS_PIL = True
except Exception:  # pragma: no cover
    HAS_PIL = False

HAS_PYTESSERACT = False
try:
    import pytesseract

    HAS_PYTESSERACT = True
except Exception:  # pragma: no cover
    HAS_PYTESSERACT = False

def _configure_tesseract_command() -> str | None:
    """Apply an explicitly configured Tesseract binary before capability checks."""
    if not HAS_PYTESSERACT or not settings.tesseract_cmd:
        return None
    candidate = Path(settings.tesseract_cmd).expanduser()
    if candidate.is_file():
        pytesseract.pytesseract.tesseract_cmd = str(candidate)
        return str(candidate)
    logger.warning("Configured Tesseract executable does not exist: %s", candidate)
    return None


_CONFIGURED_TESSERACT_CMD = _configure_tesseract_command()
_HAS_TESSERACT_BIN = False
if HAS_PYTESSERACT:
    try:
        _HAS_TESSERACT_BIN = bool(_CONFIGURED_TESSERACT_CMD) or shutil.which("tesseract") is not None or bool(
            pytesseract.get_tesseract_version()
        )
    except Exception:  # pragma: no cover - tesseract binary missing
        _HAS_TESSERACT_BIN = bool(_CONFIGURED_TESSERACT_CMD) or shutil.which("tesseract") is not None

HAS_EASYOCR = False
_EASYOCR_READER = None
if settings.ocr_engine in ("auto", "easyocr"):
    try:
        import easyocr

        HAS_EASYOCR = True
    except Exception:  # pragma: no cover
        HAS_EASYOCR = False


def available_engines() -> dict:
    return {
        "pil": HAS_PIL,
        "tesseract": HAS_PYTESSERACT and _HAS_TESSERACT_BIN,
        "easyocr": HAS_EASYOCR,
    }


def _preprocess(image_bytes: bytes) -> bytes:
    """Enhance contrast and normalize orientation for better OCR accuracy."""
    image = Image.open(io.BytesIO(image_bytes)).convert("L")
    image = ImageOps.autocontrast(image)
    image = ImageEnhance.Contrast(image).enhance(1.6)
    image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS)
    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def extract_text(image_bytes: bytes) -> dict:
    """Extract text from image bytes. Returns dict with text + metadata."""
    if not HAS_PIL:
        raise RuntimeError(
            "Pillow is required for image analysis. Install via: pip install Pillow"
        )

    preprocessed = _preprocess(image_bytes)

    if settings.ocr_engine in ("auto", "tesseract"):
        if HAS_PYTESSERACT and _HAS_TESSERACT_BIN:
            return _extract_tesseract(preprocessed)

    if settings.ocr_engine in ("auto", "easyocr"):
        if HAS_EASYOCR:
            return _extract_easyocr(preprocessed)

    if os.name == "nt":
        tesseract_help = (
            "Install Tesseract for Windows and either add it to PATH or set "
            "AEGIS_TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe."
        )
    else:
        tesseract_help = "Install Tesseract with your package manager (for example: apt install tesseract-ocr)."
    raise RuntimeError(
        f"No OCR engine available. {tesseract_help} "
        "Alternatively, set AEGIS_OCR_ENGINE=none to disable image text extraction."
    )


def _extract_tesseract(image_bytes: bytes) -> dict:
    image = Image.open(io.BytesIO(image_bytes))
    data = pytesseract.image_to_data(
        image, output_type=pytesseract.Output.DICT, lang="eng"
    )
    words = []
    for i, word in enumerate(data.get("text", [])):
        if word and str(data["conf"][i]).isdigit() and int(data["conf"][i]) >= 30:
            words.append(word)
    text = " ".join(words)
    return {
        "engine": "tesseract",
        "text": text.strip(),
        "word_count": len(words),
        "confidence": _mean_conf(data.get("conf", [])),
    }


def _extract_easyocr(image_bytes: bytes) -> dict:
    global _EASYOCR_READER
    if _EASYOCR_READER is None:
        _EASYOCR_READER = easyocr.Reader(["en"], gpu=False)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name
    try:
        result = _EASYOCR_READER.readtext(tmp_path, detail=1)
        text = " ".join(item[1] for item in result)
        confs = [float(item[2]) for item in result]
        return {
            "engine": "easyocr",
            "text": text.strip(),
            "word_count": len(result),
            "confidence": round(sum(confs) / len(confs), 3) if confs else 0.0,
        }
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _mean_conf(conf_list: list) -> float:
    values = [float(c) for c in conf_list if str(c).isdigit()]
    if not values:
        return 0.0
    return round(sum(values) / len(values), 1)
