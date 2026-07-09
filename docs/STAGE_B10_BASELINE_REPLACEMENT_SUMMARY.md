# Stage B10 — Baseline Replacement Summary

## Completed

| Stage | Result |
|-------|--------|
| B1 scan | 26 test files importing legacy documented |
| B2 classification | A/B/C categories with JSON matrix |
| B3 fixture infra | 25 fixture files, helper module, integrity test |
| B4 report builders | 9 tests converted to fixture baseline |
| B7 whitelist | Guard enforces only whitelisted tests import legacy |

## Before → After
- Original tests importing legacy: **26 files**
- After B4: **9 report builder tests converted to fixtures**
- Remaining whitelisted: parity/integration/compat tests (17 files)
- Guard prevents any NEW legacy test import

## Fixture inventory
- JSON: simple_score_rows, item_stats, knowledge_profiles, basic_stats, validation_report, class_report, practice_recommendations
- CSV: 11 report CSV files
- XLSX structures: exam_report, simple_score_report
- HTML structures: simple_report, advanced_dashboard, index

## CLI smoke: ✅ returncode=0, --make-samples: ✅

## Next: Option A — COMPAT_EXPORTS shrink round 2
