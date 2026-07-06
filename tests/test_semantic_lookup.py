import hashlib
import json
import shutil
import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path

from influencer_os.cli import main
from influencer_os.semantic_lookup import (
    DEFAULT_FLOOR_RATIO,
    DEFAULT_HALF_LIFE_DAYS,
    DEFAULT_RECENCY_FLOOR,
    _fts_query,
    authority_weight_for,
    bm25_relevance,
    chunk_markdown,
    collect_lookup_sources,
    load_lookup_config,
    query_lookup,
    rebuild_lookup,
    recency_factor,
    rerank,
)
from influencer_os.validation import ValidationError

from test_recall_index import PROJECT_SLUG, SUMMARY_ID, scaffold_indexable_workspace
from test_research_validation import load_example, write_json


RAW_MARKER = "zq_raw_marker_never_indexed"


def scaffold_lookup_workspace(temp_dir):
    """The recall-index scaffold plus every markdown lookup source, with a
    raw-analytics marker planted where the indexer must never look."""
    workspace_dir = scaffold_indexable_workspace(temp_dir)
    brand = workspace_dir / "brand_context"
    brand.mkdir(exist_ok=True)
    (brand / "identity.md").write_text(
        "# Identity\n\n## Positioning\n\nLuna helps desk workers reclaim "
        "energy with tiny movement resets.\n"
    )
    (brand / "soul.md").write_text(
        "# Soul\n\n## Beliefs\n\nConsistency beats intensity for desk workers.\n"
    )
    (brand / "personal-brand.md").write_text(
        "# Personal Brand\n\n## Promise\n\nEvery reset fits inside a lunch break.\n"
    )
    memory_dir = workspace_dir / "memory"
    memory_dir.mkdir(exist_ok=True)
    (memory_dir / "learnings.md").write_text(
        "# Learnings\n\n## Creator Lessons\n\n### hook\n\n"
        "- 2026-07-01 [single_post_signal]: Visible laptop-day constraints "
        f"lift hook retention (evidence: {SUMMARY_ID})\n"
    )
    project_dir = workspace_dir / "projects" / PROJECT_SLUG
    snapshot_path = next((project_dir / "analytics" / "snapshots").glob("*.json"))
    snapshot = json.loads(snapshot_path.read_text())
    snapshot["notes"] = f"Manual snapshot. {RAW_MARKER}"
    write_json(snapshot_path, snapshot)
    raw_dir = project_dir / "analytics" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "export.json").write_text(json.dumps({"payload": RAW_MARKER}))
    return workspace_dir


def scaffold_second_creator(temp_dir):
    """A minimal second workspace so scope probes share one database."""
    workspace_dir = Path(temp_dir) / "mira-doe"
    manifest = load_example("creator-workspace")
    manifest["creator_workspace_id"] = "creator_workspace_mira_doe"
    manifest["creator_slug"] = "mira-doe"
    manifest["creator_profile_id"] = "creator_mira_doe"
    manifest["root_path"] = "workspace-library/creators/mira-doe/"
    write_json(workspace_dir / "creator-workspace.json", manifest)
    brand = workspace_dir / "brand_context"
    brand.mkdir(parents=True, exist_ok=True)
    (brand / "identity.md").write_text(
        "# Identity\n\n## Positioning\n\nMira teaches desk workers movement "
        "resets too, but hers.\n"
    )
    return workspace_dir


def db_path_for(temp_dir):
    return Path(temp_dir) / "index" / "influencer-os.sqlite"


def all_rows(db_path, include_indexed_on=False):
    columns = (
        "creator_slug, source_path, chunk_index, heading, heading_level, "
        "start_line, end_line, content, content_hash, authority_weight, "
        "content_date"
    )
    if include_indexed_on:
        columns += ", indexed_on"
    connection = sqlite3.connect(db_path)
    try:
        chunks = connection.execute(
            f"SELECT {columns} FROM lookup_chunks "
            "ORDER BY creator_slug, source_path, chunk_index"
        ).fetchall()
        sources = connection.execute(
            "SELECT creator_slug, source_path, title, content_date, "
            "authority_weight, content_sha256 FROM lookup_sources "
            "ORDER BY creator_slug, source_path"
        ).fetchall()
    finally:
        connection.close()
    return chunks, sources


class ChunkerTests(unittest.TestCase):
    def test_heading_aware_chunks_carry_line_provenance(self):
        text = "preamble line\n\n# Title\n\nIntro text.\n\n## Section A\n\nBody A.\nMore A.\n"
        chunks = chunk_markdown(text)
        self.assertEqual(chunks, chunk_markdown(text))  # deterministic
        self.assertEqual(chunks[0]["heading"], None)
        self.assertEqual(chunks[0]["content"], "preamble line")
        self.assertEqual((chunks[0]["start_line"], chunks[0]["end_line"]), (1, 1))
        self.assertEqual(chunks[1]["heading"], "Title")
        self.assertEqual(chunks[1]["heading_level"], 1)
        self.assertEqual(chunks[2]["heading"], "Section A")
        self.assertEqual(chunks[2]["heading_level"], 2)
        self.assertEqual(chunks[2]["content"], "Body A.\nMore A.")
        self.assertEqual((chunks[2]["start_line"], chunks[2]["end_line"]), (9, 10))
        self.assertEqual(
            [chunk["chunk_index"] for chunk in chunks], [0, 1, 2]
        )
        for chunk in chunks:
            self.assertEqual(
                chunk["content_hash"],
                hashlib.sha256(chunk["content"].encode()).hexdigest(),
            )

    def test_oversized_section_window_splits_with_overlap(self):
        body = "\n".join(f"line {index:04d} " + "x" * 40 for index in range(80))
        chunks = chunk_markdown(f"## Big\n\n{body}\n")
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk["content"]), 2000)
            self.assertEqual(chunk["heading"], "Big")
        # Overlapping windows: the next chunk starts before the last ends.
        self.assertLessEqual(chunks[1]["start_line"], chunks[0]["end_line"] + 1)

    def test_not_headings(self):
        chunks = chunk_markdown("#nospace\n####### seven\n# \nplain\n")
        self.assertEqual(len(chunks), 1)
        self.assertIsNone(chunks[0]["heading"])


class RerankTests(unittest.TestCase):
    def config(self, **overrides):
        config = {
            "half_life_days": DEFAULT_HALF_LIFE_DAYS,
            "floor_ratio": DEFAULT_FLOOR_RATIO,
            "recency_floor": DEFAULT_RECENCY_FLOOR,
        }
        config.update(overrides)
        return config

    def hit(self, **overrides):
        base = {
            "relevance": 1.0,
            "authority_weight": 1.0,
            "content_date": None,
            "source_path": "a.md",
            "chunk_index": 0,
        }
        base.update(overrides)
        return base

    def test_authority_weight_orders_equal_relevance(self):
        hits = [
            self.hit(source_path="findings.md", authority_weight=1.0),
            self.hit(source_path="learnings.md", authority_weight=1.5),
        ]
        ranked = rerank(hits, self.config())
        self.assertEqual(
            [hit["source_path"] for hit in ranked],
            ["learnings.md", "findings.md"],
        )

    def test_floor_ratio_gates_weak_hits(self):
        hits = [self.hit(relevance=1.0), self.hit(relevance=0.1, source_path="b.md")]
        ranked = rerank(hits, self.config(floor_ratio=0.3))
        self.assertEqual([hit["source_path"] for hit in ranked], ["a.md"])

    def test_recency_decay_dampened_by_floor(self):
        today = date(2026, 7, 6)
        self.assertEqual(recency_factor(None, 14.0, today=today), 1.0)
        self.assertEqual(recency_factor("2026-07-06", 14.0, today=today), 1.0)
        # Future dates clamp to no boost.
        self.assertEqual(recency_factor("2026-08-01", 14.0, today=today), 1.0)
        old = self.hit(content_date="2020-01-01", source_path="old.md")
        fresh = self.hit(content_date="2026-07-06", source_path="fresh.md")
        ranked = rerank([old, fresh], self.config(), today=today)
        self.assertEqual(
            [hit["source_path"] for hit in ranked], ["fresh.md", "old.md"]
        )
        # The dampening floor keeps even ancient rows at >= floor x authority.
        self.assertGreaterEqual(ranked[1]["final_score"], DEFAULT_RECENCY_FLOOR - 1e-9)

    def test_bm25_relevance_is_positive_and_monotone(self):
        # FTS5 bm25() is lower-is-better and corpus-dependent in scale; the
        # sigmoid must keep relevance in (0, 1) and preserve the ordering so
        # authority boosts and the floor gate behave like the reference's
        # non-negative similarities.
        scores = [-5.0, -0.5, 0.0, 0.5, 5.0]
        relevances = [bm25_relevance(score) for score in scores]
        self.assertEqual(relevances, sorted(relevances, reverse=True))
        for relevance in relevances:
            self.assertGreater(relevance, 0.0)
            self.assertLess(relevance, 1.0)

    def test_fts_query_sanitizes_operators(self):
        self.assertEqual(_fts_query(["desk", "resets"]), '"desk" "resets"')
        self.assertEqual(_fts_query(["desk resets"]), '"desk" "resets"')
        self.assertEqual(_fts_query(['a"b']), '"a""b"')
        for hostile in (["AND"], ["hook*"], ["(paren"], ["col:val"]):
            _fts_query(hostile)  # must not raise later at MATCH time
        with self.assertRaises(ValidationError):
            _fts_query(["   "])


class LookupProjectionTests(unittest.TestCase):
    def test_rebuild_indexes_exactly_the_allowlist(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_lookup_workspace(temp_dir)
            db_path = db_path_for(temp_dir)
            result = rebuild_lookup(workspace_dir, db_path=db_path)
            self.assertEqual(result["creator_slug"], "luna-fit")
            chunks, sources = all_rows(db_path)
            source_paths = {row[1] for row in sources}
            self.assertEqual(source_paths, {
                "brand_context/identity.md",
                "brand_context/soul.md",
                "brand_context/personal-brand.md",
                "research/findings.md",
                "research/stable-findings/stable_finding_luna_fit_001.md",
                "memory/learnings.md",
                f"projects/{PROJECT_SLUG}/performance-summary.json",
            })
            weights = {row[1]: row[4] for row in sources}
            self.assertEqual(weights["memory/learnings.md"], 1.5)
            self.assertEqual(
                weights[f"projects/{PROJECT_SLUG}/performance-summary.json"], 1.3
            )
            self.assertEqual(weights["brand_context/identity.md"], 1.2)
            self.assertEqual(weights["research/findings.md"], 1.0)

            by_source = {}
            for row in chunks:
                by_source.setdefault(row[1], []).append(row)
            findings = by_source["research/findings.md"]
            self.assertTrue(
                any(row[3] == "Desk resets" and row[5] is not None for row in findings)
            )
            summary_rows = by_source[
                f"projects/{PROJECT_SLUG}/performance-summary.json"
            ]
            for row in summary_rows:
                self.assertEqual(row[3], SUMMARY_ID)
                self.assertIsNone(row[5])  # JSON chunks cite the record, not lines
                self.assertEqual(row[10], "2026-07-01")

    def test_index_allowed_false_is_excluded(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_lookup_workspace(temp_dir)
            summary_path = (
                workspace_dir / "projects" / PROJECT_SLUG / "performance-summary.json"
            )
            summary = json.loads(summary_path.read_text())
            summary["semantic_lookup"]["index_allowed"] = False
            write_json(summary_path, summary)
            db_path = db_path_for(temp_dir)
            rebuild_lookup(workspace_dir, db_path=db_path)
            _chunks, sources = all_rows(db_path)
            self.assertFalse(
                [row for row in sources if row[1].startswith("projects/")]
            )

    def test_raw_analytics_never_present(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_lookup_workspace(temp_dir)
            db_path = db_path_for(temp_dir)
            rebuild_lookup(workspace_dir, db_path=db_path)
            chunks, sources = all_rows(db_path)
            for row in chunks:
                self.assertNotIn(RAW_MARKER, row[7])
            for row in sources:
                self.assertNotIn("analytics", row[1])

    def test_allowlisted_symlink_to_raw_analytics_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_lookup_workspace(temp_dir)
            identity_path = workspace_dir / "brand_context" / "identity.md"
            identity_path.unlink()
            identity_path.symlink_to(
                workspace_dir / "projects" / PROJECT_SLUG / "analytics" / "raw" / "export.json"
            )

            with self.assertRaises(ValidationError):
                rebuild_lookup(workspace_dir, db_path=db_path_for(temp_dir))

    def test_allowlisted_parent_symlink_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_lookup_workspace(temp_dir)
            raw_dir = workspace_dir / "projects" / PROJECT_SLUG / "analytics" / "raw"
            (raw_dir / "identity.md").write_text(f"# Raw\n\n{RAW_MARKER}\n")
            shutil.rmtree(workspace_dir / "brand_context")
            (workspace_dir / "brand_context").symlink_to(raw_dir)

            with self.assertRaises(ValidationError):
                rebuild_lookup(workspace_dir, db_path=db_path_for(temp_dir))

    def test_creator_scope_is_a_hard_boundary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_a = scaffold_lookup_workspace(temp_dir)
            workspace_b = scaffold_second_creator(temp_dir)
            db_path = db_path_for(temp_dir)
            rebuild_lookup(workspace_a, db_path=db_path)
            rebuild_lookup(workspace_b, db_path=db_path)
            chunks, _sources = all_rows(db_path)
            self.assertEqual(
                {row[0] for row in chunks}, {"luna-fit", "mira-doe"}
            )
            # Both creators match "resets"; each query returns only its own.
            for workspace, slug in ((workspace_a, "luna-fit"), (workspace_b, "mira-doe")):
                hits = query_lookup(workspace, ["resets"], db_path=db_path)
                self.assertTrue(hits)
                self.assertEqual({hit["creator_slug"] for hit in hits}, {slug})

    def test_other_creators_do_not_change_relevance_scores(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_a = scaffold_lookup_workspace(temp_dir)
            db_path = db_path_for(temp_dir)
            rebuild_lookup(workspace_a, db_path=db_path)
            before = [
                (hit["source_path"], hit["chunk_index"],
                 round(hit["relevance"], 12), hit["final_score"])
                for hit in query_lookup(workspace_a, ["resets"], db_path=db_path)
            ]

            workspace_b = scaffold_second_creator(temp_dir)
            stable_dir = workspace_b / "research" / "stable-findings"
            stable_dir.mkdir(parents=True, exist_ok=True)
            for index in range(80):
                (stable_dir / f"2026-07-{(index % 28) + 1:02d}-mira-{index}.md").write_text(
                    "# Mira note\n\nresets resets resets resets resets\n"
                )
            rebuild_lookup(workspace_b, db_path=db_path)

            after = [
                (hit["source_path"], hit["chunk_index"],
                 round(hit["relevance"], 12), hit["final_score"])
                for hit in query_lookup(workspace_a, ["resets"], db_path=db_path)
            ]
            self.assertEqual(after, before)

    def test_rebuilding_one_creator_never_touches_another(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_a = scaffold_lookup_workspace(temp_dir)
            workspace_b = scaffold_second_creator(temp_dir)
            db_path = db_path_for(temp_dir)
            rebuild_lookup(workspace_a, db_path=db_path)
            rebuild_lookup(workspace_b, db_path=db_path)
            before = [
                rows for rows in all_rows(db_path, include_indexed_on=True)
            ]
            luna_before = [row for row in before[0] if row[0] == "luna-fit"]
            (workspace_b / "brand_context" / "identity.md").write_text(
                "# Identity\n\n## Positioning\n\nMira pivots to strength blocks.\n"
            )
            rebuild_lookup(workspace_b, db_path=db_path)
            after_chunks, _after_sources = all_rows(db_path, include_indexed_on=True)
            luna_after = [row for row in after_chunks if row[0] == "luna-fit"]
            self.assertEqual(luna_before, luna_after)

    def test_delete_and_rebuild_reproduces_identical_rows(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_lookup_workspace(temp_dir)
            db_path = db_path_for(temp_dir)
            rebuild_lookup(workspace_dir, db_path=db_path)
            first = all_rows(db_path)
            db_path.unlink()
            rebuild_lookup(workspace_dir, db_path=db_path)
            self.assertEqual(all_rows(db_path), first)

    def test_unchanged_sources_are_skipped_changed_sources_rechunk(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_lookup_workspace(temp_dir)
            db_path = db_path_for(temp_dir)
            first = rebuild_lookup(workspace_dir, db_path=db_path)
            self.assertEqual(first["unchanged_sources"], 0)
            second = rebuild_lookup(workspace_dir, db_path=db_path)
            self.assertEqual(second["unchanged_sources"], second["source_count"])
            baseline_chunks, _sources = all_rows(db_path, include_indexed_on=True)

            findings_path = workspace_dir / "research" / "findings.md"
            findings_path.write_text(
                findings_path.read_text()
                + "\n## Evening resets\n\nEvening resets are unproven so far.\n"
            )
            third = rebuild_lookup(workspace_dir, db_path=db_path)
            self.assertEqual(
                third["unchanged_sources"], third["source_count"] - 1
            )
            after_chunks, _sources = all_rows(db_path, include_indexed_on=True)
            untouched_before = [
                row for row in baseline_chunks if row[1] != "research/findings.md"
            ]
            untouched_after = [
                row for row in after_chunks if row[1] != "research/findings.md"
            ]
            self.assertEqual(untouched_before, untouched_after)
            self.assertTrue(
                any(
                    row[1] == "research/findings.md" and row[3] == "Evening resets"
                    for row in after_chunks
                )
            )

    def test_query_cites_sources_and_persists_nothing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_lookup_workspace(temp_dir)
            db_path = db_path_for(temp_dir)
            rebuild_lookup(workspace_dir, db_path=db_path)
            db_bytes = db_path.read_bytes()
            hits = query_lookup(workspace_dir, ["desk", "resets"], db_path=db_path)
            self.assertTrue(hits)
            top = hits[0]
            self.assertIn("source_path", top)
            self.assertGreater(top["final_score"], 0)
            # Learnings authority (1.5) should outrank plain findings (1.0)
            # when both match; at minimum every hit is creator-scoped.
            self.assertEqual({hit["creator_slug"] for hit in hits}, {"luna-fit"})
            # Privacy default: the query wrote nothing.
            self.assertEqual(db_path.read_bytes(), db_bytes)

    def test_query_requires_database_and_terms(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_lookup_workspace(temp_dir)
            db_path = db_path_for(temp_dir)
            with self.assertRaises(ValidationError):
                query_lookup(workspace_dir, ["resets"], db_path=db_path)
            rebuild_lookup(workspace_dir, db_path=db_path)
            with self.assertRaises(ValidationError):
                query_lookup(workspace_dir, [" "], db_path=db_path)
            with self.assertRaises(ValidationError):
                query_lookup(workspace_dir, ["resets"], db_path=db_path, limit=0)

    def test_lookup_config_overrides_and_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_lookup_workspace(temp_dir)
            config_path = workspace_dir / "context" / "lookup-config.json"
            config_path.parent.mkdir(exist_ok=True)
            write_json(config_path, {
                "half_life_days": 45,
                "authority_weights": {"memory/learnings.md": 3.0},
            })
            config = load_lookup_config(workspace_dir)
            self.assertEqual(config["half_life_days"], 45.0)
            self.assertEqual(
                authority_weight_for("memory/learnings.md", config["authority_weights"]),
                3.0,
            )
            # Unmapped paths fall back to 1.0 once the map is overridden.
            self.assertEqual(
                authority_weight_for("brand_context/identity.md",
                                     config["authority_weights"]),
                1.0,
            )
            db_path = db_path_for(temp_dir)
            rebuild_lookup(workspace_dir, db_path=db_path)
            _chunks, sources = all_rows(db_path)
            weights = {row[1]: row[4] for row in sources}
            self.assertEqual(weights["memory/learnings.md"], 3.0)

            write_json(config_path, {"floor_ratio": 2})
            with self.assertRaises(ValidationError):
                load_lookup_config(workspace_dir)
            write_json(config_path, {"unknown_knob": 1})
            with self.assertRaises(ValidationError):
                load_lookup_config(workspace_dir)

    def test_authority_weight_change_reindexes_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_lookup_workspace(temp_dir)
            db_path = db_path_for(temp_dir)
            rebuild_lookup(workspace_dir, db_path=db_path)
            config_path = workspace_dir / "context" / "lookup-config.json"
            config_path.parent.mkdir(exist_ok=True)
            write_json(config_path, {"authority_weights": {"memory/learnings.md": 3.0}})
            result = rebuild_lookup(workspace_dir, db_path=db_path)
            # learnings.md re-indexed; everything else skipped, and the
            # brand/findings weights drop to the 1.0 fallback (also a change).
            self.assertLess(result["unchanged_sources"], result["source_count"])
            _chunks, sources = all_rows(db_path)
            weights = {row[1]: row[4] for row in sources}
            self.assertEqual(weights["memory/learnings.md"], 3.0)
            self.assertEqual(weights["brand_context/identity.md"], 1.0)

    def test_collect_sources_walks_only_the_allowlist(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_lookup_workspace(temp_dir)
            (workspace_dir / "brand_context" / "voice-samples.md").write_text(
                "# Voice\n\nNot an allowlisted lookup source.\n"
            )
            (workspace_dir / "context").mkdir(exist_ok=True)
            (workspace_dir / "context" / "MEMORY.md").write_text(
                "# MEMORY\n\n## Active Threads\n\n- private thread\n"
            )
            sources = collect_lookup_sources(workspace_dir)
            paths = {source["source_path"] for source in sources}
            self.assertNotIn("brand_context/voice-samples.md", paths)
            self.assertNotIn("context/MEMORY.md", paths)


class LookupCliTests(unittest.TestCase):
    def test_rebuild_and_query_cli_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_lookup_workspace(temp_dir)
            db_path = db_path_for(temp_dir)
            self.assertEqual(
                main(["rebuild-lookup", str(workspace_dir), "--db", str(db_path)]),
                0,
            )
            self.assertEqual(
                main([
                    "query-lookup", str(workspace_dir), "desk", "resets",
                    "--db", str(db_path), "--limit", "3",
                ]),
                0,
            )

    def test_query_cli_fails_cleanly_without_database(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_lookup_workspace(temp_dir)
            self.assertEqual(
                main([
                    "query-lookup", str(workspace_dir), "resets",
                    "--db", str(db_path_for(temp_dir)),
                ]),
                1,
            )


if __name__ == "__main__":
    unittest.main()
