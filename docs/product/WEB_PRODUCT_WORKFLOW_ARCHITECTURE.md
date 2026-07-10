# Local Web Product Workflow Architecture

## Purpose and boundary

This release gives a teacher one local browser workflow for class setup,
roster import, exam preparation, image collection, exception review and final
score export. The browser is an input/presentation surface only. Business
decisions live in product services; SQLite access lives in repositories; the
web layer never calls a low-level scorer or recognition primitive.

The product is local and single-user. It does not add OCR, Qwen, cloud services,
an executable package, or a formal analytics report pipeline.

## Main flows

```text
First Run
  -> Create Class
  -> Import Roster
  -> Detect or Map Columns
  -> Validate Roster
  -> Save Class and Students (one transaction)

Daily Grading
  -> Create Exam Session
  -> Register Answer/Paper/Template Assets
  -> Select Capture Source
  -> Capture Queue
  -> Existing Offline Recognition Boundary
  -> Provisional Score + ReviewIssue[]
  -> Resolve Identity Issues
  -> Resolve Answer / Page Issues
  -> Resolve Duplicate Conflicts
  -> Finalization Gate
  -> Canonical Grading Precheck / Bridge
  -> Final CSV + JSON + Audit
```

An unknown identity does not stop answer candidate collection. An unreadable
question does not stop other questions. Neither may enter final scores before
teacher resolution. Provisional data is never exposed by the final export API.

## Layers

| Layer | Responsibility | Forbidden responsibility |
| --- | --- | --- |
| `app/web_product` | Parse HTTP input, call facade, render templates | SQL, recognition, scoring, finalization decisions |
| `app/classes`, `app/roster` | Class and roster rules | Web rendering |
| `app/exam_session` | Session and immutable asset registration | Image parsing |
| `app/capture` | Source validation, safe copy, deduplication, queueing | Grading |
| `app/product/pipeline` | Adapt existing offline recognition evidence into provisional records | Guessing identity/answers; final export |
| `app/product/review` | Issue ordering and audited teacher resolution | Overwriting original evidence |
| `app/product/finalization` | Fail-closed release gate and final exports | Accepting provisional or anonymous records |
| `app/storage` | Schema, transactions, repositories | Product policy |

## Blocking, warning and unsupported cases

Blocking includes invalid roster rows, duplicate student numbers in a class,
missing class/answer/template before capture, open review issues, anonymous or
duplicate identities, unfinished capture jobs, provisional-only scores,
missing teacher confirmation, and a failed canonical grading precheck.

Warnings include duplicate names, blank roster rows, duplicate asset/image
content, and optional question-bank absence. A warning is displayed and audited
but does not grant a finalization override.

Unsupported in this release: direct USB-phone camera control, real OCR/Qwen,
mobile apps, multi-user authorization, encrypted local databases, and formal
HTML/Excel learning analytics.

## Failure presentation

Every service returns a typed result or raises a bounded validation/state
exception. Pages show a teacher-oriented message plus retained technical audit
code. Failed transactions leave no partial class, student, issue resolution or
final score set.

Future real devices and recognition engines must enter through capture source
and recognition adapter protocols. They may add evidence, never bypass review
or finalization.
