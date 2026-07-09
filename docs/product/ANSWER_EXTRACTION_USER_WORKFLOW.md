# Answer Extraction User Workflow

Teachers can provide either one combined question-and-answer file or two files: one question file and one answer file.

The system first determines the file type and answer layout. It then extracts the question list and answer key from visible evidence such as answer tables or explicit answer-analysis lines.

If an answer is missing, duplicated, conflicting, or does not match the question type, the system marks it for teacher review instead of writing it automatically.

Teacher confirmation is required before extracted answers can be used by downstream grading. Uncertain answers are not auto-filled.

V2 adds stronger handling for common teacher formats: front-page blank answer grids, segmented answer tables, `【答案】` answer-analysis sections, and fill-in-the-blank expressions. Fill-in-the-blank answers may appear with warnings so teachers can confirm them carefully.

V3 further requires every accepted answer to show traceable evidence. When evidence is missing, the answer is sent to review instead of being accepted.
