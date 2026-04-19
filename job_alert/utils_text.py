import re
from typing import Iterable


_whitespace_re = re.compile(r"\s+")
_specials_re = re.compile(r"[^\w\s\u3130-\u318F\uAC00-\uD7AF]")  # keep Korean ranges


def normalize_whitespace(text: str) -> str:
    return _whitespace_re.sub(" ", text).strip()


def strip_specials(text: str) -> str:
    return _specials_re.sub(" ", text)


def normalize_text(text: str) -> str:
    return normalize_whitespace(strip_specials(text))


def any_contains(text: str, keywords: Iterable[str]) -> bool:
    lower = text.lower()
    return any(kw.lower() in lower for kw in keywords)
