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
    youtube_data,
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

    def test_empty_environ_does_not_defeat_env_kill_switch(self):
        # A blank `export INFLUENCER_OS_DISABLE_PAID_CONNECTORS=` must not fail the
        # safety guardrail open over a .env value of 1.
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text("OPENAI_API_KEY=sk\nINFLUENCER_OS_DISABLE_PAID_CONNECTORS=1\n")
            with mock.patch.dict(
                "os.environ", {"INFLUENCER_OS_DISABLE_PAID_CONNECTORS": ""}, clear=True
            ):
                config = env.get_config(env_path=env_path)
            self.assertTrue(config["DISABLE_PAID_CONNECTORS"])
            self.assertFalse(env.has_key(config, "OPENAI_API_KEY"))

    def test_environ_can_enable_kill_switch_when_env_file_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text("OPENAI_API_KEY=sk\n")
            with mock.patch.dict(
                "os.environ", {"INFLUENCER_OS_DISABLE_PAID_CONNECTORS": "1"}, clear=True
            ):
                config = env.get_config(env_path=env_path)
            self.assertTrue(config["DISABLE_PAID_CONNECTORS"])


class CallBudgetTests(unittest.TestCase):
    def test_budget_bounds_calls(self):
        budget = env.CallBudget(2)
        self.assertTrue(budget.spend())
        self.assertTrue(budget.spend())
        self.assertFalse(budget.spend())
        self.assertEqual(budget.remaining(), 0)


class RegistryTests(unittest.TestCase):
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

    def test_parse_rejects_off_platform_and_non_thread_reddit_urls(self):
        text = (
            '{"items": ['
            '{"title": "spoof", "url": "https://notreddit.com/r/s/comments/a/b/", "relevance": 0.9},'
            '{"title": "devs", "url": "https://developers.reddit.com/r/x/comments/a/b/", "relevance": 0.9},'
            '{"title": "listing", "url": "https://www.reddit.com/r/houseplants/", "relevance": 0.9},'
            '{"title": "real", "url": "https://old.reddit.com/r/houseplants/comments/a/b/", "relevance": 0.9}'
            ']}'
        )
        items = openai_reddit.parse_reddit_response(self._response(text))
        self.assertEqual([i["title"] for i in items], ["real"])  # only the genuine thread survives

    def test_parse_survives_unbalanced_brace_in_string(self):
        # A lone brace inside a title (code snippet, LaTeX, prose) must not
        # truncate the payload and silently drop every candidate.
        text = (
            '{"items": [{"title": "my code broke here } and then", '
            '"url": "https://www.reddit.com/r/learnpython/comments/abc/t/", "relevance": 0.9}]}'
        )
        items = openai_reddit.parse_reddit_response(self._response(text))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "my code broke here } and then")

    def test_parse_subreddit_normalization_preserves_leading_r(self):
        # Only a literal "r/" prefix is dropped; subreddits that merely start
        # with 'r' keep their first letter (lstrip stripped the char set).
        text = (
            '{"items": ['
            '{"title": "a", "url": "https://www.reddit.com/r/relationships/comments/a/b/", "subreddit": "r/relationships", "relevance": 0.9},'
            '{"title": "b", "url": "https://www.reddit.com/r/running/comments/c/d/", "subreddit": "running", "relevance": 0.9}'
            ']}'
        )
        items = openai_reddit.parse_reddit_response(self._response(text))
        self.assertEqual([i["subreddit"] for i in items], ["relationships", "running"])

    def test_parse_rejects_scheme_relative_url(self):
        # A scheme-relative URL clears the host/path filter but would fail the
        # schema ^https?:// pin, so it must be dropped as a candidate instead.
        text = (
            '{"items": ['
            '{"title": "rel", "url": "//www.reddit.com/r/s/comments/a/b/", "relevance": 0.9},'
            '{"title": "ok", "url": "https://www.reddit.com/r/s/comments/c/d/", "relevance": 0.9}'
            ']}'
        )
        items = openai_reddit.parse_reddit_response(self._response(text))
        self.assertEqual([i["title"] for i in items], ["ok"])


class OutputTextExtractionTests(unittest.TestCase):
    def test_empty_leading_item_does_not_hide_real_message(self):
        # A leading empty/placeholder output item must not short-circuit the
        # walk before the real assistant message is reached.
        from influencer_os.connectors.parse import extract_output_text
        response = {"output": [
            "",
            {"type": "message", "content": [{"type": "output_text", "text": "REAL"}]},
        ]}
        self.assertEqual(extract_output_text(response), "REAL")

    def test_empty_output_text_message_falls_through_to_next(self):
        from influencer_os.connectors.parse import extract_output_text
        response = {"output": [
            {"type": "message", "content": [{"type": "output_text", "text": ""}]},
            {"type": "message", "content": [{"type": "output_text", "text": "REAL"}]},
        ]}
        self.assertEqual(extract_output_text(response), "REAL")


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

    def test_parse_rejects_off_platform_and_non_status_urls(self):
        text = (
            '{"items": ['
            '{"text": "spoof", "url": "https://x.com.evil.com/u/status/1", "relevance": 0.9},'
            '{"text": "profile", "url": "https://x.com/someuser", "relevance": 0.9},'
            '{"text": "real", "url": "https://twitter.com/u/status/9", "relevance": 0.9}'
            ']}'
        )
        items = xai_x.parse_x_response(self._response(text))
        self.assertEqual([i["text"] for i in items], ["real"])  # only a real status URL survives

    def test_parse_survives_unbalanced_brace_in_post_text(self):
        # A lone opening brace in tweet text (code/LaTeX) must not drop candidates.
        text = (
            '{"items": [{"text": "use { to open a block", '
            '"url": "https://x.com/u/status/1", "relevance": 0.9}]}'
        )
        items = xai_x.parse_x_response(self._response(text))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["text"], "use { to open a block")

    def test_parse_rejects_scheme_relative_status_url(self):
        text = (
            '{"items": ['
            '{"text": "rel", "url": "//x.com/u/status/1", "relevance": 0.9},'
            '{"text": "ok", "url": "https://x.com/u/status/2", "relevance": 0.9}'
            ']}'
        )
        items = xai_x.parse_x_response(self._response(text))
        self.assertEqual([i["text"] for i in items], ["ok"])


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

    def test_parse_falls_back_when_sourceurl_not_http(self):
        # A non-http sourceURL from the provider must not become the candidate
        # url (it would fail the schema ^https?:// pin); fall back to the
        # caller-supplied http(s) url instead.
        response = {"success": True, "data": {"markdown": "# hi", "metadata": {"sourceURL": "ftp://internal/x"}}}
        item = firecrawl_web.parse_scrape_response(response, "https://example.com/a")
        self.assertEqual(item["url"], "https://example.com/a")


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


class SecretHandlingTests(unittest.TestCase):
    def test_redact_url_drops_query_string(self):
        from influencer_os.connectors import http
        self.assertEqual(
            http._redact_url("https://api.apify.com/v2/x?token=secret"),
            "https://api.apify.com/v2/x?<redacted>",
        )
        self.assertEqual(http._redact_url("https://x.com/a"), "https://x.com/a")

    def test_linkedin_sends_key_as_header_not_query(self):
        captured = {}

        def fake_post(url, json_data, headers=None, **kwargs):
            captured["url"] = url
            captured["headers"] = headers or {}
            return []

        with mock.patch.object(linkedin_apify.http, "post", side_effect=fake_post):
            linkedin_apify.fetch_profile_posts("secret-key", "https://linkedin.com/in/x/")
        self.assertNotIn("secret-key", captured["url"])
        self.assertEqual(captured["headers"].get("Authorization"), "Bearer secret-key")


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


class ResearchFetchCliTests(unittest.TestCase):
    def test_cli_unavailable_connector_fails_cleanly(self):
        from influencer_os.cli import main
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text("# no keys\n")
            with mock.patch.dict("os.environ", {}, clear=True):
                code = main(["research-fetch", "reddit", "pothos", "--env-file", str(env_path)])
        self.assertEqual(code, 1)

    def test_cli_provider_http_error_fails_cleanly(self):
        # A live provider fault (e.g. a bad/expired key -> 401) must surface as a
        # clean error + exit 1, not an unhandled HTTPError traceback.
        from influencer_os import cli
        from influencer_os.connectors import http
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text("OPENAI_API_KEY=sk-bad\n")
            with mock.patch.dict("os.environ", {}, clear=True), \
                    mock.patch(
                        "influencer_os.connectors.fetch.fetch_reddit",
                        side_effect=http.HTTPError("HTTP 401: Unauthorized", 401, "{}"),
                    ):
                code = cli.main(["research-fetch", "reddit", "pothos", "--env-file", str(env_path)])
        self.assertEqual(code, 1)

    def test_cli_writes_validated_result_with_mocked_fetch(self):
        from influencer_os import cli
        fake_result = {
            "connector": "reddit_openai",
            "adapter_id": "reddit_api_or_search",
            "platform": "reddit",
            "topic": "pothos",
            "from_date": "2026-06-05",
            "to_date": "2026-07-05",
            "model": "gpt-4o",
            "candidates": [{"id": "R1", "url": "https://www.reddit.com/r/s/comments/a/t/"}],
            "enriched_count": 1,
            "calls_used": 2,
            "truncated": False,
            "capped": False,
            "status": "ok",
            "notes": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text("OPENAI_API_KEY=sk-test\n")
            out_path = Path(tmp) / "result.json"
            with mock.patch.dict("os.environ", {}, clear=True), \
                    mock.patch("influencer_os.connectors.fetch.fetch_reddit", return_value=fake_result):
                code = cli.main([
                    "research-fetch", "reddit", "pothos",
                    "--env-file", str(env_path), "--out", str(out_path),
                ])
            self.assertEqual(code, 0)
            import json as json_module
            written = json_module.loads(out_path.read_text())
            self.assertEqual(written["connector"], "reddit_openai")


class YouTubeCliTests(unittest.TestCase):
    def test_research_fetch_youtube_search_writes_output(self):
        from influencer_os import cli
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
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text("YOUTUBE_API_KEY=yt-key\n")
            out_path = Path(tmp) / "youtube.json"
            with mock.patch.dict("os.environ", {}, clear=True), \
                    mock.patch.object(fetch, "fetch_youtube_search", return_value=fake_result):
                code = cli.main([
                    "research-fetch", "youtube-search", "desk stretch",
                    "--env-file", str(env_path), "--out", str(out_path),
                ])

            self.assertEqual(code, 0)
            self.assertTrue(out_path.exists())


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
