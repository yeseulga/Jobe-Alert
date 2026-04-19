"""
텍스트 정제 유틸리티
"""
import re
import unicodedata


def clean_text(text: str) -> str:
    """특수문자 제거, 공백 정규화, Unicode 정규화."""
    if not text:
        return ""
    # Unicode 정규화 (NFC)
    text = unicodedata.normalize("NFC", text)
    # HTML 엔티티 간단 치환
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", " ")
    # 불필요한 공백·개행 정규화
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def normalize_salary(salary_str: str) -> str:
    """연봉 문자열을 정규화."""
    if not salary_str:
        return "협의"
    salary_str = clean_text(salary_str)
    if not salary_str or salary_str in ["-", "회사내규에따름", "면접후결정"]:
        return "협의"
    return salary_str


def truncate(text: str, max_len: int = 60) -> str:
    """텍스트를 최대 길이로 자름."""
    if not text:
        return ""
    return text[:max_len] + ("…" if len(text) > max_len else "")
