from dataclasses import dataclass
from typing import Optional,Tuple
from app.student_recognition.errors.error_codes import ErrorCode
@dataclass(frozen=True)
class PageLocationReport:
    status:str; corners:Tuple[Tuple[float,float],...]; confidence:float; reason_codes:Tuple[ErrorCode,...]=(); normalized_image_path:Optional[str]=None; debug_overlay_path:Optional[str]=None
    def to_dict(self): return {"status":self.status,"corners":[list(x) for x in self.corners],"confidence":self.confidence,"reason_codes":[x.value for x in self.reason_codes],"normalized_image_path":self.normalized_image_path,"debug_overlay_path":self.debug_overlay_path}
