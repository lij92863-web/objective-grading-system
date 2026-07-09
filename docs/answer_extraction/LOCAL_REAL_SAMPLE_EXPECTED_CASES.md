# Local Real Sample Expected Cases

Do not commit real teacher DOCX files. Put them under `local-test-materials/answer-extraction-samples/` only.

For each local case, record expected values manually:

```json
{
  "case_id": "case1_type2_itemized_training13",
  "expected_strategy": "same_file_itemized",
  "expected_question_count": 0,
  "expected_answer_count": 0,
  "must_have_answers": {
    "1": "B"
  },
  "allowed_missing": [],
  "expected_blocking": [],
  "notes": "Teacher-approved expected answer key only."
}
```

Cases:

- case1: 基础训练13
- case2: 基础训练16 + 答案
- case3: 2026 作业
- case4: 题目 + 答案
