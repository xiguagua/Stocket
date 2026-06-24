# Stocket

A macOS/iOS app that turns SEC EDGAR filings into plain-language analysis for long-term, retail US-equity investors. A Python cron worker on a VPS pulls EDGAR daily, runs a two-stage LLM pipeline, stores shared summaries in Cloudflare R2, and pushes a daily digest via APNs. The app reads shared data via a Cloudflare Worker and stores private data (watchlist, read state) in CloudKit Private DB, mirrored to a worker SQLite read-replica for server-side processing.

## Language

**Ticker**:
A US stock symbol (e.g. AAPL) that identifies a publicly listed company. Resolved to a CIK via EDGAR's `company_tickers.json`.
_Avoid_: Symbol, stock code

**CIK**:
The SEC's Central Index Key — a unique numeric identifier for each EDGAR filer. The key the worker uses to subscribe to a filer's filings.
_Avoid_: Company number, filer id

**Accession Number**:
EDGAR's unique, permanent identifier for a single filing submission. Used as the dedup key across the worker pipeline and R2 storage.
_Avoid_: Filing id, submission id

**Filing**:
A document submitted to SEC EDGAR by a company. The MVP handles three types: **8-K** (material event), **10-K** (annual report), **10-Q** (quarterly report).
_Avoid_: Report (when it could mean a 10-K/10-Q specifically — use the precise type), document

**Filing Item**:
A numbered section within a 10-K or 10-Q (e.g. Item 1A Risk Factors, Item 7 MD&A). The unit the worker uses for selective LLM processing.
_Avoid_: Section, clause

**Event**:
A material occurrence reported in an 8-K that matters to a long-term holder. The atomic unit users consume in the Today tab and the Events section of a stock detail page.
_Avoid_: News, update, alert

**Periodic Report**:
A 10-K or 10-Q — a regularly-scheduled filing that gives a full-picture view, as opposed to an event-driven 8-K. Lives in its own section of the stock detail page.
_Avoid_: Filing (too generic — use Periodic Report when contrasting with Event)

**Digest**:
The once-daily APNs push and the corresponding Today tab view, summarizing the day's new Events and Periodic Reports across a user's watchlist.
_Avoid_: Newsletter, summary, notification (notification is the APNs signal; digest is the content)

**Position**:
A Ticker the user holds shares in. One of the two user-ticker relations. Events for a Position are surfaced with a "holder's long-term view" lens.
_Avoid_: Holding, stock, investment

**Watching**:
A Ticker the user is observing but does not hold. One of the two user-ticker relations. Events for a Watching ticker are surfaced with a "should I build a position" lens.
_Avoid_: Watchlist item, followed stock

**Watchlist**:
The collective set of a user's Positions and Watching tickers. Stored in CloudKit Private DB as the source of truth, mirrored to worker SQLite as a read-replica.
_Avoid_: Portfolio (reserved for the app tab that displays the watchlist)

**Impact Dimension**:
One of five fixed axes scored per Event: Governance, Financials, Business, Regulatory/Legal, Valuation. Each scored -2 to +2 or "no impact". The canonical set — adding or renaming a dimension breaks historical aggregation.
_Avoid_: Category, tag, factor

**Importance**:
A 1–5 rating assigned by the first-stage LLM to every 8-K, gauging how much it matters to a long-term investor. ≥4 triggers second-stage deep processing. Not shown to users as a raw number; drives processing depth and (in v2) ordering/filtering.
_Avoid_: Priority, severity

**Long-term View**:
The card field that states how an Event affects the core thesis of a Position holder or the build-position decision of a Watching user. Distinct from a factual summary — it is an interpretation.
_Avoid_: Analysis, takeaway, conclusion

**Common Misreading**:
The card field that names a misconception a retail investor is likely to hold about this Event and corrects it. The product's differentiated field; requires a model that understands retail-investor cognitive biases.
_Avoid_: Warning, caveat, risk note

**Two-stage Pipeline**:
The worker's LLM processing model: a cheap first stage classifies every 8-K (Importance + Item identification) and summarizes low-value items in 10-K/10-Q; an expensive second stage produces the full structured card only for Importance ≥4 events and high-value 10-K/10-Q items.
_Avoid_: Two-pass, cascade

**Golden Set**:
A curated set of ~20–30 historical filings with hand-written expected outputs, used as a regression baseline when models or prompts change. Created after the MVP launch once real failure cases are collected.
_Avoid_: Test set, benchmark

## Flagged ambiguities

- **"Watchlist" vs "Portfolio"**: Watchlist is the data (the set of tickers a user tracks). Portfolio is the app tab that displays it. Do not use "portfolio" to mean the data — it collides with the tab name and with Position (which is one entry in the watchlist).

- **"Event" vs "Filing"**: Every Event comes from a Filing, but not every Filing is an Event — low-Importance 8-Ks and Periodic Reports are not Events. Use Filing when talking about EDGAR/source data; use Event when talking about what the user consumes.

- **"Notification" vs "Digest"**: Notification is the APNs signal ("X new events today, tap to view"). Digest is the content — both the push payload's intent and the Today tab view. They are different layers and should not be used interchangeably.

## Example dialogue

**Dev**: "The worker missed an 8-K for AAPL yesterday — the cron failed."
**Domain**: "Did the gap-detection catch it on today's run?"
**Dev**: "Yeah, it re-pulled yesterday's daily index and found the Accession Number. But it's an Importance 2, so it only ran the first stage."
**Domain**: "Right, that one won't have Impact Dimensions — just the one-line summary. It'll show in the Events section without the Long-term View."
**Dev**: "The user has AAPL as a Position. Should the digest payload mention it specifically?"
**Domain**: "No — the payload is global per ADR-0004, just 'N new events today'. The app filters the R2 data by their Watchlist when Today opens. Personalization happens client-side."

**Dev**: "This 10-K's Item 1A added three new risk factors this year. How should the Periodic Report card show the diff?"
**Domain**: "It's the headline of that 10-K's card in the Periodic Reports section — new risks listed, removed risks listed, then the Long-term View on what the shift signals. The Common Misreading field should call out if retail investors might overreact to a boilerplate-sounding addition."
