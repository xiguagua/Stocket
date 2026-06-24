import hashlib
from datetime import datetime, timezone


def mock_first_stage(filing_text: str, accession: str, ticker: str, cik: str, filing_date: str, filing_type: str) -> dict:
    text_lower = filing_text.lower()

    if "merger" in text_lower or "acquisition" in text_lower:
        summary = "Company announced a merger or acquisition transaction."
        importance = 5
        items = ["1.01"]
    elif "chief executive" in text_lower or "officer" in text_lower or "resignation" in text_lower:
        summary = "Executive officer change reported."
        importance = 4
        items = ["5.02"]
    elif "bankruptcy" in text_lower or "chapter 11" in text_lower:
        summary = "Bankruptcy or insolvency proceedings filed."
        importance = 5
        items = ["1.03"]
    elif "material agreement" in text_lower:
        summary = "Company entered into a material agreement."
        importance = 4
        items = ["1.01"]
    elif "financial results" in text_lower or "earnings" in text_lower:
        summary = "Company reported financial results or earnings guidance."
        importance = 3
        items = ["2.02"]
    else:
        summary = "Company filed a current report."
        importance = 2
        items = ["8.01"]

    return {
        "accession": accession,
        "ticker": ticker.upper(),
        "cik": cik,
        "filingType": filing_type,
        "filingDate": filing_date,
        "importance": importance,
        "items": items,
        "oneLineSummary": summary,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
