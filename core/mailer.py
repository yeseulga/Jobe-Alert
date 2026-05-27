"""
이메일 템플릿 생성 및 SMTP 발송 모듈 (NAVER/Gmail 지원)
"""
import smtplib
import os
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from core.config import RECIPIENT_NAME, MAX_JOBS_PER_EMAIL

load_dotenv()


# ==============================================================
# 텍스트 이메일 템플릿
# ==============================================================

def _format_job_text(idx: int, job: dict) -> str:
    """개별 공고를 텍스트 블록으로 변환."""
    score_stars = "⭐" * min(job.get("score", 0), 5) or "📄"
    deadline = job.get("deadline") or "상시모집"
    salary = job.get("salary") or "협의"
    location = job.get("location") or "미기재"
    company_size = job.get("company_size") or "미기재"
    rating = job.get("rating") or "-"

    return (
        f"{idx}. {score_stars} [{job.get('platform', '?')}] {job.get('company', '?')}\n"
        f"   📌 직무     : {job.get('title', '?')}\n"
        f"   💰 연봉     : {salary}\n"
        f"   🏢 기업규모 : {company_size}\n"
        f"   📍 근무지   : {location}\n"
        f"   ⏰ 마감기한 : {deadline}\n"
        f"   📊 기업평점 : {rating}\n"
        f"   🔗 공고링크 : {job.get('url', '링크 없음')}\n"
    )


def build_text_body(jobs: list[dict]) -> str:
    """전체 이메일 본문 (텍스트) 생성."""
    today = datetime.now().strftime("%Y년 %m월 %d일")
    total = len(jobs)
    sep = "─" * 45

    lines = [
        f"{RECIPIENT_NAME}님, 오늘({today}) 맞춤 채용 공고 {total}건을 끓여왔습니다! 🥣✨\n",
        "",
        f"📬 오늘의 맞춤 채용 공고",
        sep,
        "",
    ]

    for i, job in enumerate(jobs[:MAX_JOBS_PER_EMAIL], start=1):
        lines.append(_format_job_text(i, job))
        lines.append(sep)
        lines.append("")

    lines += [
        f"📌 총 {total}개의 맞춤 공고를 추천드렸습니다 🚀",
        "",
        "본 메일은 자동 발송되었습니다.",
    ]

    return "\n".join(lines)


# ==============================================================
# HTML 이메일 템플릿
# ==============================================================

def _format_cv_draft_html(draft: str) -> str:
    """자소서 초안이 있으면 접이식 섹션으로 렌더링."""
    if not draft:
        return ""
    # 마크다운 줄바꿈 → <br>로 변환 (간단 처리)
    draft_html = draft.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    return f"""
      <details style="margin-top:12px; border-top:1px dashed #ddd; padding-top:10px;">
        <summary style="cursor:pointer; font-size:13px; font-weight:bold; color:#764ba2;">
          ✍️ 자소서 초안 보기 (클릭)
        </summary>
        <div style="margin-top:8px; padding:12px; background:#f9f5ff; border-radius:6px;
                    font-size:13px; line-height:1.7; color:#333; white-space:pre-wrap;">
          {draft_html}
        </div>
      </details>"""


def _format_job_html(idx: int, job: dict) -> str:
    score = job.get("score", 0)
    stars = "⭐" * min(score, 5) if score > 0 else "📄"
    platform_colors = {
        "사람인": "#FF6B6B",
        "원티드": "#36B37E",
        "잡코리아": "#0052CC",
        "리멤버": "#6554C0",
        "프로그래머스": "#00875A",
        "LinkedIn": "#0A66C2",
        "로켓펀치": "#FF5B35",
    }
    platform = job.get("platform", "?")
    color = platform_colors.get(platform, "#888888")

    # Track A 뱃지
    track = job.get("track_badge", "")
    track_badge = ""
    if track == "A":
        track_badge = '<span style="background:#7c3aed; color:#fff; font-size:10px; font-weight:bold; padding:2px 7px; border-radius:10px; margin-left:4px;">🏆 AI 자체솔루션</span>'
    elif track == "B":
        track_badge = '<span style="background:#0369a1; color:#fff; font-size:10px; font-weight:bold; padding:2px 7px; border-radius:10px; margin-left:4px;">🤖 AI 활용</span>'

    # 잡플래닛 평점 + 후기
    jp_rating = job.get("jobplanet_rating")
    jp_reviews = job.get("jobplanet_reviews", [])
    jp_url = job.get("jobplanet_url", "")
    jp_block = ""
    if jp_rating:
        stars_count = round(jp_rating)
        jp_stars = "★" * stars_count + "☆" * (5 - stars_count)
        jp_block = f'<span style="color:#f59e0b;">{jp_stars}</span> <b style="font-size:13px;">{jp_rating}/5.0</b> <span style="font-size:11px; color:#888;">(잡플래닛)</span>'
        if jp_reviews:
            reviews_html = " · ".join(f'"{r}"' for r in jp_reviews[:2])
            jp_block += f'<br><span style="font-size:11px; color:#555; font-style:italic;">{reviews_html}</span>'
    elif jp_url:
        jp_block = f'<a href="{jp_url}" style="font-size:12px; color:#0369a1; text-decoration:none;">📊 잡플래닛 후기 확인 →</a>'

    # 복지
    welfare = job.get("welfare", "")
    welfare_block = f'<p style="margin:4px 0; font-size:12px; color:#7c3aed;">🎁 {welfare}</p>' if welfare else ""

    # 등록 시점
    first_seen = job.get("first_seen_label", "오늘 등록")
    first_seen_color = "#16a34a" if "오늘" in first_seen else "#6b7280"

    # AI 요약
    ai_summary = job.get("ai_summary", "")
    ai_block = ""
    if ai_summary:
        # \n → <br>, 특수문자 이스케이프
        ai_html = (ai_summary
                   .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                   .replace("\n", "<br>"))
        ai_block = f"""
      <div style="margin-top:10px; padding:10px 12px; background:#f8fafc;
                  border-left:3px solid #7c3aed; border-radius:0 6px 6px 0; font-size:13px; color:#334155; line-height:1.6;">
        {ai_html}
      </div>"""

    return f"""
    <div style="border:1px solid #e0e0e0; border-radius:10px; padding:16px; margin-bottom:16px; background:#ffffff;">
      <!-- 헤더 행: 플랫폼 + 회사명 + Track 뱃지 + 별점 -->
      <div style="display:flex; align-items:center; gap:6px; margin-bottom:8px; flex-wrap:wrap;">
        <span style="background:{color}; color:#fff; font-size:11px; font-weight:bold;
                     padding:2px 8px; border-radius:12px;">{platform}</span>
        <strong style="font-size:15px;">{job.get('company', '?')}</strong>
        {track_badge}
        <span style="margin-left:auto; font-size:16px;">{stars}</span>
      </div>

      <!-- 직무 -->
      <p style="margin:4px 0; font-size:14px; color:#111; font-weight:600;">{job.get('title', '?')}</p>

      <!-- 메타 정보 -->
      <p style="margin:5px 0; font-size:12px; color:#555;">
        💰 {job.get('salary') or '연봉 미기재'} &nbsp;|&nbsp;
        📍 {job.get('location') or '미기재'} &nbsp;|&nbsp;
        ⏰ {job.get('deadline') or '상시모집'}
      </p>
      <p style="margin:3px 0; font-size:12px; color:{first_seen_color};">
        🕐 {first_seen}
      </p>

      <!-- 잡플래닛 평점 -->
      <p style="margin:5px 0;">{jp_block}</p>

      <!-- 복지 -->
      {welfare_block}

      <!-- AI 요약 -->
      {ai_block}

      <!-- 공고 보기 버튼 -->
      <a href="{job.get('url', '#')}" style="display:inline-block; margin-top:12px;
         background:{color}; color:#fff; padding:7px 18px; border-radius:6px;
         text-decoration:none; font-size:13px; font-weight:bold;">공고 보기 →</a>

      <!-- 자소서 초안 -->
      {_format_cv_draft_html(job.get('cv_draft', ''))}
    </div>
    """


def _build_summary_bar(jobs: list[dict]) -> str:
    """Track A/B 요약 바 HTML."""
    track_a = sum(1 for j in jobs if j.get("track_badge") == "A")
    track_b = sum(1 for j in jobs if j.get("track_badge") == "B")
    other = len(jobs) - track_a - track_b
    parts = []
    if track_a:
        parts.append(f'<span style="background:#7c3aed; color:#fff; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:bold;">🏆 AI 자체솔루션 {track_a}건</span>')
    if track_b:
        parts.append(f'<span style="background:#0369a1; color:#fff; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:bold;">🤖 AI 활용 {track_b}건</span>')
    if other:
        parts.append(f'<span style="background:#6b7280; color:#fff; padding:3px 10px; border-radius:12px; font-size:12px;">기타 {other}건</span>')
    return ' &nbsp;'.join(parts)


def build_html_body(jobs: list[dict]) -> str:
    today = datetime.now().strftime("%Y년 %m월 %d일")
    total = len(jobs)
    job_blocks = "\n".join(_format_job_html(i + 1, j) for i, j in enumerate(jobs[:MAX_JOBS_PER_EMAIL]))
    summary_bar = _build_summary_bar(jobs)

    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head><meta charset="UTF-8"><title>맞춤 채용 공고</title></head>
    <body style="font-family:'Apple SD Gothic Neo',Arial,sans-serif; background:#f5f5f5; padding:20px;">
      <div style="max-width:640px; margin:0 auto;">
        <!-- 헤더 -->
        <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
                    border-radius:12px; padding:28px 24px; margin-bottom:20px; text-align:center;">
          <h1 style="color:#fff; margin:0; font-size:22px;">📬 맞춤 채용 알림</h1>
          <p style="color:#e8e8ff; margin:8px 0 0;">{RECIPIENT_NAME}님, {today} 공고 {total}건 도착!</p>
        </div>

        <!-- Track 요약 바 -->
        <div style="background:#fff; border-radius:10px; padding:12px 16px; margin-bottom:16px;
                    display:flex; gap:8px; flex-wrap:wrap; align-items:center;">
          <span style="font-size:12px; color:#6b7280; margin-right:4px;">오늘 공고</span>
          {summary_bar}
        </div>

        <!-- 공고 목록 -->
        {job_blocks}

        <!-- 푸터 -->
        <div style="text-align:center; color:#aaa; font-size:12px; margin-top:20px;">
          총 {total}개의 맞춤 공고 · 본 메일은 자동 발송되었습니다
        </div>
      </div>
    </body>
    </html>
    """


# ==============================================================
# 발송
# ==============================================================

def send_email(jobs: list[dict], dry_run: bool = False) -> bool:
    """
    필터링·정렬된 공고를 이메일로 발송한다.

    Args:
        jobs: 발송할 공고 리스트
        dry_run: True이면 SMTP 전송 없이 본문만 출력

    Returns:
        발송 성공 여부
    """
    # SMTP provider 선택
    provider = (os.getenv("SMTP_PROVIDER") or "naver").lower()
    # 수신자
    recipient = os.getenv("MAIL_TO") or os.getenv("RECIPIENT_EMAIL")

    today = datetime.now().strftime("%m/%d")
    subject = f"[Job Alert] {today} 맞춤 채용 공고 {len(jobs)}건 도착 🚀"

    if not jobs:
        # 0건이라도 알림 메일 전송
        text_body = f"오늘({today}) 조건에 맞는 채용 공고가 0건이었습니다.\n내일 다시 더 신선한 공고를 끓여올게요! 🥣✨"
        html_body = f"""<!DOCTYPE html><html><body>
        <div style="font-family:Arial,sans-serif;max-width:640px;margin:0 auto;">
          <h2>📬 맞춤 채용 알림</h2>
          <p>오늘({today}) 조건에 맞는 채용 공고가 0건이었습니다.</p>
          <p>내일 다시 더 신선한 공고를 끓여올게요! 🥣✨</p>
        </div>
        </body></html>"""
    else:
        text_body = build_text_body(jobs)
        html_body = build_html_body(jobs)

    if dry_run:
        print("\n" + "=" * 60)
        print("[DRY RUN] 이메일 본문 미리보기")
        print("=" * 60)
        print(text_body)
        return True

    # Provider별 자격 정보 읽기
    if provider == "gmail":
        user = os.getenv("GMAIL_SENDER") or os.getenv("GMAIL_USER")
        password = os.getenv("GMAIL_APP_PASSWORD")
        smtp_host, smtp_port = "smtp.gmail.com", 465
        if not recipient:
            recipient = user
        if not user or not password or not recipient:
            print("[메일] Gmail 자격 정보(GMAIL_SENDER/GMAIL_USER, GMAIL_APP_PASSWORD) 또는 MAIL_TO가 없습니다.")
            return False
    else:
        # NAVER 기본
        user = os.getenv("NAVER_SENDER")
        password = os.getenv("NAVER_PASSWORD")
        smtp_host, smtp_port = "smtp.naver.com", 465
        if not recipient:
            recipient = user
        if not user or not password or not recipient:
            print("[메일] NAVER_SENDER, NAVER_PASSWORD 또는 MAIL_TO가 없습니다.")
            return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = user
        msg["To"] = recipient

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            if os.getenv("SMTP_DEBUG") == "1":
                server.set_debuglevel(1)
            server.login(user, password)
            server.sendmail(user, recipient, msg.as_string())

        print(f"[메일] ✅ 발송 완료 → {recipient} ({len(jobs)}건)")
        return True

    except Exception as e:
        print(f"[메일] ❌ 발송 실패: {e}")
        return False
