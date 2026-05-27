"""Discord AI 인텔리전스 피드 발송 — 4개 카테고리 embed, 429 backoff."""
from __future__ import annotations
import os
import time
from datetime import datetime

import requests

from .config import (
    CATEGORIES,
    DISCORD_RETRY_DELAYS,
    IMPACT_AREAS,
    MAX_ITEMS_PER_CATEGORY,
    TOP_PICKS_COUNT,
)
from .terms import get_daily_terms

_CATEGORY_COLORS = {
    "research":   0x6366F1,   # 인디고
    "skills":     0x0EA5E9,   # 하늘
    "model":      0xF59E0B,   # 앰버
    "ecosystem":  0x10B981,   # 에메랄드
}
_TOP_COLOR = 0xFF4500  # 오렌지레드 — 핫이슈


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


def _item_field(item: dict, show_cat_badge: bool = False) -> dict:
    """아이템 하나를 Discord embed field dict로 변환."""
    title = item["title"][:80]
    summary = item.get("summary_ko") or item.get("summary", "")
    summary = summary[:200]
    apply_tip = item.get("apply_tip", "")[:100]
    source = item.get("source", "")
    url = item.get("url", "")
    score = item.get("relevance_score", 0)

    impact_tags = "  ".join(
        IMPACT_AREAS[ia] for ia in item.get("impact_areas", []) if ia in IMPACT_AREAS
    )

    # TOP PICKS 섹션에서는 카테고리 뱃지 표시
    cat_badge = ""
    if show_cat_badge:
        cat_key = item.get("_cat_key", "research")
        cat_badge = CATEGORIES.get(cat_key, ("",))[0] + "  "

    # 관련성 점수 시각화 (8이상 🔥, 7 ⭐, 나머지 없음)
    score_badge = "🔥 " if score >= 8 else ("⭐ " if score >= 7 else "")

    value_parts = []
    if summary:
        value_parts.append(summary)
    if apply_tip:
        value_parts.append(f"💡 **써먹기:** {apply_tip}")
    if impact_tags:
        value_parts.append(impact_tags)

    source_line = f"출처: {source}"
    if url:
        source_line += f"  ·  [원문 🔗]({url})"
    value_parts.append(f"-# {source_line}")  # Discord subtext (작게 표시)

    return {
        "name": f"{score_badge}{cat_badge}{title}",
        "value": "\n".join(value_parts),
        "inline": False,
    }


def _chunk_embeds(embeds: list[dict], max_chars: int = 5500) -> list[list[dict]]:
    """embed 리스트를 Discord 6000자 제한 이하로 청크 분할."""
    import json
    chunks: list[list[dict]] = []
    current: list[dict] = []
    current_size = 0
    for embed in embeds:
        size = len(json.dumps(embed, ensure_ascii=False))
        if current_size + size > max_chars and current:
            chunks.append(current)
            current, current_size = [embed], size
        else:
            current.append(embed)
            current_size += size
    if current:
        chunks.append(current)
    return chunks


def send_digest(categorized_items: dict[str, list[dict]], dry_run: bool = False):
    """카테고리별 embed + 핫이슈 TOP embed를 Discord로 발송."""
    webhook_url = os.getenv("DISCORD_INTELLIGENCE_WEBHOOK_URL")
    if not webhook_url:
        raise EnvironmentError(
            "DISCORD_INTELLIGENCE_WEBHOOK_URL이 설정되지 않았습니다. "
            ".env 또는 GitHub Secrets에 추가하세요."
        )

    today = datetime.now().strftime("%Y-%m-%d (%a)")
    total = sum(len(v) for v in categorized_items.values())

    if total == 0:
        print("⚠️  발송할 AI 뉴스 아이템이 없습니다. 용어 섹션만 발송합니다.")

    embeds = []

    # ── 🔥 오늘의 핫이슈 TOP embed ──────────────────────────────
    all_items: list[dict] = []
    for cat_key, items in categorized_items.items():
        for item in items:
            item["_cat_key"] = cat_key
            all_items.append(item)

    top_items = sorted(all_items, key=lambda x: x.get("relevance_score", 0), reverse=True)[:TOP_PICKS_COUNT]

    if top_items:
        top_fields = [_item_field(item, show_cat_badge=True) for item in top_items]
        embeds.append({
            "title": "🔥  오늘의 핫이슈 TOP",
            "description": "관련성 높은 아이템 우선 큐레이션",
            "color": _TOP_COLOR,
            "fields": top_fields,
            "footer": {"text": f"AI 인텔리전스 · {today}"},
        })

    # ── 카테고리별 embed ─────────────────────────────────────────
    for cat_key, (emoji, cat_name, cat_desc) in CATEGORIES.items():
        items = sorted(
            categorized_items.get(cat_key, []),
            key=lambda x: x.get("relevance_score", 0),
            reverse=True,
        )[:MAX_ITEMS_PER_CATEGORY]
        if not items:
            continue

        fields = [_item_field(item) for item in items]
        embeds.append({
            "title": f"{emoji}  {cat_name}",
            "description": f"*{cat_desc}*",
            "color": _CATEGORY_COLORS.get(cat_key, 0x6B7280),
            "fields": fields,
            "footer": {"text": f"AI 인텔리전스 · {today}"},
        })

    # ── 📚 오늘의 IT 용어 embed ──────────────────────────────────
    daily_terms = get_daily_terms(2)
    term_fields = []
    for term, category, definition, example in daily_terms:
        term_fields.append({
            "name": f"📖  {term}  |  *{category}*",
            "value": f"{definition}\n> {example}",
            "inline": False,
        })
    if term_fields:
        embeds.append({
            "title": "📚  오늘의 IT 용어",
            "description": "몰랐으면 오늘 알고 가기",
            "color": 0x8B5CF6,  # 보라
            "fields": term_fields,
            "footer": {"text": f"AI 인텔리전스 · {today}"},
        })

    content = (
        f"🤖  **AI 엔지니어 인텔리전스** — {today}\n"
        + (f"> 오늘의 AI 동향 `{total}건` 큐레이션 완료. 🔥 핫이슈부터 확인하세요!" if total > 0
           else "> 오늘은 신규 AI 뉴스가 없습니다. 📚 용어는 매일 업데이트!")
    )
    payload = {
        "content": content,
        "embeds": embeds,
    }

    # embed가 많으면 여러 메시지로 분할 (Discord 6000자 제한)
    chunks = _chunk_embeds(embeds)

    if dry_run:
        import json
        print(f"\n[DRY RUN] {len(chunks)}개 메시지로 분할:")
        for i, chunk in enumerate(chunks):
            p = {"content": content if i == 0 else "", "embeds": chunk}
            print(f"\n--- 메시지 {i+1} ({len(chunk)}개 embed) ---")
            print(json.dumps(p, ensure_ascii=False, indent=2)[:2000])
        return

    success_count = 0
    for i, chunk in enumerate(chunks):
        p = {"content": content if i == 0 else "", "embeds": chunk}
        if _post_webhook(webhook_url, p):
            success_count += 1
        else:
            print(f"❌ 메시지 {i+1}/{len(chunks)} 전송 실패")

    if success_count == len(chunks):
        print(f"✅ Discord 인텔리전스 피드 전송 성공 ({total}건, {len(embeds)}개 embed, {len(chunks)}개 메시지)")
    else:
        print(f"⚠️  일부 전송 실패 ({success_count}/{len(chunks)} 메시지)")
