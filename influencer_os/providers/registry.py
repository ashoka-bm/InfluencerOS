"""Generation provider registry (ADR 0023, Phase 3 slice 1).

Availability is derived purely from configuration (key presence + kill
switch), so this module is fully offline. Unlike the research-connector
registry, no row here can express standing approval: `approval_model` is the
constant ``exact_approval`` and the module fails closed at import when a row
disagrees. Key presence makes a provider *available*, never *approved* — the
approval lives in a per-call GenerationApprovalRecord (slice 2).

Per ADR 0023 Decision 3, the only registered adapter is the deterministic
``mock`` test double. The first real (paid) provider adapter is chosen
explicitly by the operator and lands as its own approved batch.
"""

from typing import Any, Dict, List

from influencer_os.connectors import env

EXACT_APPROVAL = "exact_approval"

GENERATION_CAPABILITIES = ("image", "video", "audio", "render")

# Ordered provider definitions. `key` is the env var that makes the provider
# available (None = no key needed). `approval_model` must be EXACT_APPROVAL
# on every row; _validate_registry() enforces it structurally.
PROVIDERS: List[Dict[str, Any]] = [
    {
        "provider_id": "mock",
        "capabilities": ["image", "video", "audio", "render"],
        "key": None,
        "cost_notes": "Free deterministic test double; writes fixture bytes.",
        "approval_model": EXACT_APPROVAL,
        "summary": "Deterministic mock adapter for tests and dry runs (ADR 0023 Decision 3).",
    },
]


def _validate_registry() -> None:
    """Fail closed at import if any row could weaken the generation gate."""
    seen = set()
    for row in PROVIDERS:
        provider_id = row.get("provider_id")
        if not provider_id or provider_id in seen:
            raise ValueError(f"provider registry has a missing/duplicate id: {provider_id!r}")
        seen.add(provider_id)
        if row.get("approval_model") != EXACT_APPROVAL:
            raise ValueError(
                f"generation provider {provider_id!r} declares approval_model "
                f"{row.get('approval_model')!r}; generation providers are "
                f"structurally {EXACT_APPROVAL!r} (ADR 0023)"
            )
        unknown = set(row.get("capabilities", [])) - set(GENERATION_CAPABILITIES)
        if unknown:
            raise ValueError(
                f"generation provider {provider_id!r} declares unknown "
                f"capabilities {sorted(unknown)!r}"
            )


_validate_registry()


def provider_status(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Each provider annotated with availability and the reason.

    Availability means "may be named in an approval request" — it never
    implies approval. The paid-connector kill switch disables every
    generation provider, mock included, so a hard stop is total.
    """
    disabled = env.paid_connectors_disabled(config)
    rows: List[Dict[str, Any]] = []
    for row in PROVIDERS:
        key = row["key"]
        has_key = key is None or bool(config.get(key))
        if disabled:
            available, reason = False, "generation disabled by kill switch"
        elif has_key:
            available, reason = True, "no key required" if key is None else f"{key} present"
        else:
            available, reason = False, f"{key} not set"
        rows.append({**row, "available": available, "reason": reason})
    return rows


def list_providers(config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    return provider_status(config if config is not None else env.get_config())


def get_provider(provider_id: str) -> Dict[str, Any]:
    for row in PROVIDERS:
        if row["provider_id"] == provider_id:
            return row
    raise KeyError(f"unknown generation provider: {provider_id!r}")
