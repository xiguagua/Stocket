import pytest
from fastapi.testclient import TestClient

from src import db
from src.handlers import (
    DevicePayload,
    WatchlistPayload,
    get_ticker_events,
    upsert_device,
    upsert_watchlist,
)
from src.main import app


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


@pytest.mark.asyncio
async def test_upsert_device_writes_device_read_replica():
    payload = DevicePayload(userId="local-user", deviceToken="apns-token-1")

    result = await upsert_device(payload)

    assert result == {"status": "ok"}
    assert db.get_devices("local-user")[0]["device_token"] == "apns-token-1"


def test_post_devices_endpoint_upserts_device_token():
    client = TestClient(app)

    first = client.post(
        "/devices",
        json={"userId": "local-user", "deviceToken": "apns-token-1"},
    )
    second = client.post(
        "/devices",
        json={"userId": "local-user", "deviceToken": "apns-token-1"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == {"status": "ok"}
    devices = db.get_devices("local-user")
    assert len(devices) == 1
    assert devices[0]["user_id"] == "local-user"
    assert devices[0]["device_token"] == "apns-token-1"
    assert devices[0]["updated_at"]
