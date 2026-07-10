# SRE841 OCR/Qwen Interface Architecture

Responsibility: expose offline candidate interfaces with fake clients only. Inputs are sanitized references/prompts; outputs are immutable needs_review candidates. No environment, API key, network, raw response or base64 handling exists. Candidates cannot confirm identity, invent final question structure, score, or enter GradingGate.

Real clients are unsupported and policy defaults prohibit them. Future implementations require separate dependency/security approval. Risks are callers mistaking high confidence for acceptance and prompt injection; immutable `needs_review` status and strict bridge type gates contain both.
