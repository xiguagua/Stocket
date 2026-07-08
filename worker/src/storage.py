import json
import os
from datetime import datetime
from pathlib import Path


STORAGE_ROOT = Path(
    os.environ.get(
        "STORAGE_ROOT",
        Path(__file__).resolve().parent.parent / "data" / "summaries",
    )
).expanduser()


def write_event(ticker: str, accession: str, data: dict) -> None:
    if _backend() == "r2":
        _r2_write_json(_event_key(ticker, accession), data)
        return
    _local_write_json(_event_path(ticker, accession), data)


def read_event(ticker: str, accession: str) -> dict | None:
    if _backend() == "r2":
        return _r2_read_json(_event_key(ticker, accession))
    return _local_read_json(_event_path(ticker, accession))


def list_events(ticker: str, since: str | None = None) -> list[dict]:
    if _backend() == "r2":
        events = _r2_list_json(prefix=_event_prefix(ticker))
    else:
        events = _local_list_json(_event_dir(ticker))

    return _filter_and_sort_events(events, since)


def _backend() -> str:
    backend = os.environ.get("STORAGE_BACKEND", "local").lower()
    if backend not in {"local", "r2"}:
        raise ValueError(f"Unsupported STORAGE_BACKEND: {backend}")
    return backend


def _event_dir(ticker: str) -> Path:
    return STORAGE_ROOT / "tickers" / ticker.upper() / "events"


def _event_path(ticker: str, accession: str) -> Path:
    return _event_dir(ticker) / f"{accession}.json"


def _event_prefix(ticker: str) -> str:
    prefix = os.environ.get("R2_KEY_PREFIX", "").strip("/")
    key = f"tickers/{ticker.upper()}/events/"
    return f"{prefix}/{key}" if prefix else key


def _event_key(ticker: str, accession: str) -> str:
    return f"{_event_prefix(ticker)}{accession}.json"


def _local_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def _local_read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _local_list_json(directory: Path) -> list[dict]:
    if not directory.exists():
        return []
    return [json.loads(path.read_text()) for path in sorted(directory.glob("*.json"))]


def _r2_client():
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=_required_env("R2_ENDPOINT_URL"),
        aws_access_key_id=_required_env("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=_required_env("R2_SECRET_ACCESS_KEY"),
        region_name=os.environ.get("R2_REGION", "auto"),
    )


def _r2_bucket() -> str:
    return _required_env("R2_BUCKET")


def _r2_write_json(key: str, data: dict) -> None:
    _r2_client().put_object(
        Bucket=_r2_bucket(),
        Key=key,
        Body=json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json",
    )


def _r2_read_json(key: str) -> dict | None:
    client = _r2_client()
    try:
        response = client.get_object(Bucket=_r2_bucket(), Key=key)
    except client.exceptions.NoSuchKey:
        return None
    except Exception as exc:
        if _is_missing_r2_key_error(exc):
            return None
        raise
    return json.loads(response["Body"].read().decode("utf-8"))


def _r2_list_json(prefix: str) -> list[dict]:
    client = _r2_client()
    events = []
    continuation_token = None

    while True:
        request = {"Bucket": _r2_bucket(), "Prefix": prefix}
        if continuation_token:
            request["ContinuationToken"] = continuation_token

        response = client.list_objects_v2(**request)
        for item in response.get("Contents", []):
            key = item.get("Key", "")
            if key.endswith(".json"):
                event = _r2_read_json(key)
                if event:
                    events.append(event)

        if not response.get("IsTruncated"):
            break
        continuation_token = response.get("NextContinuationToken")

    return events


def _filter_and_sort_events(events: list[dict], since: str | None) -> list[dict]:
    since_dt = datetime.fromisoformat(since.replace("Z", "+00:00")) if since else None
    filtered = []

    for event in events:
        if since_dt:
            event_created = event.get("createdAt", "")
            if event_created:
                event_dt = datetime.fromisoformat(event_created.replace("Z", "+00:00"))
                if event_dt <= since_dt:
                    continue
        filtered.append(event)

    filtered.sort(key=lambda e: e.get("filingDate", ""), reverse=True)
    return filtered


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required when STORAGE_BACKEND=r2")
    return value


def _is_missing_r2_key_error(exc: Exception) -> bool:
    response = getattr(exc, "response", {})
    code = response.get("Error", {}).get("Code")
    return code in {"NoSuchKey", "404", "NotFound"}
