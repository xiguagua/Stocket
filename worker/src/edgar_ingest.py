import os

from . import db, llm, storage


def run_ingestion() -> int:
    ciks = db.get_watchlist_ciks()
    if not ciks:
        print("No tickers in watchlist — nothing to ingest.")
        return 0

    try:
        from edgar import Company, set_identity
    except ImportError:
        print("edgartools not installed — using mock filing data for tracer.")
        return _mock_ingestion(ciks)

    identity = os.environ.get("EDGAR_IDENTITY")
    if not identity:
        print("EDGAR_IDENTITY not set — using mock filing data for tracer.")
        return _mock_ingestion(ciks)

    set_identity(identity)

    processed = 0
    for cik in ciks:
        try:
            company = Company(cik)
            filings = company.get_filings(form="8-K")
            latest = filings.latest() if filings else None
            if not latest:
                continue

            accession = latest.accession_number
            filing_date = latest.filing_date.isoformat() if latest.filing_date else ""

            existing = storage.read_event(_ticker_for_cik(cik), accession)
            if existing:
                continue

            text = latest.text()[:5000] if hasattr(latest, "text") else ""
            ticker = _ticker_for_cik(cik)

            result = llm.mock_first_stage(
                filing_text=text,
                accession=accession,
                ticker=ticker,
                cik=cik,
                filing_date=filing_date,
                filing_type="8-K",
            )
            storage.write_event(ticker, accession, result)
            processed += 1
            print(f"  Processed {ticker} 8-K {accession}: {result['oneLineSummary']}")
        except Exception as e:
            print(f"  Error processing CIK {cik}: {e}")

    return processed


def _ticker_for_cik(cik: str) -> str:
    conn = db.get_connection()
    row = conn.execute(
        "SELECT ticker FROM user_tickers WHERE cik = ? LIMIT 1", (cik,)
    ).fetchone()
    conn.close()
    return row["ticker"] if row else cik


def _mock_ingestion(ciks: list[str]) -> int:
    processed = 0
    for cik in ciks:
        ticker = _ticker_for_cik(cik)
        accession = f"000-{cik}-{datetime.now(timezone.utc).strftime('%Y%m%d')}-tracer"
        existing = storage.read_event(ticker, accession)
        if existing:
            continue

        result = llm.mock_first_stage(
            filing_text="company filed a current report",
            accession=accession,
            ticker=ticker,
            cik=cik,
            filing_date=datetime.now(timezone.utc).isoformat(),
            filing_type="8-K",
        )
        storage.write_event(ticker, accession, result)
        processed += 1
        print(f"  [mock] Processed {ticker} 8-K {accession}: {result['oneLineSummary']}")
    return processed


from datetime import datetime, timezone
