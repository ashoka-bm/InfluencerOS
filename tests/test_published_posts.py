"""Phase 2 slice 1: Published Post Record registration.

Covers the register-published-post writer, the packaged -> published status
transition, and the at-rest parity checks in validate_project. Every writer
invariant has a hand-edit probe so a record edited at rest cannot validate.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from influencer_os.projects import (
    register_output_package,
    register_published_post,
    validate_project,
)
from tests.test_cli import (
    copy_example_record,
    rewrite_json,
    scaffold_project_workspace,
    switch_project_to_text_format,
    write_upload_ready_assets,
)


ROOT = Path(__file__).resolve().parents[1]


def scaffold_packaged_project(temp_dir):
    """A packaged project with the example Output Package registered."""
    workspace_dir, project_dir = scaffold_project_workspace(temp_dir)
    package_path = Path(temp_dir) / "output-package.json"
    copy_example_record("output-package.example.json", package_path)
    package = json.loads(package_path.read_text())
    asset_root = Path(temp_dir) / "source-assets"
    write_upload_ready_assets(asset_root, package)
    register_output_package(project_dir, package_path, asset_root=asset_root)
    return workspace_dir, project_dir


def stage_published_record(temp_dir, mutate=None, filename="published-post-record.json"):
    record_path = Path(temp_dir) / filename
    copy_example_record("published-post-record.example.json", record_path)
    if mutate is not None:
        rewrite_json(record_path, mutate)
    return record_path


def scaffold_packaged_article_project(temp_dir):
    """A packaged article (text-format) project whose package has no thumbnail."""
    workspace_dir, project_dir = scaffold_project_workspace(temp_dir)
    switch_project_to_text_format(workspace_dir, project_dir, "article")
    package = json.loads((ROOT / "examples" / "output-package.example.json").read_text())
    package.update(
        output_package_id="output_package_luna_article_001",
        status="upload_ready",
    )
    package["universal_core"].update(
        format_id="format_article",
        title_base="The two-minute laptop-day reset",
        caption_base="A practical article for easing out of desk tension.",
        description_base="Long-form article package for Substack.",
        primary_asset_refs=["upload_asset_luna_article_markdown"],
    )
    package["source_refs"]["production_plan_ids"] = ["article_luna_tiny_reset_001"]
    package["upload_ready"] = [
        {
            "upload_asset_id": "upload_asset_luna_article_markdown",
            "asset_role": "description",
            "path": "output-package/upload-ready/luna-article.md",
            "media_type": "text/markdown",
            "notes": "Upload-ready article body.",
        }
    ]
    package["platform_adaptations"] = [
        {
            "platform": "substack",
            "format_id": "format_article",
            "title": "The two-minute laptop-day reset",
            "caption_or_description_path": "output-package/upload-ready/luna-article.md",
            "thumbnail_or_first_frame_asset_id": None,
            "cta": "Save this reset for your next laptop-heavy day.",
            "posting_time_recommendation": "Use creator learning defaults until analytics exist.",
            "creative_performance_variant_notes": "Substack adaptation has no thumbnail requirement.",
        }
    ]
    package_path = Path(temp_dir) / "article-output-package.json"
    package_path.write_text(json.dumps(package, indent=2) + "\n")
    asset_root = Path(temp_dir) / "source-assets"
    write_upload_ready_assets(asset_root, package)
    register_output_package(project_dir, package_path, asset_root=asset_root)
    return workspace_dir, project_dir


def article_published_record(temp_dir):
    record = {
        "published_post_record_id": "ppr_luna_article_substack_001",
        "output_package_id": "output_package_luna_article_001",
        "project_id": "project_luna_tiny_reset_001",
        "creator_profile_id": "creator_luna_fit",
        "platform": "substack",
        "platform_account": "@lunafit",
        "published_at": "2026-07-05T09:00:00Z",
        "publication_status": "published",
        "public_url": "https://lunafit.substack.com/p/two-minute-laptop-day-reset",
        "platform_post_id": "substack_luna_article_001",
        "assets_used": {
            "title_used": "The two-minute laptop-day reset",
            "caption_or_description_path": "output-package/upload-ready/luna-article.md",
            "thumbnail_or_first_frame_asset_id": None,
            "primary_media_asset_ids": ["upload_asset_luna_article_markdown"],
        },
        "publication_method": {
            "method": "manual_upload",
            "actor": "operator",
            "scheduler_ref": None,
        },
        "notes": "Manual Substack publication of the article package.",
    }
    record_path = Path(temp_dir) / "article-published-post-record.json"
    record_path.write_text(json.dumps(record, indent=2) + "\n")
    return record_path


class RegisterPublishedPostTests(unittest.TestCase):
    def test_cli_registers_record_and_marks_project_published(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_packaged_project(temp_dir)
            record_path = stage_published_record(temp_dir)

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "influencer_os",
                    "register-published-post",
                    str(record_path),
                    "--project",
                    str(project_dir),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Registered published post record", result.stdout)
            destination = (
                project_dir
                / "published"
                / "published-post-records"
                / "ppr_luna_tiny_reset_youtube_001.json"
            )
            self.assertTrue(destination.exists())
            project = json.loads((project_dir / "project.json").read_text())
            self.assertEqual(project["status"], "published")
            validate_project(project_dir)

    def test_rejects_project_below_packaged(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_project_workspace(temp_dir)
            record_path = stage_published_record(temp_dir)

            with self.assertRaises(ValueError) as ctx:
                register_published_post(project_dir, record_path)

            self.assertIn("requires a packaged", str(ctx.exception))
            self.assertFalse(
                (project_dir / "published" / "published-post-records" / "ppr_luna_tiny_reset_youtube_001.json").exists()
            )

    def test_rejects_package_mismatch_without_partial_write(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_packaged_project(temp_dir)
            record_path = stage_published_record(
                temp_dir,
                lambda record: record.update(output_package_id="output_package_other_001"),
            )

            with self.assertRaises(ValueError) as ctx:
                register_published_post(project_dir, record_path)

            self.assertIn("does not match the registered package", str(ctx.exception))
            records_dir = project_dir / "published" / "published-post-records"
            self.assertEqual(list(records_dir.glob("*.json")), [])
            project = json.loads((project_dir / "project.json").read_text())
            self.assertEqual(project["status"], "packaged")

    def test_rejects_dangling_upload_asset_ref(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_packaged_project(temp_dir)
            record_path = stage_published_record(
                temp_dir,
                lambda record: record["assets_used"].update(
                    thumbnail_or_first_frame_asset_id="upload_asset_missing_thumb"
                ),
            )

            with self.assertRaises(ValueError) as ctx:
                register_published_post(project_dir, record_path)

            self.assertIn("does not declare", str(ctx.exception))

    def test_rejects_undeclared_caption_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_packaged_project(temp_dir)
            record_path = stage_published_record(
                temp_dir,
                lambda record: record["assets_used"].update(
                    caption_or_description_path="output-package/upload-ready/unlisted.md"
                ),
            )

            with self.assertRaises(ValueError) as ctx:
                register_published_post(project_dir, record_path)

            self.assertIn("not a declared upload-ready path", str(ctx.exception))

    def test_rejects_duplicate_record_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_packaged_project(temp_dir)
            record_path = stage_published_record(temp_dir)
            register_published_post(project_dir, record_path)

            with self.assertRaises(FileExistsError):
                register_published_post(project_dir, record_path)

    def test_rejects_symlinked_records_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_packaged_project(temp_dir)
            record_path = stage_published_record(temp_dir)
            records_dir = project_dir / "published" / "published-post-records"
            records_dir.rmdir()
            outside = Path(temp_dir) / "outside-records"
            outside.mkdir()
            records_dir.symlink_to(outside)

            with self.assertRaises(ValueError) as ctx:
                register_published_post(project_dir, record_path)

            self.assertIn("escapes project", str(ctx.exception))
            self.assertEqual(list(outside.glob("*.json")), [])

    def test_text_project_registers_with_null_thumbnail(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_packaged_article_project(temp_dir)
            record_path = article_published_record(temp_dir)

            result = register_published_post(project_dir, record_path)

            self.assertEqual(result["project_status"], "published")
            validate_project(project_dir)

    def test_visual_project_rejects_null_thumbnail(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_packaged_project(temp_dir)
            record_path = stage_published_record(
                temp_dir,
                lambda record: record["assets_used"].update(
                    thumbnail_or_first_frame_asset_id=None
                ),
            )

            with self.assertRaises(ValueError) as ctx:
                register_published_post(project_dir, record_path)

            self.assertIn("required for", str(ctx.exception))

    def test_duplicate_platform_post_identity_rolls_back(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_packaged_project(temp_dir)
            register_published_post(project_dir, stage_published_record(temp_dir))
            second_path = stage_published_record(
                temp_dir,
                lambda record: record.update(
                    published_post_record_id="ppr_luna_tiny_reset_youtube_002",
                    public_url="https://youtube.com/shorts/different-url",
                ),
                filename="second-record.json",
            )

            with self.assertRaises(ValueError) as ctx:
                register_published_post(project_dir, second_path)

            self.assertIn("duplicate a platform post", str(ctx.exception))
            self.assertFalse(
                (
                    project_dir
                    / "published"
                    / "published-post-records"
                    / "ppr_luna_tiny_reset_youtube_002.json"
                ).exists()
            )
            validate_project(project_dir)

    def test_second_platform_record_registers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_packaged_project(temp_dir)
            register_published_post(project_dir, stage_published_record(temp_dir))
            second_path = stage_published_record(
                temp_dir,
                lambda record: record.update(
                    published_post_record_id="ppr_luna_tiny_reset_instagram_001",
                    platform="instagram_reels",
                    public_url="https://instagram.com/reel/example-luna-tiny-reset",
                    platform_post_id="ig_reel_luna_tiny_reset_001",
                    assets_used={
                        **record["assets_used"],
                        "caption_or_description_path": "output-package/upload-ready/instagram-caption.md",
                    },
                ),
                filename="second-record.json",
            )

            result = register_published_post(project_dir, second_path)

            self.assertEqual(result["project_status"], "published")
            validate_project(project_dir)

    def test_non_live_record_registers_without_status_flip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_packaged_project(temp_dir)
            record_path = stage_published_record(
                temp_dir,
                lambda record: record.update(
                    publication_status="failed",
                    public_url=None,
                    platform_post_id=None,
                ),
            )

            result = register_published_post(project_dir, record_path)

            self.assertEqual(result["project_status"], "packaged")
            project = json.loads((project_dir / "project.json").read_text())
            self.assertEqual(project["status"], "packaged")
            validate_project(project_dir)


class PublishedRecordsAtRestTests(unittest.TestCase):
    def registered_project(self, temp_dir):
        _, project_dir = scaffold_packaged_project(temp_dir)
        record_path = stage_published_record(temp_dir)
        register_published_post(project_dir, record_path)
        return project_dir

    def registered_record_path(self, project_dir):
        return (
            project_dir
            / "published"
            / "published-post-records"
            / "ppr_luna_tiny_reset_youtube_001.json"
        )

    def test_hand_edited_creator_mismatch_fails_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = self.registered_project(temp_dir)
            rewrite_json(
                self.registered_record_path(project_dir),
                lambda record: record.update(creator_profile_id="creator_other"),
            )

            with self.assertRaises(ValueError) as ctx:
                validate_project(project_dir)

            self.assertIn("creator_profile_id does not match project", str(ctx.exception))

    def test_misnamed_record_file_fails_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = self.registered_project(temp_dir)
            record_path = self.registered_record_path(project_dir)
            record_path.rename(record_path.with_name("ppr_renamed_copy.json"))

            with self.assertRaises(ValueError) as ctx:
                validate_project(project_dir)

            self.assertIn("filename must match its id", str(ctx.exception))

    def test_published_status_without_live_record_fails_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = self.registered_project(temp_dir)
            rewrite_json(
                self.registered_record_path(project_dir),
                lambda record: record.update(publication_status="failed"),
            )

            with self.assertRaises(ValueError) as ctx:
                validate_project(project_dir)

            self.assertIn("no record attesting a live publication", str(ctx.exception))

    def test_hand_flipped_published_status_without_records_fails_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            _, project_dir = scaffold_packaged_project(temp_dir)
            rewrite_json(
                project_dir / "project.json",
                lambda project: project.update(status="published"),
            )

            with self.assertRaises(ValueError) as ctx:
                validate_project(project_dir)

            self.assertIn("no record attesting a live publication", str(ctx.exception))

    def test_live_record_on_packaged_project_fails_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = self.registered_project(temp_dir)
            rewrite_json(
                project_dir / "project.json",
                lambda project: project.update(status="packaged"),
            )

            with self.assertRaises(ValueError) as ctx:
                validate_project(project_dir)

            self.assertIn("status is below published", str(ctx.exception))

    def test_draft_package_on_published_project_fails_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = self.registered_project(temp_dir)
            rewrite_json(
                project_dir / "output-package" / "output-package.json",
                lambda package: package.update(status="draft"),
            )

            with self.assertRaises(ValueError) as ctx:
                validate_project(project_dir)

            self.assertIn("upload-ready Output Package", str(ctx.exception))

    def test_duplicate_public_url_fails_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = self.registered_project(temp_dir)
            original = json.loads(self.registered_record_path(project_dir).read_text())
            duplicate = dict(original)
            duplicate.update(
                published_post_record_id="ppr_luna_tiny_reset_youtube_002",
                platform_post_id="yt_short_luna_tiny_reset_002",
            )
            duplicate_path = (
                self.registered_record_path(project_dir)
                .with_name("ppr_luna_tiny_reset_youtube_002.json")
            )
            duplicate_path.write_text(json.dumps(duplicate, indent=2) + "\n")

            with self.assertRaises(ValueError) as ctx:
                validate_project(project_dir)

            self.assertIn("duplicate a public URL", str(ctx.exception))

    def test_symlinked_record_file_fails_at_rest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = self.registered_project(temp_dir)
            record_path = self.registered_record_path(project_dir)
            outside = Path(temp_dir) / "outside-record.json"
            outside.write_text(record_path.read_text())
            record_path.unlink()
            record_path.symlink_to(outside)

            with self.assertRaises(ValueError) as ctx:
                validate_project(project_dir)

            self.assertIn("escapes root", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
