# AGENTS.md

Repo-specific guidance for OpenCode sessions working on Stocket.

## Repo scope

This is a monorepo containing three components of the Stocket system:

- **`Stocket/`** — iOS app source (SwiftUI + SwiftData). The Xcode project is `Stocket.xcodeproj` at the repository root.
- **`STLibrary/`** — Swift Package for pure Swift logic and non-UI Swift Testing tests
- **`worker/`** — Python VPS cron + FastAPI server (EDGAR ingestion, two-stage LLM pipeline, APNs push, SQLite read-replica, R2 read endpoint for the app)

`CONTEXT.md` defines the domain glossary shared across all components. ADRs in `docs/adr/` cover cross-cutting decisions. Commit scope tags (`app`, `worker`) indicate which component a change touches.

The `worker/` directory exists and contains the initial server-side slice.

## Read first

- `CONTEXT.md` — domain glossary. Canonical terms (Ticker, CIK, Accession Number, Event vs Filing, Position vs Watching, Impact Dimension, Digest) are normative; use them verbatim and do not substitute synonyms. Misusing them breaks alignment with the worker and ADRs.
- `docs/adr/` — architecture decisions. Check here before changing data flow or storage. Notably:
  - ADR-0006: the app separates user-private models from reference data with distinct SwiftData schemas/configurations. These can be hosted by one `ModelContainer`; do not split containers unless there is a concrete need.

## Code style

- Swift files use 2 spaces for indentation.

### Localization

- Use `Localizable.xcstrings` for app user-facing strings. The source language is English; add `zh-Hans` translations for Simplified Chinese UI copy.
- Prefer explicit, stable localization keys instead of English prose as keys. Format keys as dot-separated semantic paths, with lowerCamelCase allowed inside each segment, e.g. `portfolio.empty.title`, `ticker.search.prompt`, `today.empty.lastUpdated`.
- Keep canonical domain terms from `CONTEXT.md` aligned in localized copy. Do not casually substitute terms such as Ticker, CIK, Accession Number, Event, Filing, Position, Watching, Watchlist, Impact Dimension, or Digest.
- Do not localize user/data content such as Ticker symbols, company names, Filing types returned by data, or worker-generated summaries. In SwiftUI, render these with `Text(verbatim:)` when needed to avoid treating them as localization keys.
- For interpolated UI strings, keep the template in `Localizable.xcstrings` and pass formatted values into the localized template rather than building user-visible English strings inline.

## Build & toolchain

### iOS app (`Stocket/`, root)

- Xcode project (`Stocket.xcodeproj`), not an SPM package. iOS-only target.
- Deployment target iOS 26.5, Swift 6. Build for simulator unless asked otherwise.
- Shared scheme `Stocket` is checked in. With `xcodebuild` pass `-scheme Stocket`.
- Bundle ID `com.flhcc.Stocket`, team `RW8NZD94C3`, app group `group.com.flhcc.Stocket`. Entitlements (`Stocket.entitlements`) enable CloudKit and APNs (development); keep these in sync if you touch capabilities.
- No SPM dependencies yet. If adding one, use Xcode's package integration (the `packageProductDependencies` section is currently empty).
- **CRITICAL**: ALWAYS use `xcodebuildmcp` instead of raw `xcodebuild` for local dev. Raw `xcodebuild` is slow and bypasses the daemon cache.
- **CRITICAL**: Verification only requires `build` to succeed. Avoid `build-and-run` (which installs and launches the app in the simulator) unless explicitly requested by the user, as booting the simulator and launching the app introduces significant unnecessary latency.
- **Canonical Commands**:
  - Build: `xcodebuildmcp simulator build --style minimal`
  - Run: `xcodebuildmcp simulator build-and-run --style minimal`
  - Test: `xcodebuildmcp simulator test --style minimal`
  - Screenshot: `xcodebuildmcp simulator screenshot`
- **Fallback (CI only)**:
  ```bash
  xcodebuild -scheme Stocket -destination 'platform=iOS Simulator,name=iPhone 17' build
  ```

When using raw `xcodebuild`, pick a simulator name that exists on the machine (`xcrun simctl list devices available`) before running.

### Swift library (`STLibrary/`)

- Swift Package for pure Swift logic and non-UI tests.
- Tests use Swift Testing and run via `swift test` without launching an iOS Simulator.

```bash
swift test --package-path STLibrary
```

### Worker (`worker/`, Python)

- Python 3.12+ on a VPS. FastAPI for the HTTP endpoints (`/watchlist`, `/devices`), cron for the daily EDGAR ingestion + LLM pipeline + APNs push.
- Dependencies managed via `pyproject.toml` + `uv` (or `pip`). Key libraries: `edgartools` (EDGAR XBRL/filing parsing), `boto3` (R2 S3-compatible API), `anthropic` or `openai` (LLM, configurable per ADR-0005), `httpx` (APNs), `fastapi` + `uvicorn`.
- SQLite for `devices`, `user_tickers` (read-replica), `run_log`, processed-filing state.
- No long-running server except the lightweight FastAPI process (systemd-managed).

```bash
# Install deps
uv pip install -e './worker[dev]'

# Run local API
uv run --project worker uvicorn src.main:app --reload --port 8787 --app-dir worker

# Run cron once
uv run --project worker python -m src.cron

# Run cron against live EDGAR instead of mock ingestion
EDGAR_IDENTITY='Name email@example.com' uv run --project worker python -m src.cron

# Run cron with live EDGAR and a real first-stage LLM provider
EDGAR_IDENTITY='Name email@example.com' LLM_PROVIDER=openai OPENAI_API_KEY='...' uv run --project worker python -m src.cron

# Run tests
uv run --project worker --extra dev pytest

# Run smoke test
uv run --project worker python worker/smoke.py
```

## Tests

- **Swift library tests** (`STLibrary/Tests/`) use Swift Testing: `import Testing`, `struct`-based suites, `@Test func`, `#expect`. Do not add XCTest-style classes here.
- **App UI tests** are intentionally absent. Do not add app-hosted UI/unit test targets unless explicitly requested; prefer moving pure logic into `STLibrary` and testing it with `swift test`.
- **Worker tests** (`worker/tests/`) use `pytest`. Keep tests isolated from `worker/data` by using temporary SQLite and summary storage paths.
- **Worker user-data endpoints** are `/watchlist` for Watchlist CIK replication and `/devices` for APNs device-token replication. Both upsert into SQLite and treat CloudKit/app state as the source of truth.
- **Smoke test** (`worker/smoke.py`) — local end-to-end tracer for `/watchlist` → cron → Event storage → `/tickers/{ticker}/events`. It forces mock ingestion by clearing `EDGAR_IDENTITY` and uses temporary storage, so it should not depend on live EDGAR, LLM credentials, or local `worker/data`.
- **EDGAR ingestion** scans recent 8-K filings for Watchlist CIKs. `EDGAR_LOOKBACK_DAYS` defaults to `7`; Accession Number dedupe is performed against stored Events, and each cron run records `run_log` status in SQLite.
- **LLM first-stage** is selected with `LLM_PROVIDER` (`mock`, `openai`, or `anthropic`). Keep `mock` as the default for tests and local smoke; real providers must return JSON with `importance`, `items`, and `oneLineSummary`.
- **Shared Event storage** is selected with `STORAGE_BACKEND` (`local` or `r2`). Keep `local` as the default for tests and smoke. R2 uses S3-compatible `boto3` with `R2_BUCKET`, `R2_ENDPOINT_URL`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, optional `R2_REGION`, and optional `R2_KEY_PREFIX`.
- **APNs Digest push** uses `worker/src/apns.py`. Configure `APNS_SEND_DIGEST=true`, `APNS_ENV`, `APNS_TOPIC`, `APNS_TEAM_ID`, `APNS_KEY_ID`, and either `APNS_PRIVATE_KEY` or `APNS_PRIVATE_KEY_PATH`. Keep APNs sending injectable in tests; do not hit Apple's API from pytest.
- **Digest event count** uses `worker/src/digest.py` to count unique Accession Numbers for Events created today across Watchlist Tickers. Keep this global for MVP; app-side filtering/personalization can refine the Digest content when opened.

## Git

- Remote: `origin` → `github.com:xiguagua/Stocket.git` (public). Default branch is `beta`; `main` also exists. Confirm branch/PR expectations with the user before pushing or opening PRs.
- Do not commit unless explicitly asked.
- Do not push unless explicitly asked — even if a remote is configured and a commit was requested, wait for an explicit push instruction.
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/): `type(scope): subject`. Scope indicates which component: `app`, `worker`, or `docs`/`repo` for cross-cutting. E.g. `feat(worker): add EDGAR daily index cron`, `feat(app): add ticker search`, `fix(worker): handle R2 list pagination`.
