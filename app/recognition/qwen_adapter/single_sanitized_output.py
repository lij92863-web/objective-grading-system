"""Single Qwen Sanitized Output — safe, auditable post-processing result.

Never contains API keys, base64 image data, or raw HTTP responses.
All candidate data is structured and auditable.
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


FORBIDDEN_SANITIZED_FIELDS = {
    "api_key", "authorization", "bearer", "base64",
    "image_base64", "raw_response", "raw_http_response",
}


@dataclass
class SanitizedCandidate:
    question_id: str = ""
    question_type: str = ""
    answer: str = ""
    raw_text: str = ""
    confidence: float = 0.0
    needs_review: bool = False
    invalid_option: bool = False
    warnings: List[str] = field(default_factory=list)


@dataclass
class SanitizedIdentityCandidate:
    raw_text: str = ""
    student_number: str = ""
    student_name: str = ""
    confidence: float = 0.0
    needs_review: bool = True


@dataclass
class SingleQwenSanitizedOutput:
    schema_version: int = 1
    request_id: str = ""
    engine_name: str = ""
    engine_status: str = "ok"
    real_api_called: bool = False
    raw_response_saved: bool = False
    base64_emitted: bool = False
    image_sha256: str = ""
    candidate_count: int = 0
    candidates: List[SanitizedCandidate] = field(default_factory=list)
    identity_candidate: Optional[SanitizedIdentityCandidate] = None
    warnings: List[str] = field(default_factory=list)
    exception_codes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "engine_name": self.engine_name,
            "engine_status": self.engine_status,
            "real_api_called": self.real_api_called,
            "raw_response_saved": self.raw_response_saved,
            "base64_emitted": self.base64_emitted,
            "image_sha256": self.image_sha256,
            "candidate_count": self.candidate_count,
            "candidates": [asdict(c) for c in self.candidates],
            "identity_candidate": asdict(self.identity_candidate) if self.identity_candidate else None,
            "warnings": self.warnings,
            "exception_codes": self.exception_codes,
        }
        return result


def validate_sanitized_output(output: SingleQwenSanitizedOutput) -> dict:
    blockers: List[str] = []
    warnings: List[str] = []

    if output.raw_response_saved:
        blockers.append("RAW_RESPONSE_SAVED_MUST_BE_FALSE")
    if output.base64_emitted:
        blockers.append("BASE64_EMITTED_MUST_BE_FALSE")

    # Check raw dict for forbidden fields
    raw = json.dumps(output.to_dict(), ensure_ascii=False)
    if "sk-" in raw:
        blockers.append("CONTAINS_API_KEY_PATTERN")
    if "data:image" in raw:
        blockers.append("CONTAINS_BASE64_IMAGE")
    if "Bearer " in raw:
        blockers.append("CONTAINS_AUTHORIZATION_HEADER")

    return {
        "valid": not blockers,
        "blockers": blockers,
        "warnings": warnings,
    }
