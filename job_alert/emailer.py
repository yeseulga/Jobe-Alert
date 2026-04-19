"""
이메일 템플릿 생성 및 Gmail SMTP 발송 — job_alert.emailer
환경변수: GMAIL_SENDER, GMAIL_APP_PASSWORD, MAIL_TO, RECIPIENT_NAME
"""
from __future__ import annotations
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from job_alert.config import (
    GMAIL_SENDER,
    GMAIL_APP_PASSWORD,
    MAIL_TO,
    RECIPIENT_NAME,
    MAX_JOBS_PER_EMAIL,
)

# 플랫폼별 브랜드 색상
_PLATFORM_COLOR: dict[str, str] = {
    "사람인":    "#E84545",
    "원티드":    "#36B37E",
    "잡코리아":  "#0052CC",
    "리멤버":    "#6554C0",
    "프로그래머스": "#00875A",
    "LinkedIn": "#0A66C2",
}


# ──────────────────────────────────────────────
# 텍스트 본문
# ──────────────────────────────────────────────

def _job_text(idx: int, job: dict) -> str:
    stars = "⭐" * min(job.get("score", 0), 5) or "📄"
    return (
        f"{idx}. {stars} [{job.get('platform','?')}] {job.get('company','?')}\n"
        f"   📌 직무     : {job.get('title','?')}\n"
        f"   💰 연봉     : {job.get('salary') or '협의'}\n"
        f"   🏢 기업규모 : {job.get('company_size') or '미기재'}\n"
        f"   📍 근무지   : {job.get('location') or '미기재'}\n"
        f"   ⏰ 마감기한 : {job.get('deadline') or '상시모집'}\n"
        f"   📊 기업평점 : {job.get('rating') or '-'}\n"
        f"   🔗 공고링크 : {job.get('url','링크 없음')}\n"
    )


def build_text(jobs: list[dict]) -> str:
    today = datetime.now().strftime("%Y년 %m월 %d일")
    sep = "─" * 45
    lines: list[str] = [
        f"{RECIPIENT_NAME}님, 오늘({today}) 맞춤 채용 공고 {len(jobs)}건을 끓여왔습니다! 🥣✨\n",
        "📬 오늘의 맞춤 채용 공고",
        sep, "",
    ]
    for i, job in enumerate(jobs[:MAX_JOBS_PER_EMAIL], 1):
        lines.append(_job_text(i, job))
        lines += [sep, ""]
    lines.append(f"📌 총 {len(jobs)}개의 맞춤 공고를 추천드렸습니다 🚀")
    return "\n".join(lines)


# ──────────────────────────────────────────────
# HTML 본문
# ──────────────────────────────────────────────

def _job_html(idx: int, job: dict) -> str:
    platform = job.get("platform", "?")
    color = _PLATFORM_COLOR.get(platform, "#888888")
    score = job.get("score", 0)
    stars = "⭐" * min(score, 5) if score > 0 else "📄"
    return f"""
<div style="border:1px solid #e0e0e0;border-radius:10px;padding:16px;margin-bottom:16px;background:#fff;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
    <span style="background:{color};color:#fff;font-size:11px;font-weight:bold;
                 padding:2px 8px;border-radius:12px;">{platform}</span>
    <strong style="font-size:15px;">{job.get('company','?')}</strong>
    <span style="margin-left:auto;font-size:18px;">{stars}</span>
  </div>
  <p style="margin:4px 0;font-size:14px;color:#222;"><b>📌 {job.get('title','?')}</b></p>
  <p style="margin:4px 0;font-size:13px;color:#555;">
    💰 {job.get('salary') or '협의'} &nbsp;|&nbsp;
    📍 {job.get('location') or '미기재'} &nbsp;|&nbsp;
    ⏰ {job.get('deadline') or '상시모집'}
  </p>
  <p style="margin:4px 0;font-size:13px;color:#555;">
    🏢 {job.get('company_size') or '미기재'} &nbsp;|&nbsp; 📊 {job.get('rating') or '-'}
  </p>
  <a href="{job.get('url','#')}"
     style="display:inline-block;margin-top:10px;background:{color};color:#fff;
            padding:6px 16px;border-radius:6px;text-decoration:none;
            font-size:13px;font-weight:bold;">공고 보기 →</a>
</div>"""


def build_html(jobs: list[dict]) -> str:
    today = datetime.now().strftime("%Y년 %m월 %d일")
    blocks = "\n".join(_job_html(i + 1, j) for i, j in enumerate(jobs[:MAX_JOBS_PER_EMAIL]))
    return f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"><title>맞춤 채용 공고</title></head>
<body style="font-family:'Apple SD Gothic Neo',Arial,sans-serif;background:#f5f5f5;padding:20px;">
<div style="max-width:640px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
              border-radius:12px;padding:28px 24px;margin-bottom:20px;text-align:center;">
    <h1 style="color:#fff;margin:0;font-size:22px;">📬 맞춤 채용 알림</h1>
    <p style="color:#e8e8ff;margin:8px 0 0;">{RECIPIENT_NAME}님, {today} 공고 {len(jobs)}건 도착!</p>
  </div>
  {blocks}
  <div style="text-align:center;color:#aaa;font-size:12px;margin-top:20px;">
    총 {len(jobs)}개 맞춤 공고 · 자동 발송
  </div>
</div>
</body>
</html>"""


# ──────────────────────────────────────────────
# 발송
# ──────────────────────────────────────────────

def send(jobs: list[dict], dry_run: bool = False) -> bool:
    """
    공고 리스트를 이메일로 발송한다.
    dry_run=True 이면 SMTP 전송 없이 텍스트 출력만.
    """
    if not jobs:
        print("[메일] 발송할 공고가 없습니다.")
        return False

    today = datetime.now().strftime("%m/%d")
    subject = f"[Job Alert] {today} 맞춤 채용 공고 {len(jobs)}건 도착 🚀"

    text_body = build_text(jobs)
    html_body = build_html(jobs)

    if dry_run:
        print("\n" + "=" * 60)
        print("[DRY RUN] 이메일 미리보기")
        print("=" * 60)
        print(text_body)
        return True

    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        print("[메일] GMAIL_SENDER / GMAIL_APP_PASSWORD 환경 변수 미설정")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = GMAIL_SENDER
        msg["To"] = MAIL_TO
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
            srv.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            srv.sendmail(GMAIL_SENDER, MAIL_TO, msg.as_string())

        print(f"[메일] ✅ 발송 완료 → {MAIL_TO} ({len(jobs)}건)")
        return True
    except Exception as e:
        print(f"[메일] ❌ 발송 실패: {e}")
        return False
