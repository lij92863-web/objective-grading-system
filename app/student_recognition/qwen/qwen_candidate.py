from dataclasses import dataclass
@dataclass(frozen=True)
class QwenCandidate:
    answer:str;confidence:float;reason:str='';status:str='needs_review';source:str='fake_qwen'
    @property
    def direct_accepted(self):return False
