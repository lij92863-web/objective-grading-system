# SRE Algorithm Foundation Report

Delivered: Template hardening, image backend and quality reports, fail-closed page normalization, TemplateProfile-driven ROI artifacts, conservative OMR metrics/candidates, synthetic benchmark, negative guards and automated audit.

Safety invariant: quality failure or page failure blocks downstream work; ROI failure blocks metrics; blank/weak/multi/erased marks go to review; candidate is not final answer and never writes grading outputs.

The benchmark acceptance gate is clean accuracy >= 0.98, blank false-positive <= 0.01, multi-mark review = 1.0 and wrong auto-accepted = 0.
