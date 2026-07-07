"""YouTube Data API v3 research acquisition connector (ADR 0027).

This module fetches public video/channel metadata for research runs. It does
not fetch transcripts, use OAuth, call YouTube Analytics, publish, or schedule.
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from influencer_os.connectors import http

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


def _get(path: str, params: Dict[str, Any], timeout: int = 20) -> Dict[str, Any]:
    clean_params = {k: v for k, v in params.items() if v is not None and v != ""}
    url = f"{YOUTUBE_API_BASE}/{path}?{urlencode(clean_params)}"
    return http.get(url, timeout=timeout)


def rfc3339_start(date_text: str) -> str:
    return f"{date_text}T00:00:00Z"


def rfc3339_end_exclusive(date_text: str) -> str:
    """Inclusive research to_date -> exclusive next-midnight API boundary.

    publishedBefore is a date-time cut-off, so the boundary must be the NEXT
    day's midnight or the window silently drops the to_date's videos.
    """
    next_day = date.fromisoformat(date_text) + timedelta(days=1)
    return f"{next_day.isoformat()}T00:00:00Z"


def is_channel_id(value: str) -> bool:
    return value.startswith("UC") and len(value) == 24


def search_videos(
    api_key: str,
    query: str,
    from_date: str,
    to_date: str,
    max_results: int = 10,
    order: str = "date",
    region_code: Optional[str] = None,
    relevance_language: Optional[str] = None,
    mock_response: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if mock_response is not None:
        return mock_response
    return _get("search", {
        "part": "snippet",
        "q": query,
        "type": "video",
        "order": order,
        "publishedAfter": rfc3339_start(from_date),
        "publishedBefore": rfc3339_end_exclusive(to_date),
        "maxResults": min(max_results, 50),
        "regionCode": region_code,
        "relevanceLanguage": relevance_language,
        "safeSearch": "moderate",
        "key": api_key,
    })


def fetch_video_details(
    api_key: str,
    video_ids: List[str],
    mock_response: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if mock_response is not None:
        return mock_response
    if not video_ids:
        return {"items": []}
    return _get("videos", {
        "part": "snippet,contentDetails,statistics",
        "id": ",".join(video_ids[:50]),
        "key": api_key,
    })


def resolve_channel(api_key: str, handle_or_id: str, mock_response: Optional[Dict[str, Any]] = None) -> Optional[str]:
    if is_channel_id(handle_or_id):
        return handle_or_id
    if mock_response is None:
        response = _get("channels", {
            "part": "id,contentDetails",
            "forHandle": handle_or_id.lstrip("@"),
            "key": api_key,
        })
    else:
        response = mock_response
    items = response.get("items", [])
    if items:
        return items[0].get("id")
    return None


def fetch_channel_uploads(
    api_key: str,
    channel_id: str,
    max_results: int = 10,
    mock_channel_response: Optional[Dict[str, Any]] = None,
    mock_playlist_response: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    channel_response = mock_channel_response or _get("channels", {
        "part": "contentDetails",
        "id": channel_id,
        "key": api_key,
    })
    items = channel_response.get("items", [])
    if not items:
        return {"items": []}
    uploads = items[0].get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
    if not uploads:
        return {"items": []}
    return mock_playlist_response or _get("playlistItems", {
        "part": "snippet",
        "playlistId": uploads,
        "maxResults": min(max_results, 50),
        "key": api_key,
    })


def search_items_from_playlist(response: Dict[str, Any]) -> Dict[str, Any]:
    """Adapt playlistItems.list uploads into search.list-shaped items so the
    channel path can reuse video_ids_from_search/parse_video_candidates."""
    items = []
    for item in response.get("items", []):
        snippet = item.get("snippet", {})
        video_id = snippet.get("resourceId", {}).get("videoId")
        if video_id:
            items.append({"id": {"videoId": video_id}, "snippet": snippet})
    return {"items": items}


def video_ids_from_search(response: Dict[str, Any]) -> List[str]:
    ids: List[str] = []
    for item in response.get("items", []):
        video_id = item.get("id", {}).get("videoId")
        if video_id:
            ids.append(video_id)
    return ids


def _safe_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _date_from_rfc3339(value: str) -> Optional[str]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return None


def _duration_seconds(duration: str) -> Optional[int]:
    if not duration or not duration.startswith("PT"):
        return None
    total = 0
    number = ""
    for char in duration[2:]:
        if char.isdigit():
            number += char
            continue
        if not number:
            continue
        value = int(number)
        number = ""
        if char == "H":
            total += value * 3600
        elif char == "M":
            total += value * 60
        elif char == "S":
            total += value
    return total


def parse_video_candidates(search_response: Dict[str, Any], details_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    details_by_id = {item.get("id"): item for item in details_response.get("items", [])}
    candidates: List[Dict[str, Any]] = []
    for item in search_response.get("items", []):
        video_id = item.get("id", {}).get("videoId")
        if not video_id:
            continue
        snippet = item.get("snippet", {})
        details = details_by_id.get(video_id, {})
        detail_snippet = details.get("snippet", {})
        stats = details.get("statistics", {})
        duration = details.get("contentDetails", {}).get("duration", "")
        seconds = _duration_seconds(duration)
        thumbnail = snippet.get("thumbnails", {}).get("medium", {}).get("url", "")
        candidate = {
            "id": f"YT{len(candidates) + 1}",
            "video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "title": str(snippet.get("title", "")).strip(),
            "description": str(snippet.get("description", "")).strip()[:500],
            "channel_title": str(snippet.get("channelTitle", "")).strip(),
            "channel_id": str(snippet.get("channelId", "")).strip(),
            "channel_url": f"https://www.youtube.com/channel/{snippet.get('channelId', '')}",
            "date": _date_from_rfc3339(snippet.get("publishedAt", "")),
            "duration": duration,
            "duration_seconds": seconds,
            "is_short_candidate": seconds is not None and seconds <= 180,
            "tags": detail_snippet.get("tags", []),
            "category_id": detail_snippet.get("categoryId", ""),
            "engagement": {
                "views": _safe_int(stats.get("viewCount")),
                "likes": _safe_int(stats.get("likeCount")),
                "comments": _safe_int(stats.get("commentCount")),
            },
        }
        if thumbnail:
            candidate["thumbnail_url"] = thumbnail
        candidates.append(candidate)
    return candidates
