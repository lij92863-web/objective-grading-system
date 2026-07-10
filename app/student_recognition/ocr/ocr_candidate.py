from dataclasses import dataclass
@dataclass(frozen=True)
class OCRCandidate:
    text:str; confidence:float; status:str='needs_review'; source:str='fake_ocr'
    @property
    def direct_accepted(self):return False
