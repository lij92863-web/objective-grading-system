"""SRE1091 (part) — forbid free-form reason strings in error/review appends.

Scans ``app/student_recognition/**`` source for the anti-pattern:
    blocking_errors.append("some natural language string")
    review_items.append({"reason": "some natural language string"})
Only ``ErrorCode`` enum values (or ``ReviewItem(reason_code=ErrorCode.X)``) are
permitted. This guards constitution §1 B6 (no free-form reason codes).

Run: python -m unittest discover -s tests/student_recognition
"""

import ast
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_SR_DIR = PROJECT_ROOT / "app" / "student_recognition"

TARGET_LISTS = {"blocking_errors", "review_items"}


def _list_name_of(value_node) -> str | None:
    """Return the bare or attribute name of an append receiver, if it matches."""
    if isinstance(value_node, ast.Name):
        return value_node.id if value_node.id in TARGET_LISTS else None
    if isinstance(value_node, ast.Attribute):
        return value_node.attr if value_node.attr in TARGET_LISTS else None
    return None


def _first_arg_is_freeform(arg) -> bool:
    """True if the append argument is a free-form string or a dict containing one."""
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return True
    if isinstance(arg, ast.Dict):
        for val in arg.values:
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                return True
    return False


def _find_freeform_appends(root: Path) -> list[str]:
    violations: list[str] = []
    if not root.exists():
        return violations
    for path in sorted(root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute) or func.attr != "append":
                continue
            list_name = _list_name_of(func.value)
            if list_name is None:
                continue
            if node.args and _first_arg_is_freeform(node.args[0]):
                violations.append(
                    f"{path}:{node.lineno}: free-form append to '{list_name}' "
                    f"(use ErrorCode / reason_code= instead)"
                )
    return violations


class TestNoFreeformErrorCodes(unittest.TestCase):
    def test_no_freeform_reason_strings(self):
        violations = _find_freeform_appends(APP_SR_DIR)
        self.assertEqual(
            violations,
            [],
            f"Free-form error/reason strings are forbidden: {violations}",
        )


if __name__ == "__main__":
    unittest.main()
