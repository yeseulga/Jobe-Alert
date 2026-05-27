"""
자소서 자동 생성 모듈

공고(job dict) + profile/me.md + cv/experiences.md → STAR 포맷 자소서 초안

사용:
  from core.cv_generator import generate_draft, can_generate
  if can_generate():
      job["cv_draft"] = generate_draft(job)
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_ME_PATH = _ROOT / "profile" / "me.md"
_EXP_PATH = _ROOT / "cv" / "experiences.md"


# ─────────────────────────────────────────────
# 파일 로더 (캐시: 세션 중 파일 변경 없다고 가정)
# ─────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_profile() -> str:
    parts = []
    for path in (_ME_PATH, _EXP_PATH):
        if path.exists():
            parts.append(f"=== {path.name} ===\n{path.read_text(encoding='utf-8')}")
    return "\n\n".join(parts) if parts else "(프로필 정보 없음)"


def can_generate() -> bool:
    """ANTHROPIC_API_KEY 환경변수가 있을 때만 True."""
    return bool(os.getenv("ANTHROPIC_API_KEY"))


# ─────────────────────────────────────────────
# 자소서 생성
# ─────────────────────────────────────────────

def generate_draft(job: dict, max_tokens: int = 800) -> str:
    """
    공고 하나에 대한 자소서 초안을 생성한다.

    Args:
        job:        공고 dict (company, title, description, url 포함)
        max_tokens: 생성 최대 토큰 수 (기본 800 — 이메일 가독성 고려)

    Returns:
        자소서 초안 텍스트. 실패 시 빈 문자열.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return ""

    profile = _load_profile()

    company   = job.get("company", "지원 회사")
    title     = job.get("title", "AI 엔지니어")
    desc      = job.get("description") or ""
    # 공고 본문이 너무 길면 앞 1000자만 사용
    if len(desc) > 1000:
        desc = desc[:1000] + "..."

    system_prompt = (
        "당신은 취업 컨설턴트입니다. "
        "아래 지원자 프로필과 공고 정보를 보고 STAR 형식으로 자소서 초안을 작성하세요.\n\n"
        "원칙:\n"
        "- 프로필에 없는 경험은 절대 지어내지 마세요\n"
        "- 500자 이내로 간결하게 (이메일 삽입용)\n"
        "- 항목 제목: 지원동기 / 핵심경험 / 입사후목표\n"
        "- 마크다운 사용 가능"
    )

    user_prompt = (
        f"[지원자 프로필]\n{profile}\n\n"
        f"[공고 정보]\n"
        f"회사: {company}\n"
        f"직무: {title}\n"
        f"공고 내용: {desc or '(본문 없음)'}\n\n"
        f"위 정보로 자소서 초안을 작성해주세요."
    )

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": user_prompt}],
            system=system_prompt,
        )
        return message.content[0].text
    except Exception as e:
        print(f"[자소서 생성] ⚠️ 실패 ({company}): {e}")
        return ""


# ─────────────────────────────────────────────
# 배치 생성 (main.py에서 호출용)
# ─────────────────────────────────────────────

def attach_drafts(jobs: list[dict], top_n: int = 3) -> list[dict]:
    """
    점수 상위 top_n개 공고에 cv_draft 필드를 추가해 반환한다.
    나머지 공고에는 cv_draft = "" 를 설정한다.

    Args:
        jobs:  필터링·정렬 완료된 공고 리스트
        top_n: 자소서 초안을 생성할 최대 공고 수 (비용 절감)
    """
    if not can_generate():
        print("[자소서 생성] ANTHROPIC_API_KEY 없음 — 건너뜁니다")
        for job in jobs:
            job["cv_draft"] = ""
        return jobs

    print(f"[자소서 생성] 상위 {min(top_n, len(jobs))}개 공고 초안 생성 중...")
    for i, job in enumerate(jobs):
        if i < top_n:
            draft = generate_draft(job)
            job["cv_draft"] = draft
            status = "✅" if draft else "⚠️"
            print(f"  {status} [{job.get('company', '?')}] {job.get('title', '?')}")
        else:
            job["cv_draft"] = ""
    return jobs
