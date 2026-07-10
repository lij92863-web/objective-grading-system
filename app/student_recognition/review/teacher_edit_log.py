from dataclasses import dataclass
@dataclass(frozen=True)
class TeacherEditEvent: actor:str; note:str; original_value:object; replacement_value:object; at:str
