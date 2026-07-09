# Known Bugs And Guards

| risk | guard | test file | status |
| --- | --- | --- | --- |
| Empty student answer grid mistaken as answer key | `StudentAnswerGridDetector` checks empty answer rows, early position, and class/name fields | `tests/test_answer_extraction_engine_v1.py` | covered |
| Question number rewind | `QuestionIndexBuilder` records `question_number_rewind` | `tests/test_answer_extraction_engine_v1.py` | covered through validator path |
| Analysis step numbers mistaken as questions | itemized extractor ignores circled step markers and requires explicit answer evidence | `tests/test_answer_extraction_engine_v1.py` | covered |
| Dates mistaken as question numbers | question builder and itemized extractor skip year-like prefixes | `tests/test_answer_extraction_engine_v1.py` | covered |
| Multi-choice ordering drift | `AnswerNormalizer` sorts choice letters | `tests/test_answer_extraction_engine_v1.py` | covered |
| Invalid option characters silently fixed | `AnswerNormalizer` blocks tokens such as `B0` and `8D` | `tests/test_answer_extraction_engine_v1.py` | covered |
| Question and answer file mismatch | `CrossFileAligner` blocks unexpected answer numbers | `tests/test_answer_extraction_engine_v1.py` | covered |
| Missing answers filled by AI | LLM fallback defaults disabled and validator reviews LLM candidates | `tests/test_answer_extraction_engine_v1.py` | covered |
| LLM output without evidence | fallback rejects candidates whose evidence is not in the snippet | `tests/test_answer_extraction_engine_v1.py` | covered |
| Forbidden integration or secret terms | static safety guard scans answer extraction source and CLIs | `tests/test_answer_extraction_safety_guards.py` | covered |
| Segmented answer tables missed | table normalizer detects repeated question/answer row-pairs | `tests/test_answer_extraction_v2_hardening.py` | covered |
| Complex fill blank rejected as invalid choice | itemized extractor falls back to blank normalization with warning | `tests/test_answer_extraction_v2_hardening.py` | covered |
| Accepted answer lacks evidence | v2 evidence guard checks accepted answers | `tests/test_answer_extraction_guards_v2.py` | covered |
| Real `【答案】` confused with bracket variants | direct P0 tests and v3 fixtures contain real `【答案】` | `tests/test_itemized_answer_extractor_chinese_bracket_p0.py` | covered |
| Final engine output accepted without evidence | output invariant downgrades missing evidence | `tests/test_answer_extraction_evidence_invariant.py` | covered |
