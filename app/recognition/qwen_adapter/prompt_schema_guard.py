"""Prompt Schema Guard — validates prompts for safety and correctness.

Checks:
1. Prompt contains required JSON schema instruction
2. Prompt contains no grading instruction
3. Prompt contains no final score instruction
4. Prompt contains no API key
5. Prompt contains no base64
6. Prompt contains no full local path
"""

from pathlib import Path
from typing import Dict, List


FORBIDDEN_PROMPT_PATTERNS = [
    "sk-",
    "data:image",
    "Bearer ",
    "authorization",
    "Authorization",
]

FORBIDDEN_GRADING_PATTERNS = [
    "final score",
    "final grade",
    "判分",
    "总分",
    "grade_all",
    "total_score",
    "total score",
    "final_score",
]


def validate_prompt_schema(prompt_text: str) -> dict:
    """Validate a prompt for safety and schema compliance."""
    blockers: List[str] = []
    warnings: List[str] = []

    # 1. Must contain JSON instruction
    if "json" not in prompt_text.lower() and "JSON" not in prompt_text:
        blockers.append("MISSING_JSON_INSTRUCTION")
    elif "json" in prompt_text.lower():
        # Has JSON but check for schema
        if "question_id" not in prompt_text:
            warnings.append("JSON_SCHEMA_MISSING_QUESTION_ID")

    # 2. No grading instruction
    for pattern in FORBIDDEN_GRADING_PATTERNS:
        if pattern.lower() in prompt_text.lower():
            blockers.append(f"CONTAINS_GRADING_INSTRUCTION:{pattern}")

    # 3. No API key pattern
    for pattern in FORBIDDEN_PROMPT_PATTERNS:
        if pattern in prompt_text:
            blockers.append(f"CONTAINS_FORBIDDEN_PATTERN:{pattern}")

    # 4. No full local paths (Windows or Unix)
    if "C:\\" in prompt_text or "/home/" in prompt_text or "/Users/" in prompt_text:
        warnings.append("CONTAINS_FULL_LOCAL_PATH")

    # 5. Must forbid scoring
    scoring_forbidden = any(
        phrase in prompt_text for phrase in
        ["不要判分", "不判分", "no scoring", "do not score", "do not grade",
         "不要", "禁止", "forbid", "不得"]
    )
    if "score" in prompt_text.lower() and not scoring_forbidden:
        warnings.append("MAY_ALLOW_SCORING")

    return {
        "valid": not blockers,
        "blockers": blockers,
        "warnings": warnings,
    }
