"""
원티드 채용 공고 스크래퍼
수집 방식: 공개 REST API
"""
from __future__ import annotations
import time

import requests

from job_alert.text_cleaner import clean_text, normalize_salary

API_URL = "https://www.wanted.co.kr/api/v4/jobs"
BASE_URL = "https://www.wanted.co.kr"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.wanted.co.kr/jobs",
    "wanted-user-language": "ko",
    "wanted-user-country": "KR",
}

# AI/ML 직무 카테고리 ID
CATEGORY_IDS = [655, 1024, 1025]


def _parse(item: dict) -> dict:
    job = item.get("job", item)
    company = job.get("company") or {}
    title = clean_text(job.get("position", "") if isinstance(job.get("position"), str) else "")
    if not title:
        title = clean_text(str(job.get("title", "")))
    jid = job.get("id", "")
    address = job.get("address") or {}
    return {
        "platform":     "원티드",
        "title":        title,
        "company":      clean_text(company.get("name", "?") if isinstance(company, dict) else str(company)),
        "position":     title,
        "location":     clean_text(address.get("country", "") if isinstance(address, dict) else ""),
        "deadline":     clean_text(str(job.get("due_time", "상시모집") or "상시모집")),
        "salary":       normalize_salary(str(job.get("salary", "") or "")),
        "rating":       "",
        "company_size": "",
        "url":          f"{BASE_URL}/wd/{jid}",
        "description":  clean_text((job.get("detail") or {}).get("intro", "") or ""),
    }


def scrape(max_pages: int = 5) -> list[dict]:
    session = requests.Session()
    session.headers.update(HEADERS)
    jobs: list[dict] = []
    seen_ids: set = set()

    for cat_id in CATEGORY_IDS:
        print(f"  [원티드] category={cat_id} 수집 중...")
        offset = 0
        for _ in range(max_pages):
            try:
                resp = session.get(
                    API_URL,
                    params={
                        "country":          "kr",
                        "job_sort":         "job.latest_order",
                        "locations":        "seoul.gyeonggi",
                        "years":            -1,
                        "limit":            20,
                        "offset":           offset,
                        "job_category_id":  cat_id,
                    },
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()
                items = data.get("data", [])
                if not items:
                    break

                for item in items:
                    jid = item.get("id") or (item.get("job") or {}).get("id")
                    if jid in seen_ids:
                        continue
                    seen_ids.add(jid)
                    jobs.append(_parse(item))

                offset += len(items)
                time.sleep(1.0)
                if not (data.get("links") or {}).get("next"):
                    break
            except Exception as e:
                print(f"  [원티드] 오류 (cat={cat_id}, offset={offset}): {e}")
                break

    print(f"  [원티드] 수집 완료: {len(jobs)}건")
    return jobs
