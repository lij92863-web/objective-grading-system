import subprocess
import unittest


class ReadmeNotModifiedGuardTests(unittest.TestCase):
    def test_readme_not_modified_since_stage_start(self):
        changed = subprocess.run(["git", "diff", "--name-only", "a00e393..HEAD"],
                                 capture_output=True, text=True, timeout=10).stdout.splitlines()
        self.assertNotIn("README.md", changed)


if __name__ == "__main__":
    unittest.main()
