# WEB-PRODUCT-WORKFLOW-R1 CTO Review

## Decision

**APPROVED_WITH_CAVEATS**

The local product skeleton is safe for teacher workflow trials with synthetic or
non-sensitive local material. The release provides an actual local HTTP page,
class/roster persistence, exam sessions, three capture entry modes, conservative
offline provisional processing, audited review, a fail-closed finalization gate,
and final CSV/JSON/audit exports.

It is not approval for real-device, real-student, real-image benchmark, OCR,
Qwen or production use.

## Capability review

| Question | Finding |
| --- | --- |
| Can a teacher open and try the local page? | Yes. `web_app.py` serves the product home and routes through a thin controller/facade boundary. |
| Class management? | Yes: create, list, view and persist classes. |
| Roster import? | CSV: yes. XLSX: supported only when the existing optional `openpyxl` runtime is present; otherwise the teacher gets a CSV fallback message. |
| Manual column mapping? | Yes, unknown headers return `COLUMN_MAPPING_REQUIRED` and the page requests student-number/name columns. |
| Exam creation and material upload? | Yes. Answer CSV is validated by the canonical loader; answer plus template is required for capture readiness. |
| Manual image upload? | Yes, with extension/payload checks and SHA-256 deduplication. |
| Watched folder? | Yes as an explicit safe scan/poll action. Continuous background monitoring is not included. |
| Browser camera capture? | Yes, using browser `getUserMedia` and blob upload. Availability depends on the browser/OS. |
| Provisional score? | Yes for explicit offline/mock candidates. A real image without a configured recognizer conservatively creates identity and per-question review issues. |
| Review issue classification and resolution? | Yes. Identity is presented first; answer/page issues follow. Actions preserve evidence and append resolution/audit rows. |
| Does finalization block incomplete review? | Yes. Open issues, unfinished jobs, anonymous/temporary/duplicate identity, provisional-only jobs, absent teacher confirmation, bridge failure or canonical precheck failure block release. |
| Final CSV/JSON? | Yes: `final_scores.csv`, `final_scores.json`, `finalization_audit.json`. No full learning-analysis report is generated. |
| Direct USB phone camera control? | **No.** Only cameras exposed by the OS/browser can be used. Ordinary USB file-transfer connections do not provide camera control. The UI states this. |

## Adversarial and benchmark evidence

- Product tests cover missing class/assets/template, invalid roster rows, duplicate
  student numbers and identities, duplicate images/assets, unavailable camera,
  quality/page failures, unknown identity, unreadable answers, evidence
  preservation, provisional export refusal and open-review finalization refusal.
- The retired `/api/exams/grade` path returns HTTP 410. The new web layer has no
  callable direct-grading route.
- The 50-student benchmark processed 50 capture jobs, created 10 identity, 10
  answer and 2 duplicate issues, blocked after each incomplete review stage,
  and recorded `wrong_finalized_count == 0`.
- Product architecture, code-quality and adversarial audits report PASS.

## Boundaries and caveats

- No real OCR, Qwen, AI API, API key or `.env` is used.
- No real roster, real image or real score is committed. Local data remains under
  ignored `data/local_app/` paths.
- No dependency, EXE, cloud deployment, mobile application, multi-user security,
  database encryption or formal HTML/Excel analytics report was added.
- Browser camera behavior is implemented but has not been validated against a
  specific physical device. Watched-folder capture is user-triggered polling,
  not a resident filesystem watcher.
- The conservative no-recognizer path deliberately sends each unknown identity
  and unreadable answer to teacher review. It does not claim useful real-image
  automatic recognition accuracy.

## Next-stage authorization

- `REAL-DEVICE-CAPTURE-R1`: **not started and not approved by this review**;
  recommended next, using non-sensitive test material and an explicitly selected
  system-visible camera.
- `REAL-IMAGE-BENCHMARK-R1`: **not started**; begin only after device capture and
  an authorized, anonymized local dataset protocol.
- `WEB-UI-POLISH-R1`: **not started**; defer until device and workflow findings
  stabilize, so visual work does not hide boundary defects.
