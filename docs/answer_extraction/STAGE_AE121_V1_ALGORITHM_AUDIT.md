# Stage AE121 V1 Algorithm Audit

V1 completed a synthetic foundation, but was not enough for realistic teacher DOCX pressure testing.

Findings:

- DOCX parser: completed basic paragraph/table parsing; insufficient for tabs, breaks, drawing/object placeholders, and multi-paragraph table cells.
- Merged cells: not semantically restored; v2 keeps parsing stable and fail-closed instead of reconstructing layout.
- Chinese bracket answers: v1 supported `【答案】` narrowly; v2 expands bracket and punctuation handling.
- Complex fill blanks: v1 treated non-choice tokens mostly as invalid; v2 preserves explicit blank expressions.
- Itemized answer regions: v1 extracted simple one-line cases; v2 adds broader explicit-answer and `故答案为` patterns.
- Empty student grids: v1 had a guard; v2 strengthens empty-ratio, front-position, nearby identity fields, and following question-region evidence.
- Segmented answer tables: v1 handled simple row pairs; v2 normalizes tables and tests multi row-pairs.
- QuestionIndex: v1 source spans were shallow; v2 extends spans to the next question/section/answer boundary.
- Validator: v1 blocked core hazards; v2 adds stricter blank, LLM review, evidence, duplicate, and sequence guards.
- Local real sample smoke: skipped because local sample directory was absent.

Fix plan completed in this stage: loader validation, DOCX parser hardening, table normalizer, stronger student-grid detector, stronger table/itemized extraction, sequence validators, conflict resolver, realistic fixtures, v2 CLI flags, and regression guard docs.

Safety boundaries preserved: no forbidden files, no dependencies, no real API, no grading, no workflow, no web, no formal reports.
