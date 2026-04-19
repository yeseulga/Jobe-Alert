"""
프로그래머스 채용 공고 스크래퍼
수집 방식: 공개 JSON API
"""
from __future__ import annotations
import time

import requests

from job_alert.text_cleaner import clean_text, normalize_salary

API_URL = "https://career.programmers.co.kr/api/job_positions"
BASE_URL = "https://career.programmers.co.kr"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://career.programmers.co.kr/job",
}

SEARCH_QUERIES = ["AI", "LLM", "챗봇", "자동화", "NLP", "RAG", "Machine Learning"]


def _parse(item: dict) -> dict:
    company = item.get("company") or {}
    title = clean_text(item.get("title", ""))
    return {
        "platform":     "프로그래머스",
        "title":        title,
        "company":      clean_text(company.get("name", "?") if isinstance(company, dict) else str(company)),
        "position":     title,
        "location":     clean_text(item.get("address", "") or ""),
        "deadline":     clean_text(str(item.get("deadline_at", "상시모집") or "상시모집")),
        "salary":       normalize_salary(str(item.get("salary", "") or "")),
        "rating":       "",
        "company_size": "",
        "url":          f"{BASE_URL}/job_positions/{item.get('id','')}",
        "description":  clean_text(item.get("summary", "") or ""),
    }


def scrape(max_pages: int = 5) -> list[dict]:
    session = requests.Session()
    session.headers.update(HEADERS)
    jobs: list[dict] = []
    seen_ids: set = set()

    for query in SEARCH_QUERIES:
        print(f"  [프로그래머스] '{query}' 검색 중...")
        for page in range(1, max_pages + 1):
            try:
                resp = session.get(
                    API_URL,
                    params={"page": page, "per_page": 20, "keyword": query, "order_by": "recent"},
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()
                items = data if isinstance(data, list) else (data.get("job_positions") or data.get("data") or [])
                if not items:
                    break

                for item in items:
                    jid = item.get("id")
                    if jid in seen_ids:
                        continue
                    seen_ids.add(jid)
                    jobs.append(_parse(item))

                time.sleep(0.8)
            except Exception as e:
                print(f"  [프로그래머스] 오류 (page={page}): {e}")
                break

    print(f"  [프로그래머스] 수집 완료: {len(jobs)}건")
    return jobs
