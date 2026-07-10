from abc import ABC,abstractmethod
class OCRClient(ABC):
    @abstractmethod
    def recognize(self,sanitized_reference):...
