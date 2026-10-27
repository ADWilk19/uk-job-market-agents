import json
import sys

from scripts import smoke_adzuna


def test_offline_replay_without_credentials_or_network(
    tmp_path,
    monkeypatch,
    capsys,
):
    snapshot = tmp_path / "adzuna_sample.json"

    payload = {
        "results": [
            {
                "id": "12345",
                "title": "Data Engineer",
                "description": "Python and SQL",
            }
        ]
    }

    snapshot.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    monkeypatch.delenv("ADZUNA_APP_ID", raising=False)
    monkeypatch.delenv("ADZUNA_APP_KEY", raising=False)

    def reject_network(*args, **kwargs):
        raise AssertionError("Offline replay attempted an HTTP request")

    monkeypatch.setattr(
        smoke_adzuna.requests,
        "get",
        reject_network,
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "smoke_adzuna.py",
            "--snapshot",
            str(snapshot),
        ],
    )

    smoke_adzuna.main()

    output = capsys.readouterr().out

    assert "Retrieved: 1" in output
    assert "Unique validated postings: 1" in output
