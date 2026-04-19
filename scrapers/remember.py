"""
리멤버 채용 공고 스크래퍼
수집 방식: Playwright (SPA + 로그인 필요)
"""
from __future__ import annotations
import asyncio
import json
import os
import time
from typing import Optional

from dotenv import load_dotenv
from core.text_cleaner import clean_text, normalize_salary

load_dotenv()

BASE_URL = "https://career.rememberapp.co.kr"
LOGIN_URL = "https://accounts.rememberapp.co.kr/login"
SEARCH_QUERIES = [
    "AI 엔지니어",
    "LLM",
    "챗봇",
    "자동화",
    "NLP",
    "RAG",
]


def _parse_job(item: dict) -> dict:
    company = item.get("company", {}) or {}
    title = clean_text(item.get("title", ""))
    job_id = item.get("id", "")
    return {
        "platform": "리멤버",
        "title": title,
        "company": clean_text(company.get("name", "?") if isinstance(company, dict) else str(company)),
        "position": title,
        "location": clean_text(item.get("location", "") or ""),
        "deadline": clean_text(item.get("deadline", "") or "상시모집"),
        "salary": normalize_salary(item.get("salary_note", "") or ""),
        "rating": "",
        "company_size": "",
        "url": f"{BASE_URL}/job/{job_id}" if job_id else BASE_URL,
        "description": clean_text(item.get("summary", "") or ""),
    }


async def _scrape_with_playwright(queries: list[str], max_per_query: int = 20) -> list[dict]:
    """Playwright로 리멤버 로그인 후 공고를 수집한다."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("  [리멤버] playwright가 설치되지 않았습니다. pip install playwright 후 playwright install 실행 필요")
        return []

    naver_id = os.getenv("NAVER_ID", "")
    naver_pw = os.getenv("NAVER_PASSWORD", "")

    if not naver_id or not naver_pw:
        print("  [리멤버] NAVER_ID / NAVER_PASSWORD 환경 변수 미설정 → 로그인 스킵")
        return []

    jobs = []
    seen_ids: set = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = await context.new_page()

        # 로그인
        try:
            print("  [리멤버] 로그인 시도...")
            await page.goto(LOGIN_URL, timeout=30000)
            await page.wait_for_timeout(2000)

            # 네이버 로그인 버튼 찾기
            naver_btn = page.locator("button:has-text('네이버'), a:has-text('네이버')")
            if await naver_btn.count() > 0:
                await naver_btn.first.click()
                await page.wait_for_timeout(2000)
                # 네이버 로그인 팝업
                await page.fill("#id", naver_id)
                await page.fill("#pw", naver_pw)
                await page.click(".btn_login")
                await page.wait_for_timeout(3000)
            else:
                # 이메일 로그인 폼
                email_input = page.locator("input[type='email'], input[name='email']")
                pw_input = page.locator("input[type='password']")
                if await email_input.count() > 0:
                    await email_input.fill(naver_id)
                    await pw_input.fill(naver_pw)
                    await page.locator("button[type='submit']").click()
                    await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"  [리멤버] 로그인 오류: {e}")

        # 공고 수집
        for query in queries:
            print(f"  [리멤버] '{query}' 검색 중...")
            try:
                search_url = f"{BASE_URL}/search/job?keyword={query}"
                await page.goto(search_url, timeout=30000)
                await page.wait_for_timeout(2500)

                # 스크롤로 더 많은 공고 로드
                for _ in range(3):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1500)

                # JSON 데이터 추출 시도
                job_data = await page.evaluate("""
                    () => {
                        const items = [];
                        // 공고 카드 셀렉터 (리멤버 구조에 맞게 조정)
                        const cards = document.querySelectorAll('[data-testid="job-card"], .job-card, article');
                        cards.forEach(card => {
                            const title = card.querySelector('h2, h3, [class*="title"]')?.innerText || '';
                            const company = card.querySelector('[class*="company"]')?.innerText || '';
                            const link = card.querySelector('a')?.href || '';
                            const location = card.querySelector('[class*="location"], [class*="area"]')?.innerText || '';
                            const deadline = card.querySelector('[class*="deadline"], [class*="close"]')?.innerText || '';
                            if (title) items.push({title, company, url: link, location, deadline});
                        });
                        return items;
                    }
                """)

                for item in (job_data or []):
                    url = item.get("url", "")
                    if url in seen_ids:
                        continue
                    seen_ids.add(url)
                    jobs.append({
                        "platform": "리멤버",
                        "title": clean_text(item.get("title", "")),
                        "company": clean_text(item.get("company", "?")),
                        "position": clean_text(item.get("title", "")),
                        "location": clean_text(item.get("location", "")),
                        "deadline": clean_text(item.get("deadline", "상시모집")),
                        "salary": "협의",
                        "rating": "",
                        "company_size": "",
                        "url": url,
                        "description": clean_text(item.get("title", "")),
                    })
            except Exception as e:
                print(f"  [리멤버] 수집 오류 (query={query}): {e}")

        await browser.close()

    return jobs


def scrape() -> list[dict]:
    """리멤버 채용 공고 수집 (동기 래퍼)."""
    try:
        jobs = asyncio.run(_scrape_with_playwright(SEARCH_QUERIES))
    except Exception as e:
        print(f"  [리멤버] 스크래핑 실패: {e}")
        jobs = []
    print(f"  [리멤버] 수집 완료: {len(jobs)}건")
    return jobs
