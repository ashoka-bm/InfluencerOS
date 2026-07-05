"""Fetch orchestration for research-acquisition connectors (ADR 0022).

Mirrors the Agentic OS `last30days.py` flow (discover -> enrich) but returns a
structured fetch result instead of rendering a markdown brief: the
create-research-findings skill curates candidates into ResearchEvidence and
MetricSnapshot records. Every paid call is bounded by the per-run CallBudget.
All provider entry points accept mock hooks so the pipeline is tested offline.
"""

from typing import Any, Dict, List, Optional

from influencer_os.connectors import env, models, openai_reddit, reddit_enrich


class ConnectorUnavailable(Exception):
    """Raised when a connector is requested without its key or with the tier off."""


def fetch_reddit(
    topic: str,
    config: Dict[str, Any],
    budget: env.CallBudget,
    depth: str = "default",
    enrich: bool = True,
    mock_search_response: Optional[Dict] = None,
    mock_model: Optional[str] = None,
    mock_thread_data: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Discover Reddit threads for a topic and enrich them with engagement.

    Returns a fetch result: {connector, adapter_id, platform, topic, candidates,
    calls_used, capped, status, notes}. Never raises on empty results; raises
    ConnectorUnavailable only when the connector cannot run at all.
    """
    if not env.has_key(config, "OPENAI_API_KEY"):
        raise ConnectorUnavailable(
            "reddit_openai requires OPENAI_API_KEY and the paid tier enabled"
        )

    notes: List[str] = []

    if not budget.spend():
        return _empty_result("reddit_openai", "reddit_api_or_search", "reddit", topic, budget,
                             capped=True, notes=["call cap reached before search"])

    model = mock_model or models.get_models(config, mock_openai_models=None).get("openai") \
        or openai_reddit.MODEL_FALLBACK_ORDER[0]

    raw = openai_reddit.search_reddit(
        config["OPENAI_API_KEY"], model, topic, depth=depth, mock_response=mock_search_response
    )
    candidates = openai_reddit.parse_reddit_response(raw)

    enriched: List[Dict[str, Any]] = []
    capped = False
    for item in candidates:
        if enrich and mock_thread_data is None:
            if not budget.spend():
                capped = True
                notes.append("call cap reached during enrichment; remaining threads left unenriched")
                enriched.append(item)
                continue
        if enrich:
            item = reddit_enrich.enrich_reddit_item(item, mock_thread_data=mock_thread_data)
        enriched.append(item)

    return {
        "connector": "reddit_openai",
        "adapter_id": "reddit_api_or_search",
        "platform": "reddit",
        "topic": topic,
        "model": model,
        "candidates": enriched,
        "calls_used": budget.used,
        "capped": capped,
        "status": "ok" if enriched else "no_results",
        "notes": notes,
    }


def _empty_result(connector, adapter_id, platform, topic, budget, capped=False, notes=None):
    return {
        "connector": connector,
        "adapter_id": adapter_id,
        "platform": platform,
        "topic": topic,
        "candidates": [],
        "calls_used": budget.used,
        "capped": capped,
        "status": "no_results",
        "notes": notes or [],
    }
