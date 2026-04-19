"""
LinkedIn RSS 피드 스크래퍼
수집 방식: feedparser (Google News RSS 대체 사용)
"""
from __future__ import annotations

import feedparser

from job_alert.text_cleaner import clean_text

# Google News RSS — 채용 관련 키워드 검색
RSS_FEEDS = [
    "https://news.google.com/rss/search?q=LLM+AI+개발자+채용&hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/search?q=RAG+챗봇+AI+엔지니어+채용&hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/search?q=자동화+AI+개발+채용+공고&hl=ko&gl=KR&ceid=KR:ko",
]

_RECRUIT_KEYWORDS = ["채용", "모집", "recruit", "engineer", "developer", "엔지니어"]


def _parse_entry(entry) -> dict:
    title = clean_text(getattr(entry, "title", "") or "")
    url = getattr(entry, "link", "") or ""
    summary = clean_text(getattr(entry, "summary", "") or "")

    company = "?"
    if " - " in title:
        parts = title.rsplit(" - ", 1)
        company = clean_text(parts[-1])
        title = clean_text(parts[0])

    return {
        "platform":     "LinkedIn",
        "title":        title,
        "company":      company,
        "position":     title,
        "location":     "서울/원격",
        "deadline":     "상시모집",
        "salary":       "협의",
        "rating":       "",
        "company_size": "",
        "url":          url,
        "description":  summary,
    }


def scrape() -> list[dict]:
    jobs: list[dict] = []
    seen_urls: set[str] = set()

    for feed_url in RSS_FEEDS:
        print(f"  [LinkedIn/RSS] 피드 수집: {feed_url[:70]}...")
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.get("entries", []):
                url = getattr(entry, "link", "") or ""
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                job = _parse_entry(entry)
                combined = job["title"] + job["description"]
                if any(kw in combined for kw in _RECRUIT_KEYWORDS):
                    jobs.append(job)
        except Exception as e:
            print(f"  [LinkedIn] RSS 오류: {e}")

    print(f"  [LinkedIn] 수집 완료: {len(jobs)}건")
    return jobs
