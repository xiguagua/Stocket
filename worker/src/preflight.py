import os
import sys
from pathlib import Path


def validate() -> list[str]:
    errors = []
    provider = os.environ.get("LLM_PROVIDER", "mock").lower()
    backend = os.environ.get("STORAGE_BACKEND", "local").lower()
    _validate_edgar(errors, requires_live=provider != "mock" or backend != "local")
    if provider != "mock" or backend != "local":
        _require("WORKER_API_TOKEN", errors)
    _validate_llm(errors)
    _validate_storage(errors)
    _validate_apns(errors)
    _validate_database_path(errors)
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("Worker preflight failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Worker preflight passed.")
    return 0


def _validate_edgar(errors: list[str], requires_live: bool) -> None:
    lookback = os.environ.get("EDGAR_LOOKBACK_DAYS", "7")
    try:
        if int(lookback) < 1:
            raise ValueError
    except ValueError:
        errors.append("EDGAR_LOOKBACK_DAYS must be a positive integer")
    if requires_live:
        _require("EDGAR_IDENTITY", errors)


def _validate_llm(errors: list[str]) -> None:
    provider = os.environ.get("LLM_PROVIDER", "mock").lower()
    if provider not in {"mock", "openai", "anthropic"}:
        errors.append("LLM_PROVIDER must be mock, openai, or anthropic")
    elif provider == "openai":
        _require("OPENAI_API_KEY", errors)
    elif provider == "anthropic":
        _require("ANTHROPIC_API_KEY", errors)


def _validate_storage(errors: list[str]) -> None:
    backend = os.environ.get("STORAGE_BACKEND", "local").lower()
    if backend not in {"local", "r2"}:
        errors.append("STORAGE_BACKEND must be local or r2")
    elif backend == "r2":
        for name in ("R2_BUCKET", "R2_ENDPOINT_URL", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY"):
            _require(name, errors)


def _validate_apns(errors: list[str]) -> None:
    if os.environ.get("APNS_SEND_DIGEST", "false").lower() != "true":
        return

    if os.environ.get("APNS_ENV", "development") not in {"development", "production"}:
        errors.append("APNS_ENV must be development or production")
    for name in ("APNS_TOPIC", "APNS_TEAM_ID", "APNS_KEY_ID"):
        _require(name, errors)

    inline_key = os.environ.get("APNS_PRIVATE_KEY")
    key_path = os.environ.get("APNS_PRIVATE_KEY_PATH")
    if not inline_key and not key_path:
        errors.append("APNS_PRIVATE_KEY or APNS_PRIVATE_KEY_PATH is required when APNS_SEND_DIGEST=true")
    elif key_path and not Path(key_path).expanduser().is_file():
        errors.append("APNS_PRIVATE_KEY_PATH must point to a readable file")


def _validate_database_path(errors: list[str]) -> None:
    default = Path(__file__).resolve().parent.parent / "data" / "worker.db"
    path = Path(os.environ.get("WORKER_DB_PATH", default)).expanduser()
    if not path.parent.is_dir():
        errors.append(f"WORKER_DB_PATH parent does not exist: {path.parent}")
    elif not os.access(path.parent, os.W_OK):
        errors.append(f"WORKER_DB_PATH parent is not writable: {path.parent}")


def _require(name: str, errors: list[str]) -> None:
    if not os.environ.get(name):
        errors.append(f"{name} is required")


if __name__ == "__main__":
    sys.exit(main())
