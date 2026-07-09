"""R123: Review policy matrix — centralized exception → policy mapping."""
from dataclasses import dataclass, field
from typing import Dict, List

POLICY_MATRIX: Dict[str, dict] = {
    "identity_missing": {"item_type": "identity", "severity": "blocking",
                         "blocks_submission": True, "review_required": True,
                         "teacher_actions": ["confirm_identity","correct_identity","block_identity"]},
    "identity_conflict": {"item_type": "identity", "severity": "blocking",
                          "blocks_submission": True, "review_required": True,
                          "teacher_actions": ["confirm_identity","correct_identity","block_identity"]},
    "duplicate_identity": {"item_type": "identity", "severity": "blocking",
                           "blocks_submission": True, "review_required": True,
                           "teacher_actions": ["confirm_identity","correct_identity","block_identity"]},
    "invalid_option": {"item_type": "choice", "severity": "blocking",
                       "blocks_submission": False, "review_required": True,
                       "teacher_actions": ["correct_answer","block_submission"]},
    "missing_roi": {"item_type": "roi", "severity": "blocking",
                    "blocks_submission": False, "review_required": True,
                    "teacher_actions": ["correct_answer","mark_blank","block_submission"]},
    "layout_missing": {"item_type": "layout", "severity": "blocking",
                       "blocks_submission": True, "review_required": True,
                       "teacher_actions": ["block_submission"]},
    "omr_qwen_conflict": {"item_type": "choice", "severity": "review",
                          "blocks_submission": False, "review_required": True,
                          "teacher_actions": ["correct_answer","reject_candidate","block_submission"]},
    "blank_low_confidence": {"item_type": "blank", "severity": "review",
                             "blocks_submission": False, "review_required": True,
                             "teacher_actions": ["accept_candidate","correct_answer","mark_blank","block_submission"]},
    "engine_error": {"item_type": "engine_error", "severity": "blocking",
                     "blocks_submission": False, "review_required": True,
                     "teacher_actions": ["correct_answer","block_submission"]},
    "qwen_disabled": {"item_type": "engine_error", "severity": "review",
                       "blocks_submission": False, "review_required": True,
                       "teacher_actions": ["correct_answer","accept_candidate","block_submission"]},
    "qwen_budget_exceeded": {"item_type": "engine_error", "severity": "review",
                              "blocks_submission": False, "review_required": True,
                              "teacher_actions": ["correct_answer","accept_candidate","block_submission"]},
    "malformed_response": {"item_type": "engine_error", "severity": "blocking",
                           "blocks_submission": False, "review_required": True,
                           "teacher_actions": ["correct_answer","block_submission"]},
    "low_confidence": {"item_type": "choice", "severity": "review",
                       "blocks_submission": False, "review_required": True,
                       "teacher_actions": ["accept_candidate","correct_answer","reject_candidate","block_submission"]},
    "timeout": {"item_type": "engine_error", "severity": "review",
                "blocks_submission": False, "review_required": True,
                "teacher_actions": ["correct_answer","block_submission"]},
    "rate_limit": {"item_type": "engine_error", "severity": "review",
                   "blocks_submission": False, "review_required": True,
                   "teacher_actions": ["correct_answer","block_submission"]},
    "auth_error": {"item_type": "engine_error", "severity": "blocking",
                   "blocks_submission": True, "review_required": True,
                   "teacher_actions": ["block_submission"]},
    "invalid_image": {"item_type": "layout", "severity": "blocking",
                      "blocks_submission": True, "review_required": True,
                      "teacher_actions": ["block_submission"]},
    "review_unresolved": {"item_type": "choice", "severity": "review",
                          "blocks_submission": False, "review_required": True,
                          "teacher_actions": ["correct_answer","block_submission"]},
    "block_submission": {"item_type": "choice", "severity": "blocking",
                         "blocks_submission": True, "review_required": True,
                         "teacher_actions": ["block_submission"]},
}

for _policy in POLICY_MATRIX.values():
    _policy.setdefault("allowed_actions", list(_policy.get("teacher_actions", [])))


def lookup_policy(code: str) -> dict:
    if code not in POLICY_MATRIX:
        return {"item_type": "unknown", "severity": "blocking",
                "blocks_submission": True, "review_required": True,
                "teacher_actions": ["block_submission"]}
    return POLICY_MATRIX[code]


def is_identity_code(code: str) -> bool:
    return code in {"identity_missing","identity_conflict","duplicate_identity"}
