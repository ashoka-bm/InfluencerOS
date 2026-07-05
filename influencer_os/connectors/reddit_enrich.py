"""Reddit thread enrichment with real engagement metrics.

Adapted from Agentic OS `str-trending-research/scripts/lib/reddit_enrich.py`.
Fetches the public `reddit.com/...json` view of a thread directly (stdlib
urllib) to attach true upvotes, comment counts, and upvote ratio — the raw
material the create-research-findings skill maps into a MetricSnapshot.
`mock_thread_data` allows tests without live calls.
"""

from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from influencer_os.connectors import http


def extract_reddit_path(url: str) -> Optional[str]:
    try:
        parsed = urlparse(url)
        if "reddit.com" not in parsed.netloc:
            return None
        return parsed.path
    except ValueError:
        return None


def fetch_thread_data(url: str, mock_data: Optional[Dict] = None) -> Optional[Any]:
    if mock_data is not None:
        return mock_data
    path = extract_reddit_path(url)
    if not path:
        return None
    try:
        return http.get_reddit_json(path)
    except http.HTTPError:
        return None


def parse_thread_data(data: Any) -> Dict[str, Any]:
    """Reduce the Reddit listing JSON to a submission summary + top comments."""
    result: Dict[str, Any] = {"submission": None, "comments": []}
    if not isinstance(data, list) or not data:
        return result

    children = data[0].get("data", {}).get("children", []) if isinstance(data[0], dict) else []
    if children:
        sub = children[0].get("data", {})
        result["submission"] = {
            "score": sub.get("score"),
            "num_comments": sub.get("num_comments"),
            "upvote_ratio": sub.get("upvote_ratio"),
            "created_utc": sub.get("created_utc"),
            "title": sub.get("title"),
        }

    if len(data) >= 2 and isinstance(data[1], dict):
        for child in data[1].get("data", {}).get("children", []):
            if child.get("kind") != "t1":
                continue
            c = child.get("data", {})
            if not c.get("body"):
                continue
            result["comments"].append(
                {
                    "score": c.get("score", 0),
                    "author": c.get("author", "[deleted]"),
                    "body": c.get("body", "")[:300],
                }
            )
    return result


def get_top_comments(comments: List[Dict], limit: int = 10) -> List[Dict[str, Any]]:
    valid = [c for c in comments if c.get("author") not in ("[deleted]", "[removed]")]
    return sorted(valid, key=lambda c: c.get("score", 0), reverse=True)[:limit]


def enrich_reddit_item(item: Dict[str, Any], mock_thread_data: Optional[Dict] = None) -> Dict[str, Any]:
    """Attach `engagement` and `top_comments` to a Reddit candidate item."""
    thread_data = fetch_thread_data(item.get("url", ""), mock_thread_data)
    if not thread_data:
        return item

    parsed = parse_thread_data(thread_data)
    submission = parsed.get("submission")
    if submission:
        item["engagement"] = {
            "score": submission.get("score"),
            "num_comments": submission.get("num_comments"),
            "upvote_ratio": submission.get("upvote_ratio"),
        }

    item["top_comments"] = [
        {"score": c.get("score", 0), "author": c.get("author", ""), "excerpt": c.get("body", "")[:200]}
        for c in get_top_comments(parsed.get("comments", []))
    ]
    return item
