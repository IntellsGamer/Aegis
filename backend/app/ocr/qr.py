"""QR code decoding using zxing-cpp (pure pip wheel, no system deps)."""
from __future__ import annotations

import io
import logging

logger = logging.getLogger("aegis.qr")

try:
    import zxingcpp as zxing

    HAS_ZXING = True
except Exception:  # pragma: no cover
    HAS_ZXING = False

try:
    import cv2

    HAS_CV2 = True
except Exception:  # pragma: no cover
    HAS_CV2 = False

try:
    from PIL import Image

    HAS_PIL = True
except Exception:  # pragma: no cover
    HAS_PIL = False


def decode_qr(image_bytes: bytes) -> list[dict]:
    """Decode all QR codes present in an image.

    Returns a list of dicts: {content, position, points, format, text}.
    Raises RuntimeError when no decoder is available.
    """
    if not HAS_ZXING:
        raise RuntimeError(
            "QR decoding is unavailable. Install with: pip install zxing-cpp"
        )
    if not HAS_PIL:
        raise RuntimeError("Pillow is required for QR decoding")

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    results = zxing.read_barcodes(image)
    decoded = []
    for result in results:
        decoded.append(
            {
                "content": result.text,
                "format": str(result.format),
                "position": [{"x": p.x, "y": p.y} for p in result.position],
                "bytes": len(result.bytes),
            }
        )
    return decoded
