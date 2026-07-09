# Stocket Worker Deployment

This document describes the MVP VPS deployment for the Python worker: FastAPI HTTP endpoints, daily EDGAR cron ingestion, R2 Event storage, and optional APNs Digest push.

## Layout

Assumed paths in the templates:

```text
/opt/stocket              # git checkout
/opt/stocket/worker       # worker project
/etc/stocket/worker.env   # production environment file
```

Adjust the unit files in `worker/deploy/` if your VPS uses different paths or user names.

## Prerequisites

- Linux VPS with systemd
- Python 3.12+
- `uv`
- Git checkout of this repo
- Cloudflare R2 bucket and credentials if `STORAGE_BACKEND=r2`
- EDGAR identity string for live ingestion
- OpenAI or Anthropic credentials if `LLM_PROVIDER` is not `mock`
- Apple APNs key if `APNS_SEND_DIGEST=true`

## Install

From the checkout root:

```bash
uv sync --project worker --locked
```

For a first deployment without an existing lockfile-compatible environment, run:

```bash
uv sync --project worker --locked --extra dev
uv run --project worker --extra dev pytest
```

Do not use the dev extra for the long-running production service unless you intentionally want test dependencies installed on the VPS.

## Environment

Create `/etc/stocket/worker.env` from `worker/.env.example` and fill production values.

Create the service user and config directory:

```bash
sudo useradd --system --home /var/lib/stocket --shell /usr/sbin/nologin stocket
sudo mkdir -p /etc/stocket
sudo cp worker/.env.example /etc/stocket/worker.env
sudo chown root:stocket /etc/stocket/worker.env
sudo chmod 640 /etc/stocket/worker.env
```

Recommended production baseline:

```text
EDGAR_IDENTITY=Name email@example.com
EDGAR_LOOKBACK_DAYS=7

LLM_PROVIDER=openai
LLM_FIRST_STAGE_MODEL=
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=

STORAGE_BACKEND=r2
R2_BUCKET=...
R2_ENDPOINT_URL=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_REGION=auto
R2_KEY_PREFIX=

APNS_SEND_DIGEST=false
APNS_ENV=production
APNS_TOPIC=com.flhcc.Stocket
APNS_TEAM_ID=...
APNS_KEY_ID=...
APNS_PRIVATE_KEY_PATH=/etc/stocket/AuthKey_KEYID.p8

WORKER_DB_PATH=/var/lib/stocket/worker.db
```

Create writable state directories:

```bash
sudo mkdir -p /var/lib/stocket
sudo chown stocket:stocket /var/lib/stocket
```

Use `APNS_SEND_DIGEST=false` until device registration and APNs credentials are verified.

## systemd Units

Templates live in `worker/deploy/`:

- `stocket-worker.service` runs FastAPI via uvicorn.
- `stocket-cron.service` runs one ingestion cycle.
- `stocket-cron.timer` schedules the cron service daily.

Install templates:

```bash
sudo cp worker/deploy/stocket-worker.service /etc/systemd/system/
sudo cp worker/deploy/stocket-cron.service /etc/systemd/system/
sudo cp worker/deploy/stocket-cron.timer /etc/systemd/system/
sudo systemctl daemon-reload
```

Enable API service:

```bash
sudo systemctl enable --now stocket-worker.service
```

Enable daily cron timer:

```bash
sudo systemctl enable --now stocket-cron.timer
```

Run cron once manually:

```bash
sudo systemctl start stocket-cron.service
```

## Verification

Local test suite before deployment:

```bash
uv run --project worker --extra dev pytest
```

Local smoke tracer before deployment:

```bash
uv run --project worker python worker/smoke.py
```

VPS health check:

```bash
curl http://127.0.0.1:8787/health
```

Seed a Watchlist CIK:

```bash
curl -X POST http://127.0.0.1:8787/watchlist \
  -H 'Content-Type: application/json' \
  -d '{"userId":"local-user","ticker":"AAPL","cik":"0000320193","relation":"watching"}'
```

Run ingestion once and read Events:

```bash
sudo systemctl start stocket-cron.service
curl http://127.0.0.1:8787/tickers/AAPL/events
```

## Logs

API logs:

```bash
journalctl -u stocket-worker.service -f
```

Cron logs:

```bash
journalctl -u stocket-cron.service -n 200
```

Timer state:

```bash
systemctl list-timers stocket-cron.timer
```

## Rollback

1. Disable APNs first if push behavior is suspect:

```bash
sudo systemctl edit stocket-cron.service
```

Set or override `APNS_SEND_DIGEST=false` in the environment file, then restart the cron service.

2. Roll back code:

```bash
git -C /opt/stocket checkout <known-good-commit>
cd /opt/stocket
uv sync --project worker --locked
sudo systemctl restart stocket-worker.service
sudo systemctl start stocket-cron.service
```

3. If R2 data is bad, stop cron before deleting or rewriting objects:

```bash
sudo systemctl stop stocket-cron.timer
```

Do not delete `worker.db` unless you intentionally want to discard device tokens, Watchlist CIK replicas, and run logs.
