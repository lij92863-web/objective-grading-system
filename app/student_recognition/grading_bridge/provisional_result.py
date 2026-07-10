from dataclasses import dataclass
@dataclass(frozen=True)
class ProvisionalResult: exam_id:str; status:str='provisional'; official:bool=False
