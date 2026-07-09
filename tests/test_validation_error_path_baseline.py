"""Validation error path baseline — fixture-based (B5)."""
import csv, shutil, tempfile, unittest, json
from pathlib import Path
from app.infrastructure.loaders.csv_loaders import load_answer_key, load_submissions
from app.domain.grading import grade_all
from app.application.use_cases.report_builders.validation_report import build_validation_report
from app.application.use_cases.report_builders.knowledge_profiles import build_knowledge_profiles
from app.application.use_cases.csv_report_pipeline import (
    _legacy_result_to_dict, _legacy_spec_to_dict, _legacy_sub_to_dict,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "baseline" / "json"


class ValidationErrorPathBaselineTests(unittest.TestCase):
    def test_validation_report_matches_fixture(self):
        ak = load_answer_key(DEMO_KEY)
        subs = load_submissions(DEMO_SUB, ak)
        results = grade_all(ak, subs)
        specs_d = [_legacy_spec_to_dict(s) for s in ak.questions]
        results_d = [_legacy_result_to_dict(r) for r in results]
        profiles = build_knowledge_profiles(specs_d, results_d)
        ak_dict = {"by_number": {s.number: {"question": s.number, "source_id": s.source_id,
            "tags": list(s.tags), "status": s.status, "points": s.points}
            for s in ak.questions}, "questions": [{"question": s.number,
            "source_id": s.source_id, "tags": list(s.tags), "status": s.status,
            "points": s.points} for s in ak.questions], "duplicate_questions": []}
        subs_d = [_legacy_sub_to_dict(s) for s in subs]
        profiles_d = [{"student_id": p["student_id"], "name": p["name"], "tag": p["tag"],
                        "score": p["score"], "max_score": p["max_score"], "mastery": p["mastery"],
                        "question_count": p["question_count"], "weak": p["weak"],
                        "mastery_level": p["mastery_level"]} for p in profiles]
        rows = build_validation_report(ak_dict, subs_d, results_d, profiles_d, None)
        expected = json.loads((FIXTURES / "validation_report.json").read_text("utf-8"))
        self.assertEqual(len(rows), len(expected))

    def test_no_legacy_import(self):
        import ast
        src = Path(__file__).read_text("utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names: self.assertNotIn("legacy", a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module: self.assertNotIn("legacy", node.module)


if __name__ == "__main__":
    unittest.main()
