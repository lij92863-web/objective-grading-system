from app.student_recognition.errors.error_codes import ErrorCode
from .omr_candidate import RecognizedAnswerCandidate
from .omr_policy import DEFAULT_OMR_POLICY
def recognize_single_choice(question_no,metrics,evidence=(),policy=DEFAULT_OMR_POLICY):
    strong=[m for m in metrics if m.classification=="strong"]
    if len(strong)>1: return RecognizedAnswerCandidate(question_no,(),"needs_review",(ErrorCode.OMR_MULTI_MARK_SINGLE_CHOICE,),tuple(evidence))
    if any(m.classification in ("weak","erased","dirty","ambiguous") for m in metrics): return RecognizedAnswerCandidate(question_no,(),"needs_review",(ErrorCode.OMR_LOW_CONFIDENCE,),tuple(evidence))
    ranked=sorted(metrics,key=lambda m:m.mark_score,reverse=True)
    if not ranked or ranked[0].classification=="blank": return RecognizedAnswerCandidate(question_no,(),"blank_candidate",(ErrorCode.OMR_EMPTY_MARK,),tuple(evidence))
    second=ranked[1].mark_score if len(ranked)>1 else 0
    if ranked[0].mark_score>=policy.selected_threshold and ranked[0].mark_score-second>=policy.single_choice_margin and second<policy.weak_threshold: return RecognizedAnswerCandidate(question_no,(ranked[0].option,),"auto_candidate",(),tuple(evidence))
    return RecognizedAnswerCandidate(question_no,(),"needs_review",(ErrorCode.OMR_LOW_CONFIDENCE,),tuple(evidence))
