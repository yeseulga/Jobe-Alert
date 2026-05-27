"""
Job Alert 메인 실행 스크립트
사용법:
  python main.py              # 전체 실행 (수집 → 필터 → 발송)
  python main.py --dry-run    # 이메일 발송 없이 콘솔 출력만
  python main.py --no-mark    # DB 기록 없이 실행 (테스트용)
"""
from __future__ import annotations
import argparse
import re
import sys
import traceback
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv()

from core.db import init_db, deduplicate, mark_as_sent, record_seen
from core.filter import filter_and_score
from core.mailer import send_email
from core.discord_notifier import send_discord_notification
from core.config import MIN_SCORE_TO_SEND, MAX_JOBS_PER_EMAIL
from core.cv_generator import attach_drafts
from core.enricher import enrich_jobs

# 스크래퍼 임포트
from scrapers import saramin, jobkorea, programmers, linkedin, wanted, remember, rocketpunch


# ==============================================================
# 마감일 파싱
# ==============================================================

def _parse_deadline(deadline_str: str) -> datetime | None:
    """
    다양한 형식의 마감일 문자열을 datetime으로 변환.
    파싱 불가(상시모집 등)는 None 반환.
    """
    if not deadline_str:
        return None
    s = deadline_str.strip()
    if not s or re.search(r"상시|미정|채용|접수|확인|없음|수시", s):
        return None

    now = datetime.now()

    # YYYY-MM-DD or YYYY.MM.DD
    m = re.search(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", s)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass

    # MM/DD or MM.DD or MM월DD일 (연도 없음 → 올해 or 내년)
    m = re.search(r"(\d{1,2})[./월](\d{1,2})[일]?", s)
    if m:
        try:
            month, day = int(m.group(1)), int(m.group(2))
            candidate = datetime(now.year, month, day)
            if candidate < now - timedelta(days=1):
                candidate = datetime(now.year + 1, month, day)
            return candidate
        except ValueError:
            pass

    return None


def _tag_deadline(jobs: list[dict]) -> list[dict]:
    """
    각 공고에 deadline_expired / deadline_urgent 플래그 추가.
    - deadline_expired: 마감일이 어제 이전 → 발송 목록에서 제외
    - deadline_urgent:  마감일이 7일 이내 → '마감 임박' 뱃지 표시
    """
    now = datetime.now()
    urgent_cutoff = now + timedelta(days=7)
    result = []
    for job in jobs:
        dt = _parse_deadline(job.get("deadline", ""))
        if dt is not None and dt.date() < now.date():
            print(f"  [만료] {job.get('title','')} — 마감: {job.get('deadline','')}")
            continue
        job["deadline_urgent"] = dt is not None and dt <= urgent_cutoff
        result.append(job)
    return result


# ==============================================================
# 수집
# ==============================================================

def collect_all_jobs(skip_playwright: bool = False) -> list[dict]:
    """모든 플랫폼에서 공고를 수집한다."""
    all_jobs: list[dict] = []

    scrapers = [
        ("사람인",      saramin.scrape,      {}),
        ("잡코리아",    jobkorea.scrape,     {}),
        ("프로그래머스", programmers.scrape,  {}),
        ("LinkedIn",   linkedin.scrape,     {}),
        ("원티드",      wanted.scrape,       {}),
        ("로켓펀치",    rocketpunch.scrape,  {}),
    ]

    if not skip_playwright:
        scrapers.append(("리멤버", remember.scrape, {}))

    for platform, fn, kwargs in scrapers:
        print(f"\n{'=' * 50}")
        print(f"  [{platform}] 수집 시작")
        print(f"{'=' * 50}")
        try:
            jobs = fn(**kwargs)
            print(f"  [{platform}] 원본 수집: {len(jobs)}건")
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"  [{platform}] 오류 발생: {e}")
            traceback.print_exc()

    return all_jobs


# ==============================================================
# 메인
# ==============================================================

def main():
    parser = argparse.ArgumentParser(description="Job Alert — AI 맞춤 채용 공고 발송")
    parser.add_argument("--dry-run", action="store_true", help="이메일 발송 없이 본문 미리보기")
    parser.add_argument("--no-mark", action="store_true", help="DB에 발송 기록 저장 안 함 (테스트)")
    parser.add_argument("--skip-playwright", action="store_true", help="Playwright 스크래퍼 건너뜀 (리멤버)")
    parser.add_argument("--platforms", nargs="+",
                        choices=["saramin", "jobkorea", "programmers", "linkedin", "wanted", "remember", "rocketpunch"],
                        help="특정 플랫폼만 실행")
    args = parser.parse_args()

    print(f"\n🚀 Job Alert 시작 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # DB 초기화
    init_db()

    # 1단계: 수집
    print("\n📡 채용 공고 수집 중...")
    raw_jobs = collect_all_jobs(skip_playwright=args.skip_playwright)
    print(f"\n총 원본 수집: {len(raw_jobs)}건")

    if not raw_jobs:
        print("수집된 공고가 없습니다. 종료합니다.")
        sys.exit(0)

    # 2단계: 동일 실행 내 중복 제거 (sent_jobs 차단 없음 — 매일 재발송 허용)
    print("\n🔍 중복 공고 제거 중...")
    unique_jobs = deduplicate(raw_jobs)
    print(f"중복 제거 후: {len(unique_jobs)}건")

    # 2.5단계: 마감 만료 공고 제외 + 임박 뱃지 태깅
    unique_jobs = _tag_deadline(unique_jobs)
    print(f"마감 만료 제외 후: {len(unique_jobs)}건")

    # 3단계: 키워드 필터링 + 점수 정렬
    print("\n🎯 키워드 필터링 및 점수 산정 중...")
    filtered_jobs = filter_and_score(unique_jobs)
    print(f"필터링 후: {len(filtered_jobs)}건")

    # 최소 점수 이상만 발송 (MIN_SCORE_TO_SEND = 0이면 전체)
    final_jobs = [j for j in filtered_jobs if j.get("score", 0) >= MIN_SCORE_TO_SEND]
    final_jobs = final_jobs[:MAX_JOBS_PER_EMAIL]
    print(f"최종 발송 대상: {len(final_jobs)}건")

    # 0건이어도 알림 메일 전송하도록 유지 (본문에 0건 안내)

    # 점수별 분포 출력
    print("\n📊 점수 분포:")
    score_dist: dict[int, int] = {}
    for j in final_jobs:
        s = j.get("score", 0)
        score_dist[s] = score_dist.get(s, 0) + 1
    for score in sorted(score_dist.keys(), reverse=True):
        print(f"  {score}점: {score_dist[score]}건")

    # 3.5단계: 공고 보강 (Track 뱃지, 잡플래닛, AI 요약, 복지 등)
    print("\n🔬 공고 보강 중 (Track 분류 / AI 요약 / 잡플래닛)...")
    final_jobs = enrich_jobs(final_jobs)

    # track/score 확정 후 job_history 업데이트 (캘린더 데이터)
    for job in final_jobs:
        record_seen(job)

    # 3.6단계: Track A 우선 + 점수 내림차순 재정렬
    def _sort_key(j: dict):
        track = j.get("track_badge", "")
        track_order = 0 if track == "A" else 1 if track == "B" else 2
        return (track_order, -j.get("score", 0))
    final_jobs.sort(key=_sort_key)

    # 3.7단계: 자소서 초안 자동 생성 (ANTHROPIC_API_KEY 있을 때만)
    print("\n✍️  자소서 초안 생성 중...")
    final_jobs = attach_drafts(final_jobs, top_n=3)

    # 4단계: 이메일 발송
    print("\n📧 이메일 발송 중...")
    success = send_email(final_jobs, dry_run=args.dry_run)

    # 4.5단계: 디스코드 알림 발송 (추가)
    send_discord_notification(final_jobs)

    # 5단계: DB 기록
    if success and not args.dry_run and not args.no_mark:
        mark_as_sent(final_jobs)
        print(f"✅ DB에 {len(final_jobs)}건 기록 완료")

    print(f"\n✅ Job Alert 완료 — {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    main()
