# Long-Term Architecture

This project should grow around stable data contracts, not around one large
script. The current script is still a single-file tool, but its inputs and
outputs are shaped so it can later be split cleanly.

## Core Flow

1. Class and roster management
   - This is a foundation module of the grading system.
   - Each class has `classes/<class-name>/roster.csv` with
     `student_id,name`.
   - `student_id` is the unique identity key inside one class.
   - Roster import, validation, default class selection, and student matching
     stay outside `objective_grader.py`.

2. Input normalization
   - Accept CSV now.
   - Add Excel, OCR, form exports, or LLM extraction later.
   - OCR/AI should first output `recognized_submissions.csv`.
   - The class workflow matches `recognized_student_id` against the selected
     roster and outputs a normalized `submissions.csv`.

3. Exam structure recognition
   - The teacher uploads the paper and standard answer.
   - `exam_recognizer.py` produces an editable `exam_manifest.json` plus
     `recognition_report.json`.
   - AI/OCR output is not trusted directly. A teacher confirms or edits the
     manifest before grading.
   - `confirmed_exam_manifest.json` is the only source allowed to generate
     `answer_key.csv`.
   - First version auto-grades objective items only. Solution, proof, process,
     and unknown questions are marked for manual grading.
   - The module must support arbitrary question combinations; no fixed template
     such as 8+3+3 or 10+0+2 belongs in the grading path.

4. Deterministic grading
   - Answer key plus student answers produce traceable per-question results.
   - This layer should not depend on API keys or model calls.
   - `objective_grader.py` remains the deterministic grading core and only
     receives normalized `answer_key.csv` and `submissions.csv`.

5. Diagnosis
   - Question-level results plus knowledge point tags produce
     `knowledge_profile.csv`.
   - This is the main interface for student portraits.

6. Practice generation
   - `knowledge_profile.csv` plus a question-bank export produce
     `practice_recommendations.csv`.
   - CSV is the stable bridge. `exam_report.xlsx` is the teacher-facing package.
   - The question bank is an enhancement module for personalized homework, not
     a dependency of basic grading.

7. Exam archive
   - Class-aware runs are stored in
     `exams/<class-name>/<date>_<exam-name>/`.
   - `exam_metadata.json` keeps exam name, class, subject, date, and source path.

## Class Roster Contract

Directory layout:

```text
classes/
  classes_index.json
  default_class.json
  高二3班/
    roster.csv
    class_metadata.json
```

`roster.csv` is always UTF-8 with BOM for Excel compatibility:

```csv
student_id,name
230301,张三
230302,李四
```

Roster import accepts CSV without extra dependencies. `.xlsx` import is optional
and only requires `openpyxl` when that path is used. `.xls` should be saved as
`.xlsx` or `.csv`.

Before grading, the workflow selects a class, matches each
`recognized_student_id`, writes `submissions.csv`, records unmatched rows in
`unmatched_students.csv`, then invokes the grading core.

## Exam Manifest Contract

The recognizer writes `exam_manifest.json` first. This file is editable and must
be reviewed by a teacher. Confirmation writes `confirmed_exam_manifest.json`,
which can then be exported to the grader's `answer_key.csv`.

Standard question types:

```text
single_choice -> 单选题
multiple_choice -> 多选题
blank -> 填空题
true_false -> 判断题
solution -> 解答题
proof -> 证明题
unknown -> 未知题型
```

Auto-grading policy:

- `single_choice`, `multiple_choice`, and `true_false` are auto-gradable.
- `blank` is auto-gradable only when the answer is clear and text-matchable.
- `solution`, `proof`, and `unknown` are manual-grade only in the first version.

The manifest validator checks missing metadata, question count, score totals,
duplicate or non-continuous question numbers, missing objective answers,
unknown types, difficulty range, confidence range, and zero-point questions.

## Shared Contract With The Question Bank

The question bank should export at least:

```csv
question_id,stem,answer,tags,difficulty
```

The answer key should preserve the bank ID when possible:

```csv
question,question_id,answer,points,partial_credit,partial_points,tags,difficulty
```

Difficulty should be a stable 1-5 integer. The recommendation engine should
prefer the same difficulty as the student's missed question, then one level
lower, then nearby levels.

Recommended future fields:

```csv
question_id,stem,options,answer,tags,difficulty,source,estimated_time,explanation
```

Keep `tags` stable. Treat them like IDs, for example `linear_equation` or
`geometry_area`. Display names can change, IDs should not.

## Useful Next Features

- Import `.xlsx` directly.
- Add one sheet per student to `exam_report.xlsx`.
- Add a tag dictionary file: `tag_id`, `display_name`, `parent_tag`.
- Avoid recommending questions the student has already answered correctly.
- Use `validation_report.csv` as a quality gate before trusting reports.
- Add difficulty balancing: easy first, then medium, then hard.
- Tune the difficulty ranking strategy with real student response data.
- Add historical mastery by merging multiple exams.
- Add answer explanations from the question bank into the practice output.
- Add a small GUI after the command-line workflow is stable.
