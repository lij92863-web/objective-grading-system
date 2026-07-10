# SRE OMR Algorithm Design

OMR consumes crop evidence produced from TemplateProfile queries. Metrics cover darkness, center density, connected component ratio, border noise, uniformity and erasure tendency. Thresholds live in `omr/omr_policy.py`. Blank, weak, erased, dirty and multi-mark single-choice cases never become automatic candidates. `RecognizedAnswerCandidate` is neither a final answer nor grading input.
