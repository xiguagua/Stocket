import os
from datetime import date, datetime, timedelta, timezone

from . import db, llm, storage


def run_ingestion(company_factory=None, set_identity_func=None, today: date | None = None) -> int:
    today = today or datetime.now(timezone.utc).date()
    ciks = db.get_watchlist_ciks()
    if not ciks:
        print("No tickers in watchlist — nothing to ingest.")
        db.record_run(status="completed", processed_count=0, run_date=today)
        return 0

    if company_factory is None or set_identity_func is None:
        try:
            from edgar import Company, set_identity
        except ImportError:
            print("edgartools not installed — using mock filing data for tracer.")
            processed = _mock_ingestion(ciks)
            db.record_run(status="completed", processed_count=processed, run_date=today)
            return processed

        company_factory = company_factory or Company
        set_identity_func = set_identity_func or set_identity

    identity = os.environ.get("EDGAR_IDENTITY")
    if not identity:
        print("EDGAR_IDENTITY not set — using mock filing data for tracer.")
        processed = _mock_ingestion(ciks)
        db.record_run(status="completed", processed_count=processed, run_date=today)
        return processed

    set_identity_func(identity)

    processed = 0
    errors = []
    lookback_days = int(os.environ.get("EDGAR_LOOKBACK_DAYS", "7"))
    start_date = today - timedelta(days=lookback_days)

    for cik in ciks:
        try:
            ticker = _ticker_for_cik(cik)
            company = company_factory(cik)
            filings = _get_filings(company, start_date, today)

            for filing in _iter_filings(filings):
                filing_date = _filing_date(filing)
                if filing_date and filing_date < start_date:
                    continue

                accession = filing.accession_number
                if storage.read_event(ticker, accession):
                    continue

                text = filing.text()[:5000] if hasattr(filing, "text") else ""

                result = llm.first_stage(
                    filing_text=text,
                    accession=accession,
                    ticker=ticker,
                    cik=cik,
                    filing_date=_filing_date_iso(filing),
                    filing_type="8-K",
                )
                storage.write_event(ticker, accession, result)
                processed += 1
                print(f"  Processed {ticker} 8-K {accession}: {result['oneLineSummary']}")
        except Exception as e:
            message = f"CIK {cik}: {e}"
            errors.append(message)
            print(f"  Error processing {message}")

    db.record_run(
        status="partial" if errors else "completed",
        processed_count=processed,
        error="; ".join(errors) if errors else None,
        run_date=today,
    )
    return processed


def _get_filings(company, start_date: date, end_date: date):
    date_range = f"{start_date.isoformat()}:{end_date.isoformat()}"
    try:
        return company.get_filings(form="8-K", date=date_range)
    except TypeError:
        return company.get_filings(form="8-K")


def _iter_filings(filings):
    if not filings:
        return []
    return filings if isinstance(filings, list) else list(filings)


def _filing_date(filing) -> date | None:
    value = getattr(filing, "filing_date", None)
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    return None


def _filing_date_iso(filing) -> str:
    value = getattr(filing, "filing_date", None)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value or ""


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

        result = llm.first_stage(
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
