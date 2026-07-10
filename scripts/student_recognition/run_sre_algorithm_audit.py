"""Static safety audit for the SRE algorithm foundation."""

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _imports(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            yield node.module or ""


def _parse(path, findings):
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as error:
        findings.append(
            {"severity": "high", "check": "source_parse", "detail": f"{path}: {error}"}
        )
        return None


def _has_suspicious_fractional_compare(tree):
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        values = []
        for candidate in [node.left, *node.comparators]:
            if isinstance(candidate, ast.Constant) and isinstance(candidate.value, float):
                values.append(candidate.value)
        if any(0.0 < value < 1.0 for value in values):
            return True
    return False


def _check_runtime_candidate_safety(findings):
    """Exercise the conservative recognizer rules without image or GT input."""
    from app.student_recognition.omr.mark_metrics import MarkMetrics
    from app.student_recognition.omr.multi_choice_recognizer import recognize_multi_choice
    from app.student_recognition.omr.single_choice_recognizer import recognize_single_choice

    def metric(option, score, classification):
        return MarkMetrics(
            option, score, score, score, 0.0, 1.0, 0.0, score, classification
        )

    unsafe_cases = {
        "blank": recognize_single_choice(1, [metric("A", 0.0, "blank")]),
        "weak": recognize_single_choice(1, [metric("A", 0.1, "weak")]),
        "erased": recognize_single_choice(1, [metric("A", 0.1, "erased")]),
        "multi_mark": recognize_single_choice(
            1, [metric("A", 0.8, "strong"), metric("B", 0.8, "strong")]
        ),
        "multi_choice_weak": recognize_multi_choice(
            1, [metric("A", 0.1, "weak")]
        ),
    }
    for name, candidate in unsafe_cases.items():
        if candidate.status == "auto_candidate":
            findings.append(
                {
                    "severity": "critical",
                    "check": "unsafe_mark_acceptance",
                    "detail": f"{name} became auto_candidate",
                }
            )


def run_audit(repository_root=ROOT):
    root = Path(repository_root)
    app = root / "app" / "student_recognition"
    findings = []

    anchor_path = app / "template" / "anchor_layout.py"
    anchor_tree = _parse(anchor_path, findings)
    if anchor_tree is not None and any(
        isinstance(node, (ast.FunctionDef, ast.Name, ast.Attribute))
        and getattr(node, "name", getattr(node, "id", getattr(node, "attr", "")))
        == "_clamp_roi"
        for node in ast.walk(anchor_tree)
    ):
        findings.append(
            {
                "severity": "critical",
                "check": "silent_clamp",
                "detail": "anchor expansion defines or calls _clamp_roi",
            }
        )

    algorithm_roots = [app / name for name in ("image", "omr", "roi", "template")]
    for directory in algorithm_roots:
        for path in directory.glob("*.py") if directory.exists() else ():
            tree = _parse(path, findings)
            if tree is None:
                continue
            imported = tuple(_imports(tree))
            for module in imported:
                lowered = module.lower()
                if module == "cv2" and path.name != "backend.py":
                    findings.append(
                        {"severity": "high", "check": "cv2_isolation", "detail": str(path)}
                    )
                if any(
                    forbidden in lowered
                    for forbidden in ("objective_grader", "app.workflow", "web_app", "grading")
                ):
                    findings.append(
                        {
                            "severity": "critical",
                            "check": "boundary_import",
                            "detail": f"{path}: {module}",
                        }
                    )
            if path.parent.name in ("image", "omr") and not path.name.endswith("policy.py"):
                if _has_suspicious_fractional_compare(tree):
                    findings.append(
                        {
                            "severity": "high",
                            "check": "magic_threshold",
                            "detail": str(path),
                        }
                    )

    omr_dir = app / "omr"
    recognizer_text = ""
    for path in omr_dir.glob("*.py") if omr_dir.exists() else ():
        text = path.read_text(encoding="utf-8")
        tree = _parse(path, findings)
        if tree is None:
            continue
        if path.name.endswith("recognizer.py"):
            recognizer_text += text
        if any(module == "json" for module in _imports(tree)) or "json.loads" in text:
            findings.append(
                {"severity": "high", "check": "omr_json_parse", "detail": str(path)}
            )
        if "ground_truth" in text:
            findings.append(
                {"severity": "critical", "check": "gt_leak", "detail": str(path)}
            )
        if any(token in text for token in ('{"x"', '"x":', "origin_x", "cell_w")):
            findings.append(
                {"severity": "high", "check": "roi_coordinate_dual_source", "detail": str(path)}
            )

    cropper = app / "roi" / "roi_cropper.py"
    cropper_text = cropper.read_text(encoding="utf-8") if cropper.exists() else ""
    if 'page.location.status != "page_located"' not in cropper_text:
        findings.append(
            {
                "severity": "critical",
                "check": "page_failure_gate",
                "detail": "ROI cropper lacks mandatory page_located gate",
            }
        )

    required_review_tokens = ("weak", "erased", "dirty", "needs_review")
    if not all(token in recognizer_text for token in required_review_tokens):
        findings.append(
            {
                "severity": "critical",
                "check": "unsafe_mark_acceptance",
                "detail": "recognizers do not visibly route unsafe marks to review",
            }
        )
    if "OMR_MULTI_MARK_SINGLE_CHOICE" not in recognizer_text:
        findings.append(
            {
                "severity": "critical",
                "check": "multi_mark_acceptance",
                "detail": "single-choice multi-mark guard is missing",
            }
        )

    if root.resolve() == ROOT.resolve():
        _check_runtime_candidate_safety(findings)

    findings.append(
        {
            "severity": "caveat",
            "check": "real_image_backend",
            "detail": "real-photo contour/perspective backend is not production-certified",
        }
    )
    blocking = [item for item in findings if item["severity"] in ("critical", "high")]
    status = "FAIL" if blocking else ("PASS_WITH_CAVEATS" if findings else "PASS")
    return {"status": status, "findings": findings}


def main():
    result = run_audit(ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
