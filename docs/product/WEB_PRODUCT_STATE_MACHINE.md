# Web Product State Machines

State transitions are explicit service operations. Direct repository state
mutation is not a public API.

## Class and roster

```text
ClassState: ACTIVE -> ARCHIVED

RosterImportState:
UPLOADED -> COLUMN_MAPPING_REQUIRED -> VALIDATED -> IMPORTED
UPLOADED -> VALIDATED -> IMPORTED
UPLOADED|COLUMN_MAPPING_REQUIRED|VALIDATED -> BLOCKED
```

Unknown columns require manual mapping. Blocking rows prevent `IMPORTED`; blank
rows and duplicate names are warnings.

## Exam session

```text
DRAFT -> CLASS_SELECTED -> ASSET_READY -> CAPTURE_READY
CAPTURE_READY -> CAPTURING -> PROCESSING
PROCESSING -> REVIEW_REQUIRED -> READY_TO_FINALIZE -> FINALIZED -> ARCHIVED
PROCESSING -> READY_TO_FINALIZE
```

`FINALIZED` is reachable only from `READY_TO_FINALIZE`; `ARCHIVED` is read-only.
Adding assets or captures to FINALIZED/ARCHIVED is illegal.

## Capture job

```text
CREATED -> QUEUED -> IMAGE_READY
IMAGE_READY -> QUALITY_FAILED|PAGE_FAILED|RECOGNIZED|FAILED
RECOGNIZED -> PROVISIONAL_SCORED|REVIEW_REQUIRED
PROVISIONAL_SCORED -> REVIEW_REQUIRED|CONFIRMED
REVIEW_REQUIRED -> CONFIRMED|EXCLUDED
QUALITY_FAILED|PAGE_FAILED -> REVIEW_REQUIRED|EXCLUDED
```

Quality/page failures stop recognition for that image. They become review
issues and never become zero scores automatically.

`EXCLUDED` is an audited terminal capture outcome. Exclusion requires a teacher
reason and atomically resolves all open issues for that capture while retaining
the image reference, draft and review evidence. It cannot produce a confirmed
submission or final score.

## Review and finalization

```text
ReviewIssueState: OPEN -> IN_PROGRESS -> RESOLVED
                  OPEN|IN_PROGRESS -> WAIVED|BLOCKED

FinalizationGateState: BLOCKED -> READY -> FINALIZED
```

Waiver/exclusion requires a reason and audit record. An open, in-progress or
blocked issue keeps the gate BLOCKED. READY is recalculated, not trusted from a
request. Before READY, persisted manual overrides and confirmed-snapshot
associations are rebuilt and validated. Illegal transitions raise a state error
and are tested.
