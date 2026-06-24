# AGENTS.md

Repo-specific guidance for OpenCode sessions working on Stocket.

## Repo scope

This repository is the **iOS app only**. `CONTEXT.md` describes the full system — a Python cron worker, Cloudflare Worker, R2, and a SQLite read-replica — but those components live elsewhere. Do not expect to find worker, infra, or backend code here; the app talks to them over the network and CloudKit.

The app is currently Xcode-template scaffold (`ContentView.swift`, `Item.swift`). Real feature code has not been written yet.

## Read first

- `CONTEXT.md` — domain glossary. Canonical terms (Ticker, CIK, Accession Number, Event vs Filing, Position vs Watching, Impact Dimension, Digest) are normative; use them verbatim and do not substitute synonyms. Misusing them breaks alignment with the worker and ADRs.
- `docs/adr/` — architecture decisions. Check here before changing data flow or storage. Notably:
  - ADR-0006: the app uses **two SwiftData containers** — `UserContainer` (CloudKit Private DB synced, user-private models) and `ReferenceContainer` (local-only, read-only mirror of shared data). `@Environment(\.modelContext)` must be targeted to the correct container; do not assume a single container.

## Build & toolchain

- Xcode project (`Stocket.xcodeproj`), not an SPM package. iOS-only target.
- Deployment target iOS 27.0, Swift 6. Build for simulator unless asked otherwise.
- No shared schemes are checked in; Xcode auto-generates the `Stocket` scheme. With `xcodebuild` pass `-scheme Stocket`.
- Bundle ID `com.flhcc.Stocket`, team `RW8NZD94C3`, app group `group.com.flhcc.Stocket`. Entitlements (`Stocket.entitlements`) enable CloudKit and APNs (development); keep these in sync if you touch capabilities.
- No SPM dependencies yet. If adding one, use Xcode's package integration (the `packageProductDependencies` section is currently empty).

### Commands

```bash
# Build (simulator)
xcodebuild -scheme Stocket -destination 'platform=iOS Simulator,name=iPhone 16' build

# Run unit + UI tests
xcodebuild -scheme Stocket -destination 'platform=iOS Simulator,name=iPhone 16' test

# Single test (Swift Testing)
xcodebuild -scheme Stocket -destination 'platform=iOS Simulator,name=iPhone 16' test -only-testing:StocketTests/StocketTests/example
```

Pick a simulator name that exists on the machine (`xcrun simctl list devices available`) before running.

## Tests

- **Unit tests** (`StocketTests/`) use Swift Testing: `import Testing`, `struct`-based suites, `@Test func`, `#expect`. Do not add XCTest-style classes here.
- **UI tests** (`StocketUITests/`) use `XCTestCase`. These need a runnable app target and a simulator.

## Git

- No remote is configured. Default branch is `beta`; `main` also exists. Confirm branch/PR expectations with the user before pushing or opening PRs.
- Do not commit unless explicitly asked.
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/): `type(scope): subject`, e.g. `feat(tickers): add watchlist view`, `fix(sync): handle CloudKit quota error`.
