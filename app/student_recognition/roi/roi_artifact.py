from dataclasses import dataclass, field
from typing import Dict
@dataclass(frozen=True)
class ROICropArtifact:
    question_no:int; option_label:str; path:str; x0:int;y0:int;x1:int;y1:int;width:int;height:int
    image_hash: str = ""
    template_ref: Dict[str, object] = field(default_factory=dict)
