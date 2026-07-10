"""Small deterministic behavior-parity benchmark for the canonical core."""

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.application.grading import ArchivePolicy, GradingOverride
from app.domain.grading import AnswerKey, QuestionSpec, Submission, grade_submission, run_grading_precheck


fixture = json.loads((ROOT / "tests/grading/golden/grading_core_cases.json").read_text(encoding="utf-8"))
specs = (
    QuestionSpec(1, frozenset({"A"}), points=1, answer_text="A", question_type="single_choice"),
    QuestionSpec(
        2,
        frozenset({"A", "C"}),
        points=2,
        partial_credit=True,
        partial_points=1,
        answer_text="AC",
        question_type="multiple_choice",
    ),
    QuestionSpec(3, frozenset({"T"}), points=1, answer_text="T", question_type="true_false"),
    QuestionSpec(4, frozenset({"42"}), points=1, answer_text="42", question_type="blank"),
)
key = AnswerKey(specs)
sub = Submission(
    "S1", "N",
    {1: frozenset({"A"}), 2: frozenset({"A"}), 3: frozenset({"T"}), 4: frozenset({"42"})},
    {1: "A", 2: "A", 3: "T", 4: "42"}, (), 2,
)
result = grade_submission(key, sub)
expected = {
    "score": 4.0,
    "details": [(1, 1, "correct"), (2, 1, "partial"), (3, 1, "correct"), (4, 1, "correct")],
}
actual = {
    "score": result.score,
    "details": [(d.number, d.score, d.status) for d in result.details],
}
checks = [
    actual == expected,
    run_grading_precheck(answer_key=key, submissions=[sub]).can_grade,
    ArchivePolicy(enabled=True).enabled and not ArchivePolicy(enabled=False).enabled,
    len(fixture["valid_cases"]) == 6,
    len(fixture["invalid_cases"]) == 6,
]
try:
    GradingOverride(("missing_answer_key",), "auditor", "attack", "now")
    checks.append(False)
except ValueError:
    checks.append(True)

score_parity = 100.0 if actual["score"] == expected["score"] else 0.0
detail_parity = 100.0 if actual["details"] == expected["details"] else 0.0
print(f"score parity: {score_parity:.1f}%")
print(f"question detail parity: {detail_parity:.1f}%")
if not all(checks):
    print("FAIL")
    sys.exit(1)
print("PASS")
