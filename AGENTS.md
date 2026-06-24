# AGENTS.md

Repo-specific guidance for OpenCode sessions working on Stocket.

## Repo scope

This is a monorepo containing two components of the Stocket system:

- **`Stocket/`** (root) — iOS app (SwiftUI + SwiftData, Xcode project at root)
- **`worker/`** — Python VPS cron + FastAPI server (EDGAR ingestion, two-stage LLM pipeline, APNs push, SQLite read-replica, R2 read endpoint for the app)

`CONTEXT.md` defines the domain glossary shared across all components. ADRs in `docs/adr/` cover cross-cutting decisions. Commit scope tags (`app`, `worker`) indicate which component a change touches.

The app is currently Xcode-template scaffold (`ContentView.swift`, `Item.swift`). The `worker/` directory does not exist yet — create it when implementing the first server-side slice.

## Read first

- `CONTEXT.md` — domain glossary. Canonical terms (Ticker, CIK, Accession Number, Event vs Filing, Position vs Watching, Impact Dimension, Digest) are normative; use them verbatim and do not substitute synonyms. Misusing them breaks alignment with the worker and ADRs.
- `docs/adr/` — architecture decisions. Check here before changing data flow or storage. Notably:
  - ADR-0006: the app uses **two SwiftData containers** — `UserContainer` (CloudKit Private DB synced, user-private models) and `ReferenceContainer` (local-only, read-only mirror of shared data). `@Environment(\.modelContext)` must be targeted to the correct container; do not assume a single container.

## Build & toolchain

### iOS app (`Stocket/`, root)

- Xcode project (`Stocket.xcodeproj`), not an SPM package. iOS-only target.
- Deployment target iOS 27.0, Swift 6. Build for simulator unless asked otherwise.
- No shared schemes are checked in; Xcode auto-generates the `Stocket` scheme. With `xcodebuild` pass `-scheme Stocket`.
- Bundle ID `com.flhcc.Stocket`, team `RW8NZD94C3`, app group `group.com.flhcc.Stocket`. Entitlements (`Stocket.entitlements`) enable CloudKit and APNs (development); keep these in sync if you touch capabilities.
- No SPM dependencies yet. If adding one, use Xcode's package integration (the `packageProductDependencies` section is currently empty).

```bash
# Build (simulator)
xcodebuild -scheme Stocket -destination 'platform=iOS Simulator,name=iPhone 16' build

# Run unit + UI tests
xcodebuild -scheme Stocket -destination 'platform=iOS Simulator,name=iPhone 16' test

# Single test (Swift Testing)
xcodebuild -scheme Stocket -destination 'platform=iOS Simulator,name=iPhone 16' test -only-testing:StocketTests/StocketTests/example
```

Pick a simulator name that exists on the machine (`xcrun simctl list devices available`) before running.

### Worker (`worker/`, Python)

- Python 3.12+ on a VPS. FastAPI for the HTTP endpoints (`/watchlist`, `/devices`), cron for the daily EDGAR ingestion + LLM pipeline + APNs push.
- Dependencies managed via `pyproject.toml` + `uv` (or `pip`). Key libraries: `edgartools` (EDGAR XBRL/filing parsing), `boto3` (R2 S3-compatible API), `anthropic` or `openai` (LLM, configurable per ADR-0005), `httpx` (APNs), `fastapi` + `uvicorn`.
- SQLite for `devices`, `user_tickers` (read-replica), `run_log`, processed-filing state.
- No long-running server except the lightweight FastAPI process (systemd-managed).

```bash
# Install deps
uv pip install -e worker/

# Run tests
pytest worker/tests/

# Run smoke test
python worker/smoke.py
```

## Tests

- **iOS unit tests** (`StocketTests/`) use Swift Testing: `import Testing`, `struct`-based suites, `@Test func`, `#expect`. Do not add XCTest-style classes here.
- **iOS UI tests** (`StocketUITests/`) use `XCTestCase`. These need a runnable app target and a simulator.
- **Worker tests** (`worker/tests/`) use `pytest`. Pure-function unit tests only (XBRL parser, schema validator, gap detection, payload constructor, accession dedup). See ADR-0002 and Q33-B.
- **Smoke test** (`worker/smoke.py`) — end-to-end pipeline on a known historical filing. Run before deploying worker changes.

## Git

- Remote: `origin` → `github.com:xiguagua/Stocket.git` (public). Default branch is `beta`; `main` also exists. Confirm branch/PR expectations with the user before pushing or opening PRs.
- Do not commit unless explicitly asked.
- Do not push unless explicitly asked — even if a remote is configured and a commit was requested, wait for an explicit push instruction.
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/): `type(scope): subject`. Scope indicates which component: `app`, `worker`, or `docs`/`repo` for cross-cutting. E.g. `feat(worker): add EDGAR daily index cron`, `feat(app): add ticker search`, `fix(worker): handle R2 list pagination`.
