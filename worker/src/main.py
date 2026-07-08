from fastapi import FastAPI, Query

from .handlers import (
    DevicePayload,
    WatchlistPayload,
    get_ticker_events,
    upsert_device,
    upsert_watchlist,
)

app = FastAPI(title="Stocket Worker")


@app.post("/watchlist")
async def post_watchlist(payload: WatchlistPayload):
    return await upsert_watchlist(payload)


@app.post("/devices")
async def post_device(payload: DevicePayload):
    return await upsert_device(payload)


@app.get("/tickers/{ticker}/events")
async def get_events(ticker: str, since: str | None = Query(default=None)):
    return await get_ticker_events(ticker, since)


@app.get("/health")
async def health():
    return {"status": "ok"}
