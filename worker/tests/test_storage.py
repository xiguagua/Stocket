from datetime import datetime, timedelta, timezone
from io import BytesIO

import pytest

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


def test_r2_backend_reads_writes_and_lists_events(monkeypatch):
    fake_client = FakeR2Client()
    older = datetime(2026, 6, 28, tzinfo=timezone.utc)
    newer = older + timedelta(days=1)

    monkeypatch.setenv("STORAGE_BACKEND", "r2")
    monkeypatch.setenv("R2_BUCKET", "stocket-test")
    monkeypatch.setenv("R2_KEY_PREFIX", "summaries")
    monkeypatch.setattr(storage, "_r2_client", lambda: fake_client)

    storage.write_event(
        "aapl",
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

    assert storage.read_event("AAPL", "missing") is None
    assert storage.read_event("AAPL", "newer")["accession"] == "newer"
    assert list(fake_client.objects) == [
        "summaries/tickers/AAPL/events/older.json",
        "summaries/tickers/AAPL/events/newer.json",
    ]
    assert [event["accession"] for event in storage.list_events("AAPL")] == ["newer", "older"]


def test_unsupported_storage_backend_raises(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "ftp")

    with pytest.raises(ValueError, match="Unsupported STORAGE_BACKEND"):
        storage.list_events("AAPL")


class FakeR2Client:
    class exceptions:
        class NoSuchKey(Exception):
            pass

    def __init__(self):
        self.objects = {}

    def put_object(self, Bucket, Key, Body, ContentType):
        self.objects[Key] = Body

    def get_object(self, Bucket, Key):
        if Key not in self.objects:
            raise self.exceptions.NoSuchKey()
        return {"Body": BytesIO(self.objects[Key])}

    def list_objects_v2(self, Bucket, Prefix, ContinuationToken=None):
        contents = [{"Key": key} for key in self.objects if key.startswith(Prefix)]
        return {"Contents": contents, "IsTruncated": False}
