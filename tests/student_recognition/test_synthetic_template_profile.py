"""Tests for the synthetic TemplateProfile model and validation."""

import copy
import unittest

from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.synthetic.template_profile import (
    SCHEMA_VERSION,
    SyntheticProfileError,
    TemplateProfile,
    build_default_template,
)


class TestTemplateProfileRoundTrip(unittest.TestCase):
    def test_default_template_has_all_fields(self):
        tp = build_default_template()
        d = tp.to_dict()
        for key in (
            "schema_version",
            "template_id",
            "template_version",
            "canvas",
            "bubble_grid",
            "questions",
            "identity_roi",
        ):
            self.assertIn(key, d, f"missing field {key}")
        self.assertEqual(d["schema_version"], SCHEMA_VERSION)
        self.assertEqual(d["canvas"]["width"], 240)
        self.assertEqual(d["bubble_grid"]["option_labels"], ["A", "B", "C", "D"])
        self.assertEqual(d["questions"], d["bubble_grid"]["rows"])

    def test_to_dict_from_dict_roundtrip(self):
        tp = build_default_template()
        tp2 = TemplateProfile.from_dict(tp.to_dict())
        self.assertEqual(tp.to_dict(), tp2.to_dict())


class TestTemplateProfileValidation(unittest.TestCase):
    def test_missing_bubble_grid_raises_with_error_code(self):
        d = build_default_template().to_dict()
        del d["bubble_grid"]
        with self.assertRaises(SyntheticProfileError) as ctx:
            TemplateProfile.from_dict(d)
        err = ctx.exception
        self.assertIsInstance(err.error_code, ErrorCode)
        self.assertEqual(err.error_code, ErrorCode.TEMPLATE_OPTION_CELL_MISSING)

    def test_missing_canvas_raises(self):
        d = build_default_template().to_dict()
        del d["canvas"]
        with self.assertRaises(SyntheticProfileError) as ctx:
            TemplateProfile.from_dict(d)
        self.assertEqual(ctx.exception.error_code, ErrorCode.TEMPLATE_MISSING)

    def test_missing_identity_roi_raises(self):
        d = build_default_template().to_dict()
        del d["identity_roi"]
        with self.assertRaises(SyntheticProfileError) as ctx:
            TemplateProfile.from_dict(d)
        self.assertEqual(ctx.exception.error_code, ErrorCode.TEMPLATE_IDENTITY_ROI_MISSING)

    def test_schema_version_mismatch_raises(self):
        d = build_default_template().to_dict()
        d["schema_version"] = 999
        with self.assertRaises(SyntheticProfileError) as ctx:
            TemplateProfile.from_dict(d)
        self.assertEqual(ctx.exception.error_code, ErrorCode.TEMPLATE_VERSION_MISMATCH)

    def test_synthetic_profile_error_is_value_error(self):
        # So ``except ValueError`` callers still catch it (constitution B6 friendly).
        d = build_default_template().to_dict()
        del d["bubble_grid"]
        with self.assertRaises(ValueError):
            TemplateProfile.from_dict(d)


class TestTemplateProfileGeometry(unittest.TestCase):
    def test_cell_center_layout(self):
        tp = build_default_template()
        g = tp.bubble_grid
        # question 0, option 0
        x0, y0 = tp.cell_center(0, 0)
        self.assertEqual(x0, g["origin_x"] + g["cell_w"] // 2)
        self.assertEqual(y0, g["origin_y"] + g["cell_h"] // 2)
        # question 1, option 2 is offset by one row and two columns
        x1, y1 = tp.cell_center(1, 2)
        self.assertEqual(x1, g["origin_x"] + 2 * g["cell_w"] + g["cell_w"] // 2)
        self.assertEqual(y1, g["origin_y"] + 1 * g["cell_h"] + g["cell_h"] // 2)

    def test_option_index_lookup(self):
        tp = build_default_template()
        self.assertEqual(tp.option_index("A"), 0)
        self.assertEqual(tp.option_index("D"), 3)


if __name__ == "__main__":
    unittest.main()
