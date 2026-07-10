import unittest
from app.student_recognition.image.backend import StdlibImageBackend
from app.student_recognition.image.image_types import ImageMatrix
from app.student_recognition.image.image_quality import assess_image_quality

def pattern(w=120,h=120): return ImageMatrix(w,h,tuple(20 if (x//5+y//5)%2 else 235 for y in range(h) for x in range(w)))

class TestImageBackendQuality(unittest.TestCase):
    def test_backend_crop_resize(self):
        b=StdlibImageBackend(); im=pattern(); self.assertEqual(b.crop(im,(0,0,20,30)).pixels.__len__(),600); self.assertEqual(b.resize(im,30,40).pixels.__len__(),1200)
    def test_quality_accepts_clean_synthetic(self): self.assertEqual(assess_image_quality(pattern()).status,"usable")
    def test_quality_rejects_too_small_image(self): self.assertEqual(assess_image_quality(pattern(20,20)).status,"quality_failed")
    def test_quality_flags_too_dark(self): self.assertEqual(assess_image_quality(ImageMatrix(120,120,(0,)*14400)).status,"quality_failed")
    def test_quality_flags_too_bright(self): self.assertIn(assess_image_quality(ImageMatrix(120,120,(255,)*14400)).status,("needs_review","quality_failed"))
    def test_quality_flags_low_contrast_and_blur(self):
        r=assess_image_quality(ImageMatrix(120,120,(128,)*14400)); self.assertEqual(r.status,"needs_review"); self.assertGreater(len(r.warnings),0)

if __name__=="__main__": unittest.main()
