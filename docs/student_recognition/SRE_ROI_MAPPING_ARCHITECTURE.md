# SRE ROI Mapping Architecture

Responsibility: map TemplateProfile normalized ROIs to runtime pixels and persist crop evidence. Inputs are a successfully normalized page and TemplateProfile query results. Outputs are typed `PixelROI` and `ROICropArtifact` objects carrying path, SHA-256 image hash, template reference, question and option. Dependencies flow template/image to ROI; OMR is a downstream consumer. JSON template parsing and alternate coordinate calculations are forbidden.

Bounds, zero area, missing page location and crop errors fail closed. Rounding is floor/ceil with policy epsilon. Future storage may add content-addressed paths without changing coordinates. Risks are artifact retention and hash provenance; typed metadata and temp-directory tests prevent fixture pollution.
