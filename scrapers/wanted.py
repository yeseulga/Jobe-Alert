"""
원티드 채용 공고 스크래퍼
수집 방식: Playwright (SPA — JavaScript 렌더링 필요)
"""
from __future__ import annotations
import asyncio
import json
import time
from typing import Optional

import requests
from core.text_cleaner import clean_text, normalize_salary

# 원티드는 SPA지만 공개 API 엔드포인트가 존재함
API_URL = "https://www.wanted.co.kr/api/v4/jobs"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.wanted.co.kr/jobs",
    "wanted-user-language": "ko",
    "wanted-user-country": "KR",
    "Origin": "https://www.wanted.co.kr",
}

# 직무 카테고리 ID (원티드 기준)
# 655 = AI/ML, 1024 = 데이터 엔지니어, 677 = DBA 등
JOB_CATEGORY_IDS = [
    655,   # AI/ML 엔지니어
    1024,  # 데이터 엔지니어
    1025,  # 머신러닝 엔지니어
]


def _parse_job(item: dict) -> dict:
    job_info = item.get("job", item)
    company = job_info.get("company", {}) or {}
    position = job_info.get("position", {}) or {}
    detail = job_info.get("detail", {}) or {}

    title = clean_text(job_info.get("position", "") if isinstance(job_info.get("position"), str) else position.get("name", ""))
    company_name = clean_text(company.get("name", "?") if isinstance(company, dict) else str(company))
    job_id = job_info.get("id", "")

    return {
        "platform": "원티드",
        "title": title or clean_text(str(job_info.get("title", ""))),
        "company": company_name,
        "position": title,
        "location": clean_text(job_info.get("address", {}).get("country", "") if isinstance(job_info.get("address"), dict) else ""),
        "deadline": clean_text(str(job_info.get("due_time", "상시모집") or "상시모집")),
        "salary": normalize_salary(str(job_info.get("salary", "") or "")),
        "rating": "",
        "company_size": "",
        "url": f"https://www.wanted.co.kr/wd/{job_id}",
        "description": clean_text(
            detail.get("intro", "") or job_info.get("summary", "") or ""
        ),
    }


def scrape(max_pages: int = 5) -> list[dict]:
    """원티드 API를 통해 AI/ML 직군 공고를 수집한다."""
    session = requests.Session()
    session.headers.update(HEADERS)
    jobs = []
    seen_ids: set = set()

    for category_id in JOB_CATEGORY_IDS:
        print(f"  [원티드] category_id={category_id} 수집 중...")
        offset = 0
        for _ in range(max_pages):
            try:
                params = {
                    "country": "kr",
                    "job_sort": "job.latest_order",
                    "locations": "seoul.gyeonggi",
                    "years": -1,  # 전체 경력
                    "limit": 20,
                    "offset": offset,
                    "job_category_id": category_id,
                }
                resp = session.get(API_URL, params=params, timeout=15)
                resp.raise_for_status()
                data = resp.json()

                items = data.get("data", [])
                if not items:
                    break

                for item in items:
                    job_id = item.get("id") or item.get("job", {}).get("id")
                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)
                    jobs.append(_parse_job(item))

                offset += len(items)
                time.sleep(1.0)

                if not data.get("links", {}).get("next"):
                    break
            except Exception as e:
                print(f"  [원티드] 오류 (category={category_id}, offset={offset}): {e}")
                break

    print(f"  [원티드] 수집 완료: {len(jobs)}건")
    return jobs
