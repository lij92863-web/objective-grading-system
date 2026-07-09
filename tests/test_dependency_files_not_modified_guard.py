import subprocess
import unittest


DEPENDENCY_FILES = {
    "requirements.txt", "pyproject.toml", "setup.py", "setup.cfg", "Pipfile",
    "Pipfile.lock", "poetry.lock", "package.json", "package-lock.json",
}


class DependencyFilesNotModifiedGuardTests(unittest.TestCase):
    def test_dependency_files_not_modified_since_stage_start(self):
        changed = set(subprocess.run(["git", "diff", "--name-only", "a00e393..HEAD"],
                                     capture_output=True, text=True, timeout=10).stdout.splitlines())
        self.assertFalse(changed & DEPENDENCY_FILES)


if __name__ == "__main__":
    unittest.main()
