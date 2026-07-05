"""Connector registry: which research-acquisition connectors exist and whether
each is currently available (ADR 0022).

Availability is derived purely from configuration (key presence + kill switch),
so this module is fully offline and safe to call without any network access.
Keeps adapter IDs aligned with docs/research-adapter-registry.md.
"""

from typing import Any, Dict, List

from influencer_os.connectors import env

# Ordered connector definitions. `platform` is the research-run platform each
# connector produces evidence for; `firecrawl_web` is platform-agnostic.
CONNECTORS: List[Dict[str, Any]] = [
    {
        "connector": "reddit_openai",
        "adapter_id": "reddit_api_or_search",
        "key": "OPENAI_API_KEY",
        "provider": "openai",
        "access_method": "api_backed",
        "platform": "reddit",
        "summary": "Reddit threads via OpenAI Responses web_search, enriched with real engagement.",
    },
    {
        "connector": "x_xai",
        "adapter_id": "x_api",
        "key": "XAI_API_KEY",
        "provider": "xai",
        "access_method": "api_backed",
        "platform": "x",
        "summary": "X posts with engagement via the xAI x_search tool.",
    },
    {
        "connector": "firecrawl_web",
        "adapter_id": "firecrawl_public_web",
        "key": "FIRECRAWL_API_KEY",
        "provider": "firecrawl",
        "access_method": "scraping_api",
        "platform": None,
        "summary": "Rendered public web/JS pages (incl. Reddit) via Firecrawl.",
    },
    {
        "connector": "linkedin_apify",
        "adapter_id": "linkedin_apify",
        "key": "APIFY_API_KEY",
        "provider": "apify",
        "access_method": "api_backed",
        "platform": "linkedin",
        "summary": "Public LinkedIn profile/post scraping via an Apify actor.",
    },
]


def connector_status(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return each connector annotated with availability and the reason."""
    disabled = env.paid_connectors_disabled(config)
    rows: List[Dict[str, Any]] = []
    for c in CONNECTORS:
        has_key = bool(config.get(c["key"]))
        if disabled:
            available, reason = False, "paid connectors disabled by kill switch"
        elif has_key:
            available, reason = True, f"{c['key']} present"
        else:
            available, reason = False, f"{c['key']} not set"
        rows.append({**c, "available": available, "reason": reason})
    return rows


def list_connectors(config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    return connector_status(config if config is not None else env.get_config())
