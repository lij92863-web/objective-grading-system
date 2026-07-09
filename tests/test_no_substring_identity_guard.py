import unittest
from pathlib import Path


class NoSubstringIdentityGuardTests(unittest.TestCase):
    def test_no_identity_substring_guard_in_recognition_code(self):
        root = Path("app/recognition")
        banned = ['"identity" in', "'identity' in"]
        offenders = []
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for pattern in banned:
                if pattern in text:
                    offenders.append(f"{path}:{pattern}")
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
