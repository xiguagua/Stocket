import json
import os
from datetime import datetime, timezone


FIRST_STAGE_SYSTEM_PROMPT = """You classify SEC EDGAR 8-K filings for long-term retail US-equity investors.
Return only JSON with these fields: importance, items, oneLineSummary.
importance must be an integer from 1 to 5. items must be SEC 8-K item numbers as strings.
oneLineSummary must be one concise plain-English sentence."""


def first_stage(
    filing_text: str,
    accession: str,
    ticker: str,
    cik: str,
    filing_date: str,
    filing_type: str,
) -> dict:
    provider = os.environ.get("LLM_PROVIDER", "mock").lower()
    if provider == "mock":
        raw = mock_first_stage(
            filing_text=filing_text,
            accession=accession,
            ticker=ticker,
            cik=cik,
            filing_date=filing_date,
            filing_type=filing_type,
        )
    elif provider == "openai":
        raw = _openai_first_stage(filing_text)
    elif provider == "anthropic":
        raw = _anthropic_first_stage(filing_text)
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")

    return _event_payload(
        raw,
        accession=accession,
        ticker=ticker,
        cik=cik,
        filing_date=filing_date,
        filing_type=filing_type,
    )


def mock_first_stage(
    filing_text: str,
    accession: str,
    ticker: str,
    cik: str,
    filing_date: str,
    filing_type: str,
) -> dict:
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
        "importance": importance,
        "items": items,
        "oneLineSummary": summary,
    }


def _openai_first_stage(filing_text: str) -> dict:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install openai or set LLM_PROVIDER=mock") from exc

    model = os.environ.get("LLM_FIRST_STAGE_MODEL") or "gpt-4o-mini"
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": FIRST_STAGE_SYSTEM_PROMPT},
            {"role": "user", "content": filing_text[:12000]},
        ],
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)


def _anthropic_first_stage(filing_text: str) -> dict:
    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise RuntimeError("Install anthropic or set LLM_PROVIDER=mock") from exc

    model = os.environ.get("LLM_FIRST_STAGE_MODEL") or "claude-3-5-haiku-latest"
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model=model,
        max_tokens=500,
        system=FIRST_STAGE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": filing_text[:12000]}],
    )
    text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
    return json.loads(text)


def _event_payload(
    raw: dict,
    accession: str,
    ticker: str,
    cik: str,
    filing_date: str,
    filing_type: str,
) -> dict:
    validated = _validate_first_stage(raw)
    return {
        "accession": accession,
        "ticker": ticker.upper(),
        "cik": cik,
        "filingType": filing_type,
        "filingDate": filing_date,
        "importance": validated["importance"],
        "items": validated["items"],
        "oneLineSummary": validated["oneLineSummary"],
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }


def _validate_first_stage(raw: dict) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("First-stage LLM output must be a JSON object")

    importance = raw.get("importance")
    if not isinstance(importance, int) or importance < 1 or importance > 5:
        raise ValueError("First-stage importance must be an integer from 1 to 5")

    items = raw.get("items")
    if not isinstance(items, list) or not items or not all(isinstance(item, str) for item in items):
        raise ValueError("First-stage items must be a non-empty list of strings")

    one_line_summary = raw.get("oneLineSummary")
    if not isinstance(one_line_summary, str) or not one_line_summary.strip():
        raise ValueError("First-stage oneLineSummary must be a non-empty string")

    return {
        "importance": importance,
        "items": items,
        "oneLineSummary": one_line_summary.strip(),
    }
