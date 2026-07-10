from dataclasses import dataclass
from typing import Tuple
from app.student_recognition.errors.error_codes import ErrorCode
@dataclass(frozen=True)
class RecognizedAnswerCandidate:
    question_no:int; selected:Tuple[str,...]; status:str; reason_codes:Tuple[ErrorCode,...]; evidence:Tuple[str,...]=()
    @property
    def is_final_answer(self): return False
