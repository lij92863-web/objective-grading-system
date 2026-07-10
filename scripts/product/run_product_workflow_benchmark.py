"""Deterministic 50-student, 52-capture local product workflow benchmark."""

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.capture import CaptureQueue, CaptureSourceType
from app.classes import ClassService
from app.exam_session import AssetService, AssetType, SessionService
from app.product.finalization import FinalScoreService, FinalizationGateState
from app.product.pipeline import MockRecognitionInput, ProductPipeline
from app.product.review.manual_resolution import TeacherAction
from app.product.review.review_workflow import ReviewWorkflow
from app.roster.roster_importer import RosterImporter
from app.storage import LocalDatabase
from scripts.product.product_workflow_oracle import compare_final_scores


STUDENT_COUNT = 50
VALID_CAPTURE_COUNT = 50
DUPLICATE_CAPTURE_COUNT = 2


def run_benchmark(output_dir: Path) -> dict[str, object]:
    timings: list[float] = []
    finalization_blocks = 0
    with tempfile.TemporaryDirectory(dir=ROOT / "data") as temporary:
        work = Path(temporary)
        database, session = _build_foundation(work)
        expected = _expected_truth(database, session.class_id)
        queue = CaptureQueue(database, work / "local_app")
        pipeline = ProductPipeline(database, work / "local_app")
        review = ReviewWorkflow(database)
        final = FinalScoreService(database, work / "exports")

        valid_job_to_student: dict[str, str] = {}
        for index in range(VALID_CAPTURE_COUNT):
            started = time.perf_counter()
            job = queue.add_bytes(
                session.session_id,
                f"original-{index + 1:03d}.png",
                b"\x89PNG\r\n\x1a\nbenchmark-original" + bytes([index]),
                CaptureSourceType.MANUAL_UPLOAD,
            ).job
            student_no = f"{index + 1:03d}"
            valid_job_to_student[job.capture_job_id] = student_no
            expected[index]["source_capture_job_id"] = job.capture_job_id
            pipeline.process_mock(
                job.capture_job_id,
                _recognition_for_original(index, student_no),
            )
            timings.append((time.perf_counter() - started) * 1000)

        duplicate_job_ids = []
        for offset, student_no in enumerate(("011", "012"), start=1):
            started = time.perf_counter()
            job = queue.add_bytes(
                session.session_id,
                f"duplicate-{offset}.png",
                b"\x89PNG\r\n\x1a\nbenchmark-duplicate" + bytes([offset]),
                CaptureSourceType.MANUAL_UPLOAD,
            ).job
            duplicate_job_ids.append(job.capture_job_id)
            pipeline.process_mock(
                job.capture_job_id,
                MockRecognitionInput(
                    student_no=student_no,
                    answer_candidates={1: "A", 2: "B"},
                ),
            )
            timings.append((time.perf_counter() - started) * 1000)

        first_decision = final.confirm_teacher(session.session_id)
        finalization_blocks += int(first_decision.state is FinalizationGateState.BLOCKED)
        issues = review.list_issues(session.session_id)
        identity = [item for item in issues if item.issue_type == "IDENTITY_MISSING"]
        answer_issues = [item for item in issues if item.issue_type == "ANSWER_UNREADABLE"]
        duplicates = [item for item in issues if item.issue_type == "IDENTITY_DUPLICATE"]

        issue_jobs = _issue_job_map(database, [item.issue_id for item in issues])
        for issue in identity:
            review.resolve_identity(
                issue.issue_id,
                student_no=valid_job_to_student[issue_jobs[issue.issue_id]],
            )
        identity_decision = final.confirm_teacher(session.session_id)
        finalization_blocks += int(identity_decision.state is FinalizationGateState.BLOCKED)
        for issue in answer_issues:
            review.resolve_answer(
                issue.issue_id,
                TeacherAction.MANUAL_SCORE,
                manual_score=1,
                reason="benchmark teacher verified the unreadable mark",
            )
        answer_decision = final.confirm_teacher(session.session_id)
        finalization_blocks += int(answer_decision.state is FinalizationGateState.BLOCKED)
        for issue in duplicates:
            review.exclude_capture_from_identity_issue(
                issue.issue_id,
                reason="deterministic duplicate capture fixture",
            )
        ready = final.confirm_teacher(session.session_id)
        if ready.state is not FinalizationGateState.READY:
            raise RuntimeError(f"benchmark did not reach READY: {ready.blockers}")
        final.finalize(session.session_id)

        with database.connection() as connection:
            actual = [dict(row) for row in connection.execute(
                "SELECT * FROM final_scores WHERE session_id = ? ORDER BY student_no",
                (session.session_id,),
            ).fetchall()]
            job_rows = connection.execute(
                "SELECT id, state FROM capture_jobs WHERE session_id = ?",
                (session.session_id,),
            ).fetchall()
        excluded_duplicate_count = sum(
            1 for row in job_rows
            if row["id"] in duplicate_job_ids and row["state"] == "EXCLUDED"
        )

    metrics = {
        "class_count": 1,
        "student_count": STUDENT_COUNT,
        "capture_job_count": len(job_rows),
        "valid_capture_job_count": VALID_CAPTURE_COUNT,
        "duplicate_capture_job_count": DUPLICATE_CAPTURE_COUNT,
        "excluded_duplicate_capture_count": excluded_duplicate_count,
        "processed_job_count": sum(
            row["state"] in {"CONFIRMED", "EXCLUDED"} for row in job_rows
        ),
        "identity_issue_count": len(identity),
        "answer_issue_count": len(answer_issues),
        "duplicate_issue_count": len(duplicates),
        "finalization_block_count": finalization_blocks,
        **compare_final_scores(expected, actual),
        "p95_processing_time_ms": _p95(timings),
    }
    _write_report(output_dir, metrics)
    return metrics


def _build_foundation(work: Path):
    database = LocalDatabase(work / "product.sqlite3")
    classroom = ClassService(database).create_class("Benchmark Class")
    roster = work / "roster.csv"
    roster.write_text(
        "student_no,name\n" + "".join(
            f"{number:03d},Student {number:03d}\n"
            for number in range(1, STUDENT_COUNT + 1)
        ),
        encoding="utf-8-sig",
    )
    RosterImporter(database).import_file(classroom.class_id, roster)
    session = SessionService(database).create_session("Benchmark Exam", classroom.class_id)
    assets = AssetService(database, work / "local_app")
    answer = work / "answer.csv"
    answer.write_text(
        "question,answer,type\n1,A,single_choice\n2,B,single_choice\n",
        encoding="utf-8-sig",
    )
    template = work / "template.json"
    template.write_text("{}", encoding="utf-8")
    assets.register(session.session_id, answer, AssetType.ANSWER_KEY)
    assets.register(session.session_id, template, AssetType.TEMPLATE)
    return database, session


def _expected_truth(database, class_id: str) -> list[dict[str, object]]:
    with database.connection() as connection:
        students = connection.execute(
            "SELECT id, student_no, name FROM students WHERE class_id = ? ORDER BY student_no",
            (class_id,),
        ).fetchall()
    return [
        {
            "student_id": row["id"],
            "student_no": row["student_no"],
            "student_name": row["name"],
            "normalized_answers": (
                {1: ["A"]} if index in range(10, 20)
                else {1: ["A"], 2: ["B"]}
            ),
            "manual_overrides": {2: 1} if index in range(10, 20) else {},
            "score": 2.0,
            "max_score": 2.0,
            "percent": 100.0,
            "included": True,
        }
        for index, row in enumerate(students)
    ]


def _recognition_for_original(index: int, student_no: str) -> MockRecognitionInput:
    if index < 10:
        return MockRecognitionInput(answer_candidates={1: "A", 2: "B"})
    if index < 20:
        return MockRecognitionInput(
            student_no=student_no,
            answer_candidates={1: "A", 2: None},
        )
    return MockRecognitionInput(
        student_no=student_no,
        answer_candidates={1: "A", 2: "B"},
    )


def _issue_job_map(database, issue_ids: list[str]) -> dict[str, str]:
    if not issue_ids:
        return {}
    placeholders = ",".join("?" for _ in issue_ids)
    with database.connection() as connection:
        rows = connection.execute(
            f"SELECT id, capture_job_id FROM review_issues WHERE id IN ({placeholders})",
            tuple(issue_ids),
        ).fetchall()
    return {str(row["id"]): str(row["capture_job_id"]) for row in rows}


def _p95(timings: list[float]) -> float:
    ordered = sorted(timings)
    return round(ordered[max(0, int(len(ordered) * 0.95) - 1)], 3)


def _write_report(output_dir: Path, metrics: dict[str, object]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "product_workflow_benchmark.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    markdown = "# Product Workflow Benchmark\n\n" + "\n".join(
        f"- {key}: {value}" for key, value in metrics.items()
    )
    (output_dir / "product_workflow_benchmark.md").write_text(
        markdown + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "data" / "local_app" / "benchmarks",
    )
    metrics = run_benchmark(parser.parse_args().output_dir)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    required = {
        "wrong_finalized_count": 0,
        "capture_job_count": 52,
        "excluded_duplicate_capture_count": 2,
        "actual_final_score_count": 50,
    }
    failed = any(metrics[key] != value for key, value in required.items())
    print("FAIL" if failed else "PASS")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
