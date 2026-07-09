"""Load synthetic batch fixtures by path or scenario."""
import json
from pathlib import Path
from typing import Dict

from .synthetic_batch_schema import SyntheticBatchFixture


FIXTURE_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "recognition" / "synthetic_batches"
SCENARIO_FIXTURES: Dict[str, str] = {
    "all_clear": "batch_all_clear.json",
    "with_review": "batch_with_review.json",
    "with_blocking_identity": "batch_with_blocking_identity.json",
    "qwen_budget_exceeded": "batch_qwen_budget_exceeded.json",
    "mixed_choice_blank_identity": "batch_mixed_choice_blank_identity.json",
    "malformed_qwen_response": "batch_malformed_qwen_response.json",
    "malformed_qwen": "batch_malformed_qwen_response.json",
    "missing_roi": "batch_missing_roi.json",
    "invalid_option": "batch_invalid_option.json",
}


def load_fixture_by_path(path: str | Path) -> SyntheticBatchFixture:
    fixture_path = Path(path)
    try:
        data = json.loads(fixture_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid synthetic batch JSON: {fixture_path}") from exc
    except OSError as exc:
        raise ValueError(f"cannot read synthetic batch fixture: {fixture_path}") from exc
    return SyntheticBatchFixture.from_dict(data)


def load_fixture_by_scenario(scenario: str) -> SyntheticBatchFixture:
    if scenario not in SCENARIO_FIXTURES:
        raise ValueError(f"unknown synthetic batch scenario: {scenario}")
    return load_fixture_by_path(FIXTURE_DIR / SCENARIO_FIXTURES[scenario])


def load_all_fixtures() -> list[SyntheticBatchFixture]:
    canonical = [
        "all_clear",
        "with_review",
        "with_blocking_identity",
        "qwen_budget_exceeded",
        "mixed_choice_blank_identity",
        "malformed_qwen_response",
        "missing_roi",
        "invalid_option",
    ]
    return [load_fixture_by_scenario(name) for name in canonical]
