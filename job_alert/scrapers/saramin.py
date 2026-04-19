"""
사람인 채용 공고 스크래퍼
수집 방식: requests + BeautifulSoup
"""
from __future__ import annotations
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup

from job_alert.text_cleaner import clean_text, normalize_salary
from job_alert.config import ALLOWED_REGIONS

BASE_URL = "https://www.saramin.co.kr"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}

SEARCH_QUERIES = [
    "AI 엔지니어",
    "LLM 개발",
    "RAG 개발",
    "챗봇 개발",
    "자동화 개발",
    "ML 엔지니어",
    "자연어처리",
]


def _parse_card(card: BeautifulSoup) -> Optional[dict]:
    try:
        title_tag = card.select_one(".job_tit a")
        if not title_tag:
            return None
        title = clean_text(title_tag.get_text(strip=True))
        url = BASE_URL + title_tag.get("href", "")

        company_tag = card.select_one(".corp_name a")
        company = clean_text(company_tag.get_text(strip=True)) if company_tag else "?"

        conditions = [clean_text(c.get_text(strip=True)) for c in card.select(".job_condition span")]

        location = next((c for c in conditions if any(r in c for r in ALLOWED_REGIONS)), "")

        deadline_tag = card.select_one(".job_date .date")
        deadline = clean_text(deadline_tag.get_text(strip=True)) if deadline_tag else ""

        salary_tag = card.select_one(".job_condition .salary")
        salary = normalize_salary(salary_tag.get_text(strip=True) if salary_tag else "")

        rating_tag = card.select_one(".company_grade .star_score")
        rating = clean_text(rating_tag.get_text(strip=True)) if rating_tag else ""

        return {
            "platform":     "사람인",
            "title":        title,
            "company":      company,
            "position":     title,
            "location":     location,
            "deadline":     deadline,
            "salary":       salary,
            "rating":       rating,
            "company_size": "",
            "url":          url,
            "description":  " ".join(conditions),
        }
    except Exception as e:
        print(f"  [사람인] 파싱 오류: {e}")
        return None


def scrape(max_pages: int = 3) -> list[dict]:
    session = requests.Session()
    session.headers.update(HEADERS)
    jobs: list[dict] = []
    seen_urls: set[str] = set()

    for query in SEARCH_QUERIES:
        print(f"  [사람인] '{query}' 검색 중...")
        for page in range(1, max_pages + 1):
            try:
                resp = session.get(
                    f"{BASE_URL}/zf_user/search/recruit",
                    params={
                        "searchType":       "search",
                        "searchword":       query,
                        "recruitPage":      page,
                        "recruitSort":      "relation",
                        "recruitPageCount": 40,
                        "loc_mcd":          "101000,102000",  # 서울, 경기
                    },
                    timeout=15,
                )
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.select(".item_recruit")
                if not cards:
                    break

                for card in cards:
                    job = _parse_card(card)
                    if not job or job["url"] in seen_urls:
                        continue
                    seen_urls.add(job["url"])
                    jobs.append(job)

                time.sleep(1.2)
            except Exception as e:
                print(f"  [사람인] 오류 (page={page}): {e}")
                break

    print(f"  [사람인] 수집 완료: {len(jobs)}건")
    return jobs
