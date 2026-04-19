"""
프로그래머스 채용 공고 스크래퍼
수집 방식: requests + BeautifulSoup (JSON API)
"""
from __future__ import annotations
import time
import requests
from core.text_cleaner import clean_text, normalize_salary

BASE_URL = "https://career.programmers.co.kr"
API_URL = "https://career.programmers.co.kr/api/job_positions"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://career.programmers.co.kr/job",
}

# 검색 키워드 태그 ID (프로그래머스 기술 태그 매핑)
# 실제 태그 ID는 사이트에서 확인 필요; 여기선 키워드 검색으로 대체
SEARCH_QUERIES = [
    "AI",
    "LLM",
    "챗봇",
    "자동화",
    "NLP",
    "RAG",
    "Machine Learning",
]


def _parse_job(item: dict) -> dict:
    company = item.get("company", {}) or {}
    title = clean_text(item.get("title", ""))
    return {
        "platform": "프로그래머스",
        "title": title,
        "company": clean_text(company.get("name", "?")),
        "position": title,
        "location": clean_text(item.get("address", "") or ""),
        "deadline": clean_text(item.get("deadline_at", "") or "상시모집"),
        "salary": normalize_salary(str(item.get("salary", "")) if item.get("salary") else ""),
        "rating": "",
        "company_size": "",
        "url": f"{BASE_URL}/job_positions/{item.get('id', '')}",
        "description": clean_text(item.get("summary", "")),
    }


def scrape(max_pages: int = 5) -> list[dict]:
    session = requests.Session()
    session.headers.update(HEADERS)
    jobs = []
    seen_ids: set = set()

    for query in SEARCH_QUERIES:
        print(f"  [프로그래머스] '{query}' 검색 중...")
        for page in range(1, max_pages + 1):
            try:
                params = {
                    "page": page,
                    "per_page": 20,
                    "keyword": query,
                    "order_by": "recent",
                }
                resp = session.get(API_URL, params=params, timeout=15)
                resp.raise_for_status()
                data = resp.json()

                items = data if isinstance(data, list) else data.get("job_positions", []) or data.get("data", [])
                if not items:
                    break

                for item in items:
                    job_id = item.get("id")
                    if job_id and job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)
                    jobs.append(_parse_job(item))

                time.sleep(0.8)
            except Exception as e:
                print(f"  [프로그래머스] 오류 (query={query}, page={page}): {e}")
                break

    print(f"  [프로그래머스] 수집 완료: {len(jobs)}건")
    return jobs
