from app.student_recognition.errors.error_codes import ErrorCode
from .grading_gate import ExamOfficialReportGate,GateResult,TeacherConfirmedSubmission
class ClassReportGate:
    def try_build_input(self,submissions,exam_id,answer_key_accepted=False,grading_config_confirmed=False,allow_missing=False,expected_count=None):
        if not answer_key_accepted:return GateResult(False,ErrorCode.GRADING_ANSWER_KEY_NOT_ACCEPTED)
        if not grading_config_confirmed:return GateResult(False,ErrorCode.GRADING_DRAFT_NOT_CONFIRMED)
        if expected_count is not None and len(submissions)<expected_count and not allow_missing:return GateResult(False,ErrorCode.GRADING_EXAM_HAS_MISSING_STUDENTS)
        return ExamOfficialReportGate().try_pass(submissions,exam_id)
