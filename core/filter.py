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


_RAW_SCORE_MAX = 20  # 100점 환산 기준 (raw 20 = 100점)


def calc_score(job: dict) -> tuple[int, str]:
    """
    포함 키워드 가중치 기반 점수를 계산한다.
    반환값: (0~100 정규화 점수, 매칭 근거 문자열)
    """
    search_text = _make_search_text(job)
    matched = set()
    raw = 0
    combos_hit = []

    for kw in INCLUDE_KEYWORDS:
        if kw.lower() in search_text.lower():
            if kw not in matched:
                matched.add(kw)
                raw += KEYWORD_WEIGHTS.get(kw, 1)

    for combo_set, bonus in COMBO_BONUSES:
        normalized_matched = {m.upper() for m in matched}
        normalized_combo = {c.upper() for c in combo_set}
        if normalized_combo.issubset(normalized_matched):
            raw += bonus
            combos_hit.append(f"+{bonus} ({'+'.join(sorted(combo_set))} 콤보)")

    score = min(100, round(raw / _RAW_SCORE_MAX * 100))

    # 근거 문자열 생성 — 각 키워드가 기여한 점수를 "+N" 형식으로 표시
    kw_parts = []
    for kw in sorted(matched, key=lambda k: -KEYWORD_WEIGHTS.get(k, 1)):
        w = KEYWORD_WEIGHTS.get(kw, 1)
        kw_parts.append(f"{kw} +{w}")

    combo_parts = [f"콤보({'+'.join(sorted(cs))}) +{b}" for cs, b in COMBO_BONUSES
                   if {c.upper() for c in cs}.issubset({m.upper() for m in matched})]

    reason_parts = kw_parts + combo_parts
    reason = " · ".join(reason_parts) if reason_parts else "매칭 키워드 없음"

    return score, reason


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

        score, reason = calc_score(job)
        job["score"] = score
        job["score_reason"] = reason
        results.append(job)

    # 점수 내림차순 정렬
    results.sort(key=lambda j: j.get("score", 0), reverse=True)
    return results
