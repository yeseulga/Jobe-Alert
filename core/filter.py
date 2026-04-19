"""
키워드 필터링 및 점수 산정 모듈
"""
import re
from typing import Optional
from core.config import (
    INCLUDE_KEYWORDS,
    KEYWORD_WEIGHTS,
    COMBO_BONUSES,
    EXCLUDE_KEYWORDS_PARTIAL,
    EXCLUDE_KEYWORDS_PHRASE,
    EXCLUDE_C_PATTERN,
)


def _make_search_text(job: dict) -> str:
    """제목 + 회사명 + 직무 설명을 합쳐서 검색용 텍스트 생성."""
    parts = [
        job.get("title", ""),
        job.get("company", ""),
        job.get("position", ""),
        job.get("description", ""),
    ]
    return " ".join(p for p in parts if p)


def is_excluded(job: dict) -> tuple[bool, Optional[str]]:
    """
    제외 키워드 매칭 여부를 판단한다.
    Returns:
        (True, 매칭된_키워드) or (False, None)
    """
    title = job.get("title", "")
    search_text = _make_search_text(job)

    # 구문 매칭 — 제목에서 먼저 체크
    for phrase in EXCLUDE_KEYWORDS_PHRASE:
        if phrase in title or phrase in search_text:
            return True, phrase

    # 부분 포함 매칭
    for kw in EXCLUDE_KEYWORDS_PARTIAL:
        if kw.lower() in search_text.lower():
            return True, kw

    # 단독 C 언어 패턴 (제목에서만)
    if re.search(EXCLUDE_C_PATTERN, title):
        return True, "C (단독)"

    return False, None


def calc_score(job: dict) -> int:
    """
    포함 키워드 가중치 기반 점수를 계산한다.
    """
    search_text = _make_search_text(job)
    matched = set()
    score = 0

    for kw in INCLUDE_KEYWORDS:
        # 대소문자 무시, 부분 포함 허용
        if kw.lower() in search_text.lower():
            if kw not in matched:
                matched.add(kw)
                score += KEYWORD_WEIGHTS.get(kw, 1)

    # 콤보 보너스
    for combo_set, bonus in COMBO_BONUSES:
        normalized_matched = {m.upper() for m in matched}
        normalized_combo = {c.upper() for c in combo_set}
        if normalized_combo.issubset(normalized_matched):
            score += bonus

    return score


def filter_and_score(jobs: list[dict]) -> list[dict]:
    """
    공고 리스트에서 제외 키워드 공고를 제거하고, 점수를 부여한 뒤
    점수 내림차순으로 정렬하여 반환한다.
    """
    results = []
    for job in jobs:
        excluded, reason = is_excluded(job)
        if excluded:
            print(f"  [제외] {job.get('title', '')} — 사유: {reason}")
            continue

        score = calc_score(job)
        job["score"] = score
        results.append(job)

    # 점수 내림차순 정렬
    results.sort(key=lambda j: j.get("score", 0), reverse=True)
    return results
