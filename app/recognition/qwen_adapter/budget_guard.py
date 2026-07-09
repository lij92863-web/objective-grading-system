"""R101: Qwen budget guard."""
from dataclasses import dataclass


@dataclass
class BudgetGuardResult:
    allowed_calls: int = 0
    blocked_calls: int = 0
    reason: str = ""


def compute_qwen_budget(estimated_calls: int, max_calls: int) -> BudgetGuardResult:
    if max_calls <= 0: return BudgetGuardResult(0, estimated_calls, "DISABLED")
    if estimated_calls <= max_calls: return BudgetGuardResult(estimated_calls, 0, "WITHIN_BUDGET")
    allowed = max_calls
    blocked = estimated_calls - max_calls
    return BudgetGuardResult(allowed, blocked, "BUDGET_EXCEEDED")
