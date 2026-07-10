import unittest
from app.student_recognition.identity import parse_identity_text,validate_candidate
class TestIdentityFoundation(unittest.TestCase):
    roster={'1':'李明'}
    def test_contract_variants_confirm(self):
        for text in ('1李明','1 李明','学号1 姓名李明'): self.assertEqual(validate_candidate(parse_identity_text(text),self.roster).status,'confirmed')
    def test_conflict_blocks(self): self.assertEqual(validate_candidate(parse_identity_text('1张三'),self.roster).status,'blocked')
    def test_name_only_reviews(self): self.assertEqual(validate_candidate(parse_identity_text('李明'),self.roster).status,'needs_review')
    def test_empty_blocks(self): self.assertEqual(validate_candidate(parse_identity_text(''),self.roster).status,'blocked')
    def test_duplicate_blocks(self): self.assertEqual(validate_candidate(parse_identity_text('1李明'),self.roster,('1',)).status,'blocked')
    def test_fake_hallucination_not_confirmed(self): self.assertNotEqual(validate_candidate(parse_identity_text('1李明','fake_ocr',.99),self.roster).status,'confirmed')
    def test_fuzzy_name_not_confirmed(self): self.assertEqual(validate_candidate(parse_identity_text('1李铭'),self.roster).status,'blocked')
if __name__=='__main__':unittest.main()
