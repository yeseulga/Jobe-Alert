"""
LinkedIn 채용 공고 스크래퍼
수집 방식: LinkedIn Guest Jobs API (인증 불필요 공개 엔드포인트)
"""
from __future__ import annotations
import time
from typing import Optional
import requests
from bs4 import BeautifulSoup
from core.text_cleaner import clean_text

BASE_API = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}

SEARCH_QUERIES = [
    "LLM engineer",
    "AI engineer Korea",
    "RAG developer",
    "NLP engineer Korea",
    "chatbot developer Korea",
    "generative AI developer",
]


def _parse_job_card(card: BeautifulSoup) -> Optional[dict]:
    try:
        # 제목
        title_tag = card.select_one(".base-search-card__title") or card.select_one("h3")
        if not title_tag:
            return None
        title = clean_text(title_tag.get_text(strip=True))

        # 회사명
        company_tag = card.select_one(".base-search-card__subtitle") or card.select_one("h4")
        company = clean_text(company_tag.get_text(strip=True)) if company_tag else "?"

        # 근무지
        location_tag = card.select_one(".job-search-card__location") or card.select_one(".base-search-card__metadata span")
        location = clean_text(location_tag.get_text(strip=True)) if location_tag else ""

        # URL
        link_tag = card.select_one("a.base-card__full-link") or card.select_one("a[href*='linkedin.com/jobs']")
        url = link_tag.get("href", "").split("?")[0] if link_tag else ""
        if not url:
            return None

        # 게시일
        date_tag = card.select_one("time")
        posted = clean_text(date_tag.get_text(strip=True)) if date_tag else ""

        return {
            "platform": "LinkedIn",
            "title": title,
            "company": company,
            "position": title,
            "location": location,
            "deadline": "상시모집",
            "salary": "협의",
            "rating": "",
            "company_size": "",
            "url": url,
            "description": f"{title} | {company} | {location} | {posted}",
        }
    except Exception as e:
        print(f"  [LinkedIn] 파싱 오류: {e}")
        return None


def scrape(max_pages: int = 2) -> list[dict]:
    session = requests.Session()
    session.headers.update(HEADERS)
    jobs: list[dict] = []
    seen_urls: set[str] = set()

    for query in SEARCH_QUERIES:
        print(f"  [LinkedIn] '{query}' 검색 중...")
        for page in range(max_pages):
            try:
                params = {
                    "keywords": query,
                    "location": "South Korea",
                    "f_JT": "F",        # 정규직
                    "f_WT": "1,2,3",    # 오피스/하이브리드/리모트
                    "start": page * 25,
                }
                resp = session.get(BASE_API, params=params, timeout=15)
                if resp.status_code != 200:
                    break

                soup = BeautifulSoup(resp.text, "lxml")
                cards = soup.select("li")

                if not cards:
                    break

                found = 0
                for card in cards:
                    job = _parse_job_card(card)
                    if not job or job["url"] in seen_urls:
                        continue
                    seen_urls.add(job["url"])
                    jobs.append(job)
                    found += 1

                if found == 0:
                    break

                time.sleep(1.5)
            except Exception as e:
                print(f"  [LinkedIn] 오류 (query={query}, page={page}): {e}")
                break

    print(f"  [LinkedIn] 수집 완료: {len(jobs)}건")
    return jobs
