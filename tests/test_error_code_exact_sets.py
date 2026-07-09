import unittest

from app.recognition.error_codes import IDENTITY_ERROR_CODES, all_codes, lookup


class ErrorCodeExactSetTests(unittest.TestCase):
    def test_identity_codes_are_exact(self):
        self.assertIn("identity_missing", IDENTITY_ERROR_CODES)
        self.assertIn("identity_conflict", IDENTITY_ERROR_CODES)
        self.assertIn("duplicate_identity", IDENTITY_ERROR_CODES)
        self.assertNotIn("identity_fake", IDENTITY_ERROR_CODES)

    def test_all_known_codes_have_policy(self):
        for code in all_codes():
            self.assertNotEqual(lookup(code)["item_type"], "unknown")

    def test_unknown_code_fails_closed(self):
        self.assertEqual(lookup("identity_fake")["severity"], "blocking")


if __name__ == "__main__":
    unittest.main()
