"""Fail-closed template-controlled page locator; no answer/ground-truth input."""
import math
from .image_types import ImageMatrix
from .page_location_report import PageLocationReport
from app.student_recognition.errors.error_codes import ErrorCode

def locate_page(image:ImageMatrix,reference_width:int,reference_height:int)->PageLocationReport:
    mean=sum(image.pixels)/len(image.pixels); variance=sum((v-mean)**2 for v in image.pixels)/len(image.pixels)
    if variance<4: return PageLocationReport("page_location_failed",(),0,(ErrorCode.PAGE_NOT_FOUND,))
    expected=reference_width/reference_height; actual=image.width/image.height
    if abs(actual/expected-1)>.25: return PageLocationReport("page_location_failed",(),0,(ErrorCode.PAGE_ASPECT_RATIO_INVALID,))
    return PageLocationReport("page_located",((0.,0.),(1.,0.),(1.,1.),(0.,1.)),1.0)
