# Stage AE121-AE260 Algorithm Hardening Summary

Start commit: ab42cbb feat add answer extraction engine v1

End commit: this summary is included in the final stage commit; use the final reply and `git log -1` for the immutable hash.

Push: pending at document write time; final reply records the pushed state.

V1 caveats fixed:

- Added schema-checked DocumentModel loader.
- Hardened DOCX parser for tab, line break, empty cell, multi-paragraph cell, and object placeholder handling.
- Added table normalizer and segmented row-pair extraction.
- Strengthened empty student answer-grid detection.
- Expanded itemized answer extraction for Chinese brackets, `故选`, `故答案为`, and fill-blank expressions.
- Improved question source spans and added sequence validators.
- Added conflict resolver and v2 validator tests.
- Added realistic synthetic fixtures and CLI v2 flags.

Realistic fixtures:

- type1 same-file boxed
- type1 same-file boxed with front empty grid
- type2 same-file itemized with Chinese brackets
- type2 same-file itemized with fill blanks
- type3 split boxed segmented table
- type4 split itemized with empty-grid question file
- analysis-step and unknown-review regression cases

Local smoke: skipped when `local-test-materials/answer-extraction-samples/` is absent.

Current available links: JSON DocumentModel/DOCX to deterministic extraction JSON for four realistic synthetic scenarios.

Current unavailable links: real API fallback, grading integration, workflow integration, web integration, formal reports, and committed real teacher DOCX files.

Next step: place local teacher DOCX samples outside git, fill expected templates manually, then compare smoke output case by case.
