"""Run a controlled Adzuna ingestion smoke test."""

import argparse
import os
from datetime import datetime, timezone
import json
from pathlib import Path

import requests

from uk_job_market_agents.ingestion.adzuna_client import (
    build_search_url,
    fetch_search_results,
)
from uk_job_market_agents.ingestion.pipeline import (
    prepare_adzuna_postings,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live",
        action="store_true",
        help="Fetch fresh Adzuna results instead of replaying the snapshot",
    )

    parser.add_argument(
        "--snapshot",
        type=Path,
        default=Path("data/raw/adzuna_sample.json"),
        help="Path to the Adzuna JSON snapshot",
    )

    args = parser.parse_args()
    snapshot_path = args.snapshot

    if args.live:
        app_id = os.environ.get("ADZUNA_APP_ID")
        app_key = os.environ.get("ADZUNA_APP_KEY")

        if not app_id or not app_key:
            raise SystemExit("Adzuna credentials are not configured")

        url = build_search_url(
            app_id=app_id,
            app_key=app_key,
            query="data engineer",
            results_per_page=5,
        )

        try:
            payload = fetch_search_results(
                url,
                transport=requests.get,
            )
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "unknown"
            raise SystemExit(f"Adzuna HTTP error (status {status})") from None
        except requests.exceptions.RequestException:
            raise SystemExit("Adzuna request failed") from None

        snapshot_path.parent.mkdir(parents=True, exist_ok=True)

        with snapshot_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2, ensure_ascii=False)

        print(f"Saved local snapshot: {snapshot_path}")

    else:
        if not snapshot_path.is_file():
            raise SystemExit(
                f"Snapshot not found: {snapshot_path}. "
                "Run with --live to create one."
            )

        with snapshot_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        print(f"Loaded local snapshot: {snapshot_path}")

    raw_advertisements = payload["results"]

    if raw_advertisements:
        first_job = raw_advertisements[0]

        print("Available fields:", sorted(first_job.keys()))
        print("Job ID type:", type(first_job["id"]).__name__)
        print("Salary minimum:", first_job.get("salary_min"))
        print("Salary maximum:", first_job.get("salary_max"))
        print("Salary predicted:", first_job.get("salary_is_predicted"))

    for job in raw_advertisements:
        print({
            "id": job.get("id"),
            "latitude": job.get("latitude"),
            "longitude": job.get("longitude"),
            "salary_min": job.get("salary_min"),
            "salary_max": job.get("salary_max"),
            "salary_is_predicted": job.get("salary_is_predicted"),
        })

    postings = prepare_adzuna_postings(
        raw_advertisements,
        collected_at=datetime.now(timezone.utc),
    )

    print(f"Retrieved: {len(raw_advertisements)}")
    print(f"Unique validated postings: {len(postings)}")

    for posting in postings:
        print(
            f"{posting.source_id}: "
            f"{posting.raw_title} | "
            f"{posting.company_name} | "
            f"{posting.location_raw}"
        )


if __name__ == "__main__":
    main()
