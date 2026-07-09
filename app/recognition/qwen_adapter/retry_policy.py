"""R97A: Qwen retry policy."""
from dataclasses import dataclass

RETRYABLE_ERRORS = {"timeout", "rate_limit", "temporary_server_error"}
NO_RETRY_ERRORS = {"auth_error", "invalid_image", "budget_exceeded", "qwen_disabled", "malformed_response"}


@dataclass
class RetryDecision:
    can_retry: bool = False
    max_retries: int = 0
    reason: str = ""


def should_retry(error_type: str, max_retries: int = 2, current_retry: int = 0) -> RetryDecision:
    if error_type in NO_RETRY_ERRORS:
        return RetryDecision(False, 0, f"NO_RETRY:{error_type}")
    if error_type in RETRYABLE_ERRORS:
        if current_retry >= max_retries:
            return RetryDecision(False, 0, f"MAX_RETRIES_EXCEEDED:{current_retry}")
        return RetryDecision(True, max_retries - current_retry - 1, f"RETRY_ALLOWED:{error_type}")
    if error_type == "malformed_response" and current_retry == 0:
        return RetryDecision(True, 0, "MALFORMED_ONE_RETRY")
    return RetryDecision(False, 0, f"NO_RETRY_UNKNOWN:{error_type}")
