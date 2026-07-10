from dataclasses import dataclass
from typing import Optional
@dataclass(frozen=True)
class IdentityCandidate:
    student_id:Optional[str]; name:Optional[str]; source:str; confidence:float; raw_text:str
