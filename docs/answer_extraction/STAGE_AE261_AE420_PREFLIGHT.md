# Stage AE261-AE420 Preflight

Branch: main

Start commit: 66daf0f fix harden answer extraction algorithm v2

Initial git status: clean

Preflight commands:

- `git status --short`: clean
- `git branch --show-current`: main
- `git log --oneline -15`: latest `66daf0f`
- `python run_tests.py`: passed, 1019 tests OK, 5 skipped
- `python -m unittest discover`: passed, 1006 tests OK, 5 skipped
- v2 type1/type2/type3/type4 extraction CLIs: passed
- `python scripts/run_local_answer_extraction_smoke.py --json`: passed with `status: skipped` because local samples were missing

Previous P0 caveats:

- Real `【答案】` needed direct P0 coverage, not only adjacent bracket variants.
- Any accepted or accepted-with-warnings answer needed a hard evidence invariant.

Allowed paths and forbidden paths remain the same as the task file. This stage does not call real APIs, read `.env`, connect grading/workflow/web, or generate formal score reports.
