"""
공고 보강(enrichment) 모듈

각 공고에 아래 정보를 추가한다:
  - track_badge: "A" / "B" / ""  (Track A = AI 자체 솔루션 보유)
  - first_seen_label: "3일 전 등록", "오늘 등록" 등
  - jobplanet_rating: float 또는 None
  - jobplanet_review: 요약 텍스트 또는 None
  - welfare: 복지 1~2개
  - ai_summary: AI 요약 (긍정+현실 비판 포함)
"""
from __future__ import annotations

import os
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path

_ROOT = Path(__file__).parent.parent


# ─────────────────────────────────────────────
# Track A/B 뱃지
# ─────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_company_data() -> dict[str, dict]:
    """target_companies.yaml 전체 로드 → {회사명: 회사정보}."""
    try:
        import yaml
        path = _ROOT / "profile" / "target_companies.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return {c["name"]: c for c in data.get("companies", []) if c.get("name")}
    except Exception:
        return {}


def _load_track_map() -> dict[str, str]:
    return {name: info.get("track", "") for name, info in _load_company_data().items()}


def _match_company(company: str) -> dict:
    """회사명으로 target_companies 데이터 매칭. 없으면 {}."""
    data = _load_company_data()
    for name, info in data.items():
        if name in company or company in name:
            return info
    return {}


def _get_track(company: str) -> str:
    return _match_company(company).get("track", "")


# ─────────────────────────────────────────────
# 최초 발견 날짜 레이블
# ─────────────────────────────────────────────

def _first_seen_label(first_seen_iso: str | None) -> str:
    if not first_seen_iso:
        return "오늘 등록"
    try:
        fs = datetime.fromisoformat(first_seen_iso)
        now = datetime.now()
        days = (now.date() - fs.date()).days
        if days == 0:
            return "오늘 등록"
        elif days == 1:
            return "어제 등록"
        else:
            return f"{days}일 전 등록"
    except Exception:
        return ""


# ─────────────────────────────────────────────
# 잡플래닛 Playwright 크롤링
# ─────────────────────────────────────────────

_JP_CACHE: dict[str, dict] = {}  # 세션 캐시


def get_jobplanet_url(company: str) -> str:
    import urllib.parse
    return f"https://www.jobplanet.co.kr/search?q={urllib.parse.quote(company)}&tab=company"


async def _fetch_jobplanet_async(company: str) -> dict:
    """Playwright로 잡플래닛 회사 평점/후기 수집."""
    if company in _JP_CACHE:
        return _JP_CACHE[company]

    result: dict = {"rating": None, "reviews": [], "welfare": None, "url": get_jobplanet_url(company)}

    try:
        from playwright.async_api import async_playwright
        import urllib.parse

        search_url = f"https://www.jobplanet.co.kr/companies?search%5Bquery%5D={urllib.parse.quote(company)}"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="ko-KR",
            )
            page = await context.new_page()

            try:
                await page.goto(search_url, timeout=15000, wait_until="domcontentloaded")
                await page.wait_for_timeout(2500)

                # 첫 번째 검색 결과 클릭
                first_result = page.locator("a[href*='/companies/']").first
                if await first_result.count() > 0:
                    href = await first_result.get_attribute("href")
                    if href:
                        company_url = href if href.startswith("http") else f"https://www.jobplanet.co.kr{href}"
                        await page.goto(company_url, timeout=15000, wait_until="domcontentloaded")
                        await page.wait_for_timeout(2000)

                        # 평점 추출 (다양한 셀렉터 시도)
                        for sel in [
                            ".company_score_num",
                            ".score_num",
                            "[class*='score']",
                            ".rate_score",
                            ".total_score",
                        ]:
                            el = page.locator(sel).first
                            if await el.count() > 0:
                                txt = (await el.inner_text()).strip()
                                try:
                                    result["rating"] = round(float(txt.replace(",", ".")), 1)
                                    break
                                except ValueError:
                                    pass

                        # 후기 1~2개 추출
                        for sel in [".review_cont", ".review_text", "[class*='review']"]:
                            items = page.locator(sel)
                            count = await items.count()
                            if count > 0:
                                for i in range(min(2, count)):
                                    txt = (await items.nth(i).inner_text()).strip()
                                    if txt and len(txt) > 10:
                                        result["reviews"].append(txt[:80])
                                if result["reviews"]:
                                    break

                        result["url"] = page.url

            except Exception as e:
                pass
            finally:
                await browser.close()

    except ImportError:
        pass
    except Exception:
        pass

    _JP_CACHE[company] = result
    return result




# ─────────────────────────────────────────────
# 회사 평판 웹 검색
# ─────────────────────────────────────────────

_WEB_REP_CACHE: dict[str, str] = {}


def _search_company_reputation(company: str) -> str:
    """웹 검색으로 회사 평판/규모/워라밸 수집. 결과 캐시."""
    if company in _WEB_REP_CACHE:
        return _WEB_REP_CACHE[company]

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return ""

    result = ""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 2}],
            system=(
                "한국 IT기업 평판 정보 전문가입니다. "
                "웹 검색 결과를 바탕으로 회사 규모·성장성·업계 인지도·워라밸을 2~3문장으로 요약하세요. "
                "정보가 부족하면 검색한 내용 그대로 솔직하게 적으세요. '공개 정보 부족' 대신 실제 검색 결과를 활용하세요."
            ),
            messages=[{
                "role": "user",
                "content": f"'{company}' 회사의 기업 규모, 업계 평판, 워라밸, 잡플래닛/블라인드 후기 요약해줘. 한국 IT 스타트업이면 투자 이력도 포함."
            }]
        )
        for block in resp.content:
            if hasattr(block, "text") and block.text.strip():
                result = block.text.strip()
    except Exception:
        pass

    _WEB_REP_CACHE[company] = result
    return result


# ─────────────────────────────────────────────
# AI 요약 + 비판 에이전트 (2-pass LLM)
# ─────────────────────────────────────────────

def _generate_ai_summary(job: dict) -> str:
    """
    0차: 웹 검색으로 회사 평판 수집
    1차: 직무 요약 생성
    2차: 비판 에이전트가 현실적 우려 사항 추가
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return ""

    company = job.get("company", "?")
    title = job.get("title", "?")
    desc = (job.get("description") or "")[:800]
    platform = job.get("platform", "")
    salary = job.get("salary") or "미기재"
    track = job.get("track_badge", "")
    track_label = "AI 자체 솔루션 보유 (Track A)" if track == "A" else "AI 활용 기업 (Track B)" if track == "B" else "미분류"

    # 0차: 웹 검색 회사 평판
    web_rep = _search_company_reputation(company)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        # ── 1차: 직무 요약 (웹 검색 평판 포함) ────────
        summary_resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            system=(
                "당신은 채용 공고 분석가입니다. 아래 형식으로 간결하게 작성하세요:\n\n"
                "**직무 요약**: 실제로 어떤 일을 하는지 1~2문장 (기술스택 포함)\n"
                "**회사 평판**: 제공된 웹 검색 정보를 바탕으로 규모·성장성·워라밸을 솔직하게. "
                "웹 검색 정보가 없으면 '추가 확인 필요'라고만 적을 것.\n\n"
                "과장 없이, 호의적으로 포장하지 말 것."
            ),
            messages=[{
                "role": "user",
                "content": (
                    f"회사: {company} ({track_label})\n"
                    f"직무: {title}\n"
                    f"연봉: {salary}\n"
                    f"공고 내용: {desc or '(없음)'}\n\n"
                    f"[웹 검색 결과]\n{web_rep or '검색 결과 없음'}"
                )
            }]
        )
        summary = summary_resp.content[0].text.strip()

        # ── 2차: 비판 에이전트 ────────────────────────────
        critic_resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            system=(
                "당신은 냉정한 취업 컨설턴트입니다. "
                "위 공고에서 지원 전에 반드시 확인해야 할 현실적 우려 사항을 1~2문장으로. "
                "연봉 미기재 → 협상 불리, 경력 요건 높음 → 신입 지원 리스크, "
                "회사 정보 부족 → 검증 필요, 급격한 성장 → 안정성 불확실 등. "
                "실제 단점만. '단점 없음'은 절대 금지."
            ),
            messages=[{
                "role": "user",
                "content": f"요약:\n{summary}\n\n연봉: {salary} | 플랫폼: {platform}"
            }]
        )
        critic = critic_resp.content[0].text.strip()

        return f"{summary}\n\n⚠️ **현실 체크**: {critic}"

    except Exception:
        return ""


# ─────────────────────────────────────────────
# 복지 정보 추출 (JD 텍스트 기반)
# ─────────────────────────────────────────────

_WELFARE_PATTERNS = [
    r"(스톡옵션|주식)",
    r"(재택|원격|리모트|remote)",
    r"(유연근무|플렉시블|자율출퇴근)",
    r"(점심|식대|식비)",
    r"(건강검진|의료비|보험)",
    r"(교육비|도서|컨퍼런스|세미나)",
    r"(장비|맥북|노트북)",
    r"(성과급|인센티브|보너스)",
    r"(육아|출산|휴가)",
    r"(복지포인트|포인트)",
]


def _extract_welfare(desc: str) -> str:
    """JD 텍스트에서 복지 키워드 1~2개 추출."""
    if not desc:
        return ""
    found = []
    for pattern in _WELFARE_PATTERNS:
        m = re.search(pattern, desc, re.IGNORECASE)
        if m:
            found.append(m.group(0))
        if len(found) >= 2:
            break
    return ", ".join(found) if found else ""


# ─────────────────────────────────────────────
# 메인 보강 함수
# ─────────────────────────────────────────────

def enrich_jobs(jobs: list[dict], first_seen_map: dict[str, str] | None = None) -> list[dict]:
    """
    공고 리스트에 보강 정보 추가.

    Args:
        jobs:               필터링 완료된 공고 리스트
        first_seen_map:     {job_hash: first_seen_iso}
        use_playwright_jp:  잡플래닛 Playwright 크롤링 여부 (상위 3개만)
    """
    has_api = bool(os.getenv("ANTHROPIC_API_KEY"))
    ai_count = 0
    ai_limit = 5
    jp_limit = 3  # 잡플래닛은 상위 3개만 크롤링 (느리므로)

    for i, job in enumerate(jobs):
        company = job.get("company", "")

        # 1. Track 뱃지
        job["track_badge"] = _get_track(company)

        # 2. 최초 등록일 레이블
        first_seen_iso = (first_seen_map or {}).get(job.get("_hash", ""))
        job["first_seen_label"] = _first_seen_label(first_seen_iso)

        # 3. 잡플래닛 데이터 (yaml 우선, 없으면 링크만)
        company_info = _match_company(company)
        job["jobplanet_rating"] = company_info.get("jp_rating")
        jp_review = company_info.get("jp_review") or ""
        job["jobplanet_reviews"] = [jp_review] if jp_review else []
        job["jobplanet_url"] = get_jobplanet_url(company)

        # 4. 복지 (yaml 우선, 없으면 JD에서 추출)
        if company_info.get("welfare"):
            job["welfare"] = company_info["welfare"]
        elif not job.get("welfare"):
            job["welfare"] = _extract_welfare(job.get("description", ""))

        # 5. AI 요약 + 비판 (상위 ai_limit개만)
        if has_api and ai_count < ai_limit:
            job["ai_summary"] = _generate_ai_summary(job)
            if job["ai_summary"]:
                ai_count += 1
        else:
            job.setdefault("ai_summary", "")

    return jobs
