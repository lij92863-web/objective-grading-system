"""CSV report pipeline — bridges report_builders → CSV exporters.

Orchestrates the full CSV output flow: takes grading results,
generates rows via report_builders, writes files via CSV exporters.
Does NOT write Excel or HTML. Does NOT import legacy or web.
"""

import dataclasses
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

from .report_builders.score_rows import build_simple_score_rows
from .report_builders.item_analysis import build_item_analysis_rows
from .report_builders.knowledge_profiles import build_knowledge_profiles
from .report_builders.class_report import build_class_report
from .report_builders.validation_report import build_validation_report
from .report_builders.practice_recommendations import (
    build_correct_question_ids,
    build_target_difficulties,
    build_practice_recommendations,
)

from app.infrastructure.exporters.contracts import ExportRequest
from app.infrastructure.exporters.summary_csv_exporter import SummaryCsvExporter
from app.infrastructure.exporters.detail_csv_exporter import DetailCsvExporter
from app.infrastructure.exporters.item_analysis_csv_exporter import ItemAnalysisCsvExporter
from app.infrastructure.exporters.knowledge_profiles_csv_exporter import KnowledgeProfilesCsvExporter
from app.infrastructure.exporters.practice_recommendations_csv_exporter import PracticeRecommendationsCsvExporter
from app.infrastructure.exporters.class_report_csv_exporter import ClassReportCsvExporter
from app.infrastructure.exporters.validation_report_csv_exporter import ValidationReportCsvExporter
from app.infrastructure.exporters.student_report_csv_exporter import StudentReportCsvExporter


@dataclasses.dataclass
class CsvPipelineInput:
    """Input for the CSV report pipeline — mirrors workflow data."""
    output_dir: Path = Path(".")
    answer_key: object = None     # legacy AnswerKey (dataclass)
    results: list = dataclasses.field(default_factory=list)   # legacy StudentResult list
    submissions: list = dataclasses.field(default_factory=list)  # legacy Submission list
    profiles: list = dataclasses.field(default_factory=list)    # legacy KnowledgeProfile list
    question_bank: list = dataclasses.field(default_factory=list)  # legacy BankQuestion list
    exam_meta: dict = dataclasses.field(default_factory=dict)
    weak_threshold: float = 70.0
    practice_per_tag: int = 3
    extra_validation_rows: list = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class CsvPipelineResult:
    """Output of the CSV report pipeline."""
    ok: bool = True
    generated_files: tuple = ()
    warnings: tuple = ()
    out_dir: str = ""


def _legacy_result_to_dict(r) -> dict:
    return dict(
        student_id=r.student_id, name=r.name, score=r.score,
        max_score=r.max_score, percent=r.percent,
        correct_count=r.correct_count,
        wrong_or_partial_count=r.wrong_or_partial_count,
        blank_count=r.blank_count, invalid_count=r.invalid_count,
          details=[dict(number=d.number, status=d.status, score=d.score,
                        max_score=d.max_score,
                        actual=d.actual,
                        raw_actual=d.raw_actual,
                        student_answer=d.student_answer,
                        normalized_answer=d.normalized_answer,
                        correct_answer=d.correct_answer,
                        reason=d.reason,
                        needs_review=d.needs_review)
                   for d in r.details],
    )


def _legacy_spec_to_dict(s) -> dict:
    return dict(question=s.number, tags=list(s.tags), points=s.points,
                source_id=s.source_id, status=s.status, difficulty=s.difficulty,
                answer_text=getattr(s, 'answer_text', '') or "".join(sorted(s.answers)),
                answer="".join(sorted(s.answers)),
                partial_credit=s.partial_credit)


def _legacy_sub_to_dict(s) -> dict:
    return dict(
        student_id=s.student_id, name=s.name,
        answers={k: frozenset(v) for k, v in s.answers.items()},
        raw_answers=dict(s.raw_answers),
        extra_questions=list(s.extra_questions),
    )


def _legacy_profile_to_dict(p) -> dict:
    return dict(
        student_id=p.student_id, name=p.name, tag=p.tag,
        score=p.score, max_score=p.max_score, mastery=p.mastery,
        question_count=p.question_count,
        weak=p.weak, mastery_level=p.mastery_level,
    )


def _legacy_bank_to_dict(b) -> dict:
    return dict(
        question_id=b.question_id, stem=b.stem, answer=b.answer,
        tags=list(b.tags), difficulty=b.difficulty,
    )


def run_csv_report_pipeline(inp: CsvPipelineInput) -> CsvPipelineResult:
    """Run the full CSV report pipeline.

    Generates all 8 CSV files via builders + exporters.
    Does NOT write Excel or HTML.
    """
    out_dir = Path(inp.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    request = ExportRequest(output_dir=out_dir)
    warnings: list[str] = []
    generated: list[str] = []

    ak = inp.answer_key
    results = inp.results
    specs = [_legacy_spec_to_dict(s) for s in ak.questions]
    results_d = [_legacy_result_to_dict(r) for r in results]

    # summary.csv
    summary_rows = []
    sorted_r = sorted(enumerate(results), key=lambda i: (-i[1].score, i[0]))
    ranks_dict = {}
    prev_score = None; cur_rank = 0
    for pos, (idx, res) in enumerate(sorted_r, start=1):
        if prev_score is None or res.score != prev_score: cur_rank = pos
        ranks_dict[res.student_id] = cur_rank
        prev_score = res.score
    for result in results:
        summary_rows.append(dict(
            student_id=result.student_id, name=result.name,
            rank=ranks_dict.get(result.student_id, 0),
            score=result.score, max_score=result.max_score,
            percent=result.percent, correct_count=result.correct_count,
            wrong_or_partial_count=result.wrong_or_partial_count,
            blank_count=result.blank_count, invalid_count=result.invalid_count,
        ))
    r = SummaryCsvExporter().export(request, summary_rows)
    generated.extend(r.generated_files)
    warnings.extend(r.warnings)

    # detail.csv
    detail_rows = []
    question_specs = ak.by_number
    for result in results:
        for detail in result.details:
            spec = question_specs[detail.number]
            detail_rows.append(dict(
                student_id=result.student_id, name=result.name,
                question=detail.number, question_id=spec.source_id,
                question_status=spec.status, difficulty=spec.difficulty,
                tags=";".join(spec.tags),
                expected=getattr(spec, 'answer_text', '') or "".join(sorted(spec.answers)),
                actual="".join(sorted(detail.actual)),
                raw_actual=detail.raw_actual, score=detail.score,
                max_score=detail.max_score, status=detail.status,
            ))
    r = DetailCsvExporter().export(request, detail_rows)
    generated.extend(r.generated_files)
    warnings.extend(r.warnings)

    # item_analysis.csv
    item_rows = build_item_analysis_rows(specs, results_d)
    r = ItemAnalysisCsvExporter().export(request, item_rows)
    generated.extend(r.generated_files)
    warnings.extend(r.warnings)

    # knowledge_profiles
    kp_rows = build_knowledge_profiles(specs, results_d, inp.weak_threshold)
    r = KnowledgeProfilesCsvExporter().export(request, kp_rows)
    generated.extend(r.generated_files)
    warnings.extend(r.warnings)

    # practice_recommendations
    if inp.question_bank:
        bank = [_legacy_bank_to_dict(b) for b in inp.question_bank]
        correct_ids = build_correct_question_ids(specs, results_d)
        target_diffs = build_target_difficulties(specs, results_d)
        practice_rows = build_practice_recommendations(
            kp_rows, bank, inp.practice_per_tag, correct_ids, target_diffs)
        r = PracticeRecommendationsCsvExporter().export(request, practice_rows)
    else:
        r = PracticeRecommendationsCsvExporter().export(request, [])
    generated.extend(r.generated_files)
    warnings.extend(r.warnings)

    # class_report
    profiles_d = [_legacy_profile_to_dict(p) for p in inp.profiles]
    cr_rows = build_class_report(inp.exam_meta, specs, results_d, profiles_d)
    r = ClassReportCsvExporter().export(request, cr_rows)
    generated.extend(r.generated_files)
    warnings.extend(r.warnings)

    # validation_report
    subs_d = [_legacy_sub_to_dict(s) for s in inp.submissions]
    ak_dict = {
        "by_number": {s.number: dict(question=s.number, source_id=s.source_id, tags=list(s.tags),
                                     status=s.status, points=s.points) for s in ak.questions},
        "questions": [dict(question=s.number, source_id=s.source_id, tags=list(s.tags),
                          status=s.status, points=s.points) for s in ak.questions],
        "duplicate_questions": list(getattr(ak, 'duplicate_questions', [])),
    }
    vr_rows = build_validation_report(ak_dict, subs_d, results_d, profiles_d, None)
    r = ValidationReportCsvExporter().export(request, vr_rows)
    generated.extend(r.generated_files)
    warnings.extend(r.warnings)

    # student_report — reuse ranks_dict from summary section
    from collections import defaultdict as _defaultdict
    sr_rows = []
    for result in results:
        by_status = _defaultdict(list)
        for d in result.details:
            by_status[d.status].append(str(d.number))
        student_kp = [p for p in profiles_d if p["student_id"] == result.student_id]
        weak_tags = [p["tag"] for p in student_kp if p["weak"]]
        sr_rows.append(dict(
            student_id=result.student_id, name=result.name,
            score=result.score, max_score=result.max_score,
            percent=result.percent, rank=ranks_dict.get(result.student_id, 0),
            weak_tags=";".join(weak_tags),
            wrong_questions=";".join(by_status.get("wrong", []) + by_status.get("invalid", [])),
            partial_questions=";".join(by_status.get("partial", [])),
            blank_questions=";".join(by_status.get("blank", [])),
            invalid_questions=";".join(by_status.get("invalid", [])),
        ))
    r = StudentReportCsvExporter().export(request, sr_rows)
    generated.extend(r.generated_files)
    warnings.extend(r.warnings)

    return CsvPipelineResult(
        ok=True,
        generated_files=tuple(sorted(set(generated))),
        warnings=tuple(w for w in warnings if w),
        out_dir=str(out_dir),
    )
