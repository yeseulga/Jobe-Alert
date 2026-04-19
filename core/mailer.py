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
    }
    platform = job.get("platform", "?")
    color = platform_colors.get(platform, "#888888")

    return f"""
    <div style="border:1px solid #e0e0e0; border-radius:10px; padding:16px; margin-bottom:16px; background:#ffffff;">
      <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
        <span style="background:{color}; color:#fff; font-size:11px; font-weight:bold;
                     padding:2px 8px; border-radius:12px;">{platform}</span>
        <strong style="font-size:16px;">{job.get('company', '?')}</strong>
        <span style="margin-left:auto; font-size:18px;">{stars}</span>
      </div>
      <p style="margin:4px 0; font-size:14px; color:#333;"><b>📌 직무</b>: {job.get('title', '?')}</p>
      <p style="margin:4px 0; font-size:13px; color:#555;">💰 {job.get('salary') or '협의'} &nbsp;|&nbsp;
         📍 {job.get('location') or '미기재'} &nbsp;|&nbsp;
         ⏰ {job.get('deadline') or '상시모집'}</p>
      <p style="margin:4px 0; font-size:13px; color:#555;">🏢 {job.get('company_size') or '미기재'}
         &nbsp;|&nbsp; 📊 평점 {job.get('rating') or '-'}</p>
      <a href="{job.get('url', '#')}" style="display:inline-block; margin-top:10px;
         background:{color}; color:#fff; padding:6px 16px; border-radius:6px;
         text-decoration:none; font-size:13px; font-weight:bold;">공고 보기 →</a>
    </div>
    """


def build_html_body(jobs: list[dict]) -> str:
    today = datetime.now().strftime("%Y년 %m월 %d일")
    total = len(jobs)
    job_blocks = "\n".join(_format_job_html(i + 1, j) for i, j in enumerate(jobs[:MAX_JOBS_PER_EMAIL]))

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
