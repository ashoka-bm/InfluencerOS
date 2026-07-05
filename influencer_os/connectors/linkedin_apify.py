"""Public LinkedIn profile-post scraping via the Apify actor.

Adapted from Agentic OS `tool-linkedin-scraper/scripts/scrape.py` (actor
`harvestapi~linkedin-profile-posts`, run-sync-get-dataset-items endpoint).
Stdlib only; `mock_response` allows tests without live calls.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from influencer_os.connectors import http
from influencer_os.connectors.parse import safe_int

APIFY_ACTOR = "harvestapi~linkedin-profile-posts"
APIFY_URL = f"https://api.apify.com/v2/acts/{APIFY_ACTOR}/run-sync-get-dataset-items"


def days_to_posted_limit(days: int) -> str:
    """Convert a lookback window in days to the actor's postedLimit enum."""
    if days <= 1:
        return "24h"
    if days <= 7:
        return "week"
    if days <= 30:
        return "month"
    return "any"


def fetch_profile_posts(
    api_key: str,
    profile_url: str,
    max_posts: int = 5,
    days: int = 30,
    mock_response: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Call the Apify actor for one public profile; returns raw post dicts."""
    if mock_response is not None:
        return mock_response if isinstance(mock_response, list) else []

    payload = {
        "targetUrls": [profile_url],
        "maxPosts": max_posts,
        "postedLimit": days_to_posted_limit(days),
        "includeQuotePosts": False,
        "includeReposts": False,
        "scrapeReactions": False,
        "scrapeComments": False,
    }
    # Pass the token as a Bearer header, not a query param, so it never reaches
    # request logs (Apify accepts Authorization: Bearer <token>).
    headers = {"Authorization": f"Bearer {api_key}"}
    data = http.post(APIFY_URL, payload, headers=headers, timeout=90)
    return data if isinstance(data, list) else []


def parse_post_date(post: Dict[str, Any]) -> Optional[str]:
    """Extract the posted date as YYYY-MM-DD, or None when undetermined."""
    for key in ("postedAt", "date", "publishedAt", "createdAt"):
        raw = post.get(key)
        if not raw:
            continue
        try:
            if isinstance(raw, (int, float)):
                dt = datetime.fromtimestamp(raw / 1000 if raw > 1e10 else raw, tz=timezone.utc)
            else:
                dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except (ValueError, OverflowError, OSError):
            continue
    return None


def parse_posts(posts: List[Any]) -> List[Dict[str, Any]]:
    """Reduce raw actor posts to clean candidate items."""
    clean: List[Dict[str, Any]] = []
    for i, post in enumerate(posts):
        if not isinstance(post, dict):
            continue
        url = post.get("url") or post.get("postUrl") or ""
        if not url:
            continue
        author = post.get("authorName") or (post.get("author") or {}).get("name") or ""
        clean.append(
            {
                "id": f"L{i + 1}",
                "url": url,
                "author": str(author).strip(),
                "date": parse_post_date(post),
                "text": str(post.get("text") or post.get("content") or "").strip()[:500],
                "engagement": {
                    "likes": safe_int(post.get("likesCount") or post.get("reactions")),
                    "comments": safe_int(post.get("commentsCount")),
                    "reposts": safe_int(post.get("repostsCount")),
                },
            }
        )
    return clean
