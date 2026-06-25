# AGENTS.md

Repo-specific guidance for OpenCode sessions working on Stocket.

## Repo scope

This is a monorepo containing two components of the Stocket system:

- **`Stocket/`** (root) — iOS app (SwiftUI + SwiftData, Xcode project at root)
- **`STLibrary/`** — Swift Package for pure Swift logic and non-UI Swift Testing tests
- **`worker/`** — Python VPS cron + FastAPI server (EDGAR ingestion, two-stage LLM pipeline, APNs push, SQLite read-replica, R2 read endpoint for the app)

`CONTEXT.md` defines the domain glossary shared across all components. ADRs in `docs/adr/` cover cross-cutting decisions. Commit scope tags (`app`, `worker`) indicate which component a change touches.

The `worker/` directory does not exist yet — create it when implementing the first server-side slice.

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
- Prefer XcodeBuildMCP for agent-driven app builds, runs, tests, simulator logs, screenshots, and UI inspection. Keep raw `xcodebuild` for CI, fallback, and exact command-line reproduction. Unless the user explicitly asks to run the app, inspect UI, capture screenshots, or collect runtime logs, use `build_sim` rather than `build_run_sim` so the Simulator is not launched unnecessarily.
- XcodeBuildMCP defaults are persisted in `.xcodebuildmcp/config.yaml` for the app: project `Stocket.xcodeproj`, scheme `Stocket`, configuration `Debug`, simulator `iPhone 17` (`9250ED78-3FC0-4EFE-97BB-5070F3A28AFD`). For MCP workflows, first call `session_show_defaults`; if these defaults are present, use `build_sim`, `build_run_sim`, or `test_sim` without repeating project/scheme/simulator arguments.

```bash
# Build (simulator)
xcodebuild -scheme Stocket -destination 'platform=iOS Simulator,name=iPhone 17' build
```

Pick a simulator name that exists on the machine (`xcrun simctl list devices available`) before running.

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
uv pip install -e worker/

# Run tests
pytest worker/tests/

# Run smoke test
python worker/smoke.py
```

## Tests

- **Swift library tests** (`STLibrary/Tests/`) use Swift Testing: `import Testing`, `struct`-based suites, `@Test func`, `#expect`. Do not add XCTest-style classes here.
- **App UI tests** are intentionally absent. Do not add app-hosted UI/unit test targets unless explicitly requested; prefer moving pure logic into `STLibrary` and testing it with `swift test`.
- **Worker tests** (`worker/tests/`) use `pytest`. Pure-function unit tests only (XBRL parser, schema validator, gap detection, payload constructor, accession dedup). See ADR-0002 and Q33-B.
- **Smoke test** (`worker/smoke.py`) — end-to-end pipeline on a known historical filing. Run before deploying worker changes.

## Git

- Remote: `origin` → `github.com:xiguagua/Stocket.git` (public). Default branch is `beta`; `main` also exists. Confirm branch/PR expectations with the user before pushing or opening PRs.
- Do not commit unless explicitly asked.
- Do not push unless explicitly asked — even if a remote is configured and a commit was requested, wait for an explicit push instruction.
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/): `type(scope): subject`. Scope indicates which component: `app`, `worker`, or `docs`/`repo` for cross-cutting. E.g. `feat(worker): add EDGAR daily index cron`, `feat(app): add ticker search`, `fix(worker): handle R2 list pagination`.
