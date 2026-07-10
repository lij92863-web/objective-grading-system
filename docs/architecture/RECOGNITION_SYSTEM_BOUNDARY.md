# Recognition System Boundary

`app/student_recognition/**` is the formal SRE evolution line: capture, typed drafts, review, confirmed submission and guarded bridge. `app/recognition/**` is used by older single-image/fake replay application paths and remains compatibility/research code. Current call graph contains separate models; deletion or migration is not authorized here, so model convergence is `UNRESOLVED_BOUNDARY`.

The only permitted future grading transition is an explicit adapter from SRE `TeacherConfirmedSubmission` to canonical `app.domain.grading.models.Submission`, after identity confirmation and resolved review. RecognitionDraft, OMR/OCR/Qwen candidates cannot cross that boundary. Grading domain must not import either recognition implementation. This canonicalization round adds no recognition imports or reverse dependencies.
