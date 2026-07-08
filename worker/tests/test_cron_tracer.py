from src import cron, db, storage


def test_run_cron_creates_mock_event_without_edgar_identity(monkeypatch):
    monkeypatch.delenv("EDGAR_IDENTITY", raising=False)
    monkeypatch.delenv("APNS_SEND_DIGEST", raising=False)
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


def test_run_cron_does_not_send_digest_by_default(monkeypatch):
    calls = []
    monkeypatch.delenv("APNS_SEND_DIGEST", raising=False)
    monkeypatch.setattr(cron.edgar_ingest, "run_ingestion", lambda: 2)
    monkeypatch.setattr(cron.digest, "count_today_events", lambda: calls.append("count"))
    monkeypatch.setattr(cron.apns, "send_digest", lambda event_count: calls.append(event_count))

    processed = cron.run_cron()

    assert processed == 2
    assert calls == []


def test_run_cron_sends_digest_when_enabled(monkeypatch):
    sent_counts = []
    monkeypatch.setenv("APNS_SEND_DIGEST", "true")
    monkeypatch.setattr(cron.edgar_ingest, "run_ingestion", lambda: 2)
    monkeypatch.setattr(cron.digest, "count_today_events", lambda: 3)
    monkeypatch.setattr(
        cron.apns,
        "send_digest",
        lambda event_count: sent_counts.append(event_count) or {"attempted": 1, "sent": 1, "failed": 0},
    )

    processed = cron.run_cron()

    assert processed == 2
    assert sent_counts == [3]
