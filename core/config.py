"""
설정 로더 — profile/criteria.yaml이 단일 소스.
yaml 파일이 없으면 하드코딩 기본값으로 폴백.
"""
from __future__ import annotations
import os
import re
from pathlib import Path

# ── yaml 로드 ──────────────────────────────────────────────────
_ROOT = Path(__file__).parent.parent
_CRITERIA_PATH = _ROOT / "profile" / "criteria.yaml"

def _load_criteria() -> dict:
    try:
        import yaml
        with open(_CRITERIA_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}

_c = _load_criteria()

# ── 포함 키워드 ────────────────────────────────────────────────
_inc = _c.get("include_keywords", {})
_high   = _inc.get("high_priority",   ["LLM","RAG","Agent","에이전트","AI 엔지니어","생성형 AI"])
_medium = _inc.get("medium_priority", ["자동화","챗봇","GPT","AI","머신러닝","딥러닝","NLP","자연어처리"])

INCLUDE_KEYWORDS: list[str] = _high + _medium

KEYWORD_WEIGHTS: dict[str, int] = {kw: 2 for kw in _high} | {kw: 1 for kw in _medium}

# 콤보 보너스 (기술적 규칙 — yaml에 넣기엔 복잡)
COMBO_BONUSES: list[tuple[set, int]] = [
    ({"LLM", "RAG"},      3),
    ({"LLM", "Agent"},    2),
    ({"LLM", "에이전트"}, 2),
]

# ── 제외 키워드 ────────────────────────────────────────────────
_exc = _c.get("exclude_keywords", {})
EXCLUDE_KEYWORDS_PARTIAL: list[str] = _exc.get("always", [
    "네트워크","보안","정보보호",
    "임베디드","펌웨어","반도체","하드웨어","H/W","인프라",
    "Java","Spring",".NET","C++","C#",
    "백엔드","프론트엔드","웹개발","앱개발","풀스택","윈도우개발",
    "DevOps","AWS","클라우드",
    "데이터사이언티스트","MLOps","비전","이미지처리","영상처리",
    "QA","UX","UI","GUI","DBA","로봇","자율주행","LiDAR","알고리즘","설계",
])

EXCLUDE_KEYWORDS_PHRASE: list[str] = [
    "시스템엔지니어",
    "시스템 엔지니어",
]

EXCLUDE_C_PATTERN: str = r"(?<![A-Za-z가-힣])C(?![A-Za-z+#])"

# ── 근무지 ─────────────────────────────────────────────────────
_work = _c.get("work", {})
ALLOWED_REGIONS: list[str] = _work.get("locations", [
    "서울","경기","판교","성남","수원","용인","화성",
    "광명","안양","과천","의왕","군포","시흥","인천",
])

# ── 마감/점수 ──────────────────────────────────────────────────
DEADLINE_DAYS_LIMIT: int = int(_c.get("deadline_days_limit", 60))
MIN_SCORE_TO_SEND:   int = 0
MAX_JOBS_PER_EMAIL:  int = 30

# ── 이메일 (환경변수) ──────────────────────────────────────────
RECIPIENT_NAME:    str = os.getenv("RECIPIENT_NAME", "예슬")
GMAIL_SENDER:      str = os.getenv("GMAIL_SENDER", "")
GMAIL_APP_PASSWORD:str = os.getenv("GMAIL_APP_PASSWORD", "")
MAIL_TO:           str = os.getenv("MAIL_TO", GMAIL_SENDER)
