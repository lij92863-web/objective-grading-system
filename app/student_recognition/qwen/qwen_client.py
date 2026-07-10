from abc import ABC,abstractmethod
class QwenClient(ABC):
    @abstractmethod
    def propose(self,sanitized_prompt):...
