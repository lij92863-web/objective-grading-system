import json
from pathlib import Path
import socket
import subprocess
import tempfile
import threading
import unittest

from app.exam_session.session_model import ExamSessionState
from tests.product.mobile_capture_test_support import (
    JPEG,
    PNG,
    mobile_fields,
    mobile_upload,
    prepare_web,
    set_session_state,
)


ROOT = Path(__file__).resolve().parents[2]


class MobileCaptureSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "data")
        self.root = Path(self.temp.name)
        self.web, self.session = prepare_web(self.root)

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def payload(response):
        return json.loads(response.body.decode("utf-8"))

    def assert_rejected(self, expected_status, **kwargs):
        response = mobile_upload(self.web, self.session.session_id, **kwargs)
        self.assertEqual(response.status, expected_status)
        self.assertFalse(self.payload(response)["ok"])

    def test_invalid_image_and_metadata_attacks_are_rejected(self):
        cases = [
            (400, {"client_capture_id": "empty-image", "content": b""}),
            (415, {
                "client_capture_id": "wrong-mime",
                "content_type": "text/plain",
                "fields": {"mime_type": "text/plain"},
            }),
            (415, {"client_capture_id": "suffix-mismatch", "filename": "capture.png"}),
            (415, {"client_capture_id": "fake-jpeg", "content": b"not-a-jpeg"}),
            (415, {
                "client_capture_id": "fake-png",
                "content": b"not-a-png",
                "filename": "capture.png",
                "content_type": "image/png",
                "fields": {"mime_type": "image/png"},
            }),
            (400, {"client_capture_id": "../invalid"}),
            (400, {
                "client_capture_id": "metadata-too-long",
                "fields": {"device_label": "x" * 201},
            }),
            (415, {
                "client_capture_id": "part-mime-mismatch",
                "content_type": "image/png",
            }),
        ]
        for expected, kwargs in cases:
            with self.subTest(client_capture_id=kwargs.get("client_capture_id")):
                self.assert_rejected(expected, **kwargs)

    def test_oversized_image_is_rejected_without_job(self):
        response = mobile_upload(
            self.web,
            self.session.session_id,
            client_capture_id="oversized-image",
            content=JPEG + (b"x" * (32 * 1024 * 1024)),
        )
        self.assertEqual(response.status, 413)
        self.assertEqual(self.web.facade.queue.list_jobs(self.session.session_id), [])

    def test_invalid_finalized_and_archived_sessions_fail_closed(self):
        missing = mobile_upload(self.web, "missing-session", client_capture_id="missing-session")
        self.assertEqual(missing.status, 404)
        for state in (ExamSessionState.FINALIZED, ExamSessionState.ARCHIVED):
            set_session_state(self.web.facade.database, self.session.session_id, state)
            response = mobile_upload(
                self.web,
                self.session.session_id,
                client_capture_id=f"blocked-{state.value.lower()}",
            )
            self.assertEqual(response.status, 409)
        self.assertEqual(self.web.facade.queue.list_jobs(self.session.session_id), [])

    def test_directory_traversal_filename_cannot_control_storage_path(self):
        response = mobile_upload(
            self.web,
            self.session.session_id,
            client_capture_id="safe-server-path",
            filename="../../outside.jpg",
        )
        self.assertEqual(response.status, 201)
        job = self.web.facade.queue.list_jobs(self.session.session_id)[0]
        stored = Path(job.stored_image_path)
        expected_parent = self.root / "local_app" / "uploads" / self.session.session_id
        self.assertEqual(stored.parent.resolve(), expected_parent.resolve())
        self.assertNotIn("outside", stored.name)
        self.assertFalse((self.root / "outside.jpg").exists())

    def test_mobile_boundary_has_no_grading_ai_env_cloud_or_public_listener(self):
        paths = [
            ROOT / "app/capture/mobile_web_camera_source.py",
            ROOT / "app/product/capture/mobile_capture_service.py",
            ROOT / "app/web_product/product_app.py",
            ROOT / "web/static/mobile_capture.js",
        ]
        combined = "\n".join(path.read_text(encoding="utf-8") for path in paths).lower()
        for forbidden in [
            "domain.grading", "grade_submission", "legacy.", "dotenv",
            "os.getenv", "qwen", "student_recognition", "requests.post",
        ]:
            self.assertNotIn(forbidden, combined)
        web_app = (ROOT / "web_app.py").read_text(encoding="utf-8")
        self.assertIn('def run(host: str = "127.0.0.1"', web_app)
        self.assertNotIn('def run(host: str = "0.0.0.0"', web_app)

    def test_adb_binary_and_runtime_images_are_not_trackable(self):
        tracked = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        self.assertFalse(any(path.lower().endswith(("adb", "adb.exe")) for path in tracked))
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("local-tools/", ignore)
        self.assertIn("data/mobile-capture/", ignore)


class MobileCaptureHttpSmokeTests(unittest.TestCase):
    def setUp(self):
        import web_app
        from http.server import ThreadingHTTPServer

        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "data")
        self.root = Path(self.temp.name)
        self.web, self.session = prepare_web(self.root)
        self.previous = web_app._PRODUCT_CONTROLLER
        web_app._PRODUCT_CONTROLLER = self.web
        self.web_app = web_app
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), web_app.WebHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.web_app._PRODUCT_CONTROLLER = self.previous
        self.temp.cleanup()

    def request(self, method, path, body=None, headers=None):
        payload = body or b""
        request_headers = {
            "Host": "127.0.0.1",
            "Connection": "close",
            "Content-Length": str(len(payload)),
        }
        request_headers.update(headers or {})
        head = [f"{method} {path} HTTP/1.1"]
        head.extend(f"{name}: {value}" for name, value in request_headers.items())
        raw = "\r\n".join(head).encode("ascii") + b"\r\n\r\n" + payload
        with socket.create_connection(
            ("127.0.0.1", self.server.server_port),
            timeout=5,
        ) as connection:
            connection.sendall(raw)
            chunks = []
            while True:
                chunk = connection.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
        response_head, response_body = b"".join(chunks).split(b"\r\n\r\n", 1)
        lines = response_head.decode("iso-8859-1").split("\r\n")
        status = int(lines[0].split(" ", 2)[1])
        response_headers = dict(
            line.split(": ", 1)
            for line in lines[1:]
            if ": " in line
        )
        return status, response_headers, response_body

    @staticmethod
    def multipart_body(fields, filename, content, content_type):
        boundary = "----codex-mobile-capture-boundary"
        chunks = []
        for name, value in fields.items():
            chunks.append(
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode("utf-8")
            )
        chunks.append(
            (
                f"--{boundary}\r\n"
                f"Content-Disposition: form-data; name=\"image\"; filename=\"{filename}\"\r\n"
                f"Content-Type: {content_type}\r\n\r\n"
            ).encode("utf-8")
        )
        chunks.extend([content, b"\r\n", f"--{boundary}--\r\n".encode("ascii")])
        return boundary, b"".join(chunks)

    def test_required_routes_and_legacy_grade_over_real_http(self):
        for path in [
            "/mobile-capture",
            "/mobile-capture/health.json",
            f"/mobile-capture/{self.session.session_id}",
            f"/sessions/{self.session.session_id}/capture/status.json",
        ]:
            status, _, _ = self.request("GET", path)
            self.assertEqual(status, 200, path)
        fields = mobile_fields("capture-http-smoke")
        boundary, body = self.multipart_body(fields, "capture.jpg", JPEG, "image/jpeg")
        status, headers, payload = self.request(
            "POST",
            f"/sessions/{self.session.session_id}/capture/mobile-web",
            body,
            {"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        self.assertEqual(status, 201)
        self.assertIn("application/json", headers["Content-Type"])
        self.assertTrue(json.loads(payload.decode("utf-8"))["capture_job_id"])
        legacy_status, _, _ = self.request("POST", "/api/exams/grade", b"")
        self.assertEqual(legacy_status, 410)

    def test_oversized_content_length_is_rejected_before_body_read(self):
        status, _, response_body = self.request(
            "POST",
            f"/sessions/{self.session.session_id}/capture/mobile-web",
            headers={
                "Content-Type": "multipart/form-data; boundary=x",
                "Content-Length": str(40 * 1024 * 1024),
            },
        )
        payload = json.loads(response_body.decode("utf-8"))
        self.assertEqual(status, 413)
        self.assertEqual(payload["error_code"], "REQUEST_TOO_LARGE")


if __name__ == "__main__":
    unittest.main()
