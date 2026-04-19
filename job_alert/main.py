"""
Job Alert — 메인 엔드포인트
실행: python -m job_alert.main [--dry-run] [--no-mark]
"""
from __future__ import annotations
import argparse
import sys
import traceback
from datetime import datetime

# .env 로드 (GitHub Actions 에선 환경 변수로 주입됨)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from job_alert.db import init_db, deduplicate, mark_sent
from job_alert.filtering import filter_and_score
from job_alert.emailer import send
from job_alert.config import MIN_SCORE_TO_SEND, MAX_JOBS_PER_EMAIL

from job_alert.scrapers import saramin, jobkorea, programmers, linkedin, wanted


# ──────────────────────────────────────────────
# 수집
# ──────────────────────────────────────────────

def collect_all() -> list[dict]:
    all_jobs: list[dict] = []

    _scrapers = [
        ("사람인",       saramin.scrape,      {}),
        ("잡코리아",     jobkorea.scrape,     {}),
        ("프로그래머스",  programmers.scrape,  {}),
        ("원티드",       wanted.scrape,       {}),
        ("LinkedIn",    linkedin.scrape,     {}),
    ]

    for name, fn, kwargs in _scrapers:
        print(f"\n{'=' * 50}")
        print(f"  [{name}] 수집 시작")
        print(f"{'=' * 50}")
        try:
            jobs = fn(**kwargs)
            print(f"  [{name}] 원본 수집: {len(jobs)}건")
            all_jobs.extend(jobs)
        except Exception:
            print(f"  [{name}] ⚠️  수집 실패:")
            traceback.print_exc()

    return all_jobs


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Job Alert — AI 맞춤 채용 공고 발송")
    parser.add_argument("--dry-run",  action="store_true", help="이메일 발송 없이 본문 미리보기")
    parser.add_argument("--no-mark", action="store_true", help="DB 기록 저장 안 함 (테스트)")
    args = parser.parse_args()

    print(f"\n🚀 Job Alert 시작 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. DB 초기화
    init_db()

    # 2. 수집
    print("\n📡 채용 공고 수집 중...")
    raw = collect_all()
    print(f"\n총 원본 수집: {len(raw)}건")

    if not raw:
        print("수집된 공고가 없습니다. 종료.")
        sys.exit(0)

    # 3. 중복 제거
    print("\n🔍 중복 공고 제거 중...")
    unique = deduplicate(raw)
    print(f"중복 제거 후: {len(unique)}건")

    # 4. 필터링 + 점수 정렬
    print("\n🎯 키워드 필터링 및 점수 산정 중...")
    filtered = filter_and_score(unique)
    print(f"필터링 후: {len(filtered)}건")

    # 5. 최소 점수 + 최대 개수 적용
    final = [j for j in filtered if j.get("score", 0) >= MIN_SCORE_TO_SEND]
    final = final[:MAX_JOBS_PER_EMAIL]
    print(f"최종 발송 대상: {len(final)}건")

    if not final:
        print("\n발송할 공고가 없습니다.")
        sys.exit(0)

    # 점수 분포 출력
    score_dist: dict[int, int] = {}
    for j in final:
        s = j.get("score", 0)
        score_dist[s] = score_dist.get(s, 0) + 1
    print("\n📊 점수 분포:")
    for sc in sorted(score_dist, reverse=True):
        print(f"  {sc}점: {score_dist[sc]}건")

    # 6. 이메일 발송
    print("\n📧 이메일 발송 중...")
    success = send(final, dry_run=args.dry_run)

    # 7. DB 기록
    if success and not args.dry_run and not args.no_mark:
        mark_sent(final)
        print(f"✅ DB에 {len(final)}건 기록")

    print(f"\n✅ 완료 — {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    main()
