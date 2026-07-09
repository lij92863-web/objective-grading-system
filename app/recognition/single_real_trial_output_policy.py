"""Single Real Trial Output Policy — where files can/must be written.

Rules:
- output only in data/tmp
- data/tmp must not be committed
- sanitized output may be written to data/tmp
- raw response NEVER allowed
- base64 NEVER allowed
- formal report NEVER allowed
- filename must include request_id or image_sha256 prefix
- no overwrite without --overwrite
"""

import os
from pathlib import Path
from typing import Dict, List


ALLOWED_OUTPUT_DIRS = {"data/tmp", "data\\tmp"}
FORBIDDEN_OUTPUT_DIRS = {"data/reports", "data\\reports", "data/exams", "data\\exams"}
FORBIDDEN_FILE_TYPES = {".csv", ".xlsx", ".html"}
ALLOWED_FILE_TYPES = {".json"}


def validate_output_path(output_path: str, request_id: str = "", image_sha256: str = "") -> dict:
    """Validate that output_path follows output policy."""
    blockers: List[str] = []
    warnings: List[str] = []

    path = Path(output_path)
    path_str = str(path).replace("\\", "/")

    # Rule 1: Must be in data/tmp
    in_allowed = any(allowed in path_str for allowed in ALLOWED_OUTPUT_DIRS)
    in_forbidden = any(forbidden in path_str for forbidden in FORBIDDEN_OUTPUT_DIRS)

    if in_forbidden:
        blockers.append("OUTPUT_IN_FORBIDDEN_DIR")
    if not in_allowed:
        blockers.append("OUTPUT_NOT_IN_DATA_TMP")

    # Rule 4: raw response never
    if "raw_response" in path.name.lower():
        blockers.append("RAW_RESPONSE_FILE_NOT_ALLOWED")

    # Rule 5: base64 never
    if "base64" in path.name.lower():
        blockers.append("BASE64_FILE_NOT_ALLOWED")

    # Rule 6: formal report never
    suffix = path.suffix.lower()
    if suffix in FORBIDDEN_FILE_TYPES:
        blockers.append(f"FORMAL_REPORT_TYPE_NOT_ALLOWED:{suffix}")

    # Rule 7: Must contain request_id or image_sha256 prefix
    if request_id and request_id not in path.name:
        warnings.append("FILENAME_MISSING_REQUEST_ID")
    if image_sha256 and image_sha256[:8] not in path.name:
        warnings.append("FILENAME_MISSING_IMAGE_SHA256_PREFIX")

    # Rule 8: No overwrite check (caller responsibility)
    if path.exists():
        warnings.append("FILE_ALREADY_EXISTS_NEEDS_OVERWRITE_FLAG")

    return {
        "valid": not blockers,
        "blockers": blockers,
        "warnings": warnings,
    }
