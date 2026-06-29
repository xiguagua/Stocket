from . import edgar_ingest


def run_cron():
    print("Starting cron run...")
    processed = edgar_ingest.run_ingestion()
    print(f"Cron complete. Processed {processed} filings.")
    return processed


def main():
    run_cron()


if __name__ == "__main__":
    main()
