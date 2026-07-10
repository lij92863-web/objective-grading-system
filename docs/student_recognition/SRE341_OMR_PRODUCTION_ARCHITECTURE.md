# SRE341 OMR Production Architecture

Responsibility: transform option-cell evidence into conservative candidates. Inputs are typed crop evidence and metrics; outputs are `RecognizedAnswerCandidate`, never final answers. OMR depends on image value types, ROI artifacts, policy and errors. It cannot parse template JSON or import review, grading, web, workflow, OCR or Qwen.

Blank returns blank_candidate; weak, erased, dirty, ambiguous and multi-mark single-choice return needs_review with enumerated reasons. Only strong marks satisfying threshold and margin become auto_candidate. Evidence carries crop path, metrics, template reference and image hash. Risks are synthetic threshold overfit and multi-choice corpus limitations; benchmark gates and centralized policy contain them.
