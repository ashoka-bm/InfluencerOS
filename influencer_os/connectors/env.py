"""Environment and API-key management for research-acquisition connectors.

Adapted from Agentic OS `str-trending-research/scripts/lib/env.py`. Reads keys
from the project `.env` (walking up to the repo root) and from `os.environ`,
with `os.environ` taking precedence. Adds the ADR 0022 guardrails: a per-run
call cap and a global paid-connector kill switch.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_MAX_CALLS = 12


def provider_keys() -> List[str]:
    """The provider env-var names, derived from the connector registry.

    Single source of truth: the registry defines the connectors; this reads the
    keys off it. Imported lazily to avoid a registry<->env import cycle.
    """
    from influencer_os.connectors.registry import CONNECTORS

    return [c["key"] for c in CONNECTORS]


def _find_project_env(start: Optional[Path] = None) -> Path:
    """Find the project `.env` by walking up to the repo root (AGENTS.md marker)."""
    current = (start or Path(__file__).resolve().parent)
    for _ in range(10):
        if (current / ".env").exists():
            return current / ".env"
        if (current / "AGENTS.md").exists() or (current / "CLAUDE.md").exists():
            return current / ".env"
        if current.parent == current:
            break
        current = current.parent
    return Path.cwd() / ".env"


def load_env_file(path: Path) -> Dict[str, str]:
    """Parse a simple KEY=value `.env` file, ignoring comments and blanks."""
    env: Dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if value and value[0] in ("\"", "'") and value[-1] == value[0]:
            value = value[1:-1]
        if key and value:
            env[key] = value
    return env


def get_config(env_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load connector configuration from `.env` plus `os.environ` (environ wins)."""
    file_env = load_env_file(env_path or _find_project_env())

    def resolve(name: str) -> Optional[str]:
        # os.environ takes precedence, including an explicit empty value; only
        # fall back to the file when the var is truly unset.
        value = os.environ.get(name)
        if value is not None:
            return value
        return file_env.get(name)

    config: Dict[str, Any] = {key: resolve(key) for key in provider_keys()}

    def truthy(raw: Optional[str]) -> bool:
        return (raw or "").strip().lower() in ("1", "true", "yes")

    # The kill switch is a last-resort safety guardrail, so it turns ON if EITHER
    # os.environ or the .env file enables it, and a blank environ export is
    # treated as absent. (Unlike an API key, where an explicit empty environ
    # value intentionally wins and fails closed, an empty value here must not
    # silently override a .env `=1` and fail the guardrail open.)
    kill_var = "INFLUENCER_OS_DISABLE_PAID_CONNECTORS"
    config["DISABLE_PAID_CONNECTORS"] = truthy(os.environ.get(kill_var)) or truthy(
        file_env.get(kill_var)
    )

    raw_cap = resolve("INFLUENCER_OS_CONNECTOR_MAX_CALLS")
    try:
        config["MAX_CALLS"] = int(raw_cap) if raw_cap else DEFAULT_MAX_CALLS
    except ValueError:
        config["MAX_CALLS"] = DEFAULT_MAX_CALLS

    config["OPENAI_MODEL_POLICY"] = resolve("OPENAI_MODEL_POLICY") or "auto"
    config["OPENAI_MODEL_PIN"] = resolve("OPENAI_MODEL_PIN")
    config["XAI_MODEL_POLICY"] = resolve("XAI_MODEL_POLICY") or "latest"
    config["XAI_MODEL_PIN"] = resolve("XAI_MODEL_PIN")
    return config


def paid_connectors_disabled(config: Dict[str, Any]) -> bool:
    return bool(config.get("DISABLE_PAID_CONNECTORS"))


def has_key(config: Dict[str, Any], key_name: str) -> bool:
    """A connector is available only when its key is present and the tier is on."""
    if paid_connectors_disabled(config):
        return False
    return bool(config.get(key_name))


class CallBudget:
    """Bounds paid provider calls per research run (ADR 0022 guardrail)."""

    def __init__(self, max_calls: int):
        self.max_calls = max_calls
        self.used = 0

    def remaining(self) -> int:
        return max(0, self.max_calls - self.used)

    def spend(self, n: int = 1) -> bool:
        """Consume budget for a call; returns False (without consuming) if exhausted."""
        if self.used + n > self.max_calls:
            return False
        self.used += n
        return True
