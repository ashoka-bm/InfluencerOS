"""Public-web page scraping via the Firecrawl v2 REST API.

Adapted from Agentic OS `tool-firecrawl-scraper` (its references/api-guide.md
documents the /v2/scrape contract; the SDK is not used — the repo pattern is
stdlib HTTP). Renders JS-heavy public pages (including Reddit) into markdown
plus metadata. `mock_response` allows tests without live calls.
"""

from typing import Any, Dict, Optional

from influencer_os.connectors import http

FIRECRAWL_SCRAPE_URL = "https://api.firecrawl.dev/v2/scrape"

MAX_MARKDOWN_CHARS = 20000


def scrape(
    api_key: str,
    url: str,
    only_main_content: bool = True,
    timeout: int = 60,
    mock_response: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Scrape one public page to markdown via POST /v2/scrape."""
    if mock_response is not None:
        return mock_response

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": only_main_content,
    }
    return http.post(FIRECRAWL_SCRAPE_URL, payload, headers=headers, timeout=timeout)


def parse_scrape_response(response: Dict[str, Any], url: str) -> Optional[Dict[str, Any]]:
    """Reduce a Firecrawl scrape payload to one candidate item, or None on failure."""
    if not isinstance(response, dict) or response.get("success") is False:
        return None
    data = response.get("data")
    if not isinstance(data, dict):
        return None

    markdown = data.get("markdown") or ""
    metadata = data.get("metadata") or {}
    if not markdown:
        return None

    truncated = len(markdown) > MAX_MARKDOWN_CHARS
    return {
        "id": "F1",
        "url": metadata.get("sourceURL") or url,
        "title": str(metadata.get("title", "")).strip(),
        "description": str(metadata.get("description", "")).strip(),
        "markdown": markdown[:MAX_MARKDOWN_CHARS],
        "markdown_truncated": truncated,
        "status_code": metadata.get("statusCode"),
    }
