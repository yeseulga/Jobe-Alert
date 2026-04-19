"""
잡코리아 채용 공고 스크래퍼
수집 방식: requests + BeautifulSoup
"""
from __future__ import annotations
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup

from job_alert.text_cleaner import clean_text, normalize_salary

BASE_URL = "https://www.jobkorea.co.kr"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.jobkorea.co.kr/",
}

SEARCH_QUERIES = ["AI 엔지니어", "LLM", "RAG", "챗봇 개발", "자동화 개발", "자연어처리"]


def _parse_card(card: BeautifulSoup) -> Optional[dict]:
    try:
        title_tag = card.select_one(".title") or card.select_one("h2 a") or card.select_one("a[href*='/Recruit/']")
        if not title_tag:
            return None
        title = clean_text(title_tag.get_text(strip=True))

        href = title_tag.get("href", "")
        url = href if href.startswith("http") else BASE_URL + href

        company_tag = card.select_one(".name, .corp-name, [class*='company']")
        company = clean_text(company_tag.get_text(strip=True)) if company_tag else "?"

        location_tag = card.select_one("[class*='location'], [class*='area'], .work-place")
        location = clean_text(location_tag.get_text(strip=True)) if location_tag else ""

        deadline_tag = card.select_one("[class*='deadline'], [class*='date'], .date")
        deadline = clean_text(deadline_tag.get_text(strip=True)) if deadline_tag else ""

        salary_tag = card.select_one("[class*='salary']")
        salary = normalize_salary(salary_tag.get_text(strip=True) if salary_tag else "")

        return {
            "platform":     "잡코리아",
            "title":        title,
            "company":      company,
            "position":     title,
            "location":     location,
            "deadline":     deadline,
            "salary":       salary,
            "rating":       "",
            "company_size": "",
            "url":          url,
            "description":  title,
        }
    except Exception as e:
        print(f"  [잡코리아] 파싱 오류: {e}")
        return None


def scrape(max_pages: int = 3) -> list[dict]:
    session = requests.Session()
    session.headers.update(HEADERS)
    jobs: list[dict] = []
    seen_urls: set[str] = set()

    for query in SEARCH_QUERIES:
        print(f"  [잡코리아] '{query}' 검색 중...")
        for page in range(1, max_pages + 1):
            try:
                resp = session.get(
                    f"{BASE_URL}/Search",
                    params={"stext": query, "tabType": "recruit", "Page_No": page},
                    timeout=15,
                )
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                cards = (
                    soup.select(".list-post .post-item")
                    or soup.select(".recruit-info li")
                    or soup.select("article.item")
                )
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
                print(f"  [잡코리아] 오류 (page={page}): {e}")
                break

    print(f"  [잡코리아] 수집 완료: {len(jobs)}건")
    return jobs
