from datetime import datetime, timedelta, timezone

from src import storage


def test_list_events_returns_newest_first_and_filters_since():
    older = datetime(2026, 6, 28, tzinfo=timezone.utc)
    newer = older + timedelta(days=1)

    storage.write_event(
        "AAPL",
        "older",
        {
            "accession": "older",
            "ticker": "AAPL",
            "filingDate": older.isoformat(),
            "createdAt": older.isoformat(),
        },
    )
    storage.write_event(
        "AAPL",
        "newer",
        {
            "accession": "newer",
            "ticker": "AAPL",
            "filingDate": newer.isoformat(),
            "createdAt": newer.isoformat(),
        },
    )

    all_events = storage.list_events("AAPL")
    filtered = storage.list_events("AAPL", since=older.isoformat())

    assert [event["accession"] for event in all_events] == ["newer", "older"]
    assert [event["accession"] for event in filtered] == ["newer"]
