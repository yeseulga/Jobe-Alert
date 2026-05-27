import os
import re
import requests
from datetime import datetime
from pathlib import Path


def _reason_to_korean(reason: str, score: int) -> str:
    """점수 근거 코드 문자열 → 자연어 한국어 설명."""
    if not reason or reason == "매칭 키워드 없음":
        return f"키워드 매칭 없음 ({score}점)"

    parts = [p.strip() for p in reason.split("·")]
    high_kws, med_kws, combos = [], [], []

    for part in parts:
        combo_m = re.match(r"콤보\(([^)]+)\) \+(\d+)", part)
        if combo_m:
            combos.append((combo_m.group(1), int(combo_m.group(2))))
            continue
        kw_m = re.match(r"(.+?) \+(\d+)$", part)
        if kw_m:
            kw, pts = kw_m.group(1).strip(), int(kw_m.group(2))
            (high_kws if pts >= 2 else med_kws).append((kw, pts))

    lines = []
    if high_kws:
        kw_str = ", ".join(k for k, _ in high_kws)
        pts_sum = sum(p for _, p in high_kws)
        lines.append(f"핵심 기술 **{kw_str}** 매칭 (+{pts_sum}점)")
    if med_kws:
        kw_str = ", ".join(k for k, _ in med_kws)
        pts_sum = sum(p for _, p in med_kws)
        lines.append(f"관련 키워드 **{kw_str}** (+{pts_sum}점)")
    for combo_kws, bonus in combos:
        lines.append(f"**{combo_kws}** 동시 보유 콤보 보너스 (+{bonus}점)")

    summary = " | ".join(lines)
    return f"{summary} → 종합 **{score}점**"

_ROOT = Path(__file__).parent.parent


# ─────────────────────────────────────────────
# 부트캠프/공모전 추천 로더
# ─────────────────────────────────────────────

def _load_opportunities_summary() -> str:
    """bootcamps.yaml + competitions.yaml 에서 3~4개씩 섹션 분리, 마감일 포함."""
    sections = []
    try:
        import yaml
        bc_path = _ROOT / "opportunities" / "bootcamps.yaml"
        cm_path = _ROOT / "opportunities" / "competitions.yaml"

        if bc_path.exists():
            data = yaml.safe_load(bc_path.read_text(encoding="utf-8")) or {}
            boots = data.get("bootcamps", [])[:4]
            if boots:
                boot_lines = ["**(1) 부트캠프**"]
                for b in boots:
                    url = b.get("check_url") or b.get("careers_url") or b.get("provider_url") or ""
                    name_md = f"[{b['name']}]({url})" if url else b["name"]
                    cost = b.get("cost_range") or "확인필요"
                    deadline = b.get("deadline") or "확인필요"
                    boot_lines.append(f"🎓 **{name_md}**\n　비용: {cost} / 기간: {b.get('duration','?')}\n　마감: `{deadline}`")
                sections.append("\n".join(boot_lines))

        if cm_path.exists():
            data = yaml.safe_load(cm_path.read_text(encoding="utf-8")) or {}
            comps_raw = data.get("competitions", [])[:2] + data.get("hackathons", [])[:2]
            if comps_raw:
                comp_lines = ["**(2) 공모전·해커톤**"]
                for c in comps_raw:
                    url = c.get("check_url") or c.get("url") or ""
                    name_md = f"[{c['name']}]({url})" if url else c["name"]
                    prize = (c.get("prize") or {}).get("total") or "상금 확인필요"
                    deadline = c.get("deadline") or "확인필요"
                    comp_lines.append(f"🏅 **{name_md}**\n　상금: {prize} / 참가비: {c.get('cost','무료')}\n　마감: `{deadline}`")
                sections.append("\n".join(comp_lines))
    except Exception:
        pass

    return "\n\n".join(sections) if sections else ""


# ─────────────────────────────────────────────
# 메인 발송 함수
# ─────────────────────────────────────────────

def send_discord_notification(jobs: list[dict]):
    """수집된 공고 리스트를 디스코드 웹훅으로 전송."""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("⚠️ DISCORD_WEBHOOK_URL이 설정되지 않아 디스코드 알림을 건너뜁니다.")
        return

    if not jobs:
        return

    top_jobs = jobs[:5]  # Discord embed 최대 10개, 여유있게 5개

    # ── 요약 통계 ──────────────────────────────────────
    track_a = sum(1 for j in jobs if j.get("track_badge") == "A")
    track_b = sum(1 for j in jobs if j.get("track_badge") == "B")
    other = len(jobs) - track_a - track_b

    summary_parts = []
    if track_a:
        summary_parts.append(f"🏆 AI 자체솔루션 **{track_a}건**")
    if track_b:
        summary_parts.append(f"🤖 AI 활용 **{track_b}건**")
    if other:
        summary_parts.append(f"📄 기타 **{other}건**")

    content = (
        f"📬 **오늘의 맞춤 채용 공고 — {len(jobs)}건** ({datetime.now().strftime('%m/%d %H:%M')})\n"
        f"{' · '.join(summary_parts)}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

    # ── 준비 전략 embed (맨 앞) ─────────────────────────
    embeds = []
    opp_text = _load_opportunities_summary()
    if opp_text:
        embeds.append({
            "title": "📚 오늘의 준비 전략 — 병렬 준비 추천",
            "description": opp_text,
            "color": 0x16A34A,
            "footer": {"text": "부트캠프/공모전 · opportunities/ 폴더에서 수정 가능"},
        })

    # ── 공고별 embed ────────────────────────────────────

    def _f(v, fallback="-"):
        return str(v).strip() or fallback

    def _field(label, val, inline=True):
        """레이블  ·  값 형식 — 키 왼쪽, 값 오른쪽."""
        return {
            "name": f"{label}  ·  {_f(val)}",
            "value": "\u200b",
            "inline": inline,
        }

    _rank_symbols = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"]

    for idx, job in enumerate(top_jobs):
        score      = job.get("score", 0)
        reason     = job.get("score_reason", "")
        track      = job.get("track_badge", "")
        company    = job.get("company", "?")
        title      = job.get("title", "?")
        platform   = job.get("platform", "?")
        salary     = job.get("salary") or "협의"
        location   = job.get("location") or "미기재"
        deadline   = job.get("deadline") or "상시모집"
        first_seen = job.get("first_seen_label") or "오늘 등록"
        welfare    = job.get("welfare") or ""
        jp_rating  = job.get("jobplanet_rating")
        jp_reviews = job.get("jobplanet_reviews") or []
        jp_url     = job.get("jobplanet_url") or ""
        ai_summary = job.get("ai_summary") or ""
        desc       = job.get("description") or ""

        # 트랙 설정
        if track == "A":
            track_label = "🏆 AI 자체솔루션"
            color = 0x7C3AED
        elif track == "B":
            track_label = "🤖 AI 활용"
            color = 0x0369A1
        else:
            track_label = "📄"
            color = 0x6B7280

        # embed 제목 (순위 번호 포함)
        rank = _rank_symbols[idx] if idx < len(_rank_symbols) else f"#{idx+1}"
        urgent_tag = " 🔥마감임박" if job.get("deadline_urgent") else ""
        embed_title = f"{rank} {track_label} | {company} — {title}{urgent_tag}"
        if len(embed_title) > 256:
            embed_title = embed_title[:253] + "..."

        # description: AI 요약 우선, 없으면 공고 본문 앞부분
        if ai_summary:
            clean = re.sub(r"[#*]+", "", ai_summary).strip()
            desc_text = clean[:200] + ("..." if len(clean) > 200 else "")
        elif desc:
            desc_text = desc[:150] + ("..." if len(desc) > 150 else "")
        else:
            desc_text = "—"

        # 필드 구성
        fields = [
            _field("플랫폼",  platform),
            _field("점수",    f"{score}점"),
            _field("등록",    first_seen),
            _field("연봉",    salary),
            _field("근무지",  location),
            _field("마감",    deadline),
        ]

        # 모집분야 + 하는 역할 통합
        role_title = title.replace(company, "").strip(" —-|[]()").strip()
        if not role_title or len(role_title) < 3:
            role_title = title
        # description에서 역할 설명 추출 (첫 줄 ~ 150자)
        role_desc = ""
        if desc:
            clean_desc = re.sub(r"\s+", " ", desc).strip()
            role_desc = clean_desc[:150] + ("..." if len(clean_desc) > 150 else "")
        fields.append({
            "name": f"💼 모집분야  ·  {role_title[:80]}",
            "value": role_desc or "\u200b",
            "inline": False,
        })

        # 복지
        if welfare:
            fields.append({
                "name": "🎁 복지",
                "value": welfare[:100],
                "inline": False,
            })

        # 잡플래닛 — 하이퍼링크는 value에 넣어야 클릭 가능
        if jp_rating:
            stars = "★" * round(jp_rating) + "☆" * (5 - round(jp_rating))
            jp_name = f"📊 잡플래닛  ·  {stars} {jp_rating}/5.0"
            jp_value_parts = []
            if jp_reviews:
                jp_value_parts.append(jp_reviews[0][:80])
            if jp_url:
                jp_value_parts.append(f"[검색하기 →]({jp_url})")
            fields.append({
                "name": jp_name,
                "value": "\n".join(jp_value_parts) or "\u200b",
                "inline": False,
            })
        elif jp_url:
            fields.append({
                "name": "📊 잡플래닛",
                "value": f"[{company} 검색하기 →]({jp_url})",
                "inline": False,
            })

        # 점수 근거 — 자연어 설명
        fields.append({
            "name": "🔍 점수 근거",
            "value": _reason_to_korean(reason, score),
            "inline": False,
        })

        job_url = job.get("url") or ""
        embed = {
            "title": embed_title,
            "description": desc_text,
            "color": color,
            "fields": fields,
            "footer": {"text": f"Job Alert · {datetime.now().strftime('%Y-%m-%d %H:%M')}"},
        }
        if job_url:
            embed["url"] = job_url

        embeds.append(embed)

    payload = {"content": content, "embeds": embeds}

    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 204:
            print("✅ 디스코드 알림 전송 성공")
        else:
            print(f"❌ 디스코드 알림 전송 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 디스코드 연동 중 오류: {e}")
