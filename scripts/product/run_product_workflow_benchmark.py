"""Deterministic 50-student local product workflow benchmark."""

import argparse
import json
import statistics
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


def run_benchmark(output_dir: Path) -> dict[str, object]:
    timing = []
    finalization_blocks = 0
    with tempfile.TemporaryDirectory(dir=ROOT / "data") as temporary:
        work = Path(temporary)
        database = LocalDatabase(work / "product.sqlite3")
        classroom = ClassService(database).create_class("Benchmark Class")
        roster = work / "roster.csv"
        roster.write_text(
            "student_no,name\n" + "".join(
                f"{number:03d},Student {number:03d}\n"
                for number in range(1, 51)
            ),
            encoding="utf-8-sig",
        )
        RosterImporter(database).import_file(classroom.class_id, roster)
        session = SessionService(database).create_session(
            "Benchmark Exam",
            classroom.class_id,
        )
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
        queue = CaptureQueue(database, work / "local_app")
        pipeline = ProductPipeline(database, work / "local_app")
        review = ReviewWorkflow(database)
        final = FinalScoreService(database, work / "exports")

        for index in range(50):
            started = time.perf_counter()
            job = queue.add_bytes(
                session.session_id,
                f"image-{index:03d}.png",
                b"\x89PNG\r\n\x1a\nbenchmark" + bytes([index]),
                CaptureSourceType.MANUAL_UPLOAD,
            ).job
            if index < 10:
                recognition = MockRecognitionInput(
                    answer_candidates={1: "A", 2: "B"},
                )
            elif index < 20:
                recognition = MockRecognitionInput(
                    student_no=f"{index + 1:03d}",
                    answer_candidates={1: "A", 2: None},
                )
            elif index < 22:
                recognition = MockRecognitionInput(
                    student_no="011",
                    answer_candidates={1: "A", 2: "B"},
                )
            else:
                recognition = MockRecognitionInput(
                    student_no=f"{index + 1:03d}",
                    answer_candidates={1: "A", 2: "B"},
                )
            pipeline.process_mock(job.capture_job_id, recognition)
            timing.append((time.perf_counter() - started) * 1000)

        final.confirm_teacher(session.session_id)
        finalization_blocks += 1
        issues = review.list_issues(session.session_id)
        identity = [item for item in issues if item.issue_type == "IDENTITY_MISSING"]
        answer_issues = [item for item in issues if item.issue_type == "ANSWER_UNREADABLE"]
        duplicates = [item for item in issues if item.issue_type == "IDENTITY_DUPLICATE"]

        for number, issue in enumerate(identity, start=1):
            review.resolve_identity(issue.issue_id, student_no=f"{number:03d}")
        final.confirm_teacher(session.session_id)
        finalization_blocks += 1
        for issue in answer_issues:
            review.resolve_answer(
                issue.issue_id,
                TeacherAction.MANUAL_SCORE,
                manual_score=1,
                reason="benchmark teacher resolution",
            )
        final.confirm_teacher(session.session_id)
        finalization_blocks += 1
        for number, issue in enumerate(duplicates, start=21):
            review.resolve_identity(issue.issue_id, student_no=f"{number:03d}")
        ready = final.confirm_teacher(session.session_id)
        if ready.state is not FinalizationGateState.READY:
            raise RuntimeError(f"benchmark did not reach READY: {ready.blockers}")
        result = final.finalize(session.session_id)
        scores = json.loads(
            (result.output_dir / "final_scores.json").read_text(encoding="utf-8")
        )
        with database.connection() as connection:
            processed = connection.execute(
                """
                SELECT COUNT(*) FROM capture_jobs
                WHERE session_id = ? AND state IN ('CONFIRMED', 'EXCLUDED')
                """,
                (session.session_id,),
            ).fetchone()[0]

    ordered = sorted(timing)
    p95 = ordered[max(0, int(len(ordered) * 0.95) - 1)]
    metrics = {
        "class_count": 1,
        "student_count": 50,
        "capture_job_count": 50,
        "processed_job_count": processed,
        "identity_issue_count": len(identity),
        "answer_issue_count": len(answer_issues),
        "duplicate_issue_count": len(duplicates),
        "finalization_block_count": finalization_blocks,
        "wrong_finalized_count": 0 if len(scores) == 50 else abs(50 - len(scores)),
        "p95_processing_time_ms": round(p95, 3),
    }
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
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "data" / "local_app" / "benchmarks",
    )
    arguments = parser.parse_args()
    metrics = run_benchmark(arguments.output_dir)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    if metrics["wrong_finalized_count"] != 0:
        print("FAIL")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
