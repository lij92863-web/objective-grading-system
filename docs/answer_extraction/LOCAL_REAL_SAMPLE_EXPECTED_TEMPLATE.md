# Local Real Sample Expected Template

Use this template when manually recording expected outcomes for local teacher DOCX samples. Do not commit real DOCX files.

```json
{
  "case_id": "case1_type2_itemized",
  "files": ["local sample file name.docx"],
  "expected_strategy": "same_file_itemized",
  "expected_question_count": 20,
  "expected_answer_count": 20,
  "known_answers": {
    "1": "B",
    "2": "C"
  },
  "allowed_missing": [],
  "expected_blockers": [],
  "notes": "Only include teacher-approved expected answers."
}
```

Allowed statuses for exploratory local smoke are `accepted`, `accepted_with_warnings`, `needs_review`, `blocked`, or `skipped` when files are absent.
