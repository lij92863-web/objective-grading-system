"""Fixture truthfulness guard (SRE121-220).

This test loads the *committed* synthetic fixtures under
``tests/student_recognition/fixtures/synthetic/`` and re-derives, from the image
pixels alone, what each sheet *claims* in its ``.gt.json`` ground truth. For every
sheet and every question it checks the five mark states
(strong / weak / multi / erased / none) and the selected option match.

The re-derivation is a deliberately *minimal* fill-ratio probe:

* It only counts dark pixels (<170) and near-white pixels (>200) inside each
  bubble ROI (a fixed square around the known template centre).
* It uses FIXED, locally-defined thresholds -- it never calls any recognition
  routine and never references ``omr_policy`` thresholds (constitution boundary
  lock: no OMR, no recognition).
* Because the generator only ever applies *known* transformations, a faithful
  image must reproduce exactly the ground truth it ships with. This proves the
  fixtures are trustworthy, not hallucinated.
"""

import json
import unittest
from pathlib import Path

from app.student_recognition.synthetic.raster import read_png_bytes
from app.student_recognition.synthetic.template_profile import TemplateProfile

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = PROJECT_ROOT / "tests" / "student_recognition" / "fixtures" / "synthetic"

# --- Local, fixed probe thresholds (NOT omr_policy thresholds) --------------- #
_DARK = 170          # pixel intensity below this counts as "marked"
_WHITE = 200         # pixel intensity above this counts as "erase stripe"
_FILL_THRESHOLD = 0.15   # a bubble is "filled" if dark ratio exceeds this
_STRONG_MIN = 0.60       # a filled, non-striped bubble above this is "strong"
_ERASE_MIN = 3           # >= this many internal white pixels => "erased"


def _probe_option(pixels, width, height, cx, cy, r):
    """Return the dark-pixel ratio inside the bubble circle at (cx, cy)."""
    dark = 0
    total = 0
    r2 = r * r
    for dy in range(-r, r + 1):
        yy = cy + dy
        if yy < 0 or yy >= height:
            continue
        for dx in range(-r, r + 1):
            xx = cx + dx
            if xx < 0 or xx >= width:
                continue
            if dx * dx + dy * dy > r2:
                continue
            total += 1
            if pixels[(yy * width + xx) * 3] < _DARK:
                dark += 1
    return dark / total if total else 0.0


def _count_internal_white(pixels, width, height, cx, cy, r):
    """Count white pixels *sandwiched* between dark pixels 2px above and below.

    This detects an *erased* bubble: the white erase stripes sit inside the
    (residual) dark fill, so a white pixel there has dark above and below. It
    deliberately ignores white pixels at the bubble's background edge (the weak
    mark's surrounding annulus, or empty background), which have white -- not
    dark -- neighbours, so they are never counted. This keeps the probe a simple
    sanity check and not an OMR classifier.
    """
    r2 = r * r
    count = 0
    for dy in range(-r, r + 1):
        yy = cy + dy
        if yy - 2 < 0 or yy + 2 >= height:
            continue
        for dx in range(-r, r + 1):
            xx = cx + dx
            if xx < 0 or xx >= width:
                continue
            if dx * dx + dy * dy > r2:
                continue
            if pixels[(yy * width + xx) * 3] <= _WHITE:
                continue
            up = pixels[((yy - 2) * width + xx) * 3]
            down = pixels[((yy + 2) * width + xx) * 3]
            if up < _DARK and down < _DARK:
                count += 1
    return count


def _localize_bubble(pixels, width, height, cx0, cy0, r, search):
    """Find the actual bubble centre near (cx0, cy0).

    Because geometric perturbations (shift / skew / rotate) displace the bubble,
    we scan a small window and pick the offset with the most dark pixels. This is
    a *localisation* step for the fill-ratio probe -- it never recognises content,
    it only re-centres the ROI on the known bubble so background whitespace is not
    mistaken for an erase stripe. The search window (<= perturbation magnitude)
    is far smaller than the inter-bubble spacing, so it cannot jump to a neighbour.
    """
    best_dark = -1.0
    best = (cx0, cy0)
    for dy in range(-search, search + 1):
        for dx in range(-search, search + 1):
            cx = cx0 + dx
            cy = cy0 + dy
            ratio = _probe_option(pixels, width, height, cx, cy, r)
            dark = ratio * (r * r)  # proportional to dark-pixel area
            if dark > best_dark:
                best_dark = dark
                best = (cx, cy)
    return best


def _derive_question(pixels, width, height, tp, q, labels):
    """Re-derive (mark_type, filled_option_indices) for question ``q``."""
    r = int(tp.bubble_grid["bubble_radius"])
    cols = int(tp.bubble_grid["cols"])
    search = 8  # >= max perturbation displacement (shift 5 / skew ~6 / rotate ~5)
    filled = []
    for o in range(cols):
        cx0, cy0 = tp.cell_center(q, o)
        cx, cy = _localize_bubble(pixels, width, height, cx0, cy0, r, search)
        ratio = _probe_option(pixels, width, height, cx, cy, r)
        if ratio > _FILL_THRESHOLD:
            internal_white = _count_internal_white(pixels, width, height, cx, cy, r)
            filled.append((o, ratio, internal_white))

    if not filled:
        return "none", []
    if len(filled) >= 2:
        return "multi", [o for (o, _, _) in filled]
    o, ratio, internal_white = filled[0]
    if internal_white >= _ERASE_MIN:
        return "erased", [o]
    if ratio >= _STRONG_MIN:
        return "strong", [o]
    return "weak", [o]


class TestSyntheticTruthfulnessGuard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not FIXTURE_DIR.exists():
            raise unittest.SkipTest(
                f"synthetic fixtures missing at {FIXTURE_DIR}; "
                "run scripts/student_recognition/generate_synthetic_corpus.py first"
            )
        tp_dict = json.loads((FIXTURE_DIR / "template_profile.json").read_text(encoding="utf-8"))
        cls.template = TemplateProfile.from_dict(tp_dict)
        cls.manifest = json.loads((FIXTURE_DIR / "corpus_manifest.json").read_text(encoding="utf-8"))
        cls.labels = list(cls.template.bubble_grid["option_labels"])

    def test_manifest_lists_all_sheets(self):
        self.assertGreaterEqual(len(self.manifest["sheets"]), 12)
        for entry in self.manifest["sheets"]:
            self.assertTrue((FIXTURE_DIR / entry["png"]).exists())
            self.assertTrue((FIXTURE_DIR / entry["gt"]).exists())

    def test_every_sheet_matches_its_ground_truth(self):
        failures = []
        for entry in self.manifest["sheets"]:
            sheet_id = entry["sheet_id"]
            gt = json.loads((FIXTURE_DIR / entry["gt"]).read_text(encoding="utf-8"))
            width, _height, pixels = read_png_bytes(
                (FIXTURE_DIR / entry["png"]).read_bytes()
            )
            for ans in gt["answers"]:
                q = ans["question"]
                derived, filled_idxs = _derive_question(pixels, width, _height, self.template, q, self.labels)
                expected_mark = ans["mark_type"]
                if derived != expected_mark:
                    failures.append(
                        f"{sheet_id} q{q}: derived={derived!r} expected={expected_mark!r}"
                    )
                    continue
                # selected-option consistency
                if expected_mark == "none":
                    if ans["selected"] is not None:
                        failures.append(f"{sheet_id} q{q}: none but selected={ans['selected']!r}")
                elif expected_mark == "multi":
                    primary = self.labels.index(ans["selected"])
                    if primary not in filled_idxs:
                        failures.append(
                            f"{sheet_id} q{q}: multi primary {ans['selected']} not in filled {filled_idxs}"
                        )
                else:  # strong / weak / erased -> exactly one filled bubble
                    selected_idx = self.labels.index(ans["selected"])
                    if filled_idxs != [selected_idx]:
                        failures.append(
                            f"{sheet_id} q{q}: {expected_mark} selected {ans['selected']} "
                            f"but filled idxs {filled_idxs}"
                        )
        self.assertEqual(
            failures,
            [],
            f"truthfulness mismatches ({len(failures)}):\n" + "\n".join(failures),
        )


if __name__ == "__main__":
    unittest.main()
