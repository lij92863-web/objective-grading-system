from .ocr_client import OCRClient
from .ocr_candidate import OCRCandidate
class FakeOCRClient(OCRClient):
    def __init__(self,text='',confidence=0):self.text=text;self.confidence=confidence
    def recognize(self,sanitized_reference):return OCRCandidate(self.text,self.confidence)
