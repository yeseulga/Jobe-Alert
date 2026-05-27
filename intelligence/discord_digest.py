"""Discord AI 인텔리전스 피드 발송 — 4개 카테고리 embed, 429 backoff."""
from __future__ import annotations
import os
import time
from datetime import datetime

import requests

from .config import CATEGORIES, DISCORD_RETRY_DELAYS, IMPACT_AREAS, MAX_ITEMS_PER_CATEGORY

_CATEGORY_COLORS = {
    "research":   0x6366F1,   # 인디고
    "skills":     0x0EA5E9,   # 하늘
    "model":      0xF59E0B,   # 앰버
    "ecosystem":  0x10B981,   # 에메랄드
}


def _post_webhook(url: str, payload: dict) -> bool:
    """Discord 웹훅 POST — 429 시 지수 백오프 재시도."""
    for attempt, delay in enumerate([0] + DISCORD_RETRY_DELAYS):
        if delay:
            time.sleep(delay)
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 204:
                return True
            if resp.status_code == 429:
                retry_after = resp.json().get("retry_after", delay + 1)
                print(f"  [Discord] 429 rate limit — {retry_after}s 대기 (시도 {attempt + 1})")
                time.sleep(float(retry_after))
                continue
            print(f"  [Discord] 전송 실패: {resp.status_code} — {resp.text[:200]}")
            return False
        except requests.RequestException as e:
            print(f"  [Discord] 연결 오류: {e}")
    return False


def send_digest(categorized_items: dict[str, list[dict]], dry_run: bool = False):
    """카테고리별 embed 4개를 Discord로 발송."""
    webhook_url = os.getenv("DISCORD_INTELLIGENCE_WEBHOOK_URL")
    if not webhook_url:
        raise EnvironmentError(
            "DISCORD_INTELLIGENCE_WEBHOOK_URL이 설정되지 않았습니다. "
            ".env 또는 GitHub Secrets에 추가하세요."
        )

    today = datetime.now().strftime("%Y-%m-%d (%a)")
    total = sum(len(v) for v in categorized_items.values())

    if total == 0:
        print("⚠️ 발송할 아이템이 없습니다. Discord 전송 건너뜀.")
        return

    embeds = []
    for cat_key, (emoji, cat_name, _) in CATEGORIES.items():
        items = categorized_items.get(cat_key, [])[:MAX_ITEMS_PER_CATEGORY]
        if not items:
            continue
        fields = []
        for item in items:
            title = item["title"][:100]
            summary = item.get("summary_ko") or item.get("summary", "")
            summary = summary[:150]
            source = item.get("source", "")
            url = item.get("url", "")

            name_md = f"[{title}]({url})" if url else title
            impact_tags = " · ".join(
                IMPACT_AREAS[ia] for ia in item.get("impact_areas", []) if ia in IMPACT_AREAS
            )
            value_parts = []
            if summary:
                value_parts.append(summary)
            if impact_tags:
                value_parts.append(impact_tags)
            value_parts.append(f"*{source}*")
            fields.append({
                "name": name_md,
                "value": "\n".join(value_parts),
                "inline": False,
            })

        embeds.append({
            "title": f"{emoji} {cat_name}",
            "color": _CATEGORY_COLORS.get(cat_key, 0x6B7280),
            "fields": fields,
            "footer": {"text": f"AI 인텔리전스 · {today}"},
        })

    payload = {
        "content": f"🤖 **AI 엔지니어 인텔리전스** — {today}  `{total}건 큐레이션`",
        "embeds": embeds,
    }

    if dry_run:
        import json
        print("\n[DRY RUN] Discord 페이로드:")
        print(json.dumps(payload, ensure_ascii=False, indent=2)[:2000])
        return

    success = _post_webhook(webhook_url, payload)
    if success:
        print(f"✅ Discord 인텔리전스 피드 전송 성공 ({total}건, {len(embeds)}개 embed)")
    else:
        print("❌ Discord 인텔리전스 피드 전송 실패")
