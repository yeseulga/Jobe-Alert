"""
부트캠프/공모전/해커톤 최신 정보 수집기

사용법:
  python -m core.opportunities              # 전체 수집
  python -m core.opportunities --type bootcamp
  python -m core.opportunities --type competition
"""
from __future__ import annotations
import argparse
import yaml
import os
from pathlib import Path
from datetime import datetime

OPPORTUNITIES_DIR = Path(__file__).parent.parent / "opportunities"

FASTCAMPUS_AI_CATEGORIES = [
    "https://fastcampus.co.kr/dev_camp_all",
    "https://fastcampus.co.kr/category/ai-data",
]

KERNEL_ACADEMY_URL = "https://kernelacademy.co.kr"


def load_yaml(filename: str) -> dict:
    path = OPPORTUNITIES_DIR / filename
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_yaml(filename: str, data: dict) -> None:
    path = OPPORTUNITIES_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def check_fastcampus() -> list[dict]:
    """패스트캠퍼스 AI 부트캠프 현재 모집 중인 과정 수집."""
    try:
        import requests
        from bs4 import BeautifulSoup
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
            )
        }
        results = []
        resp = requests.get(
            "https://fastcampus.co.kr/dev_camp_all",
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        # 부트캠프 카드 파싱 (구조 변경 시 업데이트 필요)
        cards = soup.select(".camp-card, .course-card, [class*='bootcamp']")
        for card in cards:
            title_el = card.select_one("h2, h3, .title, [class*='title']")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not any(kw in title for kw in ["AI", "LLM", "데이터", "머신러닝"]):
                continue
            link_el = card.select_one("a[href]")
            url = link_el["href"] if link_el else ""
            if url and not url.startswith("http"):
                url = "https://fastcampus.co.kr" + url
            results.append({
                "title": title,
                "url": url,
                "scraped_at": datetime.now().strftime("%Y-%m-%d"),
            })
        print(f"  [패스트캠퍼스] {len(results)}개 AI 과정 발견")
        return results
    except Exception as e:
        print(f"  [패스트캠퍼스] 수집 오류: {e}")
        return []


def check_kernel_academy() -> list[dict]:
    """커널아카데미 현재 모집 중인 과정 수집."""
    try:
        import requests
        from bs4 import BeautifulSoup
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(KERNEL_ACADEMY_URL, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        results = []
        # 강의/과정 카드 파싱
        cards = soup.select("[class*='course'], [class*='camp'], [class*='program']")
        for card in cards:
            title_el = card.select_one("h2, h3, h4, .title")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            link_el = card.select_one("a[href]")
            url = link_el["href"] if link_el else KERNEL_ACADEMY_URL
            if url and not url.startswith("http"):
                url = KERNEL_ACADEMY_URL + url
            results.append({
                "title": title,
                "url": url,
                "scraped_at": datetime.now().strftime("%Y-%m-%d"),
            })
        print(f"  [커널아카데미] {len(results)}개 과정 발견")
        return results
    except Exception as e:
        print(f"  [커널아카데미] 수집 오류: {e}")
        return []


def format_bootcamp_report(bootcamps_data: dict, fastcampus: list, kernel: list) -> str:
    """부트캠프 현황 리포트 생성."""
    lines = [
        "=" * 60,
        "  부트캠프 기회 리포트",
        f"  생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 60,
        "",
    ]

    # 커널아카데미 (중요 표시)
    lines.append("⭐ 커널아카데미 (중요)")
    lines.append(f"   URL: {KERNEL_ACADEMY_URL}")
    if kernel:
        lines.append(f"   현재 과정 ({len(kernel)}개):")
        for item in kernel[:5]:
            lines.append(f"   - {item['title']}")
            if item.get("url"):
                lines.append(f"     {item['url']}")
    else:
        lines.append("   직접 확인 필요: https://kernelacademy.co.kr")
    lines.append("")

    # 패스트캠퍼스
    lines.append("📚 패스트캠퍼스 AI 과정")
    if fastcampus:
        lines.append(f"   현재 AI 관련 과정 ({len(fastcampus)}개):")
        for item in fastcampus[:5]:
            lines.append(f"   - {item['title']}")
            if item.get("url"):
                lines.append(f"     {item['url']}")
    else:
        lines.append("   직접 확인: https://fastcampus.co.kr/dev_camp_all")
    lines.append("")

    # YAML의 기타 부트캠프
    for camp in bootcamps_data.get("bootcamps", []):
        if camp["provider"] in ["패스트캠퍼스", "커널아카데미"]:
            continue  # 이미 위에서 처리
        lines.append(f"📌 {camp['name']}")
        lines.append(f"   제공: {camp['provider']}")
        lines.append(f"   카테고리: {camp.get('category', '?')}")
        lines.append(f"   비용: {camp.get('cost_range', '확인 필요')}")
        lines.append(f"   기간: {camp.get('duration', '확인 필요')}")
        lines.append(f"   URL: {camp.get('check_url', camp.get('careers_url', ''))}")
        lines.append("")

    return "\n".join(lines)


def format_competition_report(competitions_data: dict) -> str:
    """공모전/해커톤 현황 리포트 생성."""
    lines = [
        "=" * 60,
        "  공모전/해커톤 기회 리포트",
        f"  생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 60,
        "",
        "🏆 공모전",
        "",
    ]

    for comp in competitions_data.get("competitions", []):
        lines.append(f"  {comp['name']}")
        lines.append(f"  주최: {comp['organizer']}")
        lines.append(f"  설명: {comp.get('description', '')}")
        prize = comp.get("prize", {})
        if prize:
            lines.append(f"  상금: {prize.get('total', '확인 필요')}")
            for detail in prize.get("details", []):
                lines.append(f"    - {detail}")
        lines.append(f"  비용: {comp.get('cost', '무료')}")
        lines.append(f"  지원자격: {comp.get('eligibility', '제한 없음')}")
        lines.append(f"  URL: {comp.get('check_url', '')}")
        lines.append("")

    lines.append("⚡ 해커톤")
    lines.append("")

    for hack in competitions_data.get("hackathons", []):
        lines.append(f"  {hack['name']}")
        lines.append(f"  주최: {hack['organizer']}")
        lines.append(f"  설명: {hack.get('description', '')}")
        prize = hack.get("prize", {})
        if prize:
            lines.append(f"  상금: {prize.get('total', '확인 필요')}")
        lines.append(f"  비용: {hack.get('cost', '무료')}")
        if hack.get("held"):
            lines.append(f"  개최: {hack['held']}")
        lines.append(f"  URL: {hack.get('check_url', '')}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="부트캠프/공모전/해커톤 수집기")
    parser.add_argument("--type", choices=["bootcamp", "competition", "all"], default="all")
    args = parser.parse_args()

    if args.type in ("bootcamp", "all"):
        print("\n📚 부트캠프 정보 수집 중...")
        bootcamps_data = load_yaml("bootcamps.yaml")
        fastcampus = check_fastcampus()
        kernel = check_kernel_academy()
        report = format_bootcamp_report(bootcamps_data, fastcampus, kernel)
        print(report)

    if args.type in ("competition", "all"):
        print("\n🏆 공모전/해커톤 정보 로드 중...")
        competitions_data = load_yaml("competitions.yaml")
        report = format_competition_report(competitions_data)
        print(report)


if __name__ == "__main__":
    main()
