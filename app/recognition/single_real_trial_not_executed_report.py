"""Single Real Trial Not-Executed Report.

Documents why a real API trial was NOT executed.
real_api_called is ALWAYS false in this report.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class SingleRealTrialNotExecutedReport:
    report_version: int = 1
    reason: str = ""
    missing_prerequisites: List[str] = field(default_factory=list)
    real_api_called: bool = False
    api_key_present: bool = False
    anonymous_confirmed: bool = False
    check_only_passed: bool = False
    next_required_steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_not_executed_report(
    reason: str = "no real API call in current stage",
    missing_prerequisites: List[str] = None,
    api_key_present: bool = False,
    anonymous_confirmed: bool = False,
    check_only_passed: bool = False,
) -> SingleRealTrialNotExecutedReport:
    """Build a not-executed report.

    Never contains API keys, base64, or raw responses.
    """
    if missing_prerequisites is None:
        missing_prerequisites = [
            "no anonymous real image provided",
            "no explicit --allow-real-api flag",
            "no explicit --confirm-anonymous flag",
            "no check-only pass confirmation",
        ]

    return SingleRealTrialNotExecutedReport(
        reason=reason,
        missing_prerequisites=missing_prerequisites,
        real_api_called=False,
        api_key_present=api_key_present,
        anonymous_confirmed=anonymous_confirmed,
        check_only_passed=check_only_passed,
        next_required_steps=[
            "1. Obtain anonymous single image (no real names/IDs/school)",
            "2. Create manifest + ROI for the image",
            "3. Validate manifest and ROI",
            "4. Run single image dry-run",
            "5. Run check-single-image-qwen-readiness --check-only",
            "6. Run fake replay with expected fixtures",
            "7. Inspect parser audit and review queue",
            "8. Only then: run_single_qwen_real_trial.py --allow-real-api --confirm-anonymous --check-only-passed --api-key-env QWEN_API_KEY --max-calls 1",
            "9. Sanitize and audit the real output",
            "10. Do NOT enter grade_all, do NOT generate formal reports, do NOT batch",
        ],
    )
