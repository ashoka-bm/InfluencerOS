"""Tests for the research-acquisition connector layer (ADR 0022).

No live provider calls: every provider entry point is exercised through its mock
hook, mirroring how Agentic OS tests its acquisition scripts.
"""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

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
)
from influencer_os.validation import validate_record

ROOT = Path(__file__).resolve().parents[1]


class EnvConfigTests(unittest.TestCase):
    def test_env_file_key_is_loaded_when_environ_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text('OPENAI_API_KEY=from-file\nXAI_API_KEY="quoted-x"\n')
            with mock.patch.dict("os.environ", {}, clear=True):
                config = env.get_config(env_path=env_path)
            self.assertEqual(config["OPENAI_API_KEY"], "from-file")
            self.assertEqual(config["XAI_API_KEY"], "quoted-x")

    def test_environ_overrides_env_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text("OPENAI_API_KEY=from-file\n")
            with mock.patch.dict("os.environ", {"OPENAI_API_KEY": "from-environ"}, clear=True):
                config = env.get_config(env_path=env_path)
            self.assertEqual(config["OPENAI_API_KEY"], "from-environ")

    def test_missing_key_makes_connector_unavailable(self):
        config = {"OPENAI_API_KEY": None}
        self.assertFalse(env.has_key(config, "OPENAI_API_KEY"))

    def test_kill_switch_disables_present_key(self):
        config = {"OPENAI_API_KEY": "sk-real", "DISABLE_PAID_CONNECTORS": True}
        self.assertFalse(env.has_key(config, "OPENAI_API_KEY"))

    def test_default_max_calls_when_unset(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text("OPENAI_API_KEY=x\n")
            config = env.get_config(env_path=env_path)
            self.assertEqual(config["MAX_CALLS"], env.DEFAULT_MAX_CALLS)


class CallBudgetTests(unittest.TestCase):
    def test_budget_bounds_calls(self):
        budget = env.CallBudget(2)
        self.assertTrue(budget.spend())
        self.assertTrue(budget.spend())
        self.assertFalse(budget.spend())
        self.assertEqual(budget.remaining(), 0)


class RegistryTests(unittest.TestCase):
    def test_all_four_connectors_present(self):
        ids = {c["adapter_id"] for c in registry.CONNECTORS}
        self.assertEqual(
            ids, {"reddit_api_or_search", "x_api", "firecrawl_public_web", "linkedin_apify"}
        )

    def test_status_reflects_key_presence(self):
        config = {"OPENAI_API_KEY": "sk", "XAI_API_KEY": None,
                  "FIRECRAWL_API_KEY": None, "APIFY_API_KEY": None}
        status = {row["connector"]: row for row in registry.connector_status(config)}
        self.assertTrue(status["reddit_openai"]["available"])
        self.assertFalse(status["x_xai"]["available"])
        self.assertIn("not set", status["x_xai"]["reason"])

    def test_kill_switch_marks_all_unavailable(self):
        config = {"OPENAI_API_KEY": "sk", "DISABLE_PAID_CONNECTORS": True}
        rows = registry.connector_status(config)
        self.assertTrue(all(not r["available"] for r in rows))
        self.assertTrue(all("kill switch" in r["reason"] for r in rows))


class RedditParseTests(unittest.TestCase):
    def _response(self, items_json):
        return {"output": [{"type": "message", "content": [{"type": "output_text", "text": items_json}]}]}

    def test_parse_extracts_and_cleans_items(self):
        text = (
            '{"items": [{"title": "Pothos root rot help", '
            '"url": "https://www.reddit.com/r/houseplants/comments/abc/pothos/", '
            '"subreddit": "r/houseplants", "date": "2026-06-30", "relevance": 1.4}]}'
        )
        items = openai_reddit.parse_reddit_response(self._response(text))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["subreddit"], "houseplants")
        self.assertEqual(items[0]["relevance"], 1.0)  # clamped

    def test_parse_rejects_non_reddit_and_bad_dates(self):
        text = (
            '{"items": ['
            '{"title": "spam", "url": "https://example.com/x", "relevance": 0.9},'
            '{"title": "ok", "url": "https://www.reddit.com/r/s/comments/z/t/", "date": "June 2026", "relevance": 0.5}'
            ']}'
        )
        items = openai_reddit.parse_reddit_response(self._response(text))
        self.assertEqual(len(items), 1)
        self.assertIsNone(items[0]["date"])

    def test_parse_handles_error_response(self):
        self.assertEqual(openai_reddit.parse_reddit_response({"error": {"message": "bad key"}}), [])

    def test_parse_ignores_extra_json_object_before_items(self):
        # Model emits an aside object before the real payload; greedy first-{ to
        # last-} matching would corrupt this, so the extractor must skip it.
        text = (
            '{"analysis": "let me think"} then the answer: '
            '{"items": [{"title": "ok", '
            '"url": "https://www.reddit.com/r/s/comments/z/t/", "relevance": 0.7}]}'
        )
        items = openai_reddit.parse_reddit_response(self._response(text))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["relevance"], 0.7)

    def test_parse_defaults_non_numeric_relevance(self):
        text = (
            '{"items": [{"title": "x", '
            '"url": "https://www.reddit.com/r/s/comments/z/t/", "relevance": "high"}]}'
        )
        items = openai_reddit.parse_reddit_response(self._response(text))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["relevance"], 0.5)  # bad value defaulted, no crash


class RedditEnrichTests(unittest.TestCase):
    def _thread(self):
        return [
            {"data": {"children": [{"data": {
                "score": 812, "num_comments": 145, "upvote_ratio": 0.97,
                "created_utc": 1751000000, "title": "Pothos"}}]}},
            {"data": {"children": [
                {"kind": "t1", "data": {"score": 60, "author": "planty", "body": "Low light is not no light, move it closer to the window."}},
                {"kind": "t1", "data": {"score": 3, "author": "[deleted]", "body": "deleted"}},
            ]}},
        ]

    def test_enrich_attaches_engagement_and_top_comments(self):
        item = {"url": "https://www.reddit.com/r/houseplants/comments/abc/pothos/"}
        enriched = reddit_enrich.enrich_reddit_item(item, mock_thread_data=self._thread())
        self.assertEqual(enriched["engagement"]["score"], 812)
        self.assertEqual(enriched["engagement"]["num_comments"], 145)
        self.assertEqual(enriched["engagement"]["upvote_ratio"], 0.97)
        self.assertEqual(len(enriched["top_comments"]), 1)  # deleted author filtered
        self.assertEqual(enriched["top_comments"][0]["author"], "planty")


class FetchRedditTests(unittest.TestCase):
    def _response(self, text):
        return {"output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}]}

    def test_unavailable_without_key(self):
        budget = env.CallBudget(5)
        with self.assertRaises(fetch.ConnectorUnavailable):
            fetch.fetch_reddit("pothos", {"OPENAI_API_KEY": None}, budget)

    def test_fetch_returns_enriched_candidates(self):
        text = ('{"items": [{"title": "t", '
                '"url": "https://www.reddit.com/r/houseplants/comments/abc/t/", "relevance": 0.8}]}')
        config = {"OPENAI_API_KEY": "sk"}
        budget = env.CallBudget(5)
        thread = [
            {"data": {"children": [{"data": {"score": 10, "num_comments": 4, "upvote_ratio": 0.9}}]}},
            {"data": {"children": []}},
        ]
        result = fetch.fetch_reddit(
            "pothos root rot", config, budget,
            mock_search_response=self._response(text), mock_model="gpt-4o", mock_thread_data=thread,
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["platform"], "reddit")
        self.assertEqual(result["adapter_id"], "reddit_api_or_search")
        self.assertEqual(len(result["candidates"]), 1)
        self.assertEqual(result["candidates"][0]["engagement"]["score"], 10)

    def test_call_cap_reached_before_search(self):
        config = {"OPENAI_API_KEY": "sk"}
        budget = env.CallBudget(0)
        result = fetch.fetch_reddit("pothos", config, budget, mock_search_response=self._response("{}"))
        self.assertTrue(result["capped"])
        self.assertEqual(result["candidates"], [])
        self.assertEqual(result["model"], "")  # coerced, never None

    def test_fetch_drops_stale_candidates(self):
        text = (
            '{"items": ['
            '{"title": "old", "url": "https://www.reddit.com/r/s/comments/a/o/", "date": "2020-01-01", "relevance": 0.9},'
            '{"title": "new", "url": "https://www.reddit.com/r/s/comments/b/n/", "date": "2026-06-20", "relevance": 0.9},'
            '{"title": "undated", "url": "https://www.reddit.com/r/s/comments/c/u/", "relevance": 0.8}'
            ']}'
        )
        config = {"OPENAI_API_KEY": "sk"}
        budget = env.CallBudget(5)
        result = fetch.fetch_reddit(
            "pothos", config, budget, from_date="2026-06-05", to_date="2026-07-05",
            mock_search_response=self._response(text), mock_model="gpt-4o",
            mock_thread_data={"x": 1},
        )
        titles = {c["title"] for c in result["candidates"]}
        self.assertEqual(titles, {"new", "undated"})  # stale dropped, unknown kept
        self.assertTrue(any("older than" in n for n in result["notes"]))

    def test_fetch_truncates_enrichment_without_dropping_candidates(self):
        text = (
            '{"items": ['
            '{"title": "a", "url": "https://www.reddit.com/r/s/comments/a/a/", "relevance": 0.9},'
            '{"title": "b", "url": "https://www.reddit.com/r/s/comments/b/b/", "relevance": 0.9}'
            ']}'
        )
        config = {"OPENAI_API_KEY": "sk"}
        budget = env.CallBudget(5)
        thread = [{"data": {"children": [{"data": {"score": 5, "num_comments": 1, "upvote_ratio": 0.9}}]}}, {"data": {"children": []}}]
        result = fetch.fetch_reddit(
            "pothos", config, budget, max_enrich=1,
            mock_search_response=self._response(text), mock_model="gpt-4o", mock_thread_data=thread,
        )
        self.assertTrue(result["truncated"])
        self.assertEqual(result["enriched_count"], 1)
        self.assertEqual(len(result["candidates"]), 2)  # tail retained, just unenriched
        self.assertEqual(result["calls_used"], 1)  # enrichment is free; only the paid search counted
        self.assertTrue(any("limited to 1" in n for n in result["notes"]))

    def test_fetch_result_conforms_to_schema(self):
        text = ('{"items": [{"title": "t", '
                '"url": "https://www.reddit.com/r/s/comments/z/t/", "relevance": 0.8}]}')
        config = {"OPENAI_API_KEY": "sk"}
        budget = env.CallBudget(5)
        thread = [{"data": {"children": [{"data": {"score": 5, "num_comments": 1, "upvote_ratio": 0.9}}]}}, {"data": {"children": []}}]
        result = fetch.fetch_reddit(
            "pothos", config, budget,
            mock_search_response=self._response(text), mock_model="gpt-4o", mock_thread_data=thread,
        )
        validate_record("research-fetch-result", result)  # raises on mismatch


class XaiParseTests(unittest.TestCase):
    def _response(self, text):
        return {"output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}]}

    def test_parse_extracts_inline_engagement(self):
        text = (
            '{"items": [{"text": "walking pad desk setup", '
            '"url": "https://x.com/user/status/123", "author_handle": "@desksetups", '
            '"date": "2026-06-30", '
            '"engagement": {"likes": 420, "reposts": 15, "replies": 30, "quotes": 2}, '
            '"relevance": 0.9}]}'
        )
        items = xai_x.parse_x_response(self._response(text))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["author_handle"], "desksetups")
        self.assertEqual(items[0]["engagement"]["likes"], 420)

    def test_parse_tolerates_null_engagement_and_bad_counts(self):
        text = (
            '{"items": ['
            '{"text": "a", "url": "https://x.com/u/status/1", "engagement": null, "relevance": 0.5},'
            '{"text": "b", "url": "https://x.com/u/status/2", '
            '"engagement": {"likes": "many", "reposts": -3}, "relevance": "high"}'
            ']}'
        )
        items = xai_x.parse_x_response(self._response(text))
        self.assertEqual(len(items), 2)
        self.assertIsNone(items[0]["engagement"])
        self.assertIsNone(items[1]["engagement"]["likes"])   # non-numeric -> None
        self.assertIsNone(items[1]["engagement"]["reposts"])  # negative -> None
        self.assertEqual(items[1]["relevance"], 0.5)

    def test_parse_handles_error_response(self):
        self.assertEqual(xai_x.parse_x_response({"error": {"message": "bad key"}}), [])


class FirecrawlParseTests(unittest.TestCase):
    def test_parse_reduces_scrape_to_candidate(self):
        response = {
            "success": True,
            "data": {
                "markdown": "# Low light plants\n...",
                "metadata": {"title": "Guide", "description": "d", "sourceURL": "https://ex.com/a", "statusCode": 200},
            },
        }
        item = firecrawl_web.parse_scrape_response(response, "https://ex.com/a")
        self.assertEqual(item["title"], "Guide")
        self.assertFalse(item["markdown_truncated"])

    def test_parse_returns_none_on_failure_or_empty(self):
        self.assertIsNone(firecrawl_web.parse_scrape_response({"success": False}, "https://x"))
        self.assertIsNone(firecrawl_web.parse_scrape_response({"success": True, "data": {"markdown": ""}}, "https://x"))

    def test_parse_truncates_long_markdown(self):
        response = {"success": True, "data": {"markdown": "x" * 30000, "metadata": {}}}
        item = firecrawl_web.parse_scrape_response(response, "https://x")
        self.assertTrue(item["markdown_truncated"])
        self.assertEqual(len(item["markdown"]), firecrawl_web.MAX_MARKDOWN_CHARS)


class LinkedinParseTests(unittest.TestCase):
    def test_parse_posts_normalizes_fields(self):
        posts = [
            {"url": "https://www.linkedin.com/posts/abc", "authorName": "Jo",
             "postedAt": "2026-06-20T10:00:00Z", "likesCount": 55, "commentsCount": 4,
             "text": "desk reset routine"},
            {"no_url": True},
        ]
        items = linkedin_apify.parse_posts(posts)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["date"], "2026-06-20")
        self.assertEqual(items[0]["engagement"]["likes"], 55)

    def test_parse_post_date_handles_epoch_millis_and_bad_values(self):
        self.assertEqual(
            linkedin_apify.parse_post_date({"postedAt": 1750000000000}), "2025-06-15")
        self.assertIsNone(linkedin_apify.parse_post_date({"postedAt": "not-a-date"}))

    def test_days_to_posted_limit_buckets(self):
        self.assertEqual(linkedin_apify.days_to_posted_limit(1), "24h")
        self.assertEqual(linkedin_apify.days_to_posted_limit(7), "week")
        self.assertEqual(linkedin_apify.days_to_posted_limit(30), "month")
        self.assertEqual(linkedin_apify.days_to_posted_limit(90), "any")


class FetchOtherConnectorsTests(unittest.TestCase):
    def _response(self, text):
        return {"output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}]}

    def test_fetch_x_returns_schema_conformant_result(self):
        text = ('{"items": [{"text": "t", "url": "https://x.com/u/status/1", '
                '"date": "2026-07-01", "engagement": {"likes": 10}, "relevance": 0.8}]}')
        budget = env.CallBudget(5)
        result = fetch.fetch_x(
            "desk resets", {"XAI_API_KEY": "xk"}, budget,
            from_date="2026-06-05", to_date="2026-07-05",
            mock_search_response=self._response(text), mock_model="grok-4-1-fast",
        )
        self.assertEqual(result["platform"], "x")
        self.assertEqual(result["enriched_count"], 1)
        validate_record("research-fetch-result", result)

    def test_fetch_x_unavailable_without_key(self):
        with self.assertRaises(fetch.ConnectorUnavailable):
            fetch.fetch_x("t", {"XAI_API_KEY": None}, env.CallBudget(5))

    def test_fetch_firecrawl_returns_schema_conformant_result(self):
        mock = {"success": True, "data": {"markdown": "# hi", "metadata": {"title": "T"}}}
        budget = env.CallBudget(5)
        result = fetch.fetch_firecrawl(
            "https://example.com/guide", {"FIRECRAWL_API_KEY": "fk"}, budget, mock_response=mock)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["calls_used"], 1)
        validate_record("research-fetch-result", result)

    def test_fetch_linkedin_filters_stale_and_conforms(self):
        posts = [
            {"url": "https://www.linkedin.com/posts/new", "authorName": "A",
             "postedAt": "2026-07-01T00:00:00Z", "likesCount": 5, "text": "x"},
            {"url": "https://www.linkedin.com/posts/old", "authorName": "B",
             "postedAt": "2020-01-01T00:00:00Z", "likesCount": 5, "text": "y"},
        ]
        budget = env.CallBudget(5)
        with mock.patch.object(fetch, "_recency_window", return_value=("2026-06-05", "2026-07-05")):
            result = fetch.fetch_linkedin(
                "https://www.linkedin.com/in/someone/", {"APIFY_API_KEY": "ak"}, budget,
                mock_response=posts)
        self.assertEqual(len(result["candidates"]), 1)
        self.assertTrue(any("older than" in n for n in result["notes"]))
        validate_record("research-fetch-result", result)

    def test_fetch_firecrawl_capped_before_scrape(self):
        result = fetch.fetch_firecrawl(
            "https://example.com", {"FIRECRAWL_API_KEY": "fk"}, env.CallBudget(0),
            mock_response={"success": True, "data": {"markdown": "x", "metadata": {}}})
        self.assertTrue(result["capped"])
        self.assertEqual(result["candidates"], [])


class ModelCacheTests(unittest.TestCase):
    def setUp(self):
        models.clear_model_cache()

    def tearDown(self):
        models.clear_model_cache()

    def test_model_selection_is_cached_and_skips_network(self):
        first = models.select_openai_model("sk", mock_models=[{"id": "gpt-5.1", "created": 2}])
        self.assertEqual(first, "gpt-5.1")
        # Second call without mocks must hit the cache, not the network.
        with mock.patch.object(models.http, "get", side_effect=AssertionError("network hit")):
            second = models.select_openai_model("sk")
        self.assertEqual(second, "gpt-5.1")


class ConnectorDriftTests(unittest.TestCase):
    def test_provider_keys_derive_from_registry(self):
        self.assertEqual(env.provider_keys(), [c["key"] for c in registry.CONNECTORS])

    def test_every_connector_documented_in_registry_doc(self):
        doc = (ROOT / "docs" / "research-adapter-registry.md").read_text()
        for c in registry.CONNECTORS:
            self.assertIn(c["adapter_id"], doc, f"{c['adapter_id']} missing from registry doc")
            self.assertIn(c["key"], doc, f"{c['key']} missing from registry doc")


if __name__ == "__main__":
    unittest.main()
