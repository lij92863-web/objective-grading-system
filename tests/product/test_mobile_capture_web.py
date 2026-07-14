import json
from pathlib import Path
import tempfile
import unittest

from tests.product.mobile_capture_test_support import prepare_web


ROOT = Path(__file__).resolve().parents[2]


class MobileCaptureWebTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "data")
        self.root = Path(self.temp.name)
        self.web, self.session = prepare_web(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_health_contract_does_not_claim_device_connection(self):
        response = self.web.get("/mobile-capture/health.json")
        payload = json.loads(response.body.decode("utf-8"))
        self.assertEqual(payload, {
            "ok": True,
            "service": "objective-grading-mobile-capture",
            "transport": "adb-reverse-compatible",
            "real_recognition_enabled": False,
        })
        self.assertNotIn("device", payload)
        self.assertNotIn("usb_connected", payload)

    def test_mobile_pages_have_session_camera_and_status_controls(self):
        landing = self.web.get("/mobile-capture")
        capture = self.web.get(f"/mobile-capture/{self.session.session_id}")
        landing_text = landing.body.decode("utf-8")
        capture_text = capture.body.decode("utf-8")
        self.assertEqual(landing.status, 200)
        self.assertIn(self.session.session_id, landing_text)
        self.assertEqual(capture.status, 200)
        for marker in [
            "mobile-video", "a4-guide", "camera-select", "capture-button",
            "last-thumbnail", "retry-button", "stop-camera", "service-state",
        ]:
            self.assertIn(marker, capture_text)
        self.assertIn("mobile_capture.js", capture_text)

    def test_mobile_javascript_uses_resilient_sequential_queue(self):
        script = (ROOT / "web/static/mobile_capture.js").read_text(encoding="utf-8")
        for marker in [
            "indexedDB.open", "LOCAL_PENDING", "UPLOADING", "ACKNOWLEDGED",
            "RETRY_WAIT", "FAILED_MANUAL", "uploadWorkerActive", "captureLocked",
            "ImageCapture", "takePhoto", "facingMode", 'ideal: "environment"',
            "width: { ideal: 3840 }", "height: { ideal: 2160 }", "0.95",
            "enumerateDevices", "pagehide", "visibilitychange",
        ]:
            self.assertIn(marker, script)
        self.assertNotIn("location.href", script)
        self.assertNotIn("location.reload", script)

    def test_desktop_capture_page_links_usb_mobile_flow(self):
        page = self.web.get(f"/sessions/{self.session.session_id}/capture")
        text = page.body.decode("utf-8")
        self.assertIn(f"/mobile-capture/{self.session.session_id}", text)
        self.assertIn("ADB 数据线转发", text)
        self.assertIn("不是 Windows 直接调用手机摄像头", text)
        self.assertIn("刷新手机采集状态", text)

    def test_manual_device_acceptance_defaults_to_not_tested(self):
        checklist = (
            ROOT / "docs/product/VIVO_X200_USB_MANUAL_ACCEPTANCE.md"
        ).read_text(encoding="utf-8")
        self.assertGreaterEqual(checklist.count("NOT TESTED"), 20)
        self.assertNotIn("真实设备结论：PASS", checklist)


if __name__ == "__main__":
    unittest.main()
