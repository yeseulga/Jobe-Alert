"""
사람인 채용 공고 스크래퍼
수집 방식: requests + BeautifulSoup (+ RSS 피드)
"""
from __future__ import annotations
import re
import time
from typing import Optional
import requests
from bs4 import BeautifulSoup
from core.text_cleaner import clean_text, normalize_salary
from core.config import ALLOWED_REGIONS

BASE_URL = "https://www.saramin.co.kr"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# 검색 키워드
SEARCH_QUERIES = [
    "AI 엔지니어",
    "LLM 개발",
    "RAG 개발",
    "챗봇 개발",
    "자동화 개발",
    "ML 엔지니어",
    "자연어처리",
]


def _parse_job_card(card: BeautifulSoup) -> Optional[dict]:
    """개별 공고 카드 파싱."""
    try:
        # 제목 & URL
        title_tag = card.select_one(".job_tit a")
        if not title_tag:
            return None
        title = clean_text(title_tag.get_text(strip=True))
        url = BASE_URL + title_tag.get("href", "")

        # 회사명
        company_tag = card.select_one(".corp_name a")
        company = clean_text(company_tag.get_text(strip=True)) if company_tag else "?"

        # 직무 조건 (경력, 학력, 고용형태 등)
        conditions = card.select(".job_condition span")
        cond_texts = [clean_text(c.get_text(strip=True)) for c in conditions]

        # 근무지
        location = ""
        for c in cond_texts:
            for region in ["서울", "경기", "판교", "성남", "수원", "인천"]:
                if region in c:
                    location = c
                    break

        # 마감일
        deadline_tag = card.select_one(".job_date .date")
        deadline = clean_text(deadline_tag.get_text(strip=True)) if deadline_tag else ""

        # 연봉 (사람인은 별도 노출이 드묾)
        salary_tag = card.select_one(".job_condition .salary")
        salary = normalize_salary(salary_tag.get_text(strip=True) if salary_tag else "")

        # 기업 평점
        rating_tag = card.select_one(".company_grade .star_score")
        rating = clean_text(rating_tag.get_text(strip=True)) if rating_tag else ""

        # 기업 규모
        company_size_tag = card.select_one(".job_condition .etc")
        company_size = clean_text(company_size_tag.get_text(strip=True)) if company_size_tag else ""

        return {
            "platform": "사람인",
            "title": title,
            "company": company,
            "position": title,
            "location": location,
            "deadline": deadline,
            "salary": salary,
            "rating": rating,
            "company_size": company_size,
            "url": url,
            "description": " ".join(cond_texts),
        }
    except Exception as e:
        print(f"  [사람인] 파싱 오류: {e}")
        return None


def _is_in_allowed_region(job: dict) -> bool:
    """서울/경기 지역 공고만 허용."""
    loc = job.get("location", "")
    if not loc:
        return True  # 위치 미기재는 일단 포함
    return any(r in loc for r in ALLOWED_REGIONS)


def scrape(max_pages: int = 3) -> list[dict]:
    """
    사람인 채용 공고를 수집한다.

    Args:
        max_pages: 검색어별 최대 페이지 수

    Returns:
        공고 딕셔너리 리스트
    """
    session = requests.Session()
    session.headers.update(HEADERS)
    jobs = []
    seen_urls = set()

    for query in SEARCH_QUERIES:
        print(f"  [사람인] '{query}' 검색 중...")
        for page in range(1, max_pages + 1):
            try:
                params = {
                    "searchType": "search",
                    "searchword": query,
                    "recruitPage": page,
                    "recruitSort": "relation",
                    "recruitPageCount": 40,
                    "inner_com_type": "",
                    "cat_mcls": "",
                    "loc_mcd": "101000,102000",  # 서울, 경기
                }
                resp = session.get(f"{BASE_URL}/zf_user/search/recruit", params=params, timeout=15)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")

                cards = soup.select(".item_recruit")
                if not cards:
                    break

                for card in cards:
                    job = _parse_job_card(card)
                    if not job:
                        continue
                    if job["url"] in seen_urls:
                        continue
                    seen_urls.add(job["url"])
                    if _is_in_allowed_region(job):
                        jobs.append(job)

                time.sleep(1.2)  # 요청 간 딜레이
            except Exception as e:
                print(f"  [사람인] 오류 (query={query}, page={page}): {e}")
                break

    print(f"  [사람인] 수집 완료: {len(jobs)}건")
    return jobs
