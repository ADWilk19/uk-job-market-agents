import pytest

from unittest.mock import Mock

from urllib.parse import parse_qs, urlsplit

from uk_job_market_agents.ingestion.adzuna_client import (
    build_search_url,
    fetch_search_results,
     fetch_search_pages,
)


def test_adzuna_search_url_uses_correct_endpoint():
    url = build_search_url(
        app_id="test-id",
        app_key="test-key",
        query="data engineer",
        page=2,
        results_per_page=5,
    )

    parsed = urlsplit(url)

    assert parsed.scheme == "https"
    assert parsed.netloc == "api.adzuna.com"
    assert parsed.path == "/v1/api/jobs/gb/search/2"

    assert parse_qs(parsed.query) == {
        "app_id": ["test-id"],
        "app_key": ["test-key"],
        "what": ["data engineer"],
        "results_per_page": ["5"],
    }



@pytest.mark.parametrize("page", [0, -1])
def test_adzuna_search_url_rejects_invalid_page(page):
    with pytest.raises(ValueError):
        build_search_url(
            app_id="test-id",
            app_key="test-key",
            query="data engineer",
            page=page,
            results_per_page=5,
        )


@pytest.mark.parametrize("results_per_page", [0, -5])
def test_adzuna_search_url_rejects_invalid_result_count(
    results_per_page,
):
    with pytest.raises(ValueError):
        build_search_url(
            app_id="test-id",
            app_key="test-key",
            query="data engineer",
            page=1,
            results_per_page=results_per_page,
        )


def test_fetch_search_results_returns_json_payload():
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "count": 1,
        "results": [{"id": "123", "title": "Data Engineer"}],
    }

    transport = Mock(return_value=response)

    payload = fetch_search_results(
        url="https://example.com/jobs",
        transport=transport,
    )

    assert payload == {
        "count": 1,
        "results": [{"id": "123", "title": "Data Engineer"}],
    }

    transport.assert_called_once_with(
        "https://example.com/jobs",
        timeout=10,
    )


def test_fetch_search_results_raises_on_http_error():
    response = Mock()
    response.raise_for_status.side_effect = RuntimeError(
        "HTTP 500: Internal Server Error"
    )

    transport = Mock(return_value=response)

    with pytest.raises(
        RuntimeError,
        match="HTTP 500",
    ):
        fetch_search_results(
            url="https://example.com/jobs",
            transport=transport,
        )

    response.raise_for_status.assert_called_once()


@pytest.mark.parametrize(
    "payload",
    [
        ["not", "a", "response", "object"],
        {"message": "Unexpected response"},
        {"results": "not a list"},
        {"results": [None]},
    ],
)
def test_fetch_search_results_rejects_invalid_payload(payload):
    response = Mock()
    response.json.return_value = payload

    transport = Mock(return_value=response)

    with pytest.raises(ValueError, match="Invalid Adzuna response"):
        fetch_search_results(
            url="https://example.com/jobs",
            transport=transport,
        )


def test_fetch_search_results_accepts_empty_results():
    response = Mock()
    response.json.return_value = {
        "count": 0,
        "results": [],
    }

    transport = Mock(return_value=response)

    payload = fetch_search_results(
        url="https://example.com/jobs",
        transport=transport,
    )

    assert payload["results"] == []


def test_fetch_search_results_propagates_json_decode_error():
    response = Mock()
    response.json.side_effect = ValueError("Invalid JSON")

    transport = Mock(return_value=response)

    with pytest.raises(ValueError, match="Invalid JSON"):
        fetch_search_results(
            url="https://example.com/jobs",
            transport=transport,
        )

    response.raise_for_status.assert_called_once()


@pytest.mark.parametrize(
    "error",
    [
        TimeoutError("Request timed out"),
        ConnectionError("Connection failed"),
    ],
)
def test_fetch_search_results_propagates_transport_errors(error):
    transport = Mock(side_effect=error)

    with pytest.raises(type(error), match=str(error)):
        fetch_search_results(
            url="https://example.com/jobs",
            transport=transport,
        )

    transport.assert_called_once_with(
        "https://example.com/jobs",
        timeout=10,
    )


def test_fetch_search_pages_combines_results_in_order():
    pages = {
        1: {"count": 4, "results": [
            {"id": "A"}, {"id": "B"}
        ]},
        2: {"count": 4, "results": [
            {"id": "C"}, {"id": "D"}
        ]},
    }

    requested_pages = []

    def fake_fetch(url, transport):
        page = int(url.split("/search/")[1].split("?")[0])
        requested_pages.append(page)
        return pages[page]

    results = fetch_search_pages(
        app_id="test-id",
        app_key="test-key",
        query="data engineer",
        max_pages=2,
        transport=object(),
        fetch=fake_fetch,
    )

    assert [job["id"] for job in results] == [
        "A", "B", "C", "D"
    ]
    assert requested_pages == [1, 2]


@pytest.mark.parametrize("max_pages", [0, -1])
def test_fetch_search_pages_rejects_invalid_page_limit(max_pages):
    fetch = Mock()

    with pytest.raises(ValueError):
        fetch_search_pages(
            app_id="test-id",
            app_key="test-key",
            query="data engineer",
            max_pages=max_pages,
            transport=object(),
            fetch=fetch,
        )

    fetch.assert_not_called()


def test_fetch_search_pages_stops_on_empty_page():
    requested_pages = []

    def fake_fetch(url, transport):
        page = int(url.split("/search/")[1].split("?")[0])
        requested_pages.append(page)

        if page == 1:
            return {"count": 1, "results": [{"id": "A"}]}

        return {"count": 1, "results": []}

    results = fetch_search_pages(
        app_id="test-id",
        app_key="test-key",
        query="data engineer",
        max_pages=5,
        transport=object(),
        fetch=fake_fetch,
    )

    assert results == [{"id": "A"}]
    assert requested_pages == [1, 2]
