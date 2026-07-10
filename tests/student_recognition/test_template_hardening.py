"""SRE945 protocol fail-closed hardening."""
import tempfile
import unittest
from pathlib import Path
from app.student_recognition.template.anchor_layout import expand_block
from app.student_recognition.template.template_profile import TemplateProfile
from app.student_recognition.template.template_store import DEFAULT_TEMPLATES_DIR, TemplateStore
from app.student_recognition.template.template_validator import TemplateValidationError
from tests.student_recognition.test_template_profile_schema import _valid_dict

class TestTemplateHardening(unittest.TestCase):
    def test_anchor_grid_out_of_bounds_is_invalid_not_clamped(self):
        d=_valid_dict(); d["pages"][0]["anchors"][0]["x"]=.99
        with self.assertRaises(TemplateValidationError): TemplateProfile.from_dict(d)
    def test_four_corner_out_of_bounds_is_invalid_not_clamped(self):
        d = _valid_dict()
        d["pages"][0]["anchors"] = [
            {"anchor_id": key, "x": x, "y": y}
            for key, x, y in (
                ("top_left", 0, 0), ("top_right", 0, 0),
                ("bottom_right", 0, 1), ("bottom_left", 0, 1),
            )
        ]
        block = d["pages"][0]["question_blocks"][0]
        block.update({"anchor_id": "top_left", "anchor_mode": "four_corner"})
        with self.assertRaises(TemplateValidationError):
            TemplateProfile.from_dict(d)
    def test_blank_roi_out_of_bounds_is_invalid_not_clamped(self):
        d=_valid_dict(); d["pages"][0]["question_blocks"][0]["blank_roi"]["dy"]=2
        with self.assertRaises(TemplateValidationError): TemplateProfile.from_dict(d)
    def test_template_rejects_invalid_x_range(self):
        d = _valid_dict(); d["coordinate_system"]["x_range"] = [0, 2]
        with self.assertRaises(TemplateValidationError): TemplateProfile.from_dict(d)

    def test_template_rejects_invalid_y_range(self):
        d = _valid_dict(); d["coordinate_system"]["y_range"] = [0, .9]
        with self.assertRaises(TemplateValidationError): TemplateProfile.from_dict(d)

    def test_coordinate_ranges_must_be_present(self):
        for key in ("x_range","y_range"):
            d=_valid_dict(); del d["coordinate_system"][key]
            with self.assertRaises(TemplateValidationError): TemplateProfile.from_dict(d)
    def test_profile_returns_defensive_copies(self):
        source=_valid_dict(); p=TemplateProfile.from_dict(source); source["pages"][0]["identity"].clear()
        p.to_dict()["pages"][0]["identity"].clear(); p.get_page(1)["identity"].clear()
        p.get_question_block(1)["options"].clear(); p.get_option_cells(1)[0].roi["x"]=.9
        p.get_identity_roi()["x"]=.9
        self.assertEqual(len(p.get_option_cells(1)),4); self.assertNotEqual(p.get_identity_roi()["x"],.9)

    def test_profile_get_page_returns_defensive_copy(self):
        profile = TemplateProfile.from_dict(_valid_dict())
        page = profile.get_page(1)
        page["identity"].clear()
        self.assertTrue(profile.get_page(1)["identity"])

    def test_profile_get_page_anchors_returns_defensive_copy(self):
        profile = TemplateProfile.from_dict(_valid_dict())
        anchors = profile.get_page_anchors(1)
        anchors[0]["x"] = .99
        self.assertNotEqual(profile.get_page_anchors(1)[0]["x"], .99)
    def test_template_store_default_dir_is_runtime_data_not_tests_fixtures(self):
        s=str(DEFAULT_TEMPLATES_DIR).replace("\\","/"); self.assertIn("data/student_recognition/templates",s); self.assertNotIn("tests/student_recognition/fixtures",s)
    def test_template_store_tests_use_tempdir(self):
        with tempfile.TemporaryDirectory() as tmp: self.assertEqual(TemplateStore(tmp).directory,Path(tmp))

if __name__=="__main__": unittest.main()
