import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "worker.db"

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
