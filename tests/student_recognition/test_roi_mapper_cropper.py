import tempfile,unittest
from app.student_recognition.image.image_types import ImageMatrix
from app.student_recognition.image.page_location_report import PageLocationReport
from app.student_recognition.image.page_normalizer import NormalizedPageImage
from app.student_recognition.roi.roi_mapper import map_normalized_roi
from app.student_recognition.roi.roi_cropper import crop_option_cells
from app.student_recognition.template.template_profile import TemplateProfile
from tests.student_recognition.test_template_profile_schema import _valid_dict
class TestROIMapperCropper(unittest.TestCase):
    def test_roi_mapper_converts_normalized_to_pixel(self): self.assertEqual(map_normalized_roi({"x":.1,"y":.2,"w":.3,"h":.4},100,200).__dict__,{"x0":10,"y0":40,"x1":40,"y1":120})
    def test_roi_mapper_rounding_is_stable(self): self.assertEqual(map_normalized_roi({"x":.101,"y":.101,"w":.101,"h":.101},100,100).__dict__,{"x0":10,"y0":10,"x1":21,"y1":21})
    def test_roi_mapper_rejects_out_of_bounds(self):
        with self.assertRaises(ValueError): map_normalized_roi({"x":.9,"y":0,"w":.2,"h":.1},100,100)
    def test_roi_cropper_outputs_crop_artifacts(self):
        p=TemplateProfile.from_dict(_valid_dict()); im=ImageMatrix(240,360,(255,)*(240*360)); page=NormalizedPageImage(im,PageLocationReport("page_located",((0,0),)*4,1))
        with tempfile.TemporaryDirectory() as tmp:
            arts=crop_option_cells(page,p,tmp); self.assertEqual(len(arts),48); self.assertTrue(all(__import__('pathlib').Path(a.path).exists() for a in arts))
    def test_roi_cropper_rejects_failed_page(self):
        p=TemplateProfile.from_dict(_valid_dict()); im=ImageMatrix(240,360,(255,)*(240*360)); page=NormalizedPageImage(im,PageLocationReport("page_location_failed",(),0))
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError): crop_option_cells(page,p,tmp)
if __name__=="__main__": unittest.main()
