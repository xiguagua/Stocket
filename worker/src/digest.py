from datetime import date, datetime, time, timezone

from . import db, storage


def count_today_events(today: date | None = None) -> int:
    today = today or datetime.now(timezone.utc).date()
    return count_events_for_date(today)


def count_events_for_date(day: date) -> int:
    since = datetime.combine(day, time.min, tzinfo=timezone.utc).isoformat()
    accessions = set()

    for ticker in db.get_watchlist_tickers():
        for event in storage.list_events(ticker, since=since):
            created_at = _parse_datetime(event.get("createdAt"))
            if not created_at or created_at.date() != day:
                continue

            accession = event.get("accession")
            if accession:
                accessions.add(accession)

    return len(accessions)


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
