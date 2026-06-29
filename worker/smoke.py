import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from src import db, storage
from src.cron import run_cron
from src.main import app


def main() -> int:
    # Keep local smoke deterministic: no EDGAR credentials required.
    os.environ.pop("EDGAR_IDENTITY", None)

    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        db.DB_PATH = root / "worker.db"
        storage.STORAGE_ROOT = root / "summaries"

        client = TestClient(app)
        watchlist_response = client.post(
            "/watchlist",
            json={
                "userId": "local-user",
                "ticker": "AAPL",
                "cik": "0000320193",
                "relation": "watching",
            },
        )
        watchlist_response.raise_for_status()

        run_cron()

        events_response = client.get("/tickers/AAPL/events")
        events_response.raise_for_status()
        events = events_response.json()

        if not events:
            print("Smoke failed: expected at least one AAPL Event.")
            return 1

        required_keys = {
            "accession",
            "ticker",
            "cik",
            "filingType",
            "filingDate",
            "importance",
            "items",
            "oneLineSummary",
            "createdAt",
        }
        missing = required_keys.difference(events[0])
        if missing:
            print(f"Smoke failed: first Event missing keys: {sorted(missing)}")
            return 1

    print(f"Smoke passed: {len(events)} AAPL Event(s) available.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
