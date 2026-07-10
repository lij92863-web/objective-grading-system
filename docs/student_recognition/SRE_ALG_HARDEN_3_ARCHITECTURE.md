# SRE-ALG-HARDEN-3 Architecture

Responsibility: make TemplateProfile geometry and algorithm audit fail closed before downstream expansion. Inputs are v2 template data and source trees; outputs are validated immutable profiles and structured audit findings. Dependencies are limited to template/errors and stdlib AST inspection. Image, OMR, review and grading may consume the protocol but cannot mutate it. Forbidden dependencies include web, workflow, grading core and network clients.

Failure modes include silent coordinate correction, mutable getter leakage, GT leakage and policy thresholds in recognizers. Each is blocking. Extension occurs through policy objects and query interfaces, never alternate coordinate sources. Unsupported real-photo behavior remains explicit. Anti-debt controls are injection tests, defensive-copy tests and a self-attacking audit.
