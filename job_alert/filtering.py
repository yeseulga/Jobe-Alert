"""
키워드 필터링 및 점수 산정 모듈 — job_alert.filtering
"""
import re
from typing import Optional

from job_alert.config import (
    INCLUDE_KEYWORDS,
    KEYWORD_WEIGHTS,
    COMBO_BONUSES,
    EXCLUDE_KEYWORDS_PARTIAL,
    EXCLUDE_KEYWORDS_PHRASE,
    EXCLUDE_C_PATTERN,
)


def _search_text(job: dict) -> str:
    parts = [
        job.get("title", ""),
        job.get("company", ""),
        job.get("position", ""),
        job.get("description", ""),
    ]
    return " ".join(p for p in parts if p)


def is_excluded(job: dict) -> tuple[bool, Optional[str]]:
    """제외 키워드 매칭 여부."""
    title = job.get("title", "")
    full_text = _search_text(job)

    for phrase in EXCLUDE_KEYWORDS_PHRASE:
        if phrase in full_text:
            return True, phrase

    for kw in EXCLUDE_KEYWORDS_PARTIAL:
        if kw.lower() in full_text.lower():
            return True, kw

    if re.search(EXCLUDE_C_PATTERN, title):
        return True, "C (단독)"

    return False, None


def calc_score(job: dict) -> int:
    """포함 키워드 가중치 기반 점수 산정."""
    full_text = _search_text(job)
    matched: set[str] = set()
    score = 0

    for kw in INCLUDE_KEYWORDS:
        if kw.lower() in full_text.lower() and kw not in matched:
            matched.add(kw)
            score += KEYWORD_WEIGHTS.get(kw, 1)

    # 콤보 보너스
    matched_upper = {m.upper() for m in matched}
    for combo_set, bonus in COMBO_BONUSES:
        if {c.upper() for c in combo_set}.issubset(matched_upper):
            score += bonus

    return score


def filter_and_score(jobs: list[dict]) -> list[dict]:
    """
    - 제외 키워드 공고 제거
    - 점수 부여
    - 점수 내림차순 정렬
    """
    results: list[dict] = []
    for job in jobs:
        excluded, reason = is_excluded(job)
        if excluded:
            print(f"  [제외] {job.get('title', '')!r}  ← {reason}")
            continue
        job["score"] = calc_score(job)
        results.append(job)

    results.sort(key=lambda j: j.get("score", 0), reverse=True)
    return results
