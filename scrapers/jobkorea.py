"""
잡코리아 채용 공고 스크래퍼
수집 방식: requests + BeautifulSoup
셀렉터: data-sentry-component="CardJob" (2026년 리뉴얼 기준)
"""
from __future__ import annotations
import re
import time
from typing import Optional
import requests
from bs4 import BeautifulSoup
from core.text_cleaner import clean_text

BASE_URL = "https://www.jobkorea.co.kr"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://www.jobkorea.co.kr/",
}

SEARCH_QUERIES = [
    "AI 엔지니어",
    "LLM",
    "RAG",
    "챗봇 개발",
    "자동화 개발",
    "자연어처리",
]

_GI_RE = re.compile(r"/GI_Read/(\d+)")


def _canonical_url(href: str) -> str:
    """검색 파라미터 제거한 정규 URL — /Recruit/GI_Read/{ID} 형식."""
    m = _GI_RE.search(href)
    return f"{BASE_URL}/Recruit/GI_Read/{m.group(1)}" if m else href


def _parse_card(card: BeautifulSoup) -> Optional[dict]:
    try:
        # 제목
        title_el = card.select_one('[data-sentry-component="Title"]')
        if not title_el:
            return None
        title = clean_text(title_el.get_text(strip=True))
        if not title:
            return None

        # URL (canonical)
        link = card.select_one('a[href*="/Recruit/GI_Read"]')
        if not link:
            return None
        url = _canonical_url(link.get("href", ""))

        # 회사명 — GI_Read 링크 중 타이틀이 아닌 텍스트
        company = "?"
        for a in card.select('a[href*="Recruit"]'):
            t = clean_text(a.get_text(strip=True))
            if t and t != title:
                company = t
                break

        # 위치 (첫번째 GrayChip)
        chips = card.select('[data-sentry-component="GrayChip"]')
        location = clean_text(chips[0].get_text(strip=True)) if chips else ""

        # 마감일 — time 태그 또는 텍스트에서 날짜 패턴 추출
        deadline = ""
        time_tag = card.select_one("time")
        if time_tag:
            deadline = clean_text(time_tag.get_text(strip=True))
        if not deadline:
            text = card.get_text(" ")
            m = re.search(r"(\d{2}/\d{2}|\d{4}-\d{2}-\d{2}|~\d{2}\.\d{2})", text)
            deadline = m.group(0) if m else ""

        return {
            "platform": "잡코리아",
            "title": title,
            "company": company,
            "position": title,
            "location": location,
            "deadline": deadline,
            "salary": "",
            "rating": "",
            "company_size": "",
            "url": url,
            "description": title,
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
                params = {
                    "stext": query,
                    "tabType": "recruit",
                    "Page_No": page,
                    "local": "101000,102000",
                }
                resp = session.get(f"{BASE_URL}/Search", params=params, timeout=15)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")

                cards = soup.select('[data-sentry-component="CardJob"]')
                if not cards:
                    break

                found = 0
                for card in cards:
                    job = _parse_card(card)
                    if not job or job["url"] in seen_urls:
                        continue
                    seen_urls.add(job["url"])
                    jobs.append(job)
                    found += 1

                if found == 0:
                    break

                time.sleep(1.2)
            except Exception as e:
                print(f"  [잡코리아] 오류 (query={query}, page={page}): {e}")
                break

    print(f"  [잡코리아] 수집 완료: {len(jobs)}건")
    return jobs
