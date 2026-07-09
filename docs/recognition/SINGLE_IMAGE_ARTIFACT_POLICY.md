# Single Image Artifact Policy

Real image files must not be committed.

Commit-safe artifacts:

- synthetic manifest JSON with no sensitive path and no base64
- synthetic ROI JSON with no real student information
- docs and tests

Not commit-safe:

- real image files
- raw Qwen response
- base64 image payload
- `data/tmp`
- `data/reports`
- formal CSV, Excel, or HTML reports

Default output is stdout JSON. If a temporary file is explicitly requested, it must be under `data/tmp`, which remains untracked.
