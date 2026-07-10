# SRE Image Normalization Design

The current foundation uses a dependency-isolated image backend. Synthetic PNG/PPM input is decoded with stdlib code. Quality failure and page-location failure are hard gates. Template-controlled synthetic pages use deterministic whole-canvas normalization only after aspect/contrast checks. A production real-photo contour, quadrilateral scoring and perspective backend remains explicitly uncertified.

Runtime flow: `ImageMatrix -> ImageQualityReport -> PageLocationReport -> NormalizedPageImage -> ROI mapper`. No answer ground truth participates in this flow.
