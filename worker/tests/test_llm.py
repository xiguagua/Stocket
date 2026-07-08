import pytest

from src import llm


def test_first_stage_mock_returns_event_payload(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    result = llm.first_stage(
        filing_text="The company announced a merger agreement.",
        accession="000-test",
        ticker="aapl",
        cik="0000320193",
        filing_date="2026-06-29",
        filing_type="8-K",
    )

    assert result["accession"] == "000-test"
    assert result["ticker"] == "AAPL"
    assert result["importance"] == 5
    assert result["items"] == ["1.01"]
    assert result["oneLineSummary"] == "Company announced a merger or acquisition transaction."
    assert "createdAt" in result


def test_first_stage_rejects_unsupported_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "unknown")

    with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"):
        llm.first_stage(
            filing_text="text",
            accession="000-test",
            ticker="AAPL",
            cik="0000320193",
            filing_date="2026-06-29",
            filing_type="8-K",
        )


def test_first_stage_dispatches_openai_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setattr(
        llm,
        "_openai_first_stage",
        lambda filing_text: {
            "importance": 4,
            "items": ["5.02"],
            "oneLineSummary": "Executive officer change reported.",
        },
    )

    result = llm.first_stage(
        filing_text="chief executive resignation",
        accession="000-test",
        ticker="AAPL",
        cik="0000320193",
        filing_date="2026-06-29",
        filing_type="8-K",
    )

    assert result["importance"] == 4
    assert result["items"] == ["5.02"]
    assert result["oneLineSummary"] == "Executive officer change reported."


def test_validate_first_stage_rejects_invalid_schema():
    with pytest.raises(ValueError, match="importance"):
        llm._validate_first_stage(
            {
                "importance": 6,
                "items": ["1.01"],
                "oneLineSummary": "Company entered into a material agreement.",
            }
        )

    with pytest.raises(ValueError, match="items"):
        llm._validate_first_stage(
            {
                "importance": 4,
                "items": [],
                "oneLineSummary": "Company entered into a material agreement.",
            }
        )

    with pytest.raises(ValueError, match="oneLineSummary"):
        llm._validate_first_stage(
            {
                "importance": 4,
                "items": ["1.01"],
                "oneLineSummary": "",
            }
        )
