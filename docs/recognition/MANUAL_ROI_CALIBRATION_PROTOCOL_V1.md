# Manual ROI Calibration Protocol V1

Version 1 does not use automatic corner detection.

The teacher or operator manually marks ROI coordinates once in JSON. A later UI can generate this JSON, but the current stage uses hand-edited fixtures.

Coordinate rules:

- origin is the top-left image corner
- `x` and `y` are non-negative
- `width` and `height` are positive
- ROI must stay inside page bounds
- identity ROI is required
- choice cell ROI marks a specific option cell
- blank ROI marks the answer-writing area

Invalid ROI fails closed. Passing ROI validation means only that coordinates are structurally valid; it does not mean recognition succeeded.
