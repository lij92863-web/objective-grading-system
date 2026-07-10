import tempfile
import unittest
from pathlib import Path

from app.web_product import ProductWebController, UploadedFile


ROOT = Path(__file__).resolve().parents[2]
PNG = b"\x89PNG\r\n\x1a\nweb-product"


class WebProductWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "data")
        self.root = Path(self.temp.name)
        self.web = ProductWebController(self.root / "local_app")

    def tearDown(self):
        self.temp.cleanup()

    def test_web_classes_page_loads_and_creates_class(self):
        self.assertEqual(self.web.get("/classes").status, 200)
        response = self.web.post(
            "/classes",
            {"class_name": "高一 3 班"},
            {},
        )
        self.assertEqual(response.status, 303)
        self.assertTrue(response.headers["Location"].startswith("/classes/"))

    def test_web_complete_local_workflow(self):
        class_response = self.web.post(
            "/classes",
            {"class_name": "高一 3 班"},
            {},
        )
        class_id = class_response.headers["Location"].rsplit("/", 1)[1]
        roster_response = self.web.post(
            f"/classes/{class_id}/roster/import",
            {},
            {"roster": UploadedFile("roster.csv", "学号,姓名\n001,张三\n".encode("utf-8-sig"))},
        )
        self.assertEqual(roster_response.status, 303)
        session_response = self.web.post(
            "/sessions",
            {"exam_name": "期中考试", "class_id": class_id},
            {},
        )
        session_id = session_response.headers["Location"].rsplit("/", 1)[1]
        answer = "question,answer,type\n1,A,single_choice\n".encode("utf-8-sig")
        for asset_type, upload in [
            ("ANSWER_KEY", UploadedFile("answer.csv", answer)),
            ("TEMPLATE", UploadedFile("template.json", b"{}")),
        ]:
            response = self.web.post(
                f"/sessions/{session_id}/assets",
                {"asset_type": asset_type},
                {"asset": upload},
            )
            self.assertEqual(response.status, 303)
        capture = self.web.post(
            f"/sessions/{session_id}/capture/upload",
            {},
            {"image": UploadedFile("image.png", PNG)},
        )
        self.assertEqual(capture.status, 303)
        review_page = self.web.get(f"/sessions/{session_id}/review")
        self.assertIn("识别不到学生", review_page.body.decode("utf-8"))
        blocked = self.web.post(f"/sessions/{session_id}/finalize", {}, {})
        self.assertEqual(blocked.status, 409)
        issues = self.web.facade.review.list_issues(session_id)
        self.web.post(
            f"/sessions/{session_id}/review/{issues[0].issue_id}/resolve",
            {"issue_type": issues[0].issue_type, "student_no": "001"},
            {},
        )
        for issue in self.web.facade.review.list_issues(session_id):
            self.web.post(
                f"/sessions/{session_id}/review/{issue.issue_id}/resolve",
                {
                    "issue_type": issue.issue_type,
                    "action": "MANUAL_SCORE",
                    "manual_score": "1",
                    "reason": "教师查看原卷确认",
                },
                {},
            )
        finalized = self.web.post(f"/sessions/{session_id}/finalize", {}, {})
        self.assertEqual(finalized.status, 303)
        csv_response = self.web.get(
            f"/sessions/{session_id}/exports/final_scores.csv"
        )
        self.assertEqual(csv_response.status, 200)
        self.assertIn("001", csv_response.body.decode("utf-8-sig"))

    def test_web_finalize_blocks_open_issues(self):
        self.test_web_complete_local_workflow()

    def test_web_layer_does_not_import_low_level_grading(self):
        import ast

        text = (ROOT / "app/web_product/product_app.py").read_text(encoding="utf-8")
        self.assertNotIn("domain.grading", text)
        self.assertNotIn("grade_submission", text)
        modules = []
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                modules.append(node.module or "")
        self.assertNotIn("sqlite3", modules)

    def test_camera_page_explains_usb_boundary(self):
        template = (
            ROOT / "web/templates/product/capture.html"
        ).read_text(encoding="utf-8")
        self.assertIn("普通 USB 数据线", template)
        self.assertIn("浏览器", template)


if __name__ == "__main__":
    unittest.main()
