from datetime import date

from src import db, digest, storage


def test_count_events_for_date_counts_watchlist_events_created_on_day():
    day = date(2026, 7, 8)
    add_watchlist_ticker("AAPL", "0000320193")
    storage.write_event("AAPL", "today-1", event("today-1", "AAPL", "2026-07-08T10:00:00+00:00"))
    storage.write_event("AAPL", "today-2", event("today-2", "AAPL", "2026-07-08T11:00:00+00:00"))
    storage.write_event("AAPL", "yesterday", event("yesterday", "AAPL", "2026-07-07T23:59:59+00:00"))

    assert digest.count_events_for_date(day) == 2


def test_count_events_for_date_ignores_non_watchlist_tickers():
    day = date(2026, 7, 8)
    add_watchlist_ticker("AAPL", "0000320193")
    storage.write_event("MSFT", "msft-today", event("msft-today", "MSFT", "2026-07-08T10:00:00+00:00"))

    assert digest.count_events_for_date(day) == 0


def test_count_events_for_date_dedupes_accession_across_watchlist_tickers():
    day = date(2026, 7, 8)
    add_watchlist_ticker("AAPL", "0000320193")
    add_watchlist_ticker("MSFT", "0000789019")
    storage.write_event("AAPL", "same-accession", event("same-accession", "AAPL", "2026-07-08T10:00:00+00:00"))
    storage.write_event("MSFT", "same-accession", event("same-accession", "MSFT", "2026-07-08T10:05:00+00:00"))

    assert digest.count_events_for_date(day) == 1


def add_watchlist_ticker(ticker: str, cik: str):
    db.upsert_user_ticker(
        user_id="local-user",
        ticker=ticker,
        cik=cik,
        relation="watching",
        updated_at="2026-07-08T00:00:00+00:00",
    )


def event(accession: str, ticker: str, created_at: str) -> dict:
    return {
        "accession": accession,
        "ticker": ticker,
        "cik": "0000000000",
        "filingType": "8-K",
        "filingDate": created_at,
        "importance": 4,
        "items": ["1.01"],
        "oneLineSummary": "Company filed a current report.",
        "createdAt": created_at,
    }
