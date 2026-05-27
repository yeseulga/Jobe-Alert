"""AI 인텔리전스 피드 진입점.

사용법:
  python main_intelligence.py            # 수집 → 큐레이션 → Discord 발송
  python main_intelligence.py --dry-run  # Discord 발송 없이 콘솔 출력
  python main_intelligence.py --no-mark  # seen DB 기록 없이 실행 (테스트)
"""
from __future__ import annotations
import argparse
import sys
from collections import defaultdict
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from intelligence.aggregator import collect_all
from intelligence.curator import curate
from intelligence.dedup import filter_new, mark_seen
from intelligence.discord_digest import send_digest
from intelligence.config import CATEGORIES


def group_by_category(items: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        cat = item.get("category", "research")
        if cat in CATEGORIES:
            grouped[cat].append(item)
        else:
            grouped["research"].append(item)
    return dict(grouped)


def main():
    parser = argparse.ArgumentParser(description="AI 인텔리전스 피드 발송")
    parser.add_argument("--dry-run", action="store_true", help="Discord 발송 없이 미리보기")
    parser.add_argument("--no-mark", action="store_true", help="seen DB 기록 생략 (테스트)")
    args = parser.parse_args()

    print(f"\n🤖 AI 인텔리전스 시작 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1단계: 수집
    print("\n📡 소스 수집 중...")
    raw_items = collect_all()
    if not raw_items:
        print("수집된 아이템이 없습니다. 종료합니다.")
        sys.exit(0)

    # 2단계: 중복 제거
    print("\n🔍 중복 제거 중...")
    new_items = filter_new(raw_items)
    print(f"신규 아이템: {len(new_items)}/{len(raw_items)}건")

    if not new_items:
        print("신규 아이템이 없습니다. 종료합니다.")
        sys.exit(0)

    # 3단계: Claude 큐레이션
    print("\n✨ Claude Haiku 큐레이션 중...")
    curated = curate(new_items)
    print(f"큐레이션 완료: {len(curated)}건")

    # 4단계: 카테고리 그루핑
    grouped = group_by_category(curated)
    for cat, items in grouped.items():
        emoji, name, _ = CATEGORIES[cat]
        print(f"  {emoji} {name}: {len(items)}건")

    # 5단계: Discord 발송
    print("\n📨 Discord 발송 중...")
    send_digest(grouped, dry_run=args.dry_run)

    # 6단계: seen 기록
    if not args.dry_run and not args.no_mark:
        mark_seen(curated)
        print(f"✅ {len(curated)}건 seen 기록 완료")

    print(f"\n✅ AI 인텔리전스 완료 — {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    main()
