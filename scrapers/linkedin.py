"""
LinkedIn RSS 피드 스크래퍼
수집 방식: feedparser (RSS)
"""
from __future__ import annotations
import feedparser
from core.text_cleaner import clean_text

# LinkedIn Job RSS 피드 URL 패턴
# keywords와 location으로 구성
RSS_FEEDS = [
    "https://www.linkedin.com/jobs/search/?keywords=LLM+engineer&location=Seoul&f_TPR=r86400&f_JT=F&f_WT=2",
    "https://www.linkedin.com/jobs/search/?keywords=AI+engineer&location=Seoul",
    "https://www.linkedin.com/jobs/search/?keywords=RAG+developer&location=Seoul",
    "https://www.linkedin.com/jobs/search/?keywords=chatbot+developer&location=Korea",
    "https://www.linkedin.com/jobs/search/?keywords=NLP+engineer&location=Seoul",
]

# feedparser용 RSS URL (LinkedIn은 직접 RSS를 지원하지 않으므로 RSSHub 또는 공개 RSS 사용)
RSSBRIDGE_FEEDS = [
    # 직접 RSS 없을 시 대안: 구글 News RSS (채용 관련)
    "https://news.google.com/rss/search?q=LLM+채용+AI+개발자&hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/search?q=RAG+챗봇+채용&hl=ko&gl=KR&ceid=KR:ko",
]


def _parse_entry(entry: dict, feed_url: str) -> dict:
    title = clean_text(getattr(entry, "title", "") or "")
    url = getattr(entry, "link", "") or ""
    summary = clean_text(getattr(entry, "summary", "") or "")
    published = getattr(entry, "published", "") or ""

    # 회사명 추출 시도 (LinkedIn 타이틀 포맷: "직무명 - 회사명")
    company = "?"
    if " - " in title:
        parts = title.split(" - ")
        if len(parts) >= 2:
            company = clean_text(parts[-1])
            title = clean_text(parts[0])

    return {
        "platform": "LinkedIn",
        "title": title,
        "company": company,
        "position": title,
        "location": "서울/원격",
        "deadline": "상시모집",
        "salary": "협의",
        "rating": "",
        "company_size": "",
        "url": url,
        "description": summary,
    }


def scrape() -> list[dict]:
    jobs = []
    seen_urls: set[str] = set()

    feeds_to_try = RSSBRIDGE_FEEDS

    for feed_url in feeds_to_try:
        print(f"  [LinkedIn/RSS] 피드 수집 중: {feed_url[:60]}...")
        try:
            feed = feedparser.parse(feed_url)
            entries = feed.get("entries", [])

            for entry in entries:
                url = getattr(entry, "link", "") or ""
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                job = _parse_entry(entry, feed_url)
                # 채용 관련 항목만 필터 (뉴스 RSS 사용 시)
                if any(kw in job["title"] + job["description"] for kw in ["채용", "모집", "recruit", "engineer", "developer"]):
                    jobs.append(job)
        except Exception as e:
            print(f"  [LinkedIn] RSS 수집 오류: {e}")

    print(f"  [LinkedIn] 수집 완료: {len(jobs)}건")
    return jobs
