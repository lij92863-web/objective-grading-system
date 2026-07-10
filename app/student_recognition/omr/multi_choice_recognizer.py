from app.student_recognition.errors.error_codes import ErrorCode
from .ambiguity_detector import in_ambiguous_band
from .omr_candidate import RecognizedAnswerCandidate
from .omr_policy import DEFAULT_OMR_POLICY
def recognize_multi_choice(question_no,metrics,evidence=(),policy=DEFAULT_OMR_POLICY):
    if any(m.classification in ("weak","erased","dirty","ambiguous") or in_ambiguous_band(m.mark_score,policy) for m in metrics): return RecognizedAnswerCandidate(question_no,(),"needs_review",(ErrorCode.OMR_AMBIGUOUS_MULTI_CHOICE,),tuple(evidence))
    selected=tuple(sorted(m.option for m in metrics if m.classification=="strong" and m.mark_score>=policy.selected_threshold))
    if not selected:return RecognizedAnswerCandidate(question_no,(),"blank_candidate",(ErrorCode.OMR_EMPTY_MARK,),tuple(evidence))
    return RecognizedAnswerCandidate(question_no,selected,"auto_candidate",(),tuple(evidence))
