import unittest

from app.recognition.identity_parser import parse_student_identity
from app.recognition.models import StudentIdentityCandidate


class IdentityParserTests(unittest.TestCase):
    def setUp(self):
        self.roster = {"1": "李明", "7": "王强", "23": "张三", "05": "王小明"}

    # -- with roster -------------------------------------------------------

    def test_number_and_name_both_match(self):
        candidate = parse_student_identity("1李明", roster=self.roster)
        self.assertEqual(candidate.status, StudentIdentityCandidate.STATUS_CONFIRMED)
        self.assertEqual(candidate.student_number, "1")
        self.assertEqual(candidate.student_name, "李明")
        self.assertEqual(candidate.matched_student_id, "1")

    def test_number_and_name_both_match_large_number(self):
        candidate = parse_student_identity("23张三", roster=self.roster)
        self.assertEqual(candidate.status, StudentIdentityCandidate.STATUS_CONFIRMED)
        self.assertEqual(candidate.student_number, "23")
        self.assertEqual(candidate.student_name, "张三")

    def test_number_and_name_both_match_zero_prefixed(self):
        candidate = parse_student_identity("05王小明", roster=self.roster)
        self.assertEqual(candidate.status, StudentIdentityCandidate.STATUS_CONFIRMED)
        self.assertEqual(candidate.student_number, "05")
        self.assertEqual(candidate.student_name, "王小明")

    def test_number_exists_but_name_mismatch(self):
        candidate = parse_student_identity("7李明", roster=self.roster)
        self.assertEqual(candidate.status, StudentIdentityCandidate.STATUS_CONFLICT)

    def test_name_exists_but_number_missing(self):
        candidate = parse_student_identity("李明", roster=self.roster)
        self.assertEqual(
            candidate.status, StudentIdentityCandidate.STATUS_NEEDS_REVIEW
        )
        self.assertEqual(candidate.student_name, "李明")
        self.assertEqual(candidate.matched_student_id, "1")

    def test_unparseable_input(self):
        candidate = parse_student_identity("123", roster=self.roster)
        self.assertEqual(candidate.status, StudentIdentityCandidate.STATUS_INVALID)

    def test_empty_input(self):
        candidate = parse_student_identity("", roster=self.roster)
        self.assertEqual(candidate.status, StudentIdentityCandidate.STATUS_INVALID)

    def test_space_between_number_and_name(self):
        candidate = parse_student_identity("1 李明", roster=self.roster)
        self.assertEqual(candidate.status, StudentIdentityCandidate.STATUS_CONFIRMED)
        self.assertEqual(candidate.student_number, "1")
        self.assertEqual(candidate.student_name, "李明")

    def test_number_not_in_roster_and_name_not_in_roster(self):
        candidate = parse_student_identity("9赵六", roster=self.roster)
        self.assertEqual(candidate.status, StudentIdentityCandidate.STATUS_INVALID)

    # -- without roster ----------------------------------------------------

    def test_without_roster_parses_normally(self):
        candidate = parse_student_identity("1李明")
        self.assertEqual(candidate.student_number, "1")
        self.assertEqual(candidate.student_name, "李明")
        self.assertEqual(candidate.status, "draft")

    def test_without_roster_no_number(self):
        candidate = parse_student_identity("李明")
        self.assertEqual(candidate.student_name, "李明")
        self.assertEqual(candidate.student_number, "")

    # -- message is human-readable ------------------------------------------

    def test_conflict_message_is_human_readable(self):
        candidate = parse_student_identity("7李明", roster=self.roster)
        self.assertIn("不一致", candidate.message)
        self.assertIn("7", candidate.message)

    def test_needs_review_message_is_human_readable(self):
        candidate = parse_student_identity("李明", roster=self.roster)
        self.assertIn("缺少序号", candidate.message)


if __name__ == "__main__":
    unittest.main()
