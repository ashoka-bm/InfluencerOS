"""Concurrent research-fetch fan-out from a search plan (ADR 0042).

The search plan is the deterministic authorization boundary: a fetch job
is derived only from a planned query or planned source whose required
adapter the plan itself marked ``use_now`` in ``adapters_considered``.
Everything else is reported as skipped with its reason — browser-path
platforms, unapproved adapters, and unroutable sources are the session's
(or a future adapter's) work, not this fan-out's.

All jobs share one thread-safe per-run call budget (the ADR 0022 cap), and
each result is validated and written under ``<run-dir>/fetch-results/`` so
results land on disk while the session continues.
"""

import re
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from influencer_os.connectors import env as connector_env
from influencer_os.connectors import fetch as connector_fetch
from influencer_os.connectors import http as connector_http
from influencer_os.json_io import write_json_atomic
from influencer_os.validation import validate_record

# platform of a planned query -> (fetch mode, adapter the plan must approve)
QUERY_ROUTES = {
    "reddit": ("reddit", "reddit_api_or_search"),
    "x": ("x", "x_api"),
    "youtube": ("youtube-search", "youtube_data_api"),
}

FETCH_DEFAULTS = {
    "depth": "default",
    "from_date": None,
    "to_date": None,
    "days": 30,
    "max_posts": 5,
    "max_results": 10,
    "order": "date",
}

_YOUTUBE_CHANNEL_PATTERN = re.compile(
    r"youtube\.com/(?:channel/(?P<id>[A-Za-z0-9_-]+)|(?P<handle>@[A-Za-z0-9._-]+))"
)


class LockedCallBudget(connector_env.CallBudget):
    """CallBudget with an atomic spend, shared across fan-out threads."""

    def __init__(self, max_calls):
        super().__init__(max_calls)
        self._lock = threading.Lock()

    def spend(self, n=1):
        with self._lock:
            return super().spend(n)


def locked_budget_from(budget):
    locked = LockedCallBudget(budget.max_calls)
    locked.used = budget.used
    return locked


def _use_now_adapters(plan):
    return {
        adapter["adapter_id"]
        for adapter in plan.get("adapters_considered", [])
        if adapter.get("decision") == "use_now"
    }


def _route_source(source):
    url = source.get("url", "")
    channel_match = _YOUTUBE_CHANNEL_PATTERN.search(url)
    if channel_match:
        target = channel_match.group("id") or channel_match.group("handle")
        return "youtube-channel", "youtube_data_api", target
    if "linkedin.com" in url:
        return "linkedin", "linkedin_apify", url
    if url.startswith("http"):
        return "firecrawl", "firecrawl_public_web", url
    return None, None, None


def plan_fetch_jobs(plan):
    """Derive (jobs, skipped) from a validated search plan. Jobs carry the
    connector mode and target; skips carry the reason they stay manual."""
    use_now = _use_now_adapters(plan)
    jobs = []
    skipped = []

    for query in plan.get("planned_queries", []):
        route = QUERY_ROUTES.get(query["platform"])
        if route is None:
            skipped.append({
                "kind": "planned_query",
                "id": query["query_id"],
                "reason": (
                    f"platform {query['platform']!r} has no research "
                    "connector; it stays on the session's browser/built-in path"
                ),
            })
            continue
        mode, required_adapter = route
        if required_adapter not in use_now:
            skipped.append({
                "kind": "planned_query",
                "id": query["query_id"],
                "reason": (
                    f"plan does not mark adapter {required_adapter!r} use_now"
                ),
            })
            continue
        jobs.append({
            "kind": "planned_query",
            "id": query["query_id"],
            "mode": mode,
            "target": query["query"],
        })

    for source in plan.get("planned_sources", []):
        mode, required_adapter, target = _route_source(source)
        if mode is None:
            skipped.append({
                "kind": "planned_source",
                "id": source["source_plan_id"],
                "reason": "source has no connector-routable URL",
            })
            continue
        if required_adapter not in use_now:
            skipped.append({
                "kind": "planned_source",
                "id": source["source_plan_id"],
                "reason": (
                    f"plan does not mark adapter {required_adapter!r} use_now"
                ),
            })
            continue
        jobs.append({
            "kind": "planned_source",
            "id": source["source_plan_id"],
            "mode": mode,
            "target": target,
        })

    return jobs, skipped


def _run_job(job, config, budget, options):
    try:
        result = connector_fetch.fetch_for_mode(
            job["mode"], job["target"], config, budget, **options
        )
    except connector_fetch.ConnectorUnavailable as exc:
        return {"job": job, "status": "unavailable", "error": str(exc)}
    except connector_http.HTTPError as exc:
        return {"job": job, "status": "provider_error", "error": str(exc)}
    return {"job": job, "status": "fetched", "result": result}


def fetch_for_plan(plan, run_dir, config, budget, max_workers=4, **options):
    """Run every connector-routable planned fetch concurrently. Returns the
    per-job outcomes, the plan-level skips, and the shared budget for the
    caller to persist. Individual job failures degrade to recorded
    outcomes, never a crash of the fan-out."""
    validate_record("research-search-plan", plan)
    run_dir = Path(run_dir)
    if not run_dir.is_dir():
        raise FileNotFoundError(f"Missing research run directory: {run_dir}")
    fetch_options = {**FETCH_DEFAULTS, **options}
    jobs, skipped = plan_fetch_jobs(plan)

    outcomes = []
    if jobs:
        results_dir = run_dir / "fetch-results"
        results_dir.mkdir(exist_ok=True)
        with ThreadPoolExecutor(
            max_workers=min(max_workers, len(jobs))
        ) as executor:
            outcomes = list(
                executor.map(
                    lambda job: _run_job(job, config, budget, fetch_options),
                    jobs,
                )
            )
        for index, outcome in enumerate(outcomes, start=1):
            if outcome["status"] != "fetched":
                continue
            validate_record("research-fetch-result", outcome["result"])
            result_path = (
                results_dir / f"{index:03d}-{outcome['job']['mode']}.json"
            )
            write_json_atomic(result_path, outcome["result"])
            outcome["result_path"] = result_path

    return {
        "jobs": outcomes,
        "skipped": skipped,
        "budget": budget,
        "fetched": sum(1 for o in outcomes if o["status"] == "fetched"),
    }
