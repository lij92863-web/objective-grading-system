# SRE221 Image Normalization Architecture

Responsibility: decode supported images, issue quality reports, locate a page and produce a normalized synthetic/template-controlled image. Inputs are image bytes/matrices plus reference-canvas metadata; outputs are typed quality/location/normalized objects. Only the isolated backend may optionally import cv2. OMR, ROI, grading, web and network dependencies are forbidden.

`quality_failed` blocks location; `page_location_failed` blocks normalization and ROI. Synthetic normalization is deterministic resize after validation. Real-photo homography is unavailable unless an isolated backend can provide it, so this stage is not production real-ready. Risks are camera distortion, contour ambiguity and misleading resize semantics. Separate status objects, debug artifact slots and explicit mode boundaries prevent silent fallback.
