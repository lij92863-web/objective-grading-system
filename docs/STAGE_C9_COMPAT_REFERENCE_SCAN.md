# Stage C9 — Compatibility & Facade Reference Scan

## App/ files importing legacy directly (besides app/compat)
- `app/analysis.py` — 17 symbols (analysis functions + CSV writers)
- `app/reports.py` — 8 symbols (HTML/Excel writers + html_escape)
- `app/core.py` — 7 symbols (dataclasses + loaders)
- `app/validators.py` — 2 symbols (validation builder + writer)

## app/compat status
- `app/compat/objective_grader_compat.py`: only app/ module designed to import legacy ✅

## Strategy
- Redirect all 4 facades from `from legacy.objective_grader_legacy import` → `from app.compat.objective_grader_compat import`
- Same symbols, same behavior, zero risk
