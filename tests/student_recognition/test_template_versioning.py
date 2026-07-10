"""SRE945 §15.6 -- versioning / TemplateStore conflict tests."""

import tempfile
import unittest
from pathlib import Path

from app.student_recognition.errors.error_codes import ErrorCode
from app.student_recognition.template.template_profile import (
    SCHEMA_VERSION,
    TemplateProfile,
    TemplateRef,
)
from app.student_recognition.template.template_store import (
    TemplateStore,
    TemplateStoreError,
)


def _valid_profile(template_id="objective_sheet_v1", version=1):
    data = {
        "schema_version": SCHEMA_VERSION,
        "template_id": template_id,
        "template_name": "测试模板",
        "template_version": version,
        "coordinate_system": {
            "type": "normalized",
            "origin": "top_left",
            "unit": "ratio",
            "x_range": [0.0, 1.0],
            "y_range": [0.0, 1.0],
        },
        "reference_canvas": {"width": 240, "height": 360, "source": "synthetic:synthetic-v1"},
        "pages": [
            {
                "template_page_id": "page_1",
                "page_no": 1,
                "anchors": [{"anchor_id": "choice_block_top_left", "x": 0.15, "y": 0.1333}],
                "identity": {
                    "combined_identity_roi": {"x": 0.0833, "y": 0.0333, "w": 0.8333, "h": 0.0667}
                },
                "question_blocks": [
                    {
                        "block_id": "choice_block_1",
                        "question_type": "single_choice",
                        "question_range": [1, 12],
                        "options": ["A", "B", "C", "D"],
                        "anchor_id": "choice_block_top_left",
                        "layout": {
                            "row_gap": 0.0722,
                            "option_gap": 0.1833,
                            "cell_w": 0.1833,
                            "cell_h": 0.0722,
                            "columns": 1,
                        },
                        "blank_roi": {"dx": 0.0, "dy": 0.0, "w": 0.1833, "h": 0.03},
                    }
                ],
                "blank_rois": [],
            }
        ],
    }
    return TemplateProfile.from_dict(data)


class TestTemplateVersioning(unittest.TestCase):
    def test_template_update_increments_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = TemplateStore(Path(tmp))
            v1 = _valid_profile(version=1)
            store.save(v1)
            # Re-saving the SAME version must be rejected.
            with self.assertRaises(TemplateStoreError) as ctx:
                store.save(v1)
            self.assertEqual(ctx.exception.error_code, ErrorCode.TEMPLATE_VERSION_CONFLICT)
            # A bumped version is accepted.
            v2 = _valid_profile(version=2)
            path = store.save(v2)
            self.assertTrue(Path(path).exists())

    def test_template_old_version_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = TemplateStore(Path(tmp))
            store.save(_valid_profile(version=1))
            listed = store.list_templates()
            self.assertEqual(len(listed), 1)
            self.assertEqual(listed[0][2], 1)
            # There is deliberately no overwrite escape hatch.
            with self.assertRaises(TemplateStoreError) as ctx:
                store.save(_valid_profile(version=1))
            self.assertEqual(ctx.exception.error_code, ErrorCode.TEMPLATE_VERSION_CONFLICT)
            self.assertEqual(len(store.list_templates()), 1)

    def test_template_ref_contains_id_and_version(self):
        ref = TemplateRef(template_id="objective_sheet_v1", template_version=3)
        d = ref.to_dict()
        self.assertEqual(d["template_id"], "objective_sheet_v1")
        self.assertEqual(d["template_version"], 3)
        restored = TemplateRef.from_dict(d)
        self.assertEqual(restored.template_id, "objective_sheet_v1")
        self.assertEqual(restored.template_version, 3)


if __name__ == "__main__":
    unittest.main()
