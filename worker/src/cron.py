import os

from . import apns, digest, edgar_ingest


def run_cron():
    print("Starting cron run...")
    processed = edgar_ingest.run_ingestion()
    if _should_send_digest():
        event_count = digest.count_today_events()
        result = apns.send_digest(event_count)
        print(f"Digest push complete. {result}")
    print(f"Cron complete. Processed {processed} filings.")
    return processed


def _should_send_digest() -> bool:
    return os.environ.get("APNS_SEND_DIGEST", "false").lower() == "true"


def main():
    run_cron()


if __name__ == "__main__":
    main()
