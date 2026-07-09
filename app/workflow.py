"""Unified grading workflow for CLI, local web UI, and future automation."""

import csv
import json
import shutil
import statistics
import tempfile
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from legacy import objective_grader_legacy as legacy
from app.validators import has_blocking_errors
from app.infrastructure.exporters.contracts import ExportRequest
from app.infrastructure.exporters.simple_score_workbook_exporter import (
    SimpleScoreWorkbookExporter,
)
from app.infrastructure.exporters.workbook_exporter import WorkbookExporter
from app.infrastructure.exporters.simple_report_html_exporter import (
    SimpleReportHtmlExporter,
)
from app.infrastructure.exporters.advanced_dashboard_html_exporter import (
    AdvancedDashboardHtmlExporter,
)
from app.infrastructure.exporters.report_index_html_exporter import (
    ReportIndexHtmlExporter,
)
from app.application.use_cases.report_builders.simple_score_rows import (
    build_simple_score_rows,
)
from app.application.use_cases.report_builders.item_stats import (
    build_item_stats,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_FILE_NAMES = {
    "summary.csv",
    "detail.csv",
    "item_analysis.csv",
    "knowledge_profile.csv",
    "practice_recommendations.csv",
    "class_report.csv",
    "validation_report.csv",
    "student_report.csv",
    "student_wrong_list.csv",
    "teaching_plan.csv",
    "class_remedial_package.csv",
    "layered_remedial_plan.csv",
    "exam_report.xlsx",
    "simple_score_report.xlsx",
    "simple_report.html",
    "advanced_dashboard.html",
    "index.html",
    "teaching_plan.html",
    "class_remedial_package.html",
    "layered_remedial_plan.html",
    "error_report.html",
}


def make_run_id(now: Optional[datetime] = None) -> str:
    return (now or datetime.now()).strftime("%Y%m%d_%H%M%S")


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def safe_slug(value: str) -> str:
    return legacy.safe_slug(value)


def write_json(path: Path, data: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_dicts(path: Path, rows: List[Dict[str, object]], fields: Optional[List[str]] = None) -> None:
    if fields is None:
        fields = list(rows[0]) if rows else []
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        if fields:
            writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv_dicts(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def display_percent(value: object) -> str:
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "0.00%"


def main_wrong_answer_from_distribution(distribution: object, expected: str = "") -> str:
    if not isinstance(distribution, dict):
        return ""
    candidates = []
    for option, count in distribution.items():
        option_text = str(option)
        if option_text in {"", "(blank)", expected}:
            continue
        try:
            candidates.append((option_text, int(count)))
        except (TypeError, ValueError):
            continue
    if not candidates:
        return ""
    option, count = max(candidates, key=lambda item: item[1])
    return f"{option}（{count}人）"


def teaching_level(accuracy: float, blank_rate: float) -> Tuple[str, str, str]:
    if accuracy < 40:
        return "重点讲评", "正确率较低或空白较多", "先讲清核心思路，再安排同类题即时巩固。"
    if accuracy < 60:
        return "选择性讲评", "部分学生掌握不稳", "针对主要错误选项讲解，保留学生订正时间。"
    if accuracy < 80:
        return "快速点拨", "多数学生已掌握", "用 2-3 分钟点拨易错点即可。"
    return "可略讲", "全班掌握较好", "可只公布答案，把课堂时间留给薄弱题。"


def build_teaching_plan(item_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for row in item_rows:
        accuracy = float(row.get("accuracy", 0) or 0)
        blank_rate = float(row.get("blank_rate", 0) or 0)
        level, reason, suggestion = teaching_level(accuracy, blank_rate)
        distribution = row.get("distribution", {})
        main_wrong = main_wrong_answer_from_distribution(distribution, str(row.get("answer", "")))
        rows.append(
            {
                "priority_level": level,
                "question_id": f"Q{row.get('question', '')}",
                "accuracy": accuracy,
                "blank_rate": blank_rate,
                "main_wrong_answer": main_wrong,
                "tags": row.get("tags", ""),
                "reason": reason,
                "teaching_suggestion": suggestion,
            }
        )
    order = {"重点讲评": 0, "选择性讲评": 1, "快速点拨": 2, "可略讲": 3}
    return sorted(rows, key=lambda item: (order.get(str(item["priority_level"]), 9), float(item["accuracy"])))


def build_student_wrong_list(results: List[legacy.StudentResult]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for result in results:
        wrong = []
        partial = []
        blank = []
        invalid = []
        for detail in result.details:
            if detail.status == "wrong":
                wrong.append(str(detail.number))
            elif detail.status == "partial":
                partial.append(str(detail.number))
            elif detail.status == "blank":
                blank.append(str(detail.number))
            elif detail.status in {"invalid", "unrecognized"}:
                invalid.append(str(detail.number))
        rows.append(
            {
                "student_id": result.student_id,
                "name": result.name,
                "wrong_questions": ";".join(wrong),
                "partial_questions": ";".join(partial),
                "blank_questions": ";".join(blank),
                "invalid_questions": ";".join(invalid),
            }
        )
    return rows


def build_class_remedial_package(
    profiles: List[legacy.KnowledgeProfile],
    teaching_rows: List[Dict[str, object]],
    question_bank: Optional[List[legacy.BankQuestion]] = None,
) -> List[Dict[str, object]]:
    question_bank = question_bank or []
    if not question_bank:
        weak_tags = sorted({profile.tag for profile in profiles if profile.mastery < 80})
        return [
            {
                "weak_tag": tag,
                "related_questions": ";".join(
                    str(row["question_id"])
                    for row in teaching_rows
                    if tag and tag in str(row.get("tags", "")).split(";")
                ),
                "class_accuracy": "",
                "affected_student_count": sum(1 for profile in profiles if profile.tag == tag and profile.mastery < 70),
                "recommended_question_ids": "",
                "suggested_difficulty": "",
                "teaching_note": "未提供题库，无法自动推荐练习；请教师根据薄弱知识点人工选择练习。",
            }
            for tag in weak_tags
        ]
    bank_by_tag: Dict[str, List[legacy.BankQuestion]] = defaultdict(list)
    for question in question_bank:
        for tag in question.tags:
            bank_by_tag[tag].append(question)

    tag_profiles: Dict[str, List[legacy.KnowledgeProfile]] = defaultdict(list)
    for profile in profiles:
        tag_profiles[profile.tag].append(profile)

    rows: List[Dict[str, object]] = []
    for tag, items in tag_profiles.items():
        mastery = statistics.mean(item.mastery for item in items) if items else 0
        affected = sum(1 for item in items if item.mastery < 70)
        if mastery >= 80 and affected == 0:
            continue
        related = [
            str(row["question_id"])
            for row in teaching_rows
            if tag and tag in str(row.get("tags", "")).split(";")
        ]
        candidates = sorted(bank_by_tag.get(tag, []), key=lambda item: (item.difficulty or 9, item.question_id))[:5]
        rows.append(
            {
                "weak_tag": tag,
                "related_questions": ";".join(related),
                "class_accuracy": round(mastery, 2),
                "affected_student_count": affected,
                "recommended_question_ids": ";".join(question.question_id for question in candidates),
                "suggested_difficulty": "基础到中档" if mastery < 60 else "中档巩固",
                "teaching_note": "先补概念和基本方法，再做短练。" if mastery < 60 else "用同类变式巩固，防止会而不稳。",
            }
        )
    return sorted(rows, key=lambda item: (float(item["class_accuracy"]), -int(item["affected_student_count"])))


def build_layered_remedial_plan(
    results: List[legacy.StudentResult],
    teaching_rows: List[Dict[str, object]],
) -> List[Dict[str, object]]:
    focus_questions = [str(row["question_id"]) for row in teaching_rows if row.get("priority_level") in {"重点讲评", "选择性讲评"}]
    quick_questions = [str(row["question_id"]) for row in teaching_rows if row.get("priority_level") == "快速点拨"]
    layers = [
        ("基础巩固层", "得分率 < 60%", lambda percent: percent < 60, "回到基础概念和典型例题，完成重点错题订正。", focus_questions[:8], "需要更明确的步骤示范和短频反馈。"),
        ("稳定提升层", "60% <= 得分率 < 80%", lambda percent: 60 <= percent < 80, "完成重点题变式练习，整理主要错误原因。", focus_questions[:5] + quick_questions[:3], "适合课堂讲评后安排 10-15 分钟巩固。"),
        ("拓展提升层", "得分率 >= 80%", lambda percent: percent >= 80, "完成少量综合变式，尝试说明解题思路。", quick_questions[:5], "以防粗心和提升迁移能力为主。"),
    ]
    rows: List[Dict[str, object]] = []
    for name, score_range, predicate, task, questions, note in layers:
        count = sum(1 for result in results if predicate(result.percent))
        rows.append(
            {
                "layer_name": name,
                "score_range": score_range,
                "student_count": count,
                "suggested_task": task,
                "recommended_question_ids": ";".join(questions),
                "teacher_note": note,
            }
        )
    return rows


def write_teacher_html(path: Path, title: str, description: str, rows: List[Dict[str, object]]) -> None:
    headers = list(rows[0]) if rows else []
    header_html = "".join(f"<th>{legacy.html_escape(header)}</th>" for header in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{legacy.html_escape(row.get(header, ''))}</td>" for header in headers) + "</tr>"
        for row in rows
    )
    empty = '<div class="empty">暂无需要特别处理的数据。</div>' if not rows else ""
    table = f"<table><thead><tr>{header_html}</tr></thead><tbody>{body}</tbody></table>" if rows else empty
    html = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{legacy.html_escape(title)}</title>
<style>
body{{margin:0;background:#f5f8fc;color:#172033;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",Arial,sans-serif;font-size:17px;line-height:1.65}}
main{{max-width:1120px;margin:0 auto;padding:32px 20px}}
.hero{{background:#fff;border:1px solid #e4ebf5;border-radius:18px;padding:26px 28px;box-shadow:0 16px 38px rgba(31,61,98,.08);margin-bottom:18px}}
h1{{margin:0 0 8px;font-size:30px}}p{{margin:0;color:#667085}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e4ebf5;border-radius:16px;overflow:hidden;box-shadow:0 12px 28px rgba(31,61,98,.06)}}
th,td{{padding:14px 16px;border-bottom:1px solid #edf2f7;text-align:left;vertical-align:top}}th{{background:#f8fbff;color:#42526b;font-weight:750}}
tr:hover{{background:#f8fbff}}.empty{{padding:24px;background:#fff;border-radius:16px;border:1px dashed #cbd8e8;color:#667085;text-align:center}}
</style></head><body><main><section class="hero"><h1>{legacy.html_escape(title)}</h1><p>{legacy.html_escape(description)}</p></section>{table}</main></body></html>"""
    path.write_text(html, encoding="utf-8")


def write_error_report(path: Path, validation_rows: List[Dict[str, object]]) -> None:
    blocking = [row for row in validation_rows if has_blocking_errors([row])]
    write_teacher_html(
        path,
        "批改前需要先处理的问题",
        "系统发现会影响成绩准确性的错误。请先修正这些问题，再重新批改。",
        blocking or validation_rows,
    )


def append_teaching_priority_to_dashboard(path: Path, teaching_rows: List[Dict[str, object]]) -> None:
    if not path.exists():
        return
    groups = ["重点讲评", "选择性讲评", "快速点拨", "可略讲"]
    cards = []
    for group in groups:
        rows = [row for row in teaching_rows if row.get("priority_level") == group]
        lines = "".join(
            f"""<tr><td>{legacy.html_escape(row.get('question_id', ''))}</td><td>{display_percent(row.get('accuracy'))}</td><td>{display_percent(row.get('blank_rate'))}</td><td>{legacy.html_escape(row.get('main_wrong_answer', ''))}</td><td>{legacy.html_escape(row.get('tags', ''))}</td><td>{legacy.html_escape(row.get('teaching_suggestion', ''))}</td></tr>"""
            for row in rows[:12]
        )
        body = (
            f"""<table class="compact-table"><thead><tr><th>题号</th><th>正确率</th><th>空白率</th><th>主要错误答案</th><th>关联知识点</th><th>建议处理方式</th></tr></thead><tbody>{lines}</tbody></table>"""
            if lines
            else '<div class="empty">暂无题目</div>'
        )
        cards.append(f'<article class="chart-card wide"><h2>{legacy.html_escape(group)}题</h2>{body}</article>')
    section = "\n".join(cards)
    html = path.read_text(encoding="utf-8")
    if "</section>" in html:
        html = html.replace("</section>", section + "\n</section>", 1)
    else:
        html = html.replace("</main>", section + "\n</main>")
    path.write_text(html, encoding="utf-8")


def replace_report_outputs(temp_dir: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in REPORT_FILE_NAMES:
        target = out_dir / name
        if target.exists():
            target.unlink()
    for item in temp_dir.iterdir():
        target = out_dir / item.name
        if item.is_file():
            shutil.copy2(str(item), str(target))
        elif item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(str(item), str(target))


def archive_exam_reports(
    source_dir: Path,
    archive_root: Path,
    meta: legacy.ExamMeta,
    report_paths: Iterable[Path],
    run_id: str,
    source_files: Optional[Dict[str, str]] = None,
) -> Path:
    class_part = safe_slug(meta.class_name or "default_class")
    exam_part = f"{safe_slug(meta.exam_date)}_{safe_slug(meta.exam_name)}_{run_id}"
    archive_dir = archive_root / class_part / exam_part
    archive_dir.mkdir(parents=True, exist_ok=False)
    metadata = {
        "exam_name": meta.exam_name,
        "class_name": meta.class_name,
        "subject": meta.subject,
        "exam_date": meta.exam_date,
        "run_id": run_id,
        "created_at": now_iso(),
        "source_files": source_files or {},
        "source_report_dir": str(source_dir.resolve()),
    }
    write_json(archive_dir / "exam_metadata.json", metadata)
    for report_path in report_paths:
        if report_path.exists():
            shutil.copy2(str(report_path), str(archive_dir / report_path.name))
    return archive_dir


def run_grading(
    answer_key_path: Path,
    submissions_path: Path,
    out_dir: Path,
    question_bank_path: Optional[Path] = None,
    exam_name: str = "demo_exam",
    class_name: str = "",
    subject: str = "",
    exam_date: Optional[str] = None,
    weak_threshold: float = 70.0,
    practice_per_tag: int = 3,
    archive_root: Optional[Path] = None,
    no_archive: bool = False,
    allow_errors: bool = False,
    run_id: Optional[str] = None,
    extra_validation_rows: Optional[List[Dict[str, object]]] = None,
    source_files: Optional[Dict[str, str]] = None,
) -> Dict[str, object]:
    answer_key_path = Path(answer_key_path)
    submissions_path = Path(submissions_path)
    out_dir = Path(out_dir)
    question_bank_path = Path(question_bank_path) if question_bank_path else None
    exam_date = exam_date or date.today().isoformat()
    run_id = run_id or make_run_id()

    answer_key = legacy.load_answer_key(answer_key_path)
    submissions = legacy.load_submissions(submissions_path, answer_key)
    results = legacy.grade_all(answer_key, submissions)
    meta = legacy.ExamMeta(exam_name=exam_name, class_name=class_name, subject=subject, exam_date=exam_date)
    profiles = legacy.build_knowledge_profiles(answer_key, results, weak_threshold=weak_threshold)
    question_bank = legacy.load_question_bank(question_bank_path) if question_bank_path else None
    validation_rows = legacy.build_validation_report(answer_key, submissions, results, profiles, question_bank)
    validation_rows.extend(extra_validation_rows or [])

    stats = legacy.basic_stats(results)
    blocked = has_blocking_errors(validation_rows)
    temp_parent = out_dir.parent if out_dir.parent.exists() else PROJECT_ROOT
    temp_dir_path = Path(tempfile.mkdtemp(prefix=f".{out_dir.name}_", dir=str(temp_parent)))
    archived_dir = None
    try:
        validation_path = temp_dir_path / "validation_report.csv"
        legacy.write_validation_report(validation_path, validation_rows)
        if blocked and not allow_errors:
            write_error_report(temp_dir_path / "error_report.html", validation_rows)
            replace_report_outputs(temp_dir_path, out_dir)
            return {
                "ok": False,
                "blocked": True,
                "message": "发现会影响成绩准确性的错误，已生成错误报告。",
                "out_dir": str(out_dir),
                "validation_report": str(out_dir / "validation_report.csv"),
                "error_report": str(out_dir / "error_report.html"),
                "run_id": run_id,
                "stats": stats,
            }

        summary_path = temp_dir_path / "summary.csv"
        detail_path = temp_dir_path / "detail.csv"
        item_analysis_path = temp_dir_path / "item_analysis.csv"
        knowledge_profile_path = temp_dir_path / "knowledge_profile.csv"
        practice_path = temp_dir_path / "practice_recommendations.csv"
        class_report_path = temp_dir_path / "class_report.csv"
        student_report_path = temp_dir_path / "student_report.csv"
        student_wrong_path = temp_dir_path / "student_wrong_list.csv"
        teaching_path = temp_dir_path / "teaching_plan.csv"
        class_remedial_path = temp_dir_path / "class_remedial_package.csv"
        layered_path = temp_dir_path / "layered_remedial_plan.csv"
        workbook_path = temp_dir_path / "exam_report.xlsx"
        simple_report_path = temp_dir_path / "simple_report.html"
        advanced_dashboard_path = temp_dir_path / "advanced_dashboard.html"
        simple_score_workbook_path = temp_dir_path / "simple_score_report.xlsx"
        index_path = temp_dir_path / "index.html"

        # -- CSV output via new pipeline ---------------------------------
        from app.application.use_cases.csv_report_pipeline import (
            run_csv_report_pipeline, CsvPipelineInput,
        )
        csv_result = run_csv_report_pipeline(CsvPipelineInput(
            output_dir=temp_dir_path,
            answer_key=answer_key,
            results=results,
            submissions=submissions,
            profiles=profiles,
            question_bank=list(question_bank) if question_bank else [],
            exam_meta={
                "exam_name": exam_name, "class_name": class_name,
                "subject": subject, "exam_date": exam_date,
            },
            weak_threshold=weak_threshold,
            practice_per_tag=practice_per_tag,
        ))
        # -- Excel / HTML analysis rows via application builders ----------
        simple_rows = build_simple_score_rows(results)
        item_rows = build_item_stats(answer_key, results)
        teaching_rows = build_teaching_plan(item_rows)
        class_remedial_rows = build_class_remedial_package(profiles, teaching_rows, question_bank)
        layered_rows = build_layered_remedial_plan(results, teaching_rows)
        wrong_rows = build_student_wrong_list(results)

        write_dicts(student_wrong_path, wrong_rows, ["student_id", "name", "wrong_questions", "partial_questions", "blank_questions", "invalid_questions"])
        write_dicts(teaching_path, teaching_rows, ["priority_level", "question_id", "accuracy", "blank_rate", "main_wrong_answer", "tags", "reason", "teaching_suggestion"])
        write_dicts(class_remedial_path, class_remedial_rows, ["weak_tag", "related_questions", "class_accuracy", "affected_student_count", "recommended_question_ids", "suggested_difficulty", "teaching_note"])
        write_dicts(layered_path, layered_rows, ["layer_name", "score_range", "student_count", "suggested_task", "recommended_question_ids", "teacher_note"])

        write_teacher_html(temp_dir_path / "teaching_plan.html", "讲评优先级建议", "按正确率、空白率和主要错误答案整理，帮助决定讲评课先讲什么。", teaching_rows)
        write_teacher_html(temp_dir_path / "class_remedial_package.html", "班级统一补救练习包", "按薄弱知识点整理，适合全班统一巩固。", class_remedial_rows)
        write_teacher_html(temp_dir_path / "layered_remedial_plan.html", "分层补救建议", "按得分率分层，给出不同层次学生的练习建议。", layered_rows)

        SimpleScoreWorkbookExporter().export(
            ExportRequest(output_dir=temp_dir_path), simple_rows)
        html_meta = {
            "exam_name": exam_name, "class_name": class_name,
            "subject": subject, "exam_date": exam_date,
        }
        SimpleReportHtmlExporter().export(
            ExportRequest(output_dir=temp_dir_path), html_meta,
            results, simple_rows, item_rows)
        AdvancedDashboardHtmlExporter().export(
            ExportRequest(output_dir=temp_dir_path), html_meta,
            results, profiles, validation_rows, item_rows)
        append_teaching_priority_to_dashboard(advanced_dashboard_path, teaching_rows)
        ReportIndexHtmlExporter().export(
            ExportRequest(output_dir=temp_dir_path), html_meta,
            simple_report_path, advanced_dashboard_path,
            simple_score_workbook_path)

        report_files = [
            ("成绩总表", summary_path),
            ("每题明细", detail_path),
            ("每题分析", item_analysis_path),
            ("知识点画像", knowledge_profile_path),
            ("学生错题", student_wrong_path),
            ("讲评计划", teaching_path),
            ("班级补救", class_remedial_path),
            ("分层补救", layered_path),
            ("数据质量检查", validation_path),
        ]
        WorkbookExporter().export(
            ExportRequest(output_dir=temp_dir_path), report_files)
        replace_report_outputs(temp_dir_path, out_dir)

        metadata = {
            "exam_name": exam_name,
            "class_name": class_name,
            "subject": subject,
            "exam_date": exam_date,
            "run_id": run_id,
            "created_at": now_iso(),
            "source_files": source_files
            or {
                "answer_key": str(answer_key_path),
                "submissions": str(submissions_path),
                "question_bank": str(question_bank_path) if question_bank_path else "",
            },
            "student_count": len(results),
            "question_count": len(answer_key.questions),
            "blocked": blocked,
            "allow_errors": allow_errors,
            "report_files": sorted(name for name in REPORT_FILE_NAMES if (out_dir / name).exists()),
        }
        write_json(out_dir / "exam_metadata.json", metadata)

        if archive_root and not no_archive:
            report_paths = [out_dir / name for name in REPORT_FILE_NAMES if (out_dir / name).exists()]
            archived_dir = archive_exam_reports(out_dir, Path(archive_root), meta, report_paths, run_id, metadata["source_files"])

        priority_counts = Counter(row["priority_level"] for row in teaching_rows)
        return {
            "ok": True,
            "blocked": False,
            "message": "批改完成，可查看报告。",
            "out_dir": str(out_dir),
            "index": str(out_dir / "index.html"),
            "advanced_dashboard": str(out_dir / "advanced_dashboard.html"),
            "teaching_plan": str(out_dir / "teaching_plan.html"),
            "exam_report": str(out_dir / "exam_report.xlsx"),
            "archived_dir": str(archived_dir) if archived_dir else "",
            "run_id": run_id,
            "stats": stats,
            "student_count": len(results),
            "question_count": len(answer_key.questions),
            "priority_counts": dict(priority_counts),
            "weak_tag_count": len(class_remedial_rows),
        }
    except Exception:
        shutil.rmtree(temp_dir_path, ignore_errors=True)
        raise
    finally:
        if temp_dir_path.exists():
            shutil.rmtree(temp_dir_path, ignore_errors=True)
