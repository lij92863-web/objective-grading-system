import dataclasses


STUDENT_NO_ALIASES = {
    "学号", "序号", "编号", "考号", "student_no", "student id", "no", "id",
}
NAME_ALIASES = {"姓名", "名字", "学生姓名", "name", "student_name"}
CLASS_ALIASES = {"班级", "class", "class_name"}


@dataclasses.dataclass(frozen=True)
class RosterColumnMapping:
    student_no_column: str
    name_column: str
    class_column: str = ""


def detect_mapping(headers: list[str]) -> RosterColumnMapping | None:
    folded = {header.strip().lower(): header for header in headers}

    def find(aliases: set[str]) -> str:
        for alias in aliases:
            if alias.lower() in folded:
                return folded[alias.lower()]
        return ""

    student_no = find(STUDENT_NO_ALIASES)
    name = find(NAME_ALIASES)
    if not student_no or not name:
        return None
    return RosterColumnMapping(student_no, name, find(CLASS_ALIASES))
