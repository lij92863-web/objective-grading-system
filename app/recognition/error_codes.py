"""R154: Recognition error codes registry."""
ERROR_CODES = {
    "identity_missing": {"severity": "blocking", "item_type": "identity", "review_required": True},
    "identity_conflict": {"severity": "blocking", "item_type": "identity", "review_required": True},
    "duplicate_identity": {"severity": "blocking", "item_type": "identity", "review_required": True},
    "invalid_option": {"severity": "blocking", "item_type": "choice", "review_required": True},
    "missing_roi": {"severity": "blocking", "item_type": "roi", "review_required": True},
    "layout_missing": {"severity": "blocking", "item_type": "layout", "review_required": True},
    "omr_qwen_conflict": {"severity": "review", "item_type": "choice", "review_required": True},
    "blank_low_confidence": {"severity": "review", "item_type": "blank", "review_required": True},
    "engine_error": {"severity": "blocking", "item_type": "engine_error", "review_required": True},
    "qwen_disabled": {"severity": "review", "item_type": "engine_error", "review_required": True},
    "qwen_budget_exceeded": {"severity": "review", "item_type": "engine_error", "review_required": True},
    "malformed_response": {"severity": "blocking", "item_type": "engine_error", "review_required": True},
    "low_confidence": {"severity": "review", "item_type": "choice", "review_required": True},
    "timeout": {"severity": "review", "item_type": "engine_error", "review_required": True},
    "rate_limit": {"severity": "review", "item_type": "engine_error", "review_required": True},
    "auth_error": {"severity": "blocking", "item_type": "engine_error", "review_required": True},
    "invalid_image": {"severity": "blocking", "item_type": "layout", "review_required": True},
    "review_unresolved": {"severity": "review", "item_type": "choice", "review_required": True},
    "block_submission": {"severity": "blocking", "item_type": "choice", "review_required": True},
}


def lookup(code: str) -> dict:
    if code not in ERROR_CODES:
        return {"severity": "blocking", "item_type": "unknown", "review_required": True}
    return ERROR_CODES[code]


def all_codes() -> set:
    return set(ERROR_CODES.keys())
