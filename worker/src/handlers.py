from datetime import datetime, timezone

from pydantic import BaseModel

from . import db, storage


class WatchlistPayload(BaseModel):
    userId: str
    ticker: str
    cik: str
    relation: str = "watching"


class DevicePayload(BaseModel):
    userId: str
    deviceToken: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def upsert_watchlist(payload: WatchlistPayload) -> dict:
    db.upsert_user_ticker(
        user_id=payload.userId,
        ticker=payload.ticker,
        cik=payload.cik,
        relation=payload.relation,
        updated_at=_now_iso(),
    )
    return {"status": "ok", "ticker": payload.ticker}


async def upsert_device(payload: DevicePayload) -> dict:
    db.upsert_device(
        user_id=payload.userId,
        device_token=payload.deviceToken,
        updated_at=_now_iso(),
    )
    return {"status": "ok"}


async def get_ticker_events(ticker: str, since: str | None) -> list[dict]:
    return storage.list_events(ticker, since)
