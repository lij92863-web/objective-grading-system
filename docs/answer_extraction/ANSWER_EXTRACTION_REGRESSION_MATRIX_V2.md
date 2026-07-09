# Answer Extraction Regression Matrix V2

| risk | guard | test file | status | remaining caveat |
| --- | --- | --- | --- | --- |
| Empty student answer grid mistaken as answer key | empty ratio, front position, identity fields, following question region | `tests/test_answer_extraction_v2_hardening.py` | covered | merged-cell semantics not restored |
| Segmented answer table missed | `table_normalizer.row_pair_indexes` and table extractor row-pair scan | `tests/test_answer_extraction_v2_hardening.py` | covered | complex visual merges remain best-effort |
| Same-file answer region split wrong | `mixed_file_splitter` scoring and answer evidence checks | `tests/test_answer_extraction_v2_hardening.py` | covered | production split not yet wired into all internals |
| Itemized `【答案】` missed | expanded itemized regex | `tests/test_answer_extraction_v2_hardening.py` | covered | very long prose answers review |
| Itemized `1.B` missed | short itemized regex | `tests/test_answer_extraction_v2_hardening.py` | covered | ambiguous no-evidence prose ignored |
| `故选` / `故答案为` missed | itemized extractor patterns | `tests/test_answer_extraction_v2_hardening.py` | covered | low confidence remains possible |
| Complex fill blank discarded | blank fallback normalization | `tests/test_answer_extraction_v2_hardening.py` | covered | accepted with warning, not final grading |
| Analysis step numbers mistaken as questions | segmenter skips circled markers | `tests/test_answer_extraction_v2_hardening.py` | covered | unusual bullets may need future samples |
| Years mistaken as questions | year-prefix skip | `tests/test_answer_extraction_v2_hardening.py` | covered | nonstandard date formats need samples |
| Duplicate answer conflict | answer sequence validator and conflict resolver | `tests/test_answer_extraction_v2_hardening.py` | covered | blank conflicts go review |
| Unexpected answer number | aligner/validator blocking | `tests/test_answer_extraction_v2_hardening.py` | covered | no semantic remapping by design |
| Single-choice multi-answer | validator blocking | `tests/test_answer_extraction_v2_hardening.py` | covered | teacher review required |
| LLM candidate no evidence | fallback rejects missing evidence | `tests/test_answer_extraction_guards_v2.py` | covered | real LLM disabled |
| Accepted answer without evidence | evidence guard | `tests/test_answer_extraction_guards_v2.py` | covered | CLI can hide evidence display only |
