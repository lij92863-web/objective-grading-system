# SRE661 Grading Bridge Architecture

Responsibility: validate TeacherConfirmedSubmission and construct typed OfficialGradingInput only. Single gate requires confirmed identity, no blocking errors and no unresolved review. Class gate requires unique students, accepted answer key, confirmed config and explicit missing-student authorization. Raw drafts and OMR/OCR candidates are rejected by type.

The bridge cannot import workflow, objective grader or grading core, write submissions.csv, calculate scores or generate reports. Future adapters may consume OfficialGradingInput after separate authorization. Main risk is semantic confusion caused by the legacy `ExamOfficialReportGate` name; behavior remains input construction only.
