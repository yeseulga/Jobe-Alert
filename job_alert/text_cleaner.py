"""텍스트 정제 유틸리티"""
import re
import unicodedata


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", " ")
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def normalize_salary(salary_str: str) -> str:
    if not salary_str:
        return "협의"
    s = clean_text(salary_str)
    if not s or s in ["-", "회사내규에따름", "면접후결정", "0"]:
        return "협의"
    return s
