"""SRE945 -- end-to-end integration + frozen-OMR contract test.

Pipeline under test (mirrors the CLI):
    SyntheticSheetGenerator -> Calibrator.calibrate_from_synthetic
    -> TemplateStore.save -> TemplateStore.load -> TemplateProfile.from_dict
    -> get_option_cells / get_identity_roi / get_blank_roi

It also asserts the *consumption contract*: OMR consumes normalized ROIs from the
TemplateProfile and must NOT recompute coordinates itself (constitution §10).
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from app.student_recognition.synthetic.template_profile import build_default_template
from app.student_recognition.template_builder.calibrator import Calibrator
from app.student_recognition.template.template_profile import TemplateProfile
from app.student_recognition.template.template_store import TemplateStore

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = REPO_ROOT / "scripts" / "student_recognition" / "build_template.py"


def _run_cli(out_dir: Path) -> Path:
    result = subprocess.run(
        [sys.executable, str(CLI), "--template-id", "objective_sheet_v1", "--out-dir", str(out_dir)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(f"CLI failed: {result.stdout}\n{result.stderr}")
    return out_dir


class TestTemplateIntegration(unittest.TestCase):
    def test_cli_calibrate_store_reload_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            _run_cli(out)
            # The store must have written exactly one template JSON + a blank PNG.
            jsons = list(out.glob("*.json"))
            self.assertEqual(len(jsons), 1)
            self.assertTrue((out / "blank-objective_sheet_v1.png").exists())

            store = TemplateStore(out)
            path, tid, ver = store.list_templates()[0]
            self.assertEqual(tid, "objective_sheet_v1")
            self.assertEqual(ver, 1)

            profile = store.load(path)
            self.assertIsInstance(profile, TemplateProfile)
            # Frozen consumer interface resolves the full grid.
            self.assertEqual(len(profile.get_option_cells(1)), 4)
            self.assertEqual(profile.question_count(), 12)
            self.assertIn("x", profile.get_identity_roi())

    def test_normalized_coords_map_back_to_synthetic_pixels(self):
        synth = build_default_template()
        cw = int(synth.canvas["width"])
        ch = int(synth.canvas["height"])
        profile = Calibrator().calibrate_from_synthetic(synth, "objective_sheet_v1")
        for q in range(1, synth.questions + 1):
            for o, label in enumerate(synth.bubble_grid["option_labels"]):
                px, py = synth.cell_center(q - 1, o)
                cell = next(
                    c for c in profile.get_option_cells(q) if c.option_label == label
                )
                nx = cell.roi["x"] + cell.roi["w"] / 2.0
                ny = cell.roi["y"] + cell.roi["h"] / 2.0
                self.assertAlmostEqual(nx, px / cw, delta=1e-6)
                self.assertAlmostEqual(ny, py / ch, delta=1e-6)

    def test_frozen_contract_returns_normalized_rois(self):
        synth = build_default_template()
        profile = Calibrator().calibrate_from_synthetic(synth, "objective_sheet_v1")

        # get_option_cells -> normalized {x,y,w,h} per option.
        cells = profile.get_option_cells(1)
        self.assertEqual(len(cells), 4)
        for cell in cells:
            roi = cell.roi
            for key in ("x", "y", "w", "h"):
                self.assertIn(key, roi)
                self.assertGreaterEqual(roi[key], 0.0)
                self.assertLessEqual(roi[key], 1.0)

        # get_identity_roi -> normalized roi.
        id_roi = profile.get_identity_roi()
        self.assertIn("w", id_roi)

        # get_blank_roi -> normalized roi for a question.
        blank = profile.get_blank_roi(1)
        self.assertIsNotNone(blank)
        self.assertIn("h", blank)


if __name__ == "__main__":
    unittest.main()
