import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "skills" / "create-lead-magnet" / "assets"


class LeadMagnetAssetCliTests(unittest.TestCase):
    def run_node(self, script, *args, env=None):
        return subprocess.run(
            ["node", str(ASSETS / script), *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    def browser_stub_env(self, temp_dir):
        temp_path = Path(temp_dir)
        chrome = temp_path / "chrome"
        chrome.write_text("browser boundary fixture\n")
        module = temp_path / "puppeteer-stub.mjs"
        module.write_text(
            """
import { writeFile } from 'node:fs/promises';
export default {
  launch: async () => ({
    newPage: async () => ({
      goto: async () => {},
      evaluate: async () => ({ width: 200, height: 200 }),
      pdf: async ({ path }) => writeFile(path, 'pdf fixture'),
      setViewport: async () => {},
      setContent: async () => {},
      screenshot: async ({ path }) => writeFile(path, 'png fixture'),
    }),
    close: async () => {},
  }),
};
""".strip()
            + "\n"
        )
        return {
            **os.environ,
            "CHROME_PATH": str(chrome),
            "PUPPETEER_MODULE": str(module),
        }

    def test_crop_requires_an_explicit_valid_rectangle_before_loading_browser(self):
        result = self.run_node("crop-portrait.mjs", "plate.png", "out.png", "0", "0", "0", "100")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("crop rectangle", result.stderr)
        self.assertNotIn("puppeteer-core", result.stderr)

    def test_render_requires_explicit_paths_before_loading_browser(self):
        result = self.run_node("render.mjs")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage:", result.stderr)
        self.assertNotIn("puppeteer-core", result.stderr)

    def test_crop_writes_output_for_a_valid_reviewed_rectangle(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            plate = temp_path / "plate.png"
            output = temp_path / "portrait.png"
            plate.write_bytes(b"identity plate fixture")

            result = self.run_node(
                "crop-portrait.mjs",
                str(plate),
                str(output),
                "10",
                "20",
                "80",
                "90",
                env=self.browser_stub_env(temp_dir),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_text(), "png fixture")

    def test_render_writes_pdf_for_valid_explicit_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source = temp_path / "index.html"
            output = temp_path / "lead-magnet.pdf"
            source.write_text("<!doctype html><title>Fixture</title>\n")

            result = self.run_node(
                "render.mjs",
                str(source),
                str(output),
                env=self.browser_stub_env(temp_dir),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_text(), "pdf fixture")


if __name__ == "__main__":
    unittest.main()
