"""Load saved Adzuna API responses for offline processing."""

import json
from pathlib import Path
from typing import Any


def load_adzuna_snapshot(path: Path) -> list[dict[str, Any]]:
    """Read advertisements from a saved Adzuna JSON response."""
    with path.open("r", encoding="utf-8") as source:
        payload = json.load(source)

    if not isinstance(payload, dict) or "results" not in payload:
        raise ValueError("Invalid Adzuna snapshot: missing results")

    results = payload["results"]

    if not isinstance(results, list):
        raise ValueError(
            "Invalid Adzuna snapshot: results must be a list"
        )

    if not all(isinstance(item, dict) for item in results):
        raise ValueError(
            "Invalid Adzuna snapshot: results must contain objects"
        )

    return results
