"""Research-acquisition connectors (ADR 0022).

An env-gated connector layer that mirrors the proven Agentic OS
`str-trending-research` acquisition path (itself adapted from the open-source
`Ronnie-Nutrition/last30days-skill`). Stdlib only; no third-party SDKs.

Each connector is available only when its API key is present in the environment
or `.env`; otherwise the run falls back to built-in public WebSearch/WebFetch.
Key presence is standing approval for research-acquisition calls (ADR 0022),
bounded by a per-run call cap and a global kill switch. Connectors return raw
candidates with real engagement where available; the create-research-findings
skill curates selected candidates into ResearchEvidence and MetricSnapshot
records. Connectors never write canonical records directly.
"""

from influencer_os.connectors.registry import (
    CONNECTORS,
    connector_status,
    list_connectors,
)

__all__ = ["CONNECTORS", "connector_status", "list_connectors"]
