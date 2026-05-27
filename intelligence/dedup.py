"""intelligence.db 기반 중복 아이템 추적 — jobs.db와 완전 분리."""
import sqlite3
import hashlib
from datetime import datetime
from .config import INTELLIGENCE_DB_PATH


def _conn():
    c = sqlite3.connect(INTELLIGENCE_DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS seen_items (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                url_hash TEXT UNIQUE NOT NULL,
                url      TEXT NOT NULL,
                title    TEXT,
                seen_at  TEXT NOT NULL
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_url_hash ON seen_items(url_hash)")


def _hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def filter_new(items: list[dict]) -> list[dict]:
    """이미 본 URL이 있는 아이템 제거 후 신규 아이템만 반환."""
    if not items:
        return []
    init_db()
    hashes = [_hash(item["url"]) for item in items]
    with _conn() as c:
        placeholders = ",".join("?" * len(hashes))
        rows = c.execute(
            f"SELECT url_hash FROM seen_items WHERE url_hash IN ({placeholders})", hashes
        ).fetchall()
    seen = {r["url_hash"] for r in rows}
    return [item for item, h in zip(items, hashes) if h not in seen]


def mark_seen(items: list[dict]):
    """발송된 아이템을 seen으로 기록."""
    if not items:
        return
    init_db()
    now = datetime.utcnow().isoformat()
    rows = [(_hash(item["url"]), item["url"], item.get("title", ""), now) for item in items]
    with _conn() as c:
        c.executemany(
            "INSERT OR IGNORE INTO seen_items (url_hash, url, title, seen_at) VALUES (?,?,?,?)",
            rows,
        )
