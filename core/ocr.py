"""
OCR 처리 모듈 — 이미지 공고를 텍스트로 변환
"""
from __future__ import annotations
import io
from typing import Optional

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


def extract_text_from_image_bytes(image_bytes: bytes, lang: str = "kor+eng") -> Optional[str]:
    """
    이미지 바이트를 받아 OCR로 텍스트를 추출한다.

    Args:
        image_bytes: 이미지 바이너리 데이터
        lang: tesseract 언어 코드 (기본: 한국어 + 영어)

    Returns:
        추출된 텍스트 또는 None
    """
    if not OCR_AVAILABLE:
        print("[OCR] pytesseract 또는 Pillow가 설치되지 않았습니다. OCR을 건너뜁니다.")
        return None

    try:
        image = Image.open(io.BytesIO(image_bytes))
        # 이미지 전처리: 그레이스케일 변환으로 인식률 향상
        image = image.convert("L")
        text = pytesseract.image_to_string(image, lang=lang)
        return text.strip() if text.strip() else None
    except Exception as e:
        print(f"[OCR] 텍스트 추출 실패: {e}")
        return None


def extract_text_from_image_url(url: str, session=None) -> Optional[str]:
    """
    이미지 URL에서 다운로드 후 OCR 처리.
    """
    try:
        import requests
        if session:
            response = session.get(url, timeout=15)
        else:
            response = requests.get(url, timeout=15)
        response.raise_for_status()
        return extract_text_from_image_bytes(response.content)
    except Exception as e:
        print(f"[OCR] 이미지 다운로드 실패 ({url}): {e}")
        return None
