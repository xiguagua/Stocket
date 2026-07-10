import hmac
import os

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status

from .handlers import (
    DevicePayload,
    WatchlistPayload,
    get_ticker_events,
    upsert_device,
    upsert_watchlist,
)

app = FastAPI(title="Stocket Worker")


def require_write_token(authorization: str | None = Header(default=None)) -> None:
    expected_token = os.environ.get("WORKER_API_TOKEN")
    if not expected_token:
        return

    provided_token = authorization.removeprefix("Bearer ") if authorization else ""
    if not hmac.compare_digest(provided_token, expected_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API token")


@app.post("/watchlist")
async def post_watchlist(payload: WatchlistPayload, _: None = Depends(require_write_token)):
    return await upsert_watchlist(payload)


@app.post("/devices")
async def post_device(payload: DevicePayload, _: None = Depends(require_write_token)):
    return await upsert_device(payload)


@app.get("/tickers/{ticker}/events")
async def get_events(ticker: str, since: str | None = Query(default=None)):
    return await get_ticker_events(ticker, since)


@app.get("/health")
async def health():
    return {"status": "ok"}
