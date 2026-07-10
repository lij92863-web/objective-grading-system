# Web Product Data Model

SQLite is the only product database. Files are stored below `data/local_app/`;
the database stores safe relative paths, hashes and audit metadata.

| Entity/table | Key facts |
| --- | --- |
| `classes` | Class identity, display name, grade, school year, ACTIVE/ARCHIVED |
| `students` | Class-scoped student number, name, aliases and status |
| `exam_sessions` | Class, exam name, lifecycle state and teacher confirmation |
| `exam_assets` | Type, original name, stored path, SHA-256 and status |
| `capture_jobs` | Session, source, stored image, hash, state and error code |
| `recognition_drafts` | Immutable evidence payload and provisional state |
| `review_issues` | Ordered identity/answer/page issues and current state |
| `review_resolutions` | Append-only teacher action, score, reason and evidence reference |
| `final_submissions` | Confirmed canonical student submission snapshot |
| `final_scores` | Final score values created only inside finalization transaction |
| `artifact_index` | Final CSV/JSON/audit paths and SHA-256 |
| `audit_events` | Append-only actor, action, entity, payload and timestamp |
| `schema_migrations` | Applied schema versions |

All tables have `id`, `created_at`, and `updated_at`. Session-owned tables have
`session_id`; class-owned records have `class_id`; stateful tables have `state`.
Database foreign keys are enabled. Student numbers are unique within a class;
names need not be unique. Asset and capture hashes support deduplication without
deleting audit evidence.

Transactions cover roster import, session creation, capture batch creation,
review resolution, and finalization. Finalization writes submissions, scores,
artifact records and audit events atomically; export files are staged and then
published only after the transaction succeeds.
