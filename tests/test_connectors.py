"""Tests for the research-acquisition connector layer (ADR 0022).

No live provider calls: every provider entry point is exercised through its mock
hook, mirroring how Agentic OS tests its acquisition scripts.
"""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from influencer_os.connectors import env, fetch, openai_reddit, reddit_enrich, registry


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


if __name__ == "__main__":
    unittest.main()
