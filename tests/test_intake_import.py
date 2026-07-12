import datetime
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from influencer_os.creator_workspaces import (
    import_intake,
    init_creator,
    set_intake_status,
    validate_creator_workspace,
)
from influencer_os.validation import ValidationError
from tests.support import write_setup_review_fixture


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_BREAKDOWN = ROOT / "examples" / "sources" / "luna-fit-breakdown.example.md"


def read_manifest(workspace_dir):
    return json.loads((workspace_dir / "creator-workspace.json").read_text())


def scaffold_valid_workspace(temp_dir):
    workspace_dir = init_creator(
        ROOT / "examples" / "creator-workspace.example.json",
        workspace_root=Path(temp_dir),
    )
    for example_name, relative_path in [
        ("creator-profile.example.json", "creator-profile.json"),
        (
            "visual-continuity-plan.example.json",
            "references/visual-continuity-plan.json",
        ),
        ("reference-library.example.json", "references/reference-library.json"),
    ]:
        (workspace_dir / relative_path).write_text((ROOT / "examples" / example_name).read_text())
    # The example manifest declares this intake file; place it so provenance resolves.
    (workspace_dir / "sources" / "intakes" / "luna-fit-breakdown.md").write_text(
        EXAMPLE_BREAKDOWN.read_text()
    )
    write_setup_review_fixture(workspace_dir)
    return workspace_dir


def write_source_file(temp_dir, name="master-breakdown-v2.md"):
    source_path = Path(temp_dir) / name
    source_path.write_text("# Master Breakdown V2\n\nSynthetic intake material.\n")
    return source_path


class ImportIntakeTests(unittest.TestCase):
    def test_import_copies_file_and_records_pending_provenance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_valid_workspace(temp_dir)
            source_path = write_source_file(temp_dir)

            result = import_intake(
                workspace_dir,
                source_path,
                source_type="breakdown",
                notes="Second breakdown provided by user.",
                imported_on="2026-07-03",
            )

            destination = workspace_dir / "sources" / "intakes" / "master-breakdown-v2.md"
            self.assertEqual(Path(result["destination"]), destination)
            self.assertEqual(destination.read_text(), source_path.read_text())

            entries = read_manifest(workspace_dir)["source_intakes"]
            entry = entries[-1]
            self.assertEqual(entry["source_id"], result["source_id"])
            self.assertEqual(entry["source_type"], "breakdown")
            self.assertEqual(entry["path"], "sources/intakes/master-breakdown-v2.md")
            self.assertEqual(entry["imported_on"], "2026-07-03")
            self.assertEqual(entry["extraction_status"], "pending")
            self.assertEqual(entry["notes"], "Second breakdown provided by user.")

            validate_creator_workspace(workspace_dir)

    def test_source_types_route_to_mapped_destinations(self):
        expected_destinations = {
            "breakdown": "sources/intakes",
            "interview": "sources/intakes",
            "handoff": "sources/imports",
            "import": "sources/imports",
            "notes": "sources/notes",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_valid_workspace(temp_dir)
            for source_type, destination_dir in expected_destinations.items():
                source_path = write_source_file(temp_dir, name=f"{source_type}-material.md")

                import_intake(
                    workspace_dir,
                    source_path,
                    source_type=source_type,
                    notes=f"{source_type} material.",
                )

                destination = workspace_dir / destination_dir / f"{source_type}-material.md"
                self.assertTrue(destination.exists(), f"{source_type} did not land in {destination_dir}")

    def test_import_refuses_to_write_through_a_symlinked_destination(self):
        # A pre-planted broken symlink at the destination must not let the
        # copy write through it to a file outside the workspace.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_valid_workspace(temp_dir)
            outside_target = Path(temp_dir) / "outside-write-target.md"
            link_path = workspace_dir / "sources" / "intakes" / "evil.md"
            link_path.symlink_to(outside_target)
            source_path = write_source_file(temp_dir, name="evil.md")
            manifest_before = read_manifest(workspace_dir)

            with self.assertRaises(FileExistsError):
                import_intake(
                    workspace_dir,
                    source_path,
                    source_type="breakdown",
                    notes="Symlink probe.",
                )

            self.assertFalse(outside_target.exists())
            self.assertEqual(read_manifest(workspace_dir), manifest_before)

    def test_import_refuses_a_symlinked_intake_directory(self):
        # sources/notes itself resolving outside the workspace must fail the
        # containment check before any write happens.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_valid_workspace(temp_dir)
            outside_dir = Path(temp_dir) / "outside-notes"
            outside_dir.mkdir()
            notes_dir = workspace_dir / "sources" / "notes"
            notes_dir.rmdir()
            notes_dir.symlink_to(outside_dir)
            source_path = write_source_file(temp_dir, name="loose-notes.md")

            with self.assertRaises(ValueError) as ctx:
                import_intake(
                    workspace_dir,
                    source_path,
                    source_type="notes",
                    notes="Symlinked directory probe.",
                )

            self.assertIn("inside the workspace", str(ctx.exception))
            self.assertFalse((outside_dir / "loose-notes.md").exists())

    def test_auto_source_ids_are_deterministic_and_skip_collisions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_valid_workspace(temp_dir)

            # The example manifest already records source_luna_fit_breakdown_001.
            breakdown_result = import_intake(
                workspace_dir,
                write_source_file(temp_dir, name="second-breakdown.md"),
                source_type="breakdown",
                notes="Second breakdown.",
            )
            self.assertEqual(breakdown_result["source_id"], "source_luna_fit_breakdown_002")

            notes_result = import_intake(
                workspace_dir,
                write_source_file(temp_dir, name="loose-notes.md"),
                source_type="notes",
                notes="Loose notes.",
            )
            self.assertEqual(notes_result["source_id"], "source_luna_fit_notes_001")

            explicit_result = import_intake(
                workspace_dir,
                write_source_file(temp_dir, name="named-notes.md"),
                source_type="notes",
                notes="Named notes.",
                source_id="source_luna_fit_custom_id",
            )
            self.assertEqual(explicit_result["source_id"], "source_luna_fit_custom_id")

    def test_duplicate_destination_fails_before_any_write(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_valid_workspace(temp_dir)
            manifest_before = read_manifest(workspace_dir)
            source_path = write_source_file(temp_dir, name="luna-fit-breakdown.md")

            with self.assertRaises(FileExistsError):
                import_intake(
                    workspace_dir,
                    source_path,
                    source_type="breakdown",
                    notes="Collides with the declared intake.",
                )

            self.assertEqual(read_manifest(workspace_dir), manifest_before)

    def test_duplicate_source_id_fails_before_any_write(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_valid_workspace(temp_dir)
            manifest_before = read_manifest(workspace_dir)
            source_path = write_source_file(temp_dir)

            with self.assertRaises(ValueError):
                import_intake(
                    workspace_dir,
                    source_path,
                    source_type="breakdown",
                    notes="Reuses an existing id.",
                    source_id="source_luna_fit_breakdown_001",
                )

            self.assertEqual(read_manifest(workspace_dir), manifest_before)
            self.assertFalse(
                (workspace_dir / "sources" / "intakes" / "master-breakdown-v2.md").exists()
            )

    def test_missing_source_file_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_valid_workspace(temp_dir)

            with self.assertRaises(FileNotFoundError):
                import_intake(
                    workspace_dir,
                    Path(temp_dir) / "does-not-exist.md",
                    source_type="breakdown",
                    notes="Missing file.",
                )

    def test_impossible_calendar_date_fails_before_any_write(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_valid_workspace(temp_dir)
            manifest_before = read_manifest(workspace_dir)
            source_path = write_source_file(temp_dir)

            with self.assertRaises(ValidationError):
                import_intake(
                    workspace_dir,
                    source_path,
                    source_type="breakdown",
                    notes="Impossible date.",
                    imported_on="2026-99-99",
                )

            self.assertEqual(read_manifest(workspace_dir), manifest_before)
            self.assertFalse(
                (workspace_dir / "sources" / "intakes" / "master-breakdown-v2.md").exists()
            )

    def test_imported_on_defaults_to_today(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_valid_workspace(temp_dir)

            result = import_intake(
                workspace_dir,
                write_source_file(temp_dir),
                source_type="breakdown",
                notes="Defaults to today.",
            )

            entries = read_manifest(workspace_dir)["source_intakes"]
            entry = next(e for e in entries if e["source_id"] == result["source_id"])
            self.assertEqual(entry["imported_on"], datetime.date.today().isoformat())


class SetIntakeStatusTests(unittest.TestCase):
    def test_status_moves_forward_and_skipping_drafted_is_allowed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_valid_workspace(temp_dir)
            first = import_intake(
                workspace_dir,
                write_source_file(temp_dir, name="first.md"),
                source_type="breakdown",
                notes="First.",
            )
            second = import_intake(
                workspace_dir,
                write_source_file(temp_dir, name="second.md"),
                source_type="breakdown",
                notes="Second.",
            )

            set_intake_status(workspace_dir, first["source_id"], "drafted")
            set_intake_status(workspace_dir, first["source_id"], "reviewed")
            set_intake_status(workspace_dir, second["source_id"], "reviewed")

            entries = {e["source_id"]: e for e in read_manifest(workspace_dir)["source_intakes"]}
            self.assertEqual(entries[first["source_id"]]["extraction_status"], "reviewed")
            self.assertEqual(entries[second["source_id"]]["extraction_status"], "reviewed")

    def test_backward_and_same_status_moves_fail(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_valid_workspace(temp_dir)
            result = import_intake(
                workspace_dir,
                write_source_file(temp_dir),
                source_type="breakdown",
                notes="Forward-only.",
            )
            set_intake_status(workspace_dir, result["source_id"], "drafted")

            with self.assertRaises(ValueError):
                set_intake_status(workspace_dir, result["source_id"], "pending")
            with self.assertRaises(ValueError):
                set_intake_status(workspace_dir, result["source_id"], "drafted")

    def test_unknown_source_id_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_valid_workspace(temp_dir)

            with self.assertRaises(ValueError):
                set_intake_status(workspace_dir, "source_luna_fit_missing_001", "drafted")


class IntakeProvenanceValidationTests(unittest.TestCase):
    def test_validate_workspace_rejects_missing_intake_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_valid_workspace(temp_dir)
            (workspace_dir / "sources" / "intakes" / "luna-fit-breakdown.md").unlink()

            with self.assertRaises(FileNotFoundError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("sources/intakes/luna-fit-breakdown.md", str(ctx.exception))

    def append_intake_entry(self, workspace_dir, path_value):
        manifest = read_manifest(workspace_dir)
        manifest["source_intakes"].append(
            {
                "source_id": "source_luna_fit_escape_001",
                "source_type": "notes",
                "path": path_value,
                "imported_on": "2026-07-03",
                "extraction_status": "pending",
                "notes": "Escape probe.",
            }
        )
        (workspace_dir / "creator-workspace.json").write_text(
            json.dumps(manifest, indent=2) + "\n"
        )

    def remove_intake_entry(self, workspace_dir, source_id):
        manifest = read_manifest(workspace_dir)
        manifest["source_intakes"] = [
            entry for entry in manifest["source_intakes"] if entry["source_id"] != source_id
        ]
        (workspace_dir / "creator-workspace.json").write_text(
            json.dumps(manifest, indent=2) + "\n"
        )

    def test_validate_workspace_rejects_traversal_and_absolute_intake_paths(self):
        # Raw escapes are rejected by the schema pattern before the
        # behavioral containment check runs.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_valid_workspace(temp_dir)
            outside_file = Path(temp_dir) / "outside-intake.md"
            outside_file.write_text("# Outside the workspace\n")

            for bad_path in ("../../outside-intake.md", str(outside_file)):
                self.append_intake_entry(workspace_dir, bad_path)
                with self.subTest(path=bad_path):
                    with self.assertRaises(ValidationError):
                        validate_creator_workspace(workspace_dir)
                self.remove_intake_entry(workspace_dir, "source_luna_fit_escape_001")

    def test_validate_workspace_rejects_duplicate_intake_ids(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_valid_workspace(temp_dir)
            (workspace_dir / "sources" / "notes" / "extra-notes.md").write_text("# Notes\n")
            manifest = read_manifest(workspace_dir)
            first = manifest["source_intakes"][0]
            manifest["source_intakes"].append(
                {
                    "source_id": first["source_id"],
                    "source_type": "notes",
                    "path": "sources/notes/extra-notes.md",
                    "imported_on": "2026-07-03",
                    "extraction_status": "pending",
                    "notes": "Duplicate id probe.",
                }
            )
            (workspace_dir / "creator-workspace.json").write_text(
                json.dumps(manifest, indent=2) + "\n"
            )

            with self.assertRaises(ValueError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("Duplicate source intake ids", str(ctx.exception))
            self.assertIn(first["source_id"], str(ctx.exception))

    def test_validate_workspace_rejects_duplicate_intake_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_valid_workspace(temp_dir)
            manifest = read_manifest(workspace_dir)
            first = manifest["source_intakes"][0]
            manifest["source_intakes"].append(
                {
                    "source_id": "source_luna_fit_notes_009",
                    "source_type": "notes",
                    "path": first["path"],
                    "imported_on": "2026-07-03",
                    "extraction_status": "pending",
                    "notes": "Duplicate path probe.",
                }
            )
            (workspace_dir / "creator-workspace.json").write_text(
                json.dumps(manifest, indent=2) + "\n"
            )

            with self.assertRaises(ValueError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("Duplicate source intake paths", str(ctx.exception))
            self.assertIn(first["path"], str(ctx.exception))

    def test_validate_workspace_rejects_symlinked_intake_escaping_the_workspace(self):
        # A schema-conforming path that resolves outside the workspace via a
        # symlink is caught by the behavioral containment check.
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_valid_workspace(temp_dir)
            outside_file = Path(temp_dir) / "outside-intake.md"
            outside_file.write_text("# Outside the workspace\n")
            link_path = workspace_dir / "sources" / "intakes" / "escape-link.md"
            link_path.symlink_to(outside_file)
            self.append_intake_entry(workspace_dir, "sources/intakes/escape-link.md")

            with self.assertRaises(ValueError) as ctx:
                validate_creator_workspace(workspace_dir)
            self.assertIn("escape-link.md", str(ctx.exception))


class IntakeCliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "influencer_os", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_import_intake_and_set_intake_status_commands(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_valid_workspace(temp_dir)
            source_path = write_source_file(temp_dir)

            import_result = self.run_cli(
                "import-intake",
                str(source_path),
                "--creator-workspace",
                str(workspace_dir),
                "--source-type",
                "breakdown",
                "--notes",
                "CLI import.",
            )
            self.assertEqual(import_result.returncode, 0, import_result.stderr)
            self.assertIn("source_luna_fit_breakdown_002", import_result.stdout)
            self.assertIn("Next phase", import_result.stdout)

            status_result = self.run_cli(
                "set-intake-status",
                str(workspace_dir),
                "source_luna_fit_breakdown_002",
                "drafted",
            )
            self.assertEqual(status_result.returncode, 0, status_result.stderr)
            self.assertIn("pending -> drafted", status_result.stdout)

    def test_import_intake_command_reports_duplicate_destination(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = scaffold_valid_workspace(temp_dir)
            source_path = write_source_file(temp_dir, name="luna-fit-breakdown.md")

            result = self.run_cli(
                "import-intake",
                str(source_path),
                "--creator-workspace",
                str(workspace_dir),
                "--source-type",
                "breakdown",
                "--notes",
                "Duplicate destination.",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("error:", result.stderr)


if __name__ == "__main__":
    unittest.main()
