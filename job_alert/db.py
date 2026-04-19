"""
SQLite 기반 중복 공고 방지 — job_alert.db
"""
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "jobs.db"


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS sent_jobs (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                job_hash  TEXT    UNIQUE NOT NULL,
                title     TEXT,
                company   TEXT,
                platform  TEXT,
                sent_at   TEXT NOT NULL
            )
        """)
        c.commit()


def _hash(job: dict) -> str:
    key = job.get("url") or f"{job.get('platform','')}|{job.get('title','')}|{job.get('company','')}"
    return hashlib.md5(key.encode()).hexdigest()


def is_sent(job: dict) -> bool:
    with _conn() as c:
        return c.execute("SELECT 1 FROM sent_jobs WHERE job_hash=?", (_hash(job),)).fetchone() is not None


def mark_sent(jobs: list[dict]) -> None:
    now = datetime.now().isoformat()
    with _conn() as c:
        for job in jobs:
            c.execute(
                "INSERT OR IGNORE INTO sent_jobs (job_hash,title,company,platform,sent_at) VALUES(?,?,?,?,?)",
                (_hash(job), job.get("title"), job.get("company"), job.get("platform"), now),
            )
        c.commit()


def deduplicate(jobs: list[dict]) -> list[dict]:
    """플랫폼 간 중복 + 이미 발송된 공고 제거."""
    seen: set[str] = set()
    result: list[dict] = []
    for job in jobs:
        h = _hash(job)
        if h in seen:
            continue
        seen.add(h)
        if is_sent(job):
            print(f"  [중복→스킵] {job.get('title','')!r} ({job.get('platform','')})")
        else:
            result.append(job)
    return result
