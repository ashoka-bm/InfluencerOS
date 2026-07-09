import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from influencer_os.calendars import rebuild_calendar, validate_calendar
from influencer_os.creator_workspaces import init_creator
from influencer_os.validation import ValidationError, validate_file


ROOT = Path(__file__).resolve().parents[1]


def write_json(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + "\n")


def make_calendar_workspace(temp_dir):
    workspace_dir = init_creator(
        ROOT / "examples" / "creator-workspace.example.json",
        workspace_root=Path(temp_dir),
    )
    profile = json.loads((ROOT / "examples" / "creator-profile.example.json").read_text())
    write_json(workspace_dir / "creator-profile.json", profile)

    schedule = json.loads(
        (ROOT / "examples" / "creator-content-schedule.example.json").read_text()
    )
    slot = schedule["calendar_slots"][0]
    slot.update({
        "working_title": "The <script>alert('x')</script> desk reset",
        "platform": "instagram",
        "format_id": "format_short_form_video",
        "theme": "Make movement easier to start",
        "funnel_role": "awareness",
        "cta": "Save this reset",
        "production_note": "Demonstrate the movement from a seated position.",
        "week_label": "1",
    })
    write_json(workspace_dir / "content-schedule.json", schedule)
    return workspace_dir


class ContentCalendarTests(unittest.TestCase):
    def test_rebuild_calendar_projects_canonical_schedule_to_portable_html(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_calendar_workspace(temp_dir)

            result = rebuild_calendar(workspace_dir)

            calendar_path = workspace_dir / "boards" / "content-calendar.html"
            html = calendar_path.read_text()
            self.assertEqual(result["calendar_path"], calendar_path)
            self.assertEqual(result["post_count"], 1)
            self.assertIn("Luna Fit Content Calendar", html)
            self.assertIn("Instagram", html)
            self.assertIn("The &lt;script&gt;alert(", html)
            self.assertIn(")&lt;/script&gt; desk reset", html)
            self.assertNotIn("<script>alert('x')</script>", html)
            self.assertIn('name="influencer-os-source-digest"', html)

    def test_validate_calendar_rejects_a_stale_projection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_calendar_workspace(temp_dir)
            rebuild_calendar(workspace_dir)
            validate_calendar(workspace_dir)

            schedule_path = workspace_dir / "content-schedule.json"
            schedule = json.loads(schedule_path.read_text())
            schedule["calendar_slots"][0]["working_title"] = "A changed title"
            write_json(schedule_path, schedule)

            with self.assertRaisesRegex(ValidationError, "stale.*rebuild-calendar"):
                validate_calendar(workspace_dir)

    def test_validate_calendar_rejects_tampered_visible_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_calendar_workspace(temp_dir)
            rebuild_calendar(workspace_dir)
            calendar_path = workspace_dir / "boards" / "content-calendar.html"
            calendar_path.write_text(
                calendar_path.read_text().replace("Luna Fit Content Calendar", "Tampered Calendar")
            )

            with self.assertRaisesRegex(ValidationError, "does not match.*rebuild-calendar"):
                validate_calendar(workspace_dir)

    def test_month_boundary_slots_render_once(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_calendar_workspace(temp_dir)
            schedule_path = workspace_dir / "content-schedule.json"
            schedule = json.loads(schedule_path.read_text())
            first = schedule["calendar_slots"][0]
            first["target_date"] = "2026-07-31"
            second = dict(first)
            second["slot_id"] = "slot_luna_2026_08_01_followup"
            second["target_date"] = "2026-08-01"
            second["working_title"] = "August follow-up"
            schedule["calendar_slots"].append(second)
            write_json(schedule_path, schedule)

            rebuild_calendar(workspace_dir)

            html = (workspace_dir / "boards" / "content-calendar.html").read_text()
            self.assertEqual(html.count('class="post"'), 2)

    def test_enriched_calendar_slot_validates_against_canonical_schema(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_calendar_workspace(temp_dir)

            validate_file(
                "creator-content-schedule",
                workspace_dir / "content-schedule.json",
            )

    def test_cli_rebuilds_and_validates_calendar(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_dir = make_calendar_workspace(temp_dir)

            rebuild = subprocess.run(
                [sys.executable, "-m", "influencer_os", "rebuild-calendar", str(workspace_dir)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            validate = subprocess.run(
                [sys.executable, "-m", "influencer_os", "validate", "calendar", str(workspace_dir)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(rebuild.returncode, 0, rebuild.stderr)
            self.assertIn("Rebuilt content calendar: 1 scheduled post", rebuild.stdout)
            self.assertEqual(validate.returncode, 0, validate.stderr)
            self.assertIn("Validated content calendar", validate.stdout)


if __name__ == "__main__":
    unittest.main()
