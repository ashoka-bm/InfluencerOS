"""Model auto-selection for OpenAI and xAI connectors.

Adapted from Agentic OS `str-trending-research/scripts/lib/models.py`. Picks the
latest mainline model when possible and falls back to a pinned default, so the
connector keeps working as providers ship new models. Stdlib only.
"""

import re
from typing import Dict, List, Optional, Tuple

from influencer_os.connectors import http

OPENAI_MODELS_URL = "https://api.openai.com/v1/models"
OPENAI_FALLBACK_MODELS = ["gpt-5.2", "gpt-5.1", "gpt-5", "gpt-4o"]

XAI_ALIASES = {"latest": "grok-4-1-fast", "stable": "grok-4-1-fast"}

# In-process cache of the resolved model per provider. A single research run
# resolves many topics in one process; without this each fetch would re-hit
# /v1/models for the same answer. Cleared only by process exit.
_MODEL_CACHE: Dict[str, str] = {}


def clear_model_cache() -> None:
    _MODEL_CACHE.clear()


def parse_version(model_id: str) -> Optional[Tuple[int, ...]]:
    match = re.search(r"(\d+(?:\.\d+)*)", model_id)
    if match:
        return tuple(int(x) for x in match.group(1).split("."))
    return None


def is_mainline_openai_model(model_id: str) -> bool:
    model_lower = model_id.lower()
    if not re.match(r"^gpt-5(\.\d+)*$", model_lower):
        return False
    return not any(exc in model_lower for exc in ("mini", "nano", "chat", "codex", "pro", "preview", "turbo"))


def select_openai_model(
    api_key: str,
    policy: str = "auto",
    pin: Optional[str] = None,
    mock_models: Optional[List[Dict]] = None,
) -> str:
    if policy == "pinned" and pin:
        return pin
    if mock_models is None and "openai" in _MODEL_CACHE:
        return _MODEL_CACHE["openai"]
    if mock_models is not None:
        models = mock_models
    else:
        try:
            response = http.get(OPENAI_MODELS_URL, headers={"Authorization": f"Bearer {api_key}"})
            models = response.get("data", [])
        except http.HTTPError:
            return OPENAI_FALLBACK_MODELS[0]

    candidates = [m for m in models if is_mainline_openai_model(m.get("id", ""))]
    if not candidates:
        return OPENAI_FALLBACK_MODELS[0]
    candidates.sort(key=lambda m: (parse_version(m.get("id", "")) or (0,), m.get("created", 0)), reverse=True)
    selected = candidates[0]["id"]
    _MODEL_CACHE["openai"] = selected
    return selected


def select_xai_model(api_key: str, policy: str = "latest", pin: Optional[str] = None) -> str:
    if policy == "pinned" and pin:
        return pin
    return XAI_ALIASES.get(policy, XAI_ALIASES["latest"])


def get_models(
    config: Dict,
    mock_openai_models: Optional[List[Dict]] = None,
) -> Dict[str, Optional[str]]:
    result: Dict[str, Optional[str]] = {"openai": None, "xai": None}
    if config.get("OPENAI_API_KEY"):
        result["openai"] = select_openai_model(
            config["OPENAI_API_KEY"],
            config.get("OPENAI_MODEL_POLICY", "auto"),
            config.get("OPENAI_MODEL_PIN"),
            mock_openai_models,
        )
    if config.get("XAI_API_KEY"):
        result["xai"] = select_xai_model(
            config["XAI_API_KEY"],
            config.get("XAI_MODEL_POLICY", "latest"),
            config.get("XAI_MODEL_PIN"),
        )
    return result
