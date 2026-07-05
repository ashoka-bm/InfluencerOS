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

from influencer_os.connectors import env, models, openai_reddit, reddit_enrich

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
        return _result(topic, from_date, to_date, model=None, candidates=[],
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

    return _result(topic, from_date, to_date, model=model, candidates=result_candidates,
                   budget=budget, enriched=enriched, truncated=truncated, capped=False,
                   notes=notes)


def _result(topic, from_date, to_date, model, candidates, budget, enriched, truncated, capped, notes):
    return {
        "connector": "reddit_openai",
        "adapter_id": "reddit_api_or_search",
        "platform": "reddit",
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
