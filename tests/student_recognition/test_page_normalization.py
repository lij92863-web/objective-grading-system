import unittest
from app.student_recognition.image.image_types import ImageMatrix
from app.student_recognition.image.page_locator import locate_page
from app.student_recognition.image.page_normalizer import normalize_page

def page(w=240,h=360): return ImageMatrix(w,h,tuple(0 if x in (10,w-11) or y in (10,h-11) else 255 for y in range(h) for x in range(w)))
class TestPageNormalization(unittest.TestCase):
    def test_page_locator_accepts_clean_synthetic(self): self.assertEqual(locate_page(page(),240,360).status,"page_located")
    def test_page_locator_handles_shifted_synthetic(self): self.assertEqual(locate_page(page(240,360),240,360).confidence,1)
    def test_page_locator_fails_closed_on_missing_page(self): self.assertEqual(locate_page(ImageMatrix(240,360,(255,)*86400),240,360).status,"page_location_failed")
    def test_page_locator_rejects_bad_aspect_ratio(self): self.assertEqual(locate_page(page(360,240),240,360).status,"page_location_failed")
    def test_normalizer_outputs_expected_size(self):
        im=page(); out=normalize_page(im,locate_page(im,240,360),120,180); self.assertEqual((out.image.width,out.image.height),(120,180))
    def test_page_location_failed_blocks_roi_mapping(self):
        im=ImageMatrix(240,360,(255,)*86400)
        with self.assertRaises(ValueError): normalize_page(im,locate_page(im,240,360),240,360)
if __name__=="__main__": unittest.main()
