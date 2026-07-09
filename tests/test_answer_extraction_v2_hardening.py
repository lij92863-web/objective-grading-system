from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from app.answer_extraction.answer_candidate_pool import AnswerCandidate, AnswerCandidatePool
from app.answer_extraction.answer_key_validator import validate_answer_key
from app.answer_extraction.answer_normalizer import normalize_answer
from app.answer_extraction.answer_sequence_validator import validate_answer_sequence
from app.answer_extraction.answer_table_extractor import extract_answer_tables
from app.answer_extraction.candidate_conflict_resolver import resolve_candidate_conflicts
from app.answer_extraction.cross_file_aligner import align_by_question_no
from app.answer_extraction.docx_native_parser import DocxParseError, parse_docx
from app.answer_extraction.document_model_loader import DocumentModelLoadError, load_document_model_json
from app.answer_extraction.extraction_engine import extract_answer_key, load_document
from app.answer_extraction.itemized_answer_extractor import extract_itemized_answers
from app.answer_extraction.itemized_block_segmenter import segment_itemized_blocks
from app.answer_extraction.llm_fallback_extractor import LlmFallbackConfig, LlmFallbackExtractor
from app.answer_extraction.mixed_file_splitter import split_mixed_document
from app.answer_extraction.question_index_builder import build_question_index
from app.answer_extraction.question_sequence_validator import validate_question_sequence
from app.answer_extraction.student_answer_grid_detector import detect_student_answer_grid
from app.answer_extraction.table_normalizer import normalize_table

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "tests" / "fixtures" / "answer_extraction" / "document_models_v2"


def fx(name: str) -> Path:
    return V2 / name


class AnswerExtractionV2HardeningTests(unittest.TestCase):
    def test_realistic_fixtures_all_load(self) -> None:
        for path in V2.glob("*.json"):
            with self.subTest(path=path.name):
                result = load_document_model_json(path)
                self.assertEqual(result.document.source_file, path.name)

    def test_document_model_loader_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text("{bad", encoding="utf-8")
            with self.assertRaises(DocumentModelLoadError):
                load_document_model_json(path)
            duplicate = {"document_id": "x", "blocks": [{"block_id": "p1", "order_index": 1}, {"block_id": "p1", "order_index": 2}], "tables": []}
            path.write_text(json.dumps(duplicate), encoding="utf-8")
            with self.assertRaises(DocumentModelLoadError):
                load_document_model_json(path)

    def test_docx_parser_handles_tabs_breaks_empty_cells_and_placeholders(self) -> None:
        xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
<w:p><w:r><w:t>前言</w:t><w:tab/><w:t>说明</w:t><w:br/><w:t>下一行</w:t></w:r></w:p>
<w:tbl><w:tr><w:tc><w:p><w:r><w:t>题号</w:t></w:r></w:p></w:tc><w:tc><w:p/></w:tc></w:tr>
<w:tr><w:tc><w:p><w:r><w:t>答案</w:t></w:r></w:p><w:p><w:r><w:t>第二段</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:drawing/></w:r></w:p></w:tc></w:tr></w:tbl>
<w:p><w:r><w:t>后记</w:t></w:r></w:p></w:body></w:document>"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.docx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("word/document.xml", xml)
            document = parse_docx(path)
            self.assertEqual([block.block_type for block in document.sorted_blocks()], ["paragraph", "table", "paragraph"])
            self.assertIn("下一行", document.sorted_blocks()[0].text)
            self.assertEqual(document.sorted_tables()[0].grid()[0][1], "")
            self.assertIn("[object]", document.sorted_tables()[0].grid()[1][1])
            with self.assertRaises(DocxParseError):
                parse_docx(Path(tmp) / "sample.txt")

    def test_table_normalizer_and_extractor_segmented_table(self) -> None:
        document = load_document(fx("type3_split_boxed_segmented_table_answer.json"))
        table = document.sorted_tables()[0]
        self.assertEqual(len(normalize_table(table).row_pair_indexes()), 2)
        pool = extract_answer_tables(document).candidate_pool
        self.assertEqual(pool.highest_confidence_candidate(3).normalized_answer, "BD")

    def test_student_answer_grid_v2_detection(self) -> None:
        document = load_document(fx("type4_question_with_empty_grid_realistic.json"))
        detection = detect_student_answer_grid(document.sorted_tables()[0], document)
        self.assertTrue(detection.is_student_answer_grid)
        self.assertIn("empty answer row", detection.reasons)
        self.assertEqual(extract_answer_tables(document).candidate_pool.question_numbers(), [])

    def test_itemized_extractor_supports_chinese_brackets_fill_blank_and_ignores_steps(self) -> None:
        choice_pool = extract_itemized_answers(load_document(fx("type2_same_file_itemized_with_chinese_brackets.json"))).candidate_pool
        self.assertEqual(choice_pool.highest_confidence_candidate(1).normalized_answer, "B")
        blank_pool = extract_itemized_answers(load_document(fx("type2_same_file_itemized_with_fill_blank.json"))).candidate_pool
        self.assertEqual(blank_pool.highest_confidence_candidate(12).normalized_answer, "x>1")
        step_pool = extract_itemized_answers(load_document(fx("type4_answer_itemized_with_analysis_steps.json"))).candidate_pool
        self.assertEqual(step_pool.question_numbers(), [1, 2])

    def test_itemized_block_segmenter_skips_years_and_step_markers(self) -> None:
        document = load_document(fx("type4_answer_itemized_with_analysis_steps.json"))
        segments = segment_itemized_blocks(document.sorted_blocks())
        self.assertEqual([segment.question_no for segment in segments], [1, 2])

    def test_answer_normalizer_v2(self) -> None:
        self.assertEqual(normalize_answer("D B").normalized_answer, "BD")
        self.assertEqual(normalize_answer("BBD").normalized_answer, "BD")
        self.assertIn("invalid_answer_token", normalize_answer("A;DROP").blocking_errors)
        self.assertEqual(normalize_answer(" \\frac{1}{2} ", "blank").normalized_answer, "\\frac{1}{2}")

    def test_question_index_source_span_and_sequence_validator(self) -> None:
        index = build_question_index(load_document(fx("type3_split_boxed_segmented_table_question.json")))
        self.assertEqual(index.by_number()[2].source_span.end_block, "p003")
        self.assertIn("duplicate_question_number", validate_question_sequence([1, 2, 2]).blocking_errors)
        self.assertIn("question_number_rewind", validate_question_sequence([1, 3, 2]).blocking_errors)

    def test_answer_sequence_validator_and_conflict_resolver(self) -> None:
        pool = AnswerCandidatePool()
        pool.add(AnswerCandidate(1, "B", "B", source_kind="answer_table", evidence_text="题号 1 答案 B", confidence=0.99))
        pool.add(AnswerCandidate(1, "C", "C", source_kind="explicit_answer", evidence_text="1.【答案】C", confidence=0.97))
        self.assertIn("duplicate_conflicting_answer", validate_answer_sequence(pool, {1}).blocking_errors)
        self.assertIn("duplicate_conflicting_answer", resolve_candidate_conflicts(pool).blocking_errors)

    def test_validator_v2_blocks_and_reviews(self) -> None:
        question_index = build_question_index(load_document(fx("type3_split_boxed_segmented_table_question.json")))
        pool = AnswerCandidatePool()
        pool.add(AnswerCandidate(1, "BD", "BD", source_kind="answer_table", evidence_text="题号 1 答案 BD", confidence=0.99))
        pool.add(AnswerCandidate(2, "C", "C", source_kind="llm_candidate", evidence_text="2.C", confidence=0.7))
        pool.add(AnswerCandidate(3, "BD", "BD", source_kind="answer_table", evidence_text="题号 3 答案 BD", confidence=0.99))
        report = validate_answer_key(question_index, pool, align_by_question_no(question_index, pool))
        self.assertIn("single_choice_multi_answer", report.blocking_errors)
        self.assertIn({"type": "llm_candidate_requires_review", "question_no": 2}, report.review_items)

    def test_mixed_file_splitter_finds_answer_region(self) -> None:
        split = split_mixed_document(load_document(fx("type2_same_file_itemized_with_chinese_brackets.json")))
        self.assertGreater(split.confidence, 0)
        self.assertEqual(split.boundary_block_id, "p004")

    def test_extraction_engine_realistic_four_paths_and_unknown_review(self) -> None:
        cases = [
            ([fx("type1_same_file_boxed_realistic.json")], "same_file_boxed"),
            ([fx("type2_same_file_itemized_with_chinese_brackets.json")], "same_file_itemized"),
            ([fx("type3_split_boxed_segmented_table_question.json"), fx("type3_split_boxed_segmented_table_answer.json")], "split_file_boxed"),
            ([fx("type4_question_with_empty_grid_realistic.json"), fx("type4_answer_itemized_realistic.json")], "split_file_itemized"),
        ]
        for files, strategy in cases:
            with self.subTest(strategy=strategy):
                result = extract_answer_key([str(path) for path in files]).to_safe_dict()
                self.assertEqual(result["strategy"], strategy)
                self.assertEqual(result["status"], "accepted")
                self.assertGreater(result["answer_count"], 0)
        unknown = extract_answer_key([str(fx("mixed_unknown_should_review.json"))]).to_safe_dict()
        self.assertIn(unknown["status"], {"needs_review", "accepted_with_warnings", "accepted"})

    def test_llm_no_direct_accept_and_no_guessing(self) -> None:
        self.assertIsNone(LlmFallbackExtractor().extract_candidate("1.【答案】B", 1, "B", "1.【答案】B"))
        self.assertIsNone(LlmFallbackExtractor(LlmFallbackConfig(enabled=True)).extract_candidate("snippet", 1, "B", "not present"))
        candidate = LlmFallbackExtractor(LlmFallbackConfig(enabled=True)).extract_candidate("1.【答案】B", 1, "B", "1.【答案】B")
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.source_kind, "llm_candidate")

    def test_cli_v2_flags_and_evidence(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/extract_answer_key.py", "--file", str(fx("type1_same_file_boxed_realistic.json")), "--json", "--show-evidence", "--strict"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        data = json.loads(completed.stdout)
        self.assertEqual(data["strategy"], "same_file_boxed")
        self.assertIn("evidence_text", data["answers"]["1"])
        summary = subprocess.run(
            [sys.executable, "scripts/extract_answer_key.py", "--file", str(fx("type1_same_file_boxed_realistic.json")), "--json", "--summary-only"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertNotIn("answers", json.loads(summary.stdout))


if __name__ == "__main__":
    unittest.main()
