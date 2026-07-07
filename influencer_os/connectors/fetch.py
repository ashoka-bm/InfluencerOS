"""Fetch orchestration for research-acquisition connectors (ADR 0022).

Mirrors the Agentic OS `last30days.py` flow (discover -> enrich) but returns a
structured fetch result (see schemas/research-fetch-result.schema.json) instead
of rendering a markdown brief: the create-research-findings skill curates
candidates into ResearchEvidence and MetricSnapshot records.

Budget model: only PAID provider calls (the OpenAI discovery search) draw on the
per-run CallBudget. Reddit thread enrichment is a free public reddit.com read,
so it does not consume the paid budget; it is bounded separately by max_enrich
to cap wall-clock. All provider entry points accept mock hooks for offline tests.
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from influencer_os.connectors import (
    env,
    firecrawl_web,
    linkedin_apify,
    models,
    openai_reddit,
    reddit_enrich,
    xai_x,
    youtube_data,
)

DEFAULT_RECENCY_DAYS = 30
DEFAULT_MAX_ENRICH = 25


class ConnectorUnavailable(Exception):
    """Raised when a connector is requested without its key or with the tier off."""


def _recency_window(from_date: Optional[str], to_date: Optional[str], days: int) -> tuple:
    """Resolve an explicit YYYY-MM-DD window, defaulting to the last `days`."""
    if from_date and to_date:
        return from_date, to_date
    today = date.today()
    return (today - timedelta(days=days)).isoformat(), today.isoformat()


def _passes_recency(item_date: Optional[str], from_date: str) -> bool:
    """Keep items whose date is unknown or within the window (YYYY-MM-DD sorts lexically)."""
    if not item_date:
        return True
    return item_date >= from_date


def fetch_reddit(
    topic: str,
    config: Dict[str, Any],
    budget: env.CallBudget,
    depth: str = "default",
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    days: int = DEFAULT_RECENCY_DAYS,
    enrich: bool = True,
    max_enrich: int = DEFAULT_MAX_ENRICH,
    mock_search_response: Optional[Dict] = None,
    mock_model: Optional[str] = None,
    mock_thread_data: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Discover recent Reddit threads for a topic and enrich them with engagement.

    Raises ConnectorUnavailable only when the connector cannot run at all; never
    raises on empty or partial results.
    """
    if not env.has_key(config, "OPENAI_API_KEY"):
        raise ConnectorUnavailable(
            "reddit_openai requires OPENAI_API_KEY and the paid tier enabled"
        )

    from_date, to_date = _recency_window(from_date, to_date, days)
    notes: List[str] = []

    # Paid discovery call draws on the budget.
    if not budget.spend():
        return _result("reddit_openai", "reddit_api_or_search", "reddit",
                       topic, from_date, to_date, model=None, candidates=[],
                       budget=budget, enriched=0, truncated=False, capped=True,
                       notes=["paid call cap reached before search"])

    model = mock_model or models.get_models(config).get("openai") or openai_reddit.MODEL_FALLBACK_ORDER[0]

    raw = openai_reddit.search_reddit(
        config["OPENAI_API_KEY"], model, topic, from_date, to_date,
        depth=depth, mock_response=mock_search_response,
    )
    candidates = openai_reddit.parse_reddit_response(raw)

    # Drop candidates with a known date older than the window; keep unknown dates.
    kept = [c for c in candidates if _passes_recency(c.get("date"), from_date)]
    dropped = len(candidates) - len(kept)
    if dropped:
        notes.append(f"dropped {dropped} candidate(s) older than {from_date}")

    # Enrichment is a free public reddit.com read, bounded by max_enrich.
    truncated = enrich and len(kept) > max_enrich
    head = kept[:max_enrich] if truncated else kept
    tail = kept[max_enrich:] if truncated else []
    if truncated:
        notes.append(f"enrichment limited to {max_enrich} of {len(kept)} candidates")

    result_candidates: List[Dict[str, Any]] = []
    enriched = 0
    for item in head:
        if enrich:
            item = reddit_enrich.enrich_reddit_item(item, mock_thread_data=mock_thread_data)
            enriched += 1
        result_candidates.append(item)
    result_candidates.extend(tail)

    return _result("reddit_openai", "reddit_api_or_search", "reddit",
                   topic, from_date, to_date, model=model, candidates=result_candidates,
                   budget=budget, enriched=enriched, truncated=truncated, capped=False,
                   notes=notes)


def fetch_x(
    topic: str,
    config: Dict[str, Any],
    budget: env.CallBudget,
    depth: str = "default",
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    days: int = DEFAULT_RECENCY_DAYS,
    mock_search_response: Optional[Dict] = None,
    mock_model: Optional[str] = None,
) -> Dict[str, Any]:
    """Discover recent X posts (engagement inline) for a topic via xAI x_search."""
    if not env.has_key(config, "XAI_API_KEY"):
        raise ConnectorUnavailable("x_xai requires XAI_API_KEY and the paid tier enabled")

    from_date, to_date = _recency_window(from_date, to_date, days)
    notes: List[str] = []

    if not budget.spend():
        return _result("x_xai", "x_api", "x", topic, from_date, to_date, model=None,
                       candidates=[], budget=budget, enriched=0, truncated=False,
                       capped=True, notes=["paid call cap reached before search"])

    model = mock_model or models.get_models(config).get("xai") or models.XAI_ALIASES["latest"]
    raw = xai_x.search_x(
        config["XAI_API_KEY"], model, topic, from_date, to_date,
        depth=depth, mock_response=mock_search_response,
    )
    candidates = xai_x.parse_x_response(raw)

    kept = [c for c in candidates if _passes_recency(c.get("date"), from_date)]
    dropped = len(candidates) - len(kept)
    if dropped:
        notes.append(f"dropped {dropped} candidate(s) older than {from_date}")

    # xAI returns engagement inline, so every kept candidate counts as enriched.
    return _result("x_xai", "x_api", "x", topic, from_date, to_date, model=model,
                   candidates=kept, budget=budget, enriched=len(kept),
                   truncated=False, capped=False, notes=notes)


def fetch_firecrawl(
    url: str,
    config: Dict[str, Any],
    budget: env.CallBudget,
    mock_response: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Render one public web/JS page to markdown via Firecrawl."""
    if not env.has_key(config, "FIRECRAWL_API_KEY"):
        raise ConnectorUnavailable("firecrawl_web requires FIRECRAWL_API_KEY and the paid tier enabled")

    from_date, to_date = _recency_window(None, None, DEFAULT_RECENCY_DAYS)
    if not budget.spend():
        return _result("firecrawl_web", "firecrawl_public_web", "web", url,
                       from_date, to_date, model=None, candidates=[], budget=budget,
                       enriched=0, truncated=False, capped=True,
                       notes=["paid call cap reached before scrape"])

    raw = firecrawl_web.scrape(config["FIRECRAWL_API_KEY"], url, mock_response=mock_response)
    candidate = firecrawl_web.parse_scrape_response(raw, url)
    candidates = [candidate] if candidate else []
    notes = [] if candidate else ["scrape returned no usable content"]
    return _result("firecrawl_web", "firecrawl_public_web", "web", url,
                   from_date, to_date, model=None, candidates=candidates, budget=budget,
                   enriched=0, truncated=False, capped=False, notes=notes)


def fetch_linkedin(
    profile_url: str,
    config: Dict[str, Any],
    budget: env.CallBudget,
    max_posts: int = 5,
    days: int = DEFAULT_RECENCY_DAYS,
    mock_response: Optional[Any] = None,
) -> Dict[str, Any]:
    """Fetch recent public posts for one LinkedIn profile via the Apify actor."""
    if not env.has_key(config, "APIFY_API_KEY"):
        raise ConnectorUnavailable("linkedin_apify requires APIFY_API_KEY and the paid tier enabled")

    from_date, to_date = _recency_window(None, None, days)
    if not budget.spend():
        return _result("linkedin_apify", "linkedin_apify", "linkedin", profile_url,
                       from_date, to_date, model=None, candidates=[], budget=budget,
                       enriched=0, truncated=False, capped=True,
                       notes=["paid call cap reached before scrape"])

    raw = linkedin_apify.fetch_profile_posts(
        config["APIFY_API_KEY"], profile_url, max_posts=max_posts, days=days,
        mock_response=mock_response,
    )
    candidates = linkedin_apify.parse_posts(raw)
    kept = [c for c in candidates if _passes_recency(c.get("date"), from_date)]
    notes = []
    if len(candidates) - len(kept):
        notes.append(f"dropped {len(candidates) - len(kept)} candidate(s) older than {from_date}")
    # The actor returns engagement inline with each post.
    return _result("linkedin_apify", "linkedin_apify", "linkedin", profile_url,
                   from_date, to_date, model=None, candidates=kept, budget=budget,
                   enriched=len(kept), truncated=False, capped=False, notes=notes)


def fetch_youtube_search(
    topic: str,
    config: Dict[str, Any],
    budget: env.CallBudget,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    days: int = DEFAULT_RECENCY_DAYS,
    max_results: int = 10,
    order: str = "date",
    mock_search_response: Optional[Dict] = None,
    mock_details_response: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Discover public YouTube videos for a creator-relevant topic.

    Two quota-drawing calls: search.list for discovery, then one videos.list
    batch for duration/statistics. Engagement arrives with the details call,
    so every parsed candidate counts as enriched.
    """
    if not env.has_key(config, "YOUTUBE_API_KEY"):
        raise ConnectorUnavailable(
            "youtube_data_api requires YOUTUBE_API_KEY and the paid tier enabled"
        )

    from_date, to_date = _recency_window(from_date, to_date, days)
    if not budget.spend():
        return _result("youtube_data_api", "youtube_data_api", "youtube",
                       topic, from_date, to_date, model=None, candidates=[],
                       budget=budget, enriched=0, truncated=False, capped=True,
                       notes=["paid call cap reached before YouTube search"])

    raw_search = youtube_data.search_videos(
        config["YOUTUBE_API_KEY"], topic, from_date, to_date,
        max_results=max_results, order=order, mock_response=mock_search_response,
    )
    video_ids = youtube_data.video_ids_from_search(raw_search)
    if video_ids and not budget.spend():
        return _result("youtube_data_api", "youtube_data_api", "youtube",
                       topic, from_date, to_date, model=None, candidates=[],
                       budget=budget, enriched=0, truncated=False, capped=True,
                       notes=["paid call cap reached before YouTube video details"])

    raw_details = youtube_data.fetch_video_details(
        config["YOUTUBE_API_KEY"], video_ids, mock_response=mock_details_response
    )
    candidates = youtube_data.parse_video_candidates(raw_search, raw_details)
    return _result("youtube_data_api", "youtube_data_api", "youtube",
                   topic, from_date, to_date, model=None, candidates=candidates,
                   budget=budget, enriched=len(candidates), truncated=False,
                   capped=False, notes=[])


def fetch_youtube_channel(
    channel: str,
    config: Dict[str, Any],
    budget: env.CallBudget,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    days: int = DEFAULT_RECENCY_DAYS,
    max_results: int = 10,
    mock_resolve_response: Optional[Dict] = None,
    mock_channel_response: Optional[Dict] = None,
    mock_playlist_response: Optional[Dict] = None,
    mock_details_response: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Fetch a reference channel's latest uploads within the recency window.

    `channel` is a UC… channel id or an @handle. Quota-drawing calls: one
    channels.list resolution for handles, then channels.list + playlistItems
    for the uploads playlist, then one videos.list batch for statistics.
    """
    if not env.has_key(config, "YOUTUBE_API_KEY"):
        raise ConnectorUnavailable(
            "youtube_data_api requires YOUTUBE_API_KEY and the paid tier enabled"
        )

    from_date, to_date = _recency_window(from_date, to_date, days)
    api_key = config["YOUTUBE_API_KEY"]
    notes: List[str] = []

    def capped(note):
        return _result("youtube_data_api", "youtube_data_api", "youtube",
                       channel, from_date, to_date, model=None, candidates=[],
                       budget=budget, enriched=0, truncated=False, capped=True,
                       notes=[note])

    channel_id = channel if youtube_data.is_channel_id(channel) else None
    if channel_id is None:
        if not budget.spend():
            return capped("paid call cap reached before YouTube channel resolution")
        channel_id = youtube_data.resolve_channel(
            api_key, channel, mock_response=mock_resolve_response
        )
        if not channel_id:
            return _result("youtube_data_api", "youtube_data_api", "youtube",
                           channel, from_date, to_date, model=None, candidates=[],
                           budget=budget, enriched=0, truncated=False, capped=False,
                           notes=[f"channel not found for {channel!r}"])

    # channels.list (uploads playlist) + playlistItems.list.
    if not budget.spend(2):
        return capped("paid call cap reached before YouTube channel uploads fetch")
    raw_playlist = youtube_data.fetch_channel_uploads(
        api_key, channel_id, max_results=max_results,
        mock_channel_response=mock_channel_response,
        mock_playlist_response=mock_playlist_response,
    )
    search_shaped = youtube_data.search_items_from_playlist(raw_playlist)
    video_ids = youtube_data.video_ids_from_search(search_shaped)
    if video_ids and not budget.spend():
        return capped("paid call cap reached before YouTube video details")

    raw_details = youtube_data.fetch_video_details(
        api_key, video_ids, mock_response=mock_details_response
    )
    candidates = youtube_data.parse_video_candidates(search_shaped, raw_details)
    kept = [c for c in candidates if _passes_recency(c.get("date"), from_date)]
    if len(candidates) - len(kept):
        notes.append(f"dropped {len(candidates) - len(kept)} candidate(s) older than {from_date}")
    return _result("youtube_data_api", "youtube_data_api", "youtube",
                   channel, from_date, to_date, model=None, candidates=kept,
                   budget=budget, enriched=len(kept), truncated=False,
                   capped=False, notes=notes)


def _result(connector, adapter_id, platform, topic, from_date, to_date,
            model, candidates, budget, enriched, truncated, capped, notes):
    return {
        "connector": connector,
        "adapter_id": adapter_id,
        "platform": platform,
        "topic": topic,
        "from_date": from_date,
        "to_date": to_date,
        "model": model or "",
        "candidates": candidates,
        "enriched_count": enriched,
        "calls_used": budget.used,
        "truncated": truncated,
        "capped": capped,
        "status": "ok" if candidates else "no_results",
        "notes": notes,
    }
