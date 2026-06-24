from datetime import datetime, timezone

from pydantic import BaseModel

from . import db, storage


class WatchlistPayload(BaseModel):
    userId: str
    ticker: str
    cik: str
    relation: str = "watching"


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


async def get_ticker_events(ticker: str, since: str | None) -> list[dict]:
    return storage.list_events(ticker, since)
