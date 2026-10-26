import urllib.parse

"""Build a validated Adzuna UK job-search URL without making an HTTP request."""
def build_search_url(
    app_id: str,
    app_key: str,
    query: str,
    page: int = 1,
    results_per_page: int = 10,
) -> str:
    if page < 1:
        raise ValueError("Page number must be a positive integer.")
    if results_per_page < 1:
        raise ValueError("Results per page must be a positive integer.")

    base_url = "https://api.adzuna.com/v1/api/jobs/gb/search/"
    path = f"{page}"
    query_params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": query,
        "results_per_page": str(results_per_page),
    }

    url_parts = urllib.parse.urlparse(base_url + path)
    query_string = urllib.parse.urlencode(query_params)
    full_url = urllib.parse.urlunparse(
        (url_parts.scheme, url_parts.netloc, url_parts.path, "", query_string, "")
    )

    return full_url


def fetch_search_results(url: str, transport):
    """Fetch and validate an Adzuna search response."""
    response = transport(url, timeout=10)
    response.raise_for_status()

    payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError("Invalid Adzuna response")

    results = payload.get("results")

    if not isinstance(results, list):
        raise ValueError("Invalid Adzuna response")

    if not all(isinstance(item, dict) for item in results):
        raise ValueError("Invalid Adzuna response")

    return payload


def fetch_search_pages(
    app_id: str,
    app_key: str,
    query: str,
    max_pages: int,
    transport,
    fetch=fetch_search_results,
) -> list[dict]:
    """Fetch a bounded number of Adzuna pages in order."""
    if max_pages <1:
        raise ValueError("Number of pages must be greater than 0.")

    all_results = []

    for page in range(1, max_pages+1):
        url = build_search_url(
                    app_id=app_id,
                    app_key=app_key,
                    query=query,
                    page=page
                )

        payload = fetch(url, transport)

        if not payload["results"]:
            break

        all_results.extend(payload["results"])

    return all_results
