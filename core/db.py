"""
SQLite 기반 중복 공고 방지 모듈
"""
import re
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "jobs.db"

_COMPANY_NOISE = re.compile(r"[\(\（]?주[\)\）]?|주식회사|㈜|\s+")


def _normalize_company(name: str) -> str:
    """(주), ㈜, 주식회사 등을 제거하고 소문자 정규화 — 플랫폼 간 회사명 차이 흡수."""
    return _COMPANY_NOISE.sub("", name).lower()


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


SENT_JOBS_TTL_DAYS = 7  # 이 기간이 지난 sent_jobs는 다시 발송 대상에 포함


def init_db():
    """DB 초기화 — 테이블이 없으면 생성하고 TTL 만료 항목 삭제."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sent_jobs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                job_hash    TEXT    UNIQUE NOT NULL,
                title       TEXT,
                company     TEXT,
                platform    TEXT,
                sent_at     TEXT    NOT NULL
            )
        """)
        # 공고 최초 발견 이력 (캘린더 데이터용)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS job_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                job_hash    TEXT    UNIQUE NOT NULL,
                title       TEXT,
                company     TEXT,
                platform    TEXT,
                url         TEXT,
                score       INTEGER DEFAULT 0,
                track       TEXT,
                first_seen  TEXT    NOT NULL
            )
        """)
        # TTL 만료 항목 삭제 (7일 이상 된 sent_jobs)
        conn.execute(
            "DELETE FROM sent_jobs WHERE sent_at < datetime('now', ?)",
            (f"-{SENT_JOBS_TTL_DAYS} days",)
        )
        conn.commit()


def _make_hash(job: dict) -> str:
    """
    정규화된 (회사명 + 제목 앞 50자) 기반 해시.
    플랫폼별 URL 차이에 무관하게 같은 공고를 동일 해시로 인식.
    각 스크래퍼 내 seen_urls가 플랫폼 내 중복을 처리하므로,
    여기서는 플랫폼 간 교차 중복 제거에 집중.
    """
    company = _normalize_company(job.get("company", ""))
    title = job.get("title", "").strip().lower()
    key = f"{company}|{title[:50]}"
    return hashlib.md5(key.encode("utf-8")).hexdigest()


def is_already_sent(job: dict) -> bool:
    """이미 발송된 공고인지 확인."""
    job_hash = _make_hash(job)
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM sent_jobs WHERE job_hash = ?", (job_hash,)
        ).fetchone()
    return row is not None


def mark_as_sent(jobs: list[dict]):
    """발송된 공고를 DB에 기록."""
    now = datetime.now().isoformat()
    with _get_conn() as conn:
        for job in jobs:
            job_hash = _make_hash(job)
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO sent_jobs (job_hash, title, company, platform, sent_at) VALUES (?,?,?,?,?)",
                    (job_hash, job.get("title"), job.get("company"), job.get("platform"), now)
                )
            except sqlite3.IntegrityError:
                pass
        conn.commit()


def record_seen(job: dict):
    """공고 최초 발견 시 job_history에 기록. 이미 있으면 track/score만 업데이트."""
    job_hash = _make_hash(job)
    now = datetime.now().isoformat()
    with _get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM job_history WHERE job_hash = ?", (job_hash,)
        ).fetchone()
        if existing:
            # 이미 있으면 track/score만 업데이트 (enrichment 후 재호출 시)
            conn.execute(
                "UPDATE job_history SET score=?, track=? WHERE job_hash=?",
                (job.get("score", 0), job.get("track_badge") or job.get("track", ""), job_hash)
            )
        else:
            conn.execute(
                """INSERT INTO job_history
                   (job_hash, title, company, platform, url, score, track, first_seen)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (job_hash, job.get("title"), job.get("company"), job.get("platform"),
                 job.get("url"), job.get("score", 0),
                 job.get("track_badge") or job.get("track", ""), now)
            )
        conn.commit()


def get_first_seen(job: dict) -> str | None:
    """공고가 처음 발견된 날짜 반환. 없으면 None."""
    job_hash = _make_hash(job)
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT first_seen FROM job_history WHERE job_hash = ?", (job_hash,)
        ).fetchone()
    return row["first_seen"] if row else None


def deduplicate(jobs: list[dict]) -> list[dict]:
    """
    같은 실행 내 중복(같은 URL/해시)만 제거.
    sent_jobs 기반 차단 없음 — 매일 동일 공고를 다시 볼 수 있도록 허용.
    job_history에 최초 발견 기록.
    """
    seen_hashes = set()
    unique_jobs = []
    for job in jobs:
        job_hash = _make_hash(job)
        if job_hash in seen_hashes:
            continue
        seen_hashes.add(job_hash)
        record_seen(job)
        unique_jobs.append(job)
    return unique_jobs
