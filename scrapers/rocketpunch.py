"""
로켓펀치 채용 공고 스크래퍼
수집 방식: requests + BeautifulSoup (공개 API 활용)
"""
from __future__ import annotations
import time
import requests
from core.text_cleaner import clean_text, normalize_salary
from core.config import ALLOWED_REGIONS

BASE_URL = "https://www.rocketpunch.com"
API_URL = "https://api.rocketpunch.com/v1/jobs/search"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://www.rocketpunch.com/jobs",
}

# 검색 키워드
SEARCH_QUERIES = [
    "AI 엔지니어",
    "LLM",
    "RAG",
    "챗봇",
    "자연어처리",
    "머신러닝 엔지니어",
]


def _parse_job(item: dict) -> dict:
    """로켓펀치 API 응답에서 공고 정보 파싱."""
    company = item.get("company", {}) or {}
    return {
        "platform": "로켓펀치",
        "title": clean_text(item.get("name", "")),
        "company": clean_text(company.get("name", "?")),
        "position": clean_text(item.get("name", "")),
        "location": clean_text(item.get("address", "") or company.get("address", "")),
        "deadline": clean_text(str(item.get("due", "상시모집") or "상시모집")),
        "salary": normalize_salary(str(item.get("salary", "") or "")),
        "rating": "",
        "company_size": clean_text(str(company.get("size", "") or "")),
        "url": f"{BASE_URL}/jobs/{item.get('id', '')}",
        "description": clean_text(item.get("description", "") or item.get("summary", "")),
    }


def _is_in_allowed_region(job: dict) -> bool:
    loc = job.get("location", "")
    if not loc:
        return True
    return any(r in loc for r in ALLOWED_REGIONS)


def scrape(max_pages: int = 3) -> list[dict]:
    """로켓펀치에서 AI 관련 공고를 수집한다."""
    session = requests.Session()
    session.headers.update(HEADERS)
    jobs = []
    seen_ids: set = set()

    for query in SEARCH_QUERIES:
        print(f"  [로켓펀치] '{query}' 검색 중...")
        for page in range(1, max_pages + 1):
            try:
                params = {
                    "query": query,
                    "page": page,
                    "size": 20,
                }
                resp = session.get(API_URL, params=params, timeout=15)
                resp.raise_for_status()
                data = resp.json()

                items = data.get("data", {}).get("results", [])
                if not items:
                    # 페이지 방식 시도
                    items = data.get("results", []) or data.get("data", [])
                if not items:
                    break

                for item in items:
                    job_id = item.get("id")
                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)
                    job = _parse_job(item)
                    if _is_in_allowed_region(job):
                        jobs.append(job)

                time.sleep(1.0)

                total = data.get("data", {}).get("count", 0) or data.get("count", 0)
                if page * 20 >= total:
                    break

            except Exception as e:
                print(f"  [로켓펀치] 오류 (query={query}, page={page}): {e}")
                break

    print(f"  [로켓펀치] 수집 완료: {len(jobs)}건")
    return jobs
