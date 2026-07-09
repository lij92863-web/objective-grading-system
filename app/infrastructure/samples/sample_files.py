"""Create sample CSV files for demo / testing.

Mirrors ``legacy.create_sample_files`` exactly — same filenames, fields,
content, encoding.  Uses only stdlib ``pathlib``.
"""

from pathlib import Path


def create_sample_files(directory: Path) -> None:
    """Create answer_key, submissions, and question_bank sample CSVs."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    key_path = directory / "answer_key_sample.csv"
    submissions_path = directory / "submissions_sample.csv"
    bank_path = directory / "question_bank_sample.csv"

    if not key_path.exists():
        key_path.write_text(
            "question,question_id,answer,points,partial_credit,"
            "partial_points,tags,difficulty\n"
            "1,B001,A,1,false,,linear_equation,1\n"
            "2,B003,BD,2,true,1,function_concept,3\n"
            "3,B004,C,1,false,,geometry_area,2\n",
            encoding="utf-8-sig",
        )
    if not submissions_path.exists():
        submissions_path.write_text(
            "student_id,name,Q1,Q2,Q3\n"
            "S001,Student One,A,B,C\n"
            "S002,Student Two,B,BD,\n",
            encoding="utf-8-sig",
        )
    if not bank_path.exists():
        bank_path.write_text(
            "question_id,stem,answer,tags,difficulty\n"
            "B001,Solve a basic linear equation.,A,linear_equation,1\n"
            "B002,Choose an equivalent equation form.,C,linear_equation,2\n"
            "B003,Identify the correct function statements.,BD,"
            "function_concept,3\n"
            "B004,Find the area from the given dimensions.,C,"
            "geometry_area,2\n",
            encoding="utf-8-sig",
        )
