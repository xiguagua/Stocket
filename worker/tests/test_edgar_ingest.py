from datetime import date

from src import db, edgar_ingest, storage


class FakeFiling:
    def __init__(self, accession_number: str, filing_date: date, text: str):
        self.accession_number = accession_number
        self.filing_date = filing_date
        self._text = text

    def text(self) -> str:
        return self._text


class FakeCompany:
    calls = []

    def __init__(self, cik: str):
        self.cik = cik

    def get_filings(self, form: str, date: str):
        self.calls.append((self.cik, form, date))
        return [
            FakeFiling("recent-merger", date_from(2026, 6, 28), "merger agreement"),
            FakeFiling("recent-officer", date_from(2026, 6, 27), "chief executive resignation"),
            FakeFiling("old-filing", date_from(2026, 6, 1), "material agreement"),
        ]


def date_from(year: int, month: int, day: int) -> date:
    return date(year, month, day)


def test_real_ingestion_processes_recent_filings_and_skips_duplicate(monkeypatch):
    monkeypatch.setenv("EDGAR_IDENTITY", "Test User test@example.com")
    monkeypatch.setenv("EDGAR_LOOKBACK_DAYS", "7")
    FakeCompany.calls = []
    db.upsert_user_ticker(
        user_id="local-user",
        ticker="AAPL",
        cik="0000320193",
        relation="watching",
        updated_at="2026-06-29T00:00:00+00:00",
    )
    storage.write_event("AAPL", "recent-officer", {"accession": "recent-officer"})

    processed = edgar_ingest.run_ingestion(
        company_factory=FakeCompany,
        set_identity_func=lambda identity: None,
        today=date_from(2026, 6, 29),
    )
    events = storage.list_events("AAPL")
    run_log = db.get_latest_run_log()

    assert processed == 1
    assert FakeCompany.calls == [("0000320193", "8-K", "2026-06-22:2026-06-29")]
    assert {event["accession"] for event in events} == {"recent-merger", "recent-officer"}
    assert storage.read_event("AAPL", "old-filing") is None
    assert storage.read_event("AAPL", "recent-merger")["importance"] == 5
    assert run_log == {
        "date": "2026-06-29",
        "status": "completed",
        "processed_count": 1,
        "error": None,
    }


def test_real_ingestion_records_partial_run_on_cik_error(monkeypatch):
    class BrokenCompany:
        def __init__(self, cik: str):
            self.cik = cik

        def get_filings(self, form: str, date: str):
            raise RuntimeError("EDGAR unavailable")

    monkeypatch.setenv("EDGAR_IDENTITY", "Test User test@example.com")
    db.upsert_user_ticker(
        user_id="local-user",
        ticker="AAPL",
        cik="0000320193",
        relation="watching",
        updated_at="2026-06-29T00:00:00+00:00",
    )

    processed = edgar_ingest.run_ingestion(
        company_factory=BrokenCompany,
        set_identity_func=lambda identity: None,
        today=date_from(2026, 6, 29),
    )
    run_log = db.get_latest_run_log()

    assert processed == 0
    assert run_log["status"] == "partial"
    assert run_log["processed_count"] == 0
    assert "EDGAR unavailable" in run_log["error"]
