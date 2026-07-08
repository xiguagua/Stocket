import os
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

DB_PATH = Path(
    os.environ.get(
        "WORKER_DB_PATH",
        Path(__file__).resolve().parent.parent / "data" / "worker.db",
    )
).expanduser()

SCHEMA = """
CREATE TABLE IF NOT EXISTS user_tickers (
    user_id  TEXT NOT NULL,
    ticker   TEXT NOT NULL,
    cik      TEXT NOT NULL,
    relation TEXT NOT NULL DEFAULT 'watching',
    updated_at TEXT NOT NULL,
    PRIMARY KEY (user_id, ticker)
);

CREATE TABLE IF NOT EXISTS devices (
    user_id      TEXT NOT NULL,
    device_token TEXT NOT NULL,
    updated_at   TEXT NOT NULL,
    PRIMARY KEY (user_id, device_token)
);

CREATE TABLE IF NOT EXISTS run_log (
    date           TEXT PRIMARY KEY,
    status         TEXT NOT NULL,
    processed_count INTEGER DEFAULT 0,
    error          TEXT
);
"""


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def get_watchlist_ciks() -> list[str]:
    conn = get_connection()
    rows = conn.execute("SELECT DISTINCT cik FROM user_tickers").fetchall()
    conn.close()
    return [r["cik"] for r in rows]


def upsert_user_ticker(
    user_id: str, ticker: str, cik: str, relation: str, updated_at: str
) -> None:
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO user_tickers (user_id, ticker, cik, relation, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT (user_id, ticker)
        DO UPDATE SET cik=excluded.cik, relation=excluded.relation, updated_at=excluded.updated_at
        """,
        (user_id, ticker, cik, relation, updated_at),
    )
    conn.commit()
    conn.close()


def upsert_device(user_id: str, device_token: str, updated_at: str) -> None:
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO devices (user_id, device_token, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT (user_id, device_token)
        DO UPDATE SET updated_at=excluded.updated_at
        """,
        (user_id, device_token, updated_at),
    )
    conn.commit()
    conn.close()


def get_devices(user_id: str | None = None) -> list[dict]:
    conn = get_connection()
    if user_id:
        rows = conn.execute(
            "SELECT user_id, device_token, updated_at FROM devices WHERE user_id = ? ORDER BY device_token",
            (user_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT user_id, device_token, updated_at FROM devices ORDER BY user_id, device_token"
        ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def record_run(
    status: str,
    processed_count: int,
    error: str | None = None,
    run_date: date | None = None,
) -> None:
    run_date = run_date or datetime.now(timezone.utc).date()
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO run_log (date, status, processed_count, error)
        VALUES (?, ?, ?, ?)
        ON CONFLICT (date)
        DO UPDATE SET status=excluded.status,
                      processed_count=excluded.processed_count,
                      error=excluded.error
        """,
        (run_date.isoformat(), status, processed_count, error),
    )
    conn.commit()
    conn.close()


def get_latest_run_log() -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT date, status, processed_count, error FROM run_log ORDER BY date DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return dict(row) if row else None
