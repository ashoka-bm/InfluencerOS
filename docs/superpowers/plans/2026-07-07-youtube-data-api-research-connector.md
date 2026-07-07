# YouTube Data API Research Connector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a key-gated YouTube Data API connector for creator research runs, so agents can discover YouTube videos/channels, capture public video metrics, and curate them into the existing ResearchEvidence, MetricSnapshot, and ResearchSourceYield records.

**Architecture:** Treat YouTube as an approved research acquisition platform for this slice, not as publishing, scheduling, or owned-channel analytics. Add `youtube_data_api` to the existing connector layer and update the research schemas/validators so YouTube evidence can be stored canonically. Keep transcripts/video-content analysis outside this connector; route actual video inspection to the existing VideoUnderstandingPack boundary.

**Tech Stack:** Python stdlib HTTP helpers in `influencer_os/connectors/http.py`, JSON Schema files in `schemas/`, unittest tests under `tests/`, CLI extensions in `influencer_os/cli.py`.

---

## External API Facts To Preserve

Official YouTube Data API docs:

- `search.list` finds videos/channels/playlists by query and supports `publishedAfter`, `order`, `type`, `channelId`, `videoDuration`, and `maxResults` up to 50: https://developers.google.com/youtube/v3/docs/search/list
- `videos.list` fetches video `snippet`, `contentDetails`, and `statistics`: https://developers.google.com/youtube/v3/docs/videos/list
- `channels.list` resolves `forHandle` and retrieves `contentDetails.relatedPlaylists.uploads`: https://developers.google.com/youtube/v3/docs/channels/list
- `commentThreads.list` can fetch top-level public comments for a video: https://developers.google.com/youtube/v3/docs/commentThreads/list
- Google documents quota costs separately; do not assume unlimited calls even when the current free allowance is sufficient: https://developers.google.com/youtube/v3/determine_quota_cost

Do not implement captions/transcripts in this slice. The official captions API is not a simple public API-key transcript path and video understanding already has a separate boundary.

## File Structure

Create:

- `influencer_os/connectors/youtube_data.py`: YouTube Data API HTTP calls and response parsers.
- `docs/adr/0027-youtube-data-api-research-connector.md`: Decision record activating YouTube Data API for research acquisition.

Modify:

- `influencer_os/connectors/env.py`: include `YOUTUBE_API_KEY` through the registry-derived key list.
- `influencer_os/connectors/registry.py`: add `youtube_data_api`.
- `influencer_os/connectors/fetch.py`: dispatch YouTube search/channel fetches.
- `influencer_os/connectors/__init__.py`: import/export `youtube_data` if the package currently lists connector modules.
- `influencer_os/cli.py`: add `youtube-search` and `youtube-channel` research-fetch modes.
- `influencer_os/validation.py`: add YouTube to standing-approved adapter methods after ADR 0027, preserving exact adapter/method pinning.
- `schemas/research-fetch-result.schema.json`: allow candidates with YouTube-specific optional fields; add `youtube` to platform enum.
- `schemas/research-search-plan.schema.json`: add `youtube` to plan/query/source platform enums.
- `schemas/research-source-yield.schema.json`: add `youtube` to platform enum.
- `schemas/research-evidence.schema.json`: add `youtube` platform and content types.
- `schemas/metric-snapshot.schema.json`: add `youtube` platform.
- `examples/research-search-plan.example.json`: change YouTube from future connector to an active/key-gated connector example, or add a second active adapter example while preserving at least one deferred adapter example.
- `docs/research-adapter-registry.md`: move `youtube_data_api` from planned/deferred to key-gated research connectors.
- `docs/adr/0022-research-acquisition-connector-layer.md`: append a short supersession note pointing to ADR 0027.
- `skills/create-research-findings/SKILL.md`: include YouTube usage instructions and the transcript boundary.
- `README.md`: add YouTube examples to research connector docs.
- `tests/test_connectors.py`: add parser, fetch, registry, and CLI tests.
- `tests/test_schema_validation.py`: update search-plan standing-approval tests.
- `tests/test_research_validation.py`: update source-yield tests.
- `tests/test_drift_checks.py`: update any enum/registry drift expectations if they assert exact platform/adapter sets.

## Design Decisions

1. `youtube_data_api` is standing-approved by key presence only for public YouTube Data API research acquisition.
2. The adapter uses `access_method: "api_backed"` and env key `YOUTUBE_API_KEY`.
3. The canonical platform is `youtube`, with content types `youtube_video`, `youtube_short`, and `youtube_comment`.
4. The first implementation emits video candidates; comment fetching is a parser/helper capability but not wired into the CLI until the basic video path is stable.
5. YouTube Analytics API is out of scope. It belongs to owned-channel post-publication analytics ingestion, not public research acquisition.
6. Transcripts are out of scope. If a real video needs content analysis, create a VideoUnderstandingPack through the existing video-understanding workflow.

---

### Task 1: Record The YouTube Research Decision

**Files:**
- Create: `docs/adr/0027-youtube-data-api-research-connector.md`
- Modify: `docs/research-adapter-registry.md`
- Modify: `docs/adr/0022-research-acquisition-connector-layer.md`

- [x] **Step 1: Add the ADR**

Create `docs/adr/0027-youtube-data-api-research-connector.md`:

```markdown
# ADR 0027: YouTube Data API Research Connector

## Status

Accepted

## Context

InfluencerOS previously named `youtube_data_api` as a planned adapter because
YouTube was not in the ADR 0020 research platform set and API-backed adapters
needed explicit auth, quota, retention, and approval decisions. The operator has
now configured `YOUTUBE_API_KEY` and approved using the YouTube Data API for
lightweight public research acquisition.

The connector is useful for topic and trend research because it can search
recent videos, resolve channels and handles, inspect latest uploads, and capture
public video statistics. It does not provide owned-channel analytics, publishing,
scheduling, or a simple public transcript path.

## Decision

Activate `youtube_data_api` as a key-gated research-acquisition connector:

- provider: YouTube Data API v3
- env var: `YOUTUBE_API_KEY`
- access method: `api_backed`
- standing approval: key presence, bounded by the existing connector call cap
  and kill switch
- canonical platform: `youtube`
- content types: `youtube_video`, `youtube_short`, `youtube_comment`

The connector may be used inside explicit, user-initiated research runs. It
maps provider responses into transient `ResearchFetchResult` candidates, which
the `create-research-findings` skill curates into `ResearchEvidence`,
`MetricSnapshot`, and `ResearchSourceYield` records.

The first implementation supports video search and channel latest-upload
fetches. Comment fetching may be added behind the same adapter when needed for
audience-language research. Transcripts remain outside this connector and must
use the VideoUnderstandingPack boundary when video content analysis is needed.

## Consequences

- YouTube can now contribute public trend/topic evidence with visible metrics.
- Research schemas and validators must include `youtube` as a research platform.
- The standing-approval exemption remains exact: only `youtube_data_api` with
  `api_backed` is approved. Logged-in access, YouTube Analytics API, captions
  downloads, scheduled jobs, and publishing remain out of scope.
- Quota usage is bounded by the existing call budget and must be summarized in
  run output through `calls_used`, `source-yield.jsonl`, and `run-summary.md`.
```

- [x] **Step 2: Update the adapter registry**

In `docs/research-adapter-registry.md`, move `youtube_data_api` from the "Planned / Deferred Adapters" table into "Key-Gated Research-Acquisition Connectors":

```markdown
| `youtube_data_api` | `youtube_data_api` | `api_backed` | `YOUTUBE_API_KEY` | `ResearchEvidence` + `MetricSnapshot` (views/likes/comments) |
```

Add this paragraph after the key-gated connector table:

```markdown
`youtube_data_api` is active as a public research-acquisition connector only.
It searches public videos/channels and captures public metadata/statistics. It
does not authorize logged-in YouTube access, YouTube Analytics API ingestion,
caption downloads, publishing, scheduling, or transcript extraction.
```

Remove the `youtube_data_api` row from the planned/deferred table. Keep `youtube_public_video` in the planned/deferred table if the repo still wants a separate external-video-understanding boundary.

- [x] **Step 3: Add a supersession note to ADR 0022**

At the end of `docs/adr/0022-research-acquisition-connector-layer.md`, add:

```markdown
## Supersession Note

ADR 0027 adds `youtube_data_api` to the standing-approved research-acquisition
connector set. The same guardrails apply: key presence is standing approval only
for explicit research acquisition runs, bounded by the connector call cap and
kill switch. YouTube Analytics, publishing, scheduled jobs, captions downloads,
and logged-in access remain out of scope.
```

- [x] **Step 4: Commit**

```bash
git add docs/adr/0027-youtube-data-api-research-connector.md docs/research-adapter-registry.md docs/adr/0022-research-acquisition-connector-layer.md
git commit -m "docs: approve YouTube research connector"
```

---

### Task 2: Update Schemas And Validation Gates

**Files:**
- Modify: `schemas/research-fetch-result.schema.json`
- Modify: `schemas/research-search-plan.schema.json`
- Modify: `schemas/research-source-yield.schema.json`
- Modify: `schemas/research-evidence.schema.json`
- Modify: `schemas/metric-snapshot.schema.json`
- Modify: `influencer_os/validation.py`
- Modify: `tests/test_schema_validation.py`
- Modify: `tests/test_research_validation.py`

- [x] **Step 1: Write failing schema validation tests**

In `tests/test_schema_validation.py`, add:

```python
    def test_search_plan_allows_active_youtube_data_api_use_now(self):
        example = load_json("examples/research-search-plan.example.json")
        valid = deepcopy(example)
        valid["platforms"].append("youtube")
        valid["adapters_considered"].append({
            "adapter_id": "youtube_data_api",
            "access_method": "api_backed",
            "adapter_status": "active",
            "auth_required": True,
            "approval_required": False,
            "decision": "use_now",
            "reason": "YOUTUBE_API_KEY present; standing-approved public YouTube research connector.",
        })
        valid["planned_queries"].append({
            "query_id": "query_luna_fit_youtube_001",
            "platform": "youtube",
            "query_intent": "trend_scan",
            "query": "desk stretch routine",
            "source_type": "search_term",
            "purpose": "Check current YouTube video patterns around desk reset routines.",
            "expected_signal": "Recent public videos with visible engagement and reusable hooks.",
            "routing_basis": "Term from creator_profile.json desk wellness pillar.",
            "term_basis": ["creator_profile"],
        })

        validate_record("research-search-plan", valid)
```

In `tests/test_research_validation.py`, update the existing `test_source_yield_rejects_unapproved_api_backed_adapter` by replacing `youtube_data_api` with a still-unapproved adapter id:

```python
            record["adapter_id"] = "instagram_logged_in_api"
```

Add:

```python
    def test_source_yield_allows_youtube_data_api_connector(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_research_workspace(temp_dir)
            yield_path = workspace_dir / "research" / "runs" / RUN_ID / "source-yield.jsonl"
            record = load_example("research-source-yield")
            record["platform"] = "youtube"
            record["access_method"] = "api_backed"
            record["adapter_id"] = "youtube_data_api"
            write_jsonl(yield_path, [record])

            validate_research(workspace_dir)
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m pytest tests/test_schema_validation.py::SchemaValidationTests::test_search_plan_allows_active_youtube_data_api_use_now -q
python3 -m pytest tests/test_research_validation.py::ResearchValidationTests::test_source_yield_allows_youtube_data_api_connector -q
```

Expected: both fail because `youtube` is not in the schemas and `youtube_data_api` is not standing-approved.

- [x] **Step 3: Update schema enums**

In each listed schema, add `"youtube"` to platform enums:

- `schemas/research-fetch-result.schema.json`
- `schemas/research-search-plan.schema.json`
- `schemas/research-source-yield.schema.json`
- `schemas/research-evidence.schema.json`
- `schemas/metric-snapshot.schema.json`

In `schemas/research-evidence.schema.json`, add these content types:

```json
"youtube_video",
"youtube_short",
"youtube_comment"
```

- [x] **Step 4: Update standing-approved adapter pinning**

In `influencer_os/validation.py`, update `STANDING_APPROVED_ADAPTER_METHODS`:

```python
STANDING_APPROVED_ADAPTER_METHODS = {
    "reddit_api_or_search": "api_backed",
    "x_api": "api_backed",
    "firecrawl_public_web": "scraping_api",
    "linkedin_apify": "api_backed",
    "youtube_data_api": "api_backed",
}
```

Keep `is_standing_approved_adapter()` unchanged so the approval remains per exact `(adapter_id, access_method)`.

- [x] **Step 5: Run schema and research validation tests**

Run:

```bash
python3 -m pytest tests/test_schema_validation.py tests/test_research_validation.py -q
```

Expected: pass, except any exact assertion text that still says there are only four standing-approved connectors.

- [x] **Step 6: Commit**

```bash
git add schemas/research-fetch-result.schema.json schemas/research-search-plan.schema.json schemas/research-source-yield.schema.json schemas/research-evidence.schema.json schemas/metric-snapshot.schema.json influencer_os/validation.py tests/test_schema_validation.py tests/test_research_validation.py
git commit -m "feat: allow YouTube research evidence"
```

---

### Task 3: Add The YouTube Connector Module

**Files:**
- Create: `influencer_os/connectors/youtube_data.py`
- Modify: `tests/test_connectors.py`

- [x] **Step 1: Write parser tests**

In `tests/test_connectors.py`, add `youtube_data` to the connector imports:

```python
from influencer_os.connectors import (
    env,
    fetch,
    firecrawl_web,
    linkedin_apify,
    models,
    openai_reddit,
    reddit_enrich,
    registry,
    xai_x,
    youtube_data,
)
```

Add this test class:

```python
class YouTubeDataParseTests(unittest.TestCase):
    def test_parse_video_search_results_extracts_video_candidates(self):
        search_response = {
            "items": [{
                "id": {"videoId": "abc123xyz09"},
                "snippet": {
                    "title": "Desk stretch routine",
                    "channelTitle": "Desk Wellness",
                    "channelId": "UC123",
                    "publishedAt": "2026-07-01T12:00:00Z",
                    "description": "A short desk reset.",
                    "thumbnails": {"medium": {"url": "https://i.ytimg.com/vi/abc123xyz09/mqdefault.jpg"}},
                },
            }]
        }
        video_response = {
            "items": [{
                "id": "abc123xyz09",
                "snippet": {"tags": ["desk", "stretch"], "categoryId": "27"},
                "contentDetails": {"duration": "PT58S"},
                "statistics": {"viewCount": "1200", "likeCount": "90", "commentCount": "12"},
            }]
        }

        items = youtube_data.parse_video_candidates(search_response, video_response)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], "YT1")
        self.assertEqual(items[0]["video_id"], "abc123xyz09")
        self.assertEqual(items[0]["url"], "https://www.youtube.com/watch?v=abc123xyz09")
        self.assertEqual(items[0]["title"], "Desk stretch routine")
        self.assertEqual(items[0]["channel_title"], "Desk Wellness")
        self.assertEqual(items[0]["channel_id"], "UC123")
        self.assertEqual(items[0]["date"], "2026-07-01")
        self.assertEqual(items[0]["duration"], "PT58S")
        self.assertTrue(items[0]["is_short_candidate"])
        self.assertEqual(items[0]["engagement"]["views"], 1200)
        self.assertEqual(items[0]["engagement"]["likes"], 90)
        self.assertEqual(items[0]["engagement"]["comments"], 12)

    def test_parse_video_candidates_survives_missing_statistics(self):
        search_response = {
            "items": [{
                "id": {"videoId": "abc123xyz09"},
                "snippet": {
                    "title": "Desk stretch routine",
                    "channelTitle": "Desk Wellness",
                    "channelId": "UC123",
                    "publishedAt": "2026-07-01T12:00:00Z",
                },
            }]
        }
        video_response = {"items": [{"id": "abc123xyz09", "contentDetails": {"duration": "PT4M10S"}}]}

        items = youtube_data.parse_video_candidates(search_response, video_response)

        self.assertEqual(items[0]["engagement"], {"views": None, "likes": None, "comments": None})
        self.assertFalse(items[0]["is_short_candidate"])

    def test_resolve_search_video_ids_ignores_non_video_results(self):
        response = {
            "items": [
                {"id": {"channelId": "UC123"}},
                {"id": {"videoId": "abc123xyz09"}},
            ]
        }

        self.assertEqual(youtube_data.video_ids_from_search(response), ["abc123xyz09"])
```

- [x] **Step 2: Run parser tests to verify they fail**

Run:

```bash
python3 -m pytest tests/test_connectors.py::YouTubeDataParseTests -q
```

Expected: import or attribute failure because `youtube_data.py` does not exist.

- [x] **Step 3: Implement `youtube_data.py`**

Create `influencer_os/connectors/youtube_data.py`:

```python
"""YouTube Data API v3 research acquisition connector.

This module fetches public video/channel metadata for research runs. It does
not fetch transcripts, use OAuth, call YouTube Analytics, publish, or schedule.
"""

from datetime import datetime, timezone
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
        "publishedBefore": rfc3339_start(to_date),
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
    if handle_or_id.startswith("UC") and len(handle_or_id) == 24:
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
    for index, item in enumerate(search_response.get("items", []), start=1):
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
        candidates.append({
            "id": f"YT{len(candidates) + 1}",
            "video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "title": str(snippet.get("title", "")).strip(),
            "description": str(snippet.get("description", "")).strip()[:500],
            "channel_title": str(snippet.get("channelTitle", "")).strip(),
            "channel_id": str(snippet.get("channelId", "")).strip(),
            "channel_url": f"https://www.youtube.com/channel/{snippet.get('channelId', '')}",
            "date": _date_from_rfc3339(snippet.get("publishedAt", "")),
            "thumbnail_url": thumbnail,
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
        })
    return candidates
```

- [x] **Step 4: Run parser tests**

Run:

```bash
python3 -m pytest tests/test_connectors.py::YouTubeDataParseTests -q
```

Expected: pass.

- [x] **Step 5: Commit**

```bash
git add influencer_os/connectors/youtube_data.py tests/test_connectors.py
git commit -m "feat: add YouTube Data API parser"
```

---

### Task 4: Register And Fetch YouTube Candidates

**Files:**
- Modify: `influencer_os/connectors/registry.py`
- Modify: `influencer_os/connectors/fetch.py`
- Modify: `influencer_os/connectors/__init__.py`
- Modify: `tests/test_connectors.py`

- [x] **Step 1: Write registry and fetch tests**

In `tests/test_connectors.py`, update `RegistryTests.test_all_four_connectors_present` to:

```python
    def test_all_research_connectors_present(self):
        ids = {c["adapter_id"] for c in registry.CONNECTORS}
        self.assertEqual(
            ids,
            {
                "reddit_api_or_search",
                "x_api",
                "firecrawl_public_web",
                "linkedin_apify",
                "youtube_data_api",
            },
        )
```

Add:

```python
class YouTubeFetchTests(unittest.TestCase):
    def test_fetch_youtube_search_returns_valid_result(self):
        config = {"YOUTUBE_API_KEY": "yt-key"}
        budget = env.CallBudget(5)
        search_response = {
            "items": [{
                "id": {"videoId": "abc123xyz09"},
                "snippet": {
                    "title": "Desk stretch routine",
                    "channelTitle": "Desk Wellness",
                    "channelId": "UC123",
                    "publishedAt": "2026-07-01T12:00:00Z",
                },
            }]
        }
        details_response = {
            "items": [{
                "id": "abc123xyz09",
                "contentDetails": {"duration": "PT58S"},
                "statistics": {"viewCount": "1200", "likeCount": "90", "commentCount": "12"},
            }]
        }

        result = fetch.fetch_youtube_search(
            "desk stretch routine",
            config,
            budget,
            days=30,
            mock_search_response=search_response,
            mock_details_response=details_response,
        )

        self.assertEqual(result["connector"], "youtube_data_api")
        self.assertEqual(result["adapter_id"], "youtube_data_api")
        self.assertEqual(result["platform"], "youtube")
        self.assertEqual(result["calls_used"], 2)
        self.assertEqual(len(result["candidates"]), 1)
        validate_record("research-fetch-result", result)

    def test_fetch_youtube_requires_key(self):
        with self.assertRaises(fetch.ConnectorUnavailable):
            fetch.fetch_youtube_search("desk", {"YOUTUBE_API_KEY": None}, env.CallBudget(5))
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
python3 -m pytest tests/test_connectors.py::RegistryTests::test_all_research_connectors_present tests/test_connectors.py::YouTubeFetchTests -q
```

Expected: fail because registry and fetch are not wired.

- [x] **Step 3: Register the connector**

In `influencer_os/connectors/registry.py`, append:

```python
    {
        "connector": "youtube_data_api",
        "adapter_id": "youtube_data_api",
        "key": "YOUTUBE_API_KEY",
        "provider": "youtube",
        "access_method": "api_backed",
        "platform": "youtube",
        "summary": "Public YouTube video/channel discovery via YouTube Data API v3.",
    },
```

- [x] **Step 4: Wire fetch orchestration**

In `influencer_os/connectors/fetch.py`, add `youtube_data` to imports:

```python
    youtube_data,
```

Add:

```python
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
    """Discover public YouTube videos for a creator-relevant topic."""
    if not env.has_key(config, "YOUTUBE_API_KEY"):
        raise ConnectorUnavailable("youtube_data_api requires YOUTUBE_API_KEY and the paid tier enabled")

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
                   topic, from_date, to_date, model="", candidates=candidates,
                   budget=budget, enriched=len(candidates), truncated=False,
                   capped=False, notes=[])
```

- [x] **Step 5: Export connector if needed**

If `influencer_os/connectors/__init__.py` imports concrete modules, add:

```python
from influencer_os.connectors import youtube_data
```

If it only contains package docs, leave it unchanged.

- [x] **Step 6: Run connector tests**

Run:

```bash
python3 -m pytest tests/test_connectors.py -q
```

Expected: pass.

- [x] **Step 7: Commit**

```bash
git add influencer_os/connectors/registry.py influencer_os/connectors/fetch.py influencer_os/connectors/__init__.py tests/test_connectors.py
git commit -m "feat: fetch YouTube research candidates"
```

---

### Task 5: Add CLI Commands

**Files:**
- Modify: `influencer_os/cli.py`
- Modify: `tests/test_connectors.py`
- Modify: `README.md`

- [x] **Step 1: Write CLI tests**

In `tests/test_connectors.py`, add:

```python
class YouTubeCliTests(unittest.TestCase):
    def test_research_fetch_youtube_search_writes_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            out_path = Path(tmp) / "youtube.json"
            env_path.write_text("YOUTUBE_API_KEY=yt-key\n")
            fake_result = {
                "connector": "youtube_data_api",
                "adapter_id": "youtube_data_api",
                "platform": "youtube",
                "topic": "desk stretch",
                "from_date": "2026-06-07",
                "to_date": "2026-07-07",
                "model": "",
                "candidates": [{"id": "YT1", "url": "https://www.youtube.com/watch?v=abc123xyz09"}],
                "enriched_count": 1,
                "calls_used": 2,
                "truncated": False,
                "capped": False,
                "status": "ok",
                "notes": [],
            }
            with mock.patch.object(fetch, "fetch_youtube_search", return_value=fake_result):
                code = main([
                    "research-fetch", "youtube-search", "desk stretch",
                    "--env-file", str(env_path),
                    "--out", str(out_path),
                ])

            self.assertEqual(code, 0)
            self.assertTrue(out_path.exists())
```

- [x] **Step 2: Run CLI test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_connectors.py::YouTubeCliTests -q
```

Expected: fail because `youtube-search` is not an accepted connector.

- [x] **Step 3: Add CLI choices**

In `influencer_os/cli.py`, update the `fetch_parser.add_argument("connector", choices=...)` line to include:

```python
choices=["reddit", "x", "firecrawl", "linkedin", "youtube-search"]
```

Add arguments:

```python
    fetch_parser.add_argument("--max-results", dest="max_results", type=int, default=10, help="Max YouTube search results or channel uploads (default 10).")
    fetch_parser.add_argument("--order", choices=["date", "relevance", "viewCount", "rating"], default="date", help="YouTube search order (default date).")
```

In the `research-fetch` dispatch block, add before the LinkedIn fallback:

```python
                elif args.connector == "youtube-search":
                    result = connector_fetch.fetch_youtube_search(
                        args.target, config, budget,
                        from_date=args.from_date, to_date=args.to_date,
                        days=args.days, max_results=args.max_results,
                        order=args.order,
                    )
```

- [x] **Step 4: Update README**

In `README.md`, add:

```bash
python3 -m influencer_os research-fetch youtube-search "desk stretch routine" --days 30 --max-results 10 --out .tmp/youtube-fetch.json
```

Add a note:

```markdown
The YouTube connector uses public YouTube Data API video/channel metadata and
visible statistics only. It does not fetch transcripts, call YouTube Analytics,
publish, schedule, or use logged-in access.
```

- [x] **Step 5: Run CLI tests**

Run:

```bash
python3 -m pytest tests/test_connectors.py::YouTubeCliTests tests/test_connectors.py::ResearchFetchCliTests -q
```

Expected: pass.

- [x] **Step 6: Commit**

```bash
git add influencer_os/cli.py tests/test_connectors.py README.md
git commit -m "feat: expose YouTube research fetch"
```

---

### Task 6: Update Research Skill Instructions And Examples

**Files:**
- Modify: `skills/create-research-findings/SKILL.md`
- Modify: `examples/research-search-plan.example.json`
- Modify: `docs/research-adapter-registry.md`

- [x] **Step 1: Update the research skill**

In `skills/create-research-findings/SKILL.md`, add this connector row under "Key-Gated Connectors":

```markdown
- `youtube_data_api` (`youtube_data_api`, needs `YOUTUBE_API_KEY`): public
  YouTube video/channel discovery with visible views, likes, and comments.
```

Add to usage instructions:

```markdown
- Use YouTube for topic/trend discovery, reference-channel latest uploads, and
  public video metadata. Curate only creator-relevant candidates into
  `evidence.jsonl`; map views/likes/comments into `metric-snapshots.jsonl`.
  Do not treat titles/descriptions as full video understanding. If the actual
  video content matters, create a VideoUnderstandingPack through the existing
  video-understanding boundary.
```

Add command example:

```bash
python3 -m influencer_os research-fetch youtube-search "<topic>" --days 30 --max-results 10 --out .tmp/<run-id>-youtube.json
```

- [x] **Step 2: Update example search plan**

In `examples/research-search-plan.example.json`, add `"youtube"` to `platforms`, add an active YouTube adapter:

```json
{
  "adapter_id": "youtube_data_api",
  "access_method": "api_backed",
  "adapter_status": "active",
  "auth_required": true,
  "approval_required": false,
  "decision": "use_now",
  "reason": "YOUTUBE_API_KEY present; public YouTube metadata is standing-approved for research acquisition."
}
```

Add one planned query:

```json
{
  "query_id": "query_luna_fit_youtube_001",
  "platform": "youtube",
  "query_intent": "trend_scan",
  "query": "walking pad desk setup",
  "source_type": "watchlist_topic",
  "purpose": "Check recent YouTube video packaging and visible engagement around desk setup patterns.",
  "expected_signal": "Recent public videos with high visible metrics and reusable title/thumbnail/hook framing.",
  "routing_basis": "Term from Luna's office-worker audience and prior queue entry idea_queue_entry_luna_fit_001; YouTube chosen for public video packaging signals.",
  "term_basis": ["creator_profile", "prior_queue"]
}
```

Remove `youtube_data_api` from `skipped_sources` if it is present there.

- [x] **Step 3: Validate examples**

Run:

```bash
python3 -m influencer_os validate examples
```

Expected: all example records validate.

- [x] **Step 4: Commit**

```bash
git add skills/create-research-findings/SKILL.md examples/research-search-plan.example.json docs/research-adapter-registry.md
git commit -m "docs: document YouTube research usage"
```

---

### Task 7: Add Live Smoke Test Notes Without Hardcoding Secrets

**Files:**
- Modify: `README.md`

- [x] **Step 1: Add smoke check command**

In `README.md`, add:

```markdown
YouTube smoke check:

```bash
python3 -m influencer_os list-connectors
python3 -m influencer_os research-fetch youtube-search "desk stretch routine" --days 30 --max-results 3 --out .tmp/youtube-smoke.json
python3 -m influencer_os validate record research-fetch-result .tmp/youtube-smoke.json
```

Expected: `youtube_data_api` is available when `YOUTUBE_API_KEY` is set, and the
fetch result validates. The `.tmp/` output is transient candidate data; curate
only useful candidates into research records.
```

- [x] **Step 2: Run unit tests and example validation**

Run:

```bash
python3 -m pytest tests/test_connectors.py tests/test_schema_validation.py tests/test_research_validation.py -q
python3 -m influencer_os validate examples
```

Expected: pass.

- [x] **Step 3: Run one live smoke test**

Run:

```bash
python3 -m influencer_os research-fetch youtube-search "desk stretch routine" --days 30 --max-results 3 --out .tmp/youtube-smoke.json
python3 -m influencer_os validate record research-fetch-result .tmp/youtube-smoke.json
```

Expected: first command writes `.tmp/youtube-smoke.json`; second command validates it.

- [x] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add YouTube connector smoke check"
```

---

## Acceptance Criteria

- `python3 -m influencer_os list-connectors` shows `youtube_data_api` available when `YOUTUBE_API_KEY` is set.
- `python3 -m influencer_os research-fetch youtube-search "<topic>" --days 30 --max-results 3 --out .tmp/youtube-smoke.json` succeeds with valid `research-fetch-result` output.
- YouTube search-plan entries with `adapter_status: "active"`, `access_method: "api_backed"`, `approval_required: false`, and `decision: "use_now"` validate only for `adapter_id: "youtube_data_api"`.
- Source-yield records using `platform: "youtube"`, `adapter_id: "youtube_data_api"`, and `access_method: "api_backed"` validate.
- Non-approved api-backed adapters still fail the search-plan and source-yield gates.
- No code logs `YOUTUBE_API_KEY` or raw URLs containing the key.
- No transcript, YouTube Analytics, publishing, scheduling, OAuth, or logged-in access is added.

## Final Verification

Run:

```bash
python3 -m pytest tests/test_connectors.py tests/test_schema_validation.py tests/test_research_validation.py tests/test_drift_checks.py -q
python3 -m influencer_os validate examples
python3 -m influencer_os list-connectors
python3 -m influencer_os research-fetch youtube-search "desk stretch routine" --days 30 --max-results 3 --out .tmp/youtube-smoke.json
python3 -m influencer_os validate record research-fetch-result .tmp/youtube-smoke.json
git status --short
```

Expected:

- tests pass,
- examples validate,
- connector list includes YouTube,
- smoke fetch validates,
- only intended files are modified.

## Self-Review

Spec coverage:

- Public YouTube search: Task 3 and Task 4.
- Public video metrics: Task 3 parser and Task 4 fetch result.
- Standing approval by key presence: Task 1 and Task 2.
- Canonical research records: Task 2 schema updates and Task 6 skill guidance.
- Quota/call guardrails: Task 4 uses existing `CallBudget`.
- No transcripts/analytics/publishing: Design Decisions, ADR, skill docs, acceptance criteria.

Placeholder scan:

- No placeholder markers or unspecified generic implementation steps remain.

Type consistency:

- Connector id: `youtube_data_api`.
- Env key: `YOUTUBE_API_KEY`.
- Platform: `youtube`.
- Content types: `youtube_video`, `youtube_short`, `youtube_comment`.
