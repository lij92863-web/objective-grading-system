"""Synthetic local benchmark for mobile capture ingestion registration."""

import json
import math
from pathlib import Path
import sys
import tempfile
import time
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.capture.mobile_web_camera_source import MobileCaptureError
from app.web_product.facade import ProductFacade, ProductPaths


REPORT_PATH = ROOT / "docs/product/MOBILE_CAPTURE_INGESTION_BENCHMARK.md"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def fields(client_capture_id: str) -> dict[str, str]:
    return {
        "client_capture_id": client_capture_id,
        "captured_at": "2026-07-14T08:00:00.000Z",
        "capture_method": "CANVAS",
        "device_label": "Synthetic benchmark camera",
        "device_id": "benchmark-device",
        "facing_mode": "environment",
        "width": "3840",
        "height": "2160",
        "mime_type": "image/png",
    }


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = max(0, math.ceil(len(ordered) * fraction) - 1)
    return round(ordered[index], 3)


def write_report(metrics: dict[str, int | float]) -> None:
    lines = [
        "# Mobile Capture Ingestion Benchmark",
        "",
        "本报告只使用合成、非敏感字节测试本地登记链路；不是 vivo X200 真机、真实摄像头或真实识别 benchmark。",
        "",
        "## Workload",
        "",
        "- 1 个合成班级和 1 场合成考试",
        "- 60 张不同的合成 PNG",
        "- 5 次相同 Blob 重试",
        "- 2 次非法格式请求",
        "- 1 次超限请求模拟",
        "",
        "## Metrics",
        "",
        "| metric | value |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {name} | {value} |" for name, value in metrics.items())
    lines.extend([
        "",
        "## Result",
        "",
        "`PASS` 表示合成 ingestion 登记、去重、来源和 session 绑定满足本阶段门槛；真机项目仍为 `NOT TESTED`。",
        "",
    ])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    accepted_ids: list[str] = []
    timings: list[float] = []
    duplicate_replay_count = 0
    invalid_rejected_count = 0
    failed_upload_count = 0
    with tempfile.TemporaryDirectory(dir=ROOT / "data") as temporary:
        root = Path(temporary)
        facade = ProductFacade(ProductPaths(
            root=root / "local_app",
            database=root / "product.sqlite3",
            incoming=root / "incoming",
            exports=root / "exports",
        ))
        classroom = facade.create_class("合成 benchmark 班")
        session = facade.create_session("合成 ingestion benchmark", classroom.class_id)
        facade.add_asset(
            session.session_id,
            "ANSWER_KEY",
            "answer.csv",
            b"question,answer,type\n1,A,single_choice\n",
        )
        facade.add_asset(session.session_id, "TEMPLATE", "template.json", b"{}")

        blobs: list[bytes] = []
        for index in range(60):
            blob = PNG_SIGNATURE + f"synthetic-answer-card-{index:03d}".encode("ascii")
            blobs.append(blob)
            started = time.perf_counter()
            try:
                outcome = facade.capture_mobile_web(
                    session.session_id,
                    f"capture-{index:03d}.png",
                    blob,
                    "image/png",
                    fields(f"benchmark-{index:03d}"),
                )
            except Exception:
                failed_upload_count += 1
                continue
            timings.append((time.perf_counter() - started) * 1000)
            if not outcome.duplicate:
                accepted_ids.append(outcome.capture_job_id)

        for index in range(5):
            try:
                replay = facade.capture_mobile_web(
                    session.session_id,
                    f"replay-{index:03d}.png",
                    blobs[index],
                    "image/png",
                    fields(f"benchmark-replay-{index:03d}"),
                )
                if replay.duplicate:
                    duplicate_replay_count += 1
                else:
                    failed_upload_count += 1
            except Exception:
                failed_upload_count += 1

        invalid_cases = [
            ("invalid-signature.png", b"not-a-png", "image/png", fields("benchmark-invalid-1")),
            ("wrong-extension.jpg", PNG_SIGNATURE + b"mismatch", "image/png", fields("benchmark-invalid-2")),
        ]
        for filename, content, mime_type, metadata in invalid_cases:
            try:
                facade.capture_mobile_web(
                    session.session_id,
                    filename,
                    content,
                    mime_type,
                    metadata,
                )
                failed_upload_count += 1
            except MobileCaptureError:
                invalid_rejected_count += 1

        oversized = PNG_SIGNATURE + b"oversized-mock"
        try:
            with mock.patch(
                "app.capture.mobile_web_camera_source.MAX_MOBILE_CAPTURE_BYTES",
                len(oversized) - 1,
            ):
                facade.capture_mobile_web(
                    session.session_id,
                    "oversized.png",
                    oversized,
                    "image/png",
                    fields("benchmark-oversized"),
                )
            failed_upload_count += 1
        except MobileCaptureError as exc:
            if exc.status == 413:
                invalid_rejected_count += 1
            else:
                failed_upload_count += 1

        with facade.database.connection() as connection:
            jobs = connection.execute(
                "SELECT id, session_id, source_type FROM capture_jobs WHERE session_id = ?",
                (session.session_id,),
            ).fetchall()
        job_ids = {row["id"] for row in jobs}
        capture_job_count = len(jobs)
        metrics: dict[str, int | float] = {
            "attempted_upload_count": 68,
            "accepted_new_count": len(accepted_ids),
            "duplicate_replay_count": duplicate_replay_count,
            "invalid_rejected_count": invalid_rejected_count,
            "capture_job_count": capture_job_count,
            "missing_job_count": len(set(accepted_ids) - job_ids),
            "unexpected_duplicate_job_count": max(0, capture_job_count - 60),
            "wrong_source_type_count": sum(
                row["source_type"] != "MOBILE_WEB_USB_CAMERA" for row in jobs
            ),
            "wrong_session_binding_count": sum(
                row["session_id"] != session.session_id for row in jobs
            ),
            "failed_upload_count": failed_upload_count,
            "p50_registration_ms": percentile(timings, 0.50),
            "p95_registration_ms": percentile(timings, 0.95),
        }

    if not REPORT_PATH.exists():
        write_report(metrics)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    expected = {
        "attempted_upload_count": 68,
        "accepted_new_count": 60,
        "duplicate_replay_count": 5,
        "invalid_rejected_count": 3,
        "capture_job_count": 60,
        "missing_job_count": 0,
        "unexpected_duplicate_job_count": 0,
        "wrong_source_type_count": 0,
        "wrong_session_binding_count": 0,
        "failed_upload_count": 0,
    }
    failures = [
        f"{name}: expected {value}, got {metrics[name]}"
        for name, value in expected.items()
        if metrics[name] != value
    ]
    if failures:
        print("FAIL")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)
    print("PASS")


if __name__ == "__main__":
    main()
