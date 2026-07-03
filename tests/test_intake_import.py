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
        ("reference-library.example.json", "references/reference-library.json"),
    ]:
        (workspace_dir / relative_path).write_text((ROOT / "examples" / example_name).read_text())
    # The example manifest declares this intake file; place it so provenance resolves.
    (workspace_dir / "sources" / "intakes" / "luna-fit-breakdown.md").write_text(
        EXAMPLE_BREAKDOWN.read_text()
    )
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
