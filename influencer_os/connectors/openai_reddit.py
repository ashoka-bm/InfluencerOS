"""Reddit discovery via the OpenAI Responses API `web_search` tool.

Adapted from Agentic OS `str-trending-research/scripts/lib/openai_reddit.py`.
The `web_search` tool is domain-locked to reddit.com; it returns candidate
threads (url/title/subreddit/relevance) which `reddit_enrich` then enriches with
real engagement. Stdlib only. `mock_response` allows tests without live calls.
"""

import json
import re
from typing import Any, Dict, List, Optional

from influencer_os.connectors import http

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
MODEL_FALLBACK_ORDER = ["gpt-4o", "gpt-4o-mini"]

DEPTH_CONFIG = {"quick": (15, 25), "default": (30, 50), "deep": (70, 100)}

REDDIT_SEARCH_PROMPT = """Find Reddit discussion threads about: {topic}

Search broadly for the core subject on reddit.com. Prefer threads from
{from_date} to {to_date}; research is time-sensitive, so favor recent activity
and set "date" to "YYYY-MM-DD" when you can determine it (null if you cannot).

REQUIRED: URLs must contain "/r/" AND "/comments/".
REJECT: developers.reddit.com, business.reddit.com.

Find {min_items}-{max_items} threads. Return MORE rather than fewer.

Return JSON:
{{
  "items": [
    {{
      "title": "Thread title",
      "url": "https://www.reddit.com/r/sub/comments/xyz/title/",
      "subreddit": "subreddit_name",
      "date": "YYYY-MM-DD or null",
      "why_relevant": "Why relevant",
      "relevance": 0.85
    }}
  ]
}}"""


def _is_model_access_error(error: http.HTTPError) -> bool:
    if error.status_code != 400 or not error.body:
        return False
    body_lower = error.body.lower()
    return any(
        phrase in body_lower
        for phrase in ("verified", "organization must be", "does not have access", "not available", "not found")
    )


def search_reddit(
    api_key: str,
    model: str,
    topic: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
    mock_response: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Call the OpenAI Responses API to find Reddit threads for a topic.

    `from_date`/`to_date` (YYYY-MM-DD) bias the search toward the recency window;
    research is time-sensitive, so the caller always passes an explicit window.
    """
    if mock_response is not None:
        return mock_response

    min_items, max_items = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["default"])
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    timeout = 90 if depth == "quick" else 120 if depth == "default" else 180
    input_text = REDDIT_SEARCH_PROMPT.format(
        topic=topic, from_date=from_date, to_date=to_date,
        min_items=min_items, max_items=max_items,
    )

    models_to_try = [model] + [m for m in MODEL_FALLBACK_ORDER if m != model]
    last_error: Optional[http.HTTPError] = None
    for current_model in models_to_try:
        payload = {
            "model": current_model,
            "tools": [{"type": "web_search", "filters": {"allowed_domains": ["reddit.com"]}}],
            "include": ["web_search_call.action.sources"],
            "input": input_text,
        }
        try:
            return http.post(OPENAI_RESPONSES_URL, payload, headers=headers, timeout=timeout)
        except http.HTTPError as exc:
            last_error = exc
            if _is_model_access_error(exc):
                continue
            raise
    raise last_error or http.HTTPError("No models available")


def _extract_output_text(response: Dict[str, Any]) -> str:
    """Pull the assistant text out of an OpenAI Responses payload."""
    output = response.get("output")
    if isinstance(output, str):
        return output
    if isinstance(output, list):
        for item in output:
            if isinstance(item, dict):
                if item.get("type") == "message":
                    for c in item.get("content", []):
                        if isinstance(c, dict) and c.get("type") == "output_text":
                            return c.get("text", "")
                elif "text" in item:
                    return item["text"]
            elif isinstance(item, str):
                return item
    for choice in response.get("choices", []):
        if "message" in choice:
            return choice["message"].get("content", "")
    return ""


def _iter_balanced_objects(text: str):
    """Yield every balanced ``{...}`` substring, left to right."""
    for start, ch in enumerate(text):
        if ch != "{":
            continue
        depth = 0
        for j in range(start, len(text)):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    yield text[start:j + 1]
                    break


def _extract_items(output_text: str) -> List[Any]:
    """Find the JSON object that carries "items", tolerating surrounding text
    or other JSON objects (a greedy first-brace-to-last-brace match corrupts
    the payload when the model emits more than one object)."""
    for candidate in _iter_balanced_objects(output_text):
        if '"items"' not in candidate:
            continue
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            return data["items"]
    return []


def _safe_relevance(value: Any) -> float:
    """Coerce a model-supplied relevance to [0, 1], defaulting on bad input."""
    try:
        return min(1.0, max(0.0, float(value)))
    except (TypeError, ValueError):
        return 0.5


def parse_reddit_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract clean Reddit candidate items from an OpenAI response."""
    if response.get("error"):
        return []
    output_text = _extract_output_text(response)
    if not output_text:
        return []

    clean: List[Dict[str, Any]] = []
    for i, item in enumerate(_extract_items(output_text)):
        if not isinstance(item, dict):
            continue
        url = item.get("url", "")
        if not url or "reddit.com" not in url:
            continue
        date = item.get("date")
        if date and not re.match(r"^\d{4}-\d{2}-\d{2}$", str(date)):
            date = None
        clean.append(
            {
                "id": f"R{i + 1}",
                "title": str(item.get("title", "")).strip(),
                "url": url,
                "subreddit": str(item.get("subreddit", "")).strip().lstrip("r/"),
                "date": date,
                "why_relevant": str(item.get("why_relevant", "")).strip(),
                "relevance": _safe_relevance(item.get("relevance", 0.5)),
            }
        )
    return clean
