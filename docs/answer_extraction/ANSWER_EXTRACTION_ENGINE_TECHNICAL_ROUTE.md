# Answer Extraction Engine Technical Route

The engine covers four teacher-file scenarios: same file with boxed answers, same file with itemized answers, split question plus boxed answer file, and split question plus itemized answer file.

A single regex is not enough because teacher files mix question regions, answer regions, empty student answer grids, itemized explanations, tables, dates, and section headings. The route is structured first, regex second.

`DocumentModel` is the neutral input model. It keeps paragraphs and tables in stable order with source spans and JSON-serializable evidence.

The main chain is:

1. `FileRoleClassifier` separates question-only, answer-only, mixed, and unknown files.
2. `AnswerLayoutClassifier` detects boxed tables, itemized explanations, mixed layouts, or no answer layout.
3. `StudentAnswerGridDetector` blocks empty student answer grids from becoming answer keys.
4. `AnswerTableExtractor` reads horizontal, segmented horizontal, and vertical answer tables.
5. `ItemizedAnswerExtractor` reads explicit `【答案】`, short `1.B`, `故选`, and `故答案为` evidence.
6. `QuestionIndexBuilder` builds question numbers and question types from section headings.
7. `CrossFileAligner` aligns only by question number.
8. `AnswerKeyValidator` applies missing, unexpected, duplicate, type mismatch, invalid token, and review rules.
9. `ExtractionReport` emits a safe summary without local absolute paths or API payloads.

LLM fallback is a disabled stub. When enabled in tests, it only creates review candidates with explicit evidence already present in the snippet. It never directly accepts an answer and never calls a network API.

Fail-closed principle: uncertain extraction becomes missing, review, or blocked. The engine does not process real student answer-card photos, does not perform grading, and does not generate formal score reports.

V2 hardening adds realistic synthetic fixtures, schema-checked `DocumentModel` loading, table normalization, stronger empty-grid detection, segmented answer tables, Chinese bracket answer formats, fill-blank expression preservation, question/answer sequence validators, and conflict resolution. The validator continues to prefer review or warning over silent guessing.

V3 adds direct real `【答案】` support, split-paragraph itemized answer blocks, a final evidence invariant, synthetic DOCX generation, and a matrix fixture suite. Accepted answers are evidence-driven at both validator and output-schema levels.
