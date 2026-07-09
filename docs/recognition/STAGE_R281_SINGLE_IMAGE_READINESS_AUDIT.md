# Stage R281 Single Image Readiness Audit

Current project status before this stage:

| Capability | Status |
| --- | --- |
| ImageAsset manifest schema | missing |
| anonymous image sample rules | missing |
| single image ROI schema | missing |
| manual ROI calibration protocol | missing |
| Qwen check-only gate | partial, generic Qwen sample only |
| artifact output policy | missing |
| single image dry-run script | missing |
| single image trial report template | missing |
| no real API default guard | present for controlled Qwen sample |
| no data/tmp commit guard | present generally, missing single-image-specific guard |

Plan completed in this round:

- add `SingleImageManifest`
- add `ManualROIFile`
- add manifest and ROI validators
- add synthetic manifest and ROI fixtures
- add single-image dry-run
- add single-image Qwen check-only wrapper
- add trial report model and CLI
- add artifact/no API/no formal report guards
- update readiness and small-batch gates

Reason not to enter real API in this round:

No real anonymous image has been supplied or manually audited. This stage only prepares contracts and dry-run checks.
