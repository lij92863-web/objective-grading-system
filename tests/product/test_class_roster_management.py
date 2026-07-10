import csv
import tempfile
import unittest
from pathlib import Path

from app.classes import ClassService
from app.roster.roster_importer import RosterImporter
from app.roster.roster_mapping import RosterColumnMapping
from app.roster.roster_validator import RosterImportState
from app.storage import LocalDatabase


ROOT = Path(__file__).resolve().parents[2]


class ClassRosterManagementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "data")
        self.root = Path(self.temp.name)
        self.database = LocalDatabase(self.root / "product.sqlite3")
        self.classes = ClassService(self.database)
        self.rosters = RosterImporter(self.database)
        self.classroom = self.classes.create_class("高一 3 班")

    def tearDown(self):
        self.temp.cleanup()

    def write_csv(self, name, content):
        path = self.root / name
        path.write_text(content, encoding="utf-8-sig")
        return path

    def test_create_class(self):
        self.assertEqual(self.classroom.class_name, "高一 3 班")
        self.assertEqual(len(self.classes.list_classes()), 1)

    def test_import_roster_csv_success(self):
        path = self.write_csv("roster.csv", "学号,姓名\n001,张三\n002,李四\n")
        result = self.rosters.import_file(self.classroom.class_id, path)
        self.assertEqual(result.state, RosterImportState.IMPORTED)
        self.assertEqual(result.student_count, 2)
        self.assertEqual(self.rosters.list_students(self.classroom.class_id)[0].student_no, "001")

    def test_roster_unknown_columns_requires_mapping(self):
        path = self.write_csv("unknown.csv", "column_a,column_b\n001,张三\n")
        result = self.rosters.import_file(self.classroom.class_id, path)
        self.assertEqual(result.state, RosterImportState.COLUMN_MAPPING_REQUIRED)
        mapped = self.rosters.import_file(
            self.classroom.class_id,
            path,
            RosterColumnMapping("column_a", "column_b"),
        )
        self.assertEqual(mapped.state, RosterImportState.IMPORTED)

    def test_duplicate_and_missing_fields_block_without_partial_import(self):
        cases = {
            "duplicate.csv": "学号,姓名\n001,张三\n001,李四\n",
            "missing_no.csv": "学号,姓名\n,张三\n",
            "missing_name.csv": "学号,姓名\n001,\n",
        }
        for filename, content in cases.items():
            with self.subTest(filename=filename):
                result = self.rosters.import_file(
                    self.classroom.class_id,
                    self.write_csv(filename, content),
                )
                self.assertEqual(result.state, RosterImportState.BLOCKED)
                self.assertEqual(self.rosters.list_students(self.classroom.class_id), [])

    def test_same_name_warns_but_cross_class_is_allowed(self):
        first = self.write_csv("first.csv", "学号,姓名\n001,张三\n002,张三\n")
        result = self.rosters.import_file(self.classroom.class_id, first)
        self.assertEqual(result.state, RosterImportState.IMPORTED)
        self.assertTrue(any(issue.code == "duplicate_name" for issue in result.warnings))
        other = self.classes.create_class("高一 4 班")
        second = self.write_csv("second.csv", "学号,姓名\n001,张三\n")
        self.assertEqual(
            self.rosters.import_file(other.class_id, second).state,
            RosterImportState.IMPORTED,
        )

    def test_import_roster_excel_success_or_graceful_skip(self):
        try:
            from openpyxl import Workbook
        except ImportError:
            self.skipTest("openpyxl is not installed")
        path = self.root / "roster.xlsx"
        workbook = Workbook()
        workbook.active.append(["学号", "姓名"])
        workbook.active.append(["001", "张三"])
        workbook.save(path)
        workbook.close()
        result = self.rosters.import_file(self.classroom.class_id, path)
        self.assertEqual(result.state, RosterImportState.IMPORTED)


if __name__ == "__main__":
    unittest.main()
