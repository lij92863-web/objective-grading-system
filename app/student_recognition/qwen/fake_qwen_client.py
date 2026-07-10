from .qwen_client import QwenClient
from .qwen_candidate import QwenCandidate
class FakeQwenClient(QwenClient):
    def __init__(self,answer='',confidence=0,reason='fake'):self.answer=answer;self.confidence=confidence;self.reason=reason
    def propose(self,sanitized_prompt):return QwenCandidate(self.answer,self.confidence,self.reason)
