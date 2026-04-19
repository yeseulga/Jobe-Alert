"""
OCR 처리 — job_alert.ocr
pytesseract가 없거나 Tesseract가 설치되지 않아도 import 에러 없이 graceful하게 처리
"""
from __future__ import annotations
import io
from typing import Optional

try:
    from PIL import Image
    import pytesseract
    _OCR_OK = True
except ImportError:
    _OCR_OK = False


def extract_text(image_bytes: bytes, lang: str = "kor+eng") -> Optional[str]:
    """
    이미지 바이트 → OCR 텍스트.
    pytesseract / Tesseract 미설치 시 None 반환 (에러 없음).
    """
    if not _OCR_OK:
        return None
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("L")
        text = pytesseract.image_to_string(img, lang=lang)
        return text.strip() or None
    except Exception as e:
        print(f"[OCR] 실패: {e}")
        return None


def extract_from_url(url: str) -> Optional[str]:
    """이미지 URL 다운로드 후 OCR."""
    try:
        import requests
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return extract_text(r.content)
    except Exception as e:
        print(f"[OCR] URL 다운로드 실패 ({url}): {e}")
        return None
