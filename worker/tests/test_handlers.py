import pytest

from src import db
from src.handlers import WatchlistPayload, get_ticker_events, upsert_watchlist


@pytest.mark.asyncio
async def test_upsert_watchlist_writes_read_replica():
    payload = WatchlistPayload(
        userId="local-user",
        ticker="AAPL",
        cik="0000320193",
        relation="watching",
    )

    result = await upsert_watchlist(payload)

    assert result == {"status": "ok", "ticker": "AAPL"}
    assert db.get_watchlist_ciks() == ["0000320193"]


@pytest.mark.asyncio
async def test_get_ticker_events_returns_empty_list_when_no_storage():
    assert await get_ticker_events("AAPL", since=None) == []
