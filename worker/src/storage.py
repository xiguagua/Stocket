import json
from datetime import datetime, timezone
from pathlib import Path

STORAGE_ROOT = Path(__file__).resolve().parent.parent / "data" / "summaries"


def _event_path(ticker: str, accession: str) -> Path:
    return STORAGE_ROOT / "tickers" / ticker.upper() / "events" / f"{accession}.json"


def write_event(ticker: str, accession: str, data: dict) -> None:
    path = _event_path(ticker, accession)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def read_event(ticker: str, accession: str) -> dict | None:
    path = _event_path(ticker, accession)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def list_events(ticker: str, since: str | None = None) -> list[dict]:
    ticker_dir = STORAGE_ROOT / "tickers" / ticker.upper() / "events"
    if not ticker_dir.exists():
        return []

    since_dt = None
    if since:
        since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))

    events = []
    for path in sorted(ticker_dir.glob("*.json")):
        data = json.loads(path.read_text())
        if since_dt:
            event_created = data.get("createdAt", "")
            if event_created:
                event_dt = datetime.fromisoformat(
                    event_created.replace("Z", "+00:00")
                )
                if event_dt <= since_dt:
                    continue
        events.append(data)

    events.sort(key=lambda e: e.get("filingDate", ""), reverse=True)
    return events
