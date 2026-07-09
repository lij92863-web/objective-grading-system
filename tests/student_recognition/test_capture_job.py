"""Capture job store + safe paths + ids tests (constitution §4 / §5 / §6)."""

import unittest
import tempfile
from pathlib import Path

from app.student_recognition.capture.camera_device_contract import (
    UnsupportedCaptureSourceError,
    assert_supported_source,
)
from app.student_recognition.capture.capture_job import ARTIFACT_EVENTS, ARTIFACT_MANIFEST, ARTIFACT_ORIGINAL, ARTIFACT_SHA256, CaptureJobStore
from app.student_recognition.common import ids, safe_paths
from app.student_recognition.common.atomic_io import atomic_write_text
from app.student_recognition.state_model import State


class TestCaptureStore(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        safe_paths.set_captures_root(self.tmp)
        # fresh dedup index for isolation
        ids.DedupIndex(self.tmp).reset()

    def tearDown(self):
        safe_paths.reset_captures_root()

    def test_create_persists_original_sha_manifest_events(self):
        store = CaptureJobStore(root=self.tmp)
        img = b"fake-jpeg-bytes"
        job = store.create(img, source="browser")
        jdir = safe_paths.job_dir(job.job_id)
        self.assertTrue((jdir / ARTIFACT_ORIGINAL).exists())
        self.assertTrue((jdir / ARTIFACT_SHA256).exists())
        self.assertTrue((jdir / ARTIFACT_MANIFEST).exists())
        self.assertTrue((jdir / ARTIFACT_EVENTS).exists())
        self.assertEqual((jdir / ARTIFACT_SHA256).read_text().strip(), ids.compute_sha256(img))
        self.assertEqual(job.status, State.JOB_CREATED)

    def test_get_roundtrip(self):
        store = CaptureJobStore(root=self.tmp)
        job = store.create(b"abc", source="browser")
        loaded = store.get(job.job_id)
        self.assertEqual(loaded.job_id, job.job_id)
        self.assertEqual(loaded.status, State.JOB_CREATED)
        self.assertGreaterEqual(len(loaded.events), 1)

    def test_idempotent_dedup(self):
        store = CaptureJobStore(root=self.tmp)
        j1 = store.create(b"same-bytes", source="browser")
        j2 = store.create(b"same-bytes", source="browser")
        self.assertEqual(j1.job_id, j2.job_id)

    def test_list_jobs(self):
        store = CaptureJobStore(root=self.tmp)
        store.create(b"x", source="browser")
        store.create(b"y", source="browser")
        self.assertEqual(len(store.list_job_ids()), 2)

    def test_unsupported_source_rejected(self):
        store = CaptureJobStore(root=self.tmp)
        with self.assertRaises(UnsupportedCaptureSourceError):
            store.create(b"z", source="adb")
        with self.assertRaises(UnsupportedCaptureSourceError):
            # any non-browser source must be refused by the contract
            assert_supported_source("usb_phone")


class TestSafePaths(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        safe_paths.set_captures_root(self.tmp)

    def tearDown(self):
        safe_paths.reset_captures_root()

    def test_traversal_rejected(self):
        with self.assertRaises(ValueError):
            safe_paths.validate_job_id("../escape")
        with self.assertRaises(ValueError):
            safe_paths.validate_job_id("a/../b")

    def test_job_dir_under_root(self):
        d = safe_paths.job_dir("job_abc")
        self.assertTrue(str(d).startswith(str(self.tmp)))

    def test_safe_join_escapes_base(self):
        base = self.tmp / "jobs"
        base.mkdir(parents=True, exist_ok=True)
        with self.assertRaises(ValueError):
            safe_paths.safe_join(base, "..", "secret")


class TestAtomicIo(unittest.TestCase):
    def test_atomic_write_visible_after_replace(self):
        p = Path(tempfile.mkdtemp()) / "f.txt"
        atomic_write_text(p, "hello")
        self.assertEqual(p.read_text(), "hello")


if __name__ == "__main__":
    unittest.main()
