from src import cron, db, storage


def test_run_cron_creates_mock_event_without_edgar_identity(monkeypatch):
    monkeypatch.delenv("EDGAR_IDENTITY", raising=False)
    db.upsert_user_ticker(
        user_id="local-user",
        ticker="AAPL",
        cik="0000320193",
        relation="watching",
        updated_at="2026-06-29T00:00:00+00:00",
    )

    processed = cron.run_cron()
    events = storage.list_events("AAPL")

    assert processed == 1
    assert len(events) == 1
    assert events[0]["ticker"] == "AAPL"
    assert events[0]["filingType"] == "8-K"
    assert events[0]["oneLineSummary"] == "Company filed a current report."
