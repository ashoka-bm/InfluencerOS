"""X (Twitter) discovery via the xAI API `x_search` tool.

Adapted from Agentic OS `str-trending-research/scripts/lib/xai_x.py`. Unlike
Reddit, engagement comes back inline with each post, so there is no separate
enrichment step. Stdlib only; `mock_response` allows tests without live calls.
"""

import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from influencer_os.connectors import http
from influencer_os.connectors.parse import extract_items, extract_output_text, safe_int, safe_relevance

_X_HOSTS = {
    "x.com", "www.x.com", "mobile.x.com",
    "twitter.com", "www.twitter.com", "mobile.twitter.com",
}


def is_x_status_url(url: str) -> bool:
    """True only for a real X/Twitter status URL (known host + /status/ path)."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    host = (parsed.netloc or "").lower().split(":")[0]
    return host in _X_HOSTS and "/status/" in parsed.path

XAI_RESPONSES_URL = "https://api.x.ai/v1/responses"

DEPTH_CONFIG = {"quick": (8, 12), "default": (20, 30), "deep": (40, 60)}

X_SEARCH_PROMPT = """You have access to real-time X (Twitter) data. Search for posts about: {topic}

Focus on posts from {from_date} to {to_date}. Find {min_items}-{max_items} high-quality, relevant posts.

IMPORTANT: Return ONLY valid JSON in this exact format, no other text:
{{
  "items": [
    {{
      "text": "Post text content (truncated if long)",
      "url": "https://x.com/user/status/...",
      "author_handle": "username",
      "date": "YYYY-MM-DD or null if unknown",
      "engagement": {{
        "likes": 100,
        "reposts": 25,
        "replies": 15,
        "quotes": 5
      }},
      "why_relevant": "Brief explanation of relevance",
      "relevance": 0.85
    }}
  ]
}}

Rules:
- relevance is 0.0 to 1.0 (1.0 = highly relevant)
- date must be YYYY-MM-DD format or null
- engagement can be null if unknown
- Include diverse voices/accounts if applicable
- Prefer posts with substantive content, not just links"""


def search_x(
    api_key: str,
    model: str,
    topic: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
    mock_response: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Search X for relevant posts using the xAI API with live search."""
    if mock_response is not None:
        return mock_response

    min_items, max_items = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["default"])
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    timeout = 90 if depth == "quick" else 120 if depth == "default" else 180

    payload = {
        "model": model,
        "tools": [{"type": "x_search"}],
        "input": [
            {
                "role": "user",
                "content": X_SEARCH_PROMPT.format(
                    topic=topic, from_date=from_date, to_date=to_date,
                    min_items=min_items, max_items=max_items,
                ),
            }
        ],
    }
    return http.post(XAI_RESPONSES_URL, payload, headers=headers, timeout=timeout)


def parse_x_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract clean X candidate items (with inline engagement) from an xAI response."""
    if response.get("error"):
        return []
    output_text = extract_output_text(response)
    if not output_text:
        return []

    clean: List[Dict[str, Any]] = []
    for i, item in enumerate(extract_items(output_text)):
        if not isinstance(item, dict):
            continue
        url = item.get("url", "")
        if not is_x_status_url(url):
            continue

        engagement = None
        eng_raw = item.get("engagement")
        if isinstance(eng_raw, dict):
            engagement = {
                "likes": safe_int(eng_raw.get("likes")),
                "reposts": safe_int(eng_raw.get("reposts")),
                "replies": safe_int(eng_raw.get("replies")),
                "quotes": safe_int(eng_raw.get("quotes")),
            }

        date = item.get("date")
        if date and not re.match(r"^\d{4}-\d{2}-\d{2}$", str(date)):
            date = None

        clean.append(
            {
                "id": f"X{i + 1}",
                "text": str(item.get("text", "")).strip()[:500],
                "url": url,
                "author_handle": str(item.get("author_handle", "")).strip().lstrip("@"),
                "date": date,
                "engagement": engagement,
                "why_relevant": str(item.get("why_relevant", "")).strip(),
                "relevance": safe_relevance(item.get("relevance", 0.5)),
            }
        )
    return clean
