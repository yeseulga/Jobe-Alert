"""다중 소스에서 AI 인텔리전스 아이템 수집 — config-driven, sources/ 폴더 없음."""
from __future__ import annotations
import re
import time
from datetime import datetime, timedelta, timezone

import feedparser
import requests

from .config import SOURCES, GITHUB_QUERY


def _safe_text(text: str | None, max_chars: int = 500) -> str:
    """None 안전 처리 + 길이 절단."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip())[:max_chars]


# ── RSS ──────────────────────────────────────────────────────

def _fetch_rss(url: str, name: str) -> list[dict]:
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:15]:
            title = _safe_text(getattr(entry, "title", ""))
            summary = _safe_text(getattr(entry, "summary", "") or getattr(entry, "description", ""))
            link = getattr(entry, "link", "")
            if not title or not link:
                continue
            items.append({"source": name, "title": title, "summary": summary, "url": link})
        print(f"  [{name}] RSS 수집: {len(items)}건")
        return items
    except Exception as e:
        print(f"  [{name}] RSS 오류: {e}")
        return []


# ── HuggingFace Daily Papers API ─────────────────────────────

def _fetch_huggingface(url: str) -> list[dict]:
    try:
        resp = requests.get(url, timeout=10, headers={"Accept": "application/json"})
        resp.raise_for_status()
        papers = resp.json()
        if isinstance(papers, dict):
            papers = papers.get("papers", [])
        items = []
        for p in papers[:10]:
            title = _safe_text(p.get("title") or p.get("paper", {}).get("title", ""))
            summary = _safe_text(p.get("abstract") or p.get("paper", {}).get("abstract", ""))
            paper_id = p.get("paper", {}).get("id") or p.get("id", "")
            link = f"https://huggingface.co/papers/{paper_id}" if paper_id else ""
            if not title or not link:
                continue
            items.append({"source": "HuggingFace", "title": title, "summary": summary, "url": link})
        print(f"  [HuggingFace] API 수집: {len(items)}건")
        return items
    except Exception as e:
        print(f"  [HuggingFace] API 오류: {e}")
        return []


# ── GitHub Search API (HTML 스크래핑 대신 API 우선) ───────────

def _fetch_github(url: str) -> list[dict]:
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    query = GITHUB_QUERY.format(date=yesterday)
    params = {"q": f"topic:ai created:>{yesterday}", "sort": "stars", "order": "desc", "per_page": 10}
    try:
        resp = requests.get(
            url,
            params=params,
            timeout=10,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        if resp.status_code == 403:
            print("  [GitHub] rate limit — 건너뜀")
            return []
        resp.raise_for_status()
        repos = resp.json().get("items", [])
        items = []
        for r in repos:
            title = _safe_text(r.get("full_name", ""))
            summary = _safe_text(r.get("description", ""))
            stars = r.get("stargazers_count", 0)
            link = r.get("html_url", "")
            if not link:
                continue
            items.append({
                "source": "GitHub",
                "title": title,
                "summary": f"⭐{stars:,}  {summary}",
                "url": link,
            })
        print(f"  [GitHub] API 수집: {len(items)}건")
        return items
    except Exception as e:
        print(f"  [GitHub] API 오류: {e}")
        return []


# ── Papers with Code API ─────────────────────────────────────

def _fetch_pwc(url: str) -> list[dict]:
    try:
        resp = requests.get(
            url,
            params={"ordering": "-github_link", "has_github": True},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])[:10]
        items = []
        for p in results:
            title = _safe_text(p.get("title", ""))
            summary = _safe_text(p.get("abstract", ""))
            link = p.get("url_abs") or p.get("paper_url") or ""
            if not title or not link:
                continue
            items.append({"source": "PwC", "title": title, "summary": summary, "url": link})
        print(f"  [Papers w/ Code] API 수집: {len(items)}건")
        return items
    except Exception as e:
        print(f"  [Papers w/ Code] API 오류: {e}")
        return []


# ── 공개 진입점 ──────────────────────────────────────────────

def collect_all() -> list[dict]:
    """모든 소스에서 아이템 수집 후 합쳐 반환."""
    all_items: list[dict] = []

    for name, url, source_type in SOURCES:
        if source_type == "rss":
            all_items.extend(_fetch_rss(url, name))
        elif source_type == "hf_api":
            all_items.extend(_fetch_huggingface(url))
        elif source_type == "github_api":
            all_items.extend(_fetch_github(url))
        elif source_type == "pwc_api":
            all_items.extend(_fetch_pwc(url))

    print(f"\n총 수집: {len(all_items)}건")
    return all_items
