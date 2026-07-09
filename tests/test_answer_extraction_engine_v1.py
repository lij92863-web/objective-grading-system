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
from app.answer_extraction.answer_table_extractor import extract_answer_tables
from app.answer_extraction.cross_file_aligner import align_by_question_no
from app.answer_extraction.docx_native_parser import DocxParseError, parse_docx
from app.answer_extraction.document_model import DocumentModel
from app.answer_extraction.extraction_engine import extract_answer_key, load_document
from app.answer_extraction.extraction_strategy_router import ExtractionStrategy, choose_strategy
from app.answer_extraction.file_role_classifier import FileRole, classify_file_role
from app.answer_extraction.itemized_answer_extractor import extract_itemized_answers
from app.answer_extraction.llm_fallback_extractor import LlmFallbackConfig, LlmFallbackExtractor
from app.answer_extraction.question_index_builder import build_question_index
from app.answer_extraction.student_answer_grid_detector import detect_student_answer_grid

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "answer_extraction" / "document_models"


def fixture(name: str) -> Path:
    return FIXTURES / name


class AnswerExtractionEngineV1Tests(unittest.TestCase):
    def load(self, name: str) -> DocumentModel:
        return load_document(fixture(name))

    def test_document_model_round_trip(self) -> None:
        document = self.load("type1_same_file_boxed.json")
        copied = DocumentModel.from_dict(document.to_dict())
        self.assertEqual([block.block_id for block in copied.sorted_blocks()], ["p_001", "p_002", "p_003", "p_004", "p_005", "p_006", "tb_007"])
        self.assertEqual(copied.sorted_tables()[0].grid()[1][3], "BD")

    def test_role_and_layout_classifiers_cover_four_shapes(self) -> None:
        self.assertEqual(classify_file_role(self.load("type1_same_file_boxed.json")).role, FileRole.MIXED_QUESTION_ANSWER)
        self.assertEqual(classify_file_role(self.load("type3_question_only.json")).role, FileRole.QUESTION_ONLY)
        self.assertEqual(classify_file_role(self.load("type3_answer_boxed.json")).role, FileRole.ANSWER_ONLY)
        self.assertEqual(classify_file_role(self.load("type4_question_with_empty_grid.json")).role, FileRole.QUESTION_ONLY)

    def test_student_answer_grid_is_ignored(self) -> None:
        document = self.load("type4_question_with_empty_grid.json")
        detection = detect_student_answer_grid(document.sorted_tables()[0], document)
        self.assertTrue(detection.is_student_answer_grid)
        self.assertEqual(extract_answer_tables(document).candidate_pool.question_numbers(), [])

    def test_table_extractor_handles_horizontal_segmented_vertical_and_multi(self) -> None:
        horizontal = extract_answer_tables(self.load("type1_same_file_boxed.json")).candidate_pool
        self.assertEqual(horizontal.highest_confidence_candidate(3).normalized_answer, "BD")
        vertical = extract_answer_tables(self.load("type3_answer_boxed.json")).candidate_pool
        self.assertEqual(vertical.highest_confidence_candidate(2).normalized_answer, "C")

    def test_itemized_extractor_supports_explicit_short_and_guxuan(self) -> None:
        same_file = extract_itemized_answers(self.load("type2_same_file_itemized.json")).candidate_pool
        self.assertEqual(same_file.highest_confidence_candidate(1).normalized_answer, "B")
        split_file = extract_itemized_answers(self.load("type4_answer_itemized.json")).candidate_pool
        self.assertEqual(split_file.highest_confidence_candidate(2).source_kind, "guxuan")

    def test_question_index_builder_assigns_types_and_stops_at_answers(self) -> None:
        index = build_question_index(self.load("type1_same_file_boxed.json"))
        self.assertEqual([(item.question_no, item.question_type) for item in index.questions], [(1, "single_choice"), (2, "single_choice"), (3, "multi_choice")])

    def test_answer_normalizer_guardrails(self) -> None:
        self.assertEqual(normalize_answer("DB").normalized_answer, "BD")
        self.assertEqual(normalize_answer("b，d").normalized_answer, "BD")
        self.assertIn("invalid_answer_token", normalize_answer("B0").blocking_errors)
        self.assertIn("invalid_answer_token", normalize_answer("8D").blocking_errors)
        self.assertEqual(normalize_answer("  x + 1 ", "blank").normalized_answer, "x + 1")

    def test_aligner_and_validator_block_key_mismatches(self) -> None:
        question_index = build_question_index(self.load("type3_question_only.json"))
        pool = AnswerCandidatePool()
        pool.add(AnswerCandidate(1, "B", "B", source_kind="answer_table", evidence_text="题号 1 答案 B", confidence=0.99))
        pool.add(AnswerCandidate(1, "C", "C", source_kind="answer_table", evidence_text="题号 1 答案 C", confidence=0.98))
        pool.add(AnswerCandidate(9, "D", "D", source_kind="answer_table", evidence_text="题号 9 答案 D", confidence=0.99))
        alignment = align_by_question_no(question_index, pool)
        report = validate_answer_key(question_index, pool, alignment)
        self.assertIn("unexpected_answer_number", report.blocking_errors)
        self.assertIn("duplicate_conflicting_answer", report.blocking_errors)

    def test_single_choice_multi_answer_blocks(self) -> None:
        question_index = build_question_index(self.load("type3_question_only.json"))
        pool = AnswerCandidatePool()
        pool.add(AnswerCandidate(1, "BD", "BD", source_kind="answer_table", evidence_text="题号 1 答案 BD", confidence=0.99))
        pool.add(AnswerCandidate(2, "C", "C", source_kind="answer_table", evidence_text="题号 2 答案 C", confidence=0.99))
        report = validate_answer_key(question_index, pool, align_by_question_no(question_index, pool))
        self.assertIn("single_choice_multi_answer", report.blocking_errors)

    def test_llm_fallback_disabled_and_never_direct_accepted(self) -> None:
        self.assertIsNone(LlmFallbackExtractor().extract_candidate("1.【答案】B", 1, "B", "1.【答案】B"))
        candidate = LlmFallbackExtractor(LlmFallbackConfig(enabled=True)).extract_candidate("1.【答案】B", 1, "B", "1.【答案】B")
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.source_kind, "llm_candidate")
        self.assertIn("llm_candidate_requires_review", candidate.warnings)
        self.assertIsNone(LlmFallbackExtractor(LlmFallbackConfig(enabled=True)).extract_candidate("snippet", 1, "B", "missing"))

    def test_four_synthetic_strategies_run_end_to_end(self) -> None:
        cases = [
            ([fixture("type1_same_file_boxed.json")], "same_file_boxed", "accepted"),
            ([fixture("type2_same_file_itemized.json")], "same_file_itemized", "accepted"),
            ([fixture("type3_question_only.json"), fixture("type3_answer_boxed.json")], "split_file_boxed", "accepted"),
            ([fixture("type4_question_with_empty_grid.json"), fixture("type4_answer_itemized.json")], "split_file_itemized", "accepted"),
        ]
        for files, strategy, status in cases:
            with self.subTest(strategy=strategy):
                result = extract_answer_key([str(path) for path in files]).to_safe_dict()
                self.assertEqual(result["strategy"], strategy)
                self.assertEqual(result["status"], status)
                self.assertGreater(result["answer_count"], 0)

    def test_strategy_router_unknown_safe_fallback(self) -> None:
        doc = self.load("type1_same_file_boxed.json")
        strategy = choose_strategy([classify_file_role(doc)], [])
        self.assertEqual(strategy.strategy, ExtractionStrategy.MIXED_OR_UNKNOWN)

    def test_docx_native_parser_minimal_docx(self) -> None:
        xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
<w:p><w:r><w:t>一、单选题</w:t></w:r></w:p>
<w:tbl><w:tr><w:tc><w:p><w:r><w:t>题号</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>1</w:t></w:r></w:p></w:tc></w:tr>
<w:tr><w:tc><w:p><w:r><w:t>答案</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>B</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
</w:body></w:document>"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.docx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("word/document.xml", xml)
            document = parse_docx(path)
            self.assertEqual(document.sorted_blocks()[0].text, "一,单选题")
            self.assertEqual(document.sorted_tables()[0].grid()[1][1], "B")
            with self.assertRaises(DocxParseError):
                parse_docx(Path(tmp) / "missing.docx")

    def test_cli_outputs_json(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/extract_answer_key.py", "--file", str(fixture("type1_same_file_boxed.json")), "--json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(json.loads(completed.stdout)["strategy"], "same_file_boxed")


if __name__ == "__main__":
    unittest.main()
