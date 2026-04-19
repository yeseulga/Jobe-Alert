"""
SQLite 기반 중복 공고 방지 모듈
"""
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "jobs.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """DB 초기화 — 테이블이 없으면 생성."""
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
        conn.commit()


def _make_hash(job: dict) -> str:
    """공고 URL 또는 (platform + title + company) 조합으로 고유 해시 생성."""
    key = job.get("url") or f"{job.get('platform', '')}|{job.get('title', '')}|{job.get('company', '')}"
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


def deduplicate(jobs: list[dict]) -> list[dict]:
    """
    이미 발송된 공고를 제거하고, 플랫폼 내/간 중복도 제거.
    """
    seen_hashes = set()
    new_jobs = []
    for job in jobs:
        job_hash = _make_hash(job)
        if job_hash in seen_hashes:
            continue
        seen_hashes.add(job_hash)
        if not is_already_sent(job):
            new_jobs.append(job)
        else:
            print(f"  [중복] {job.get('title', '')} ({job.get('platform', '')})")
    return new_jobs
