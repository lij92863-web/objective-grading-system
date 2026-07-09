# R361: Controlled Single Qwen Trial Audit

Starting commit: 825b49b

## 已有能力
1. single image manifest ✅
2. manual ROI ✅
3. qwen check-only gate ✅
4. qwen prompt contract ✅
5. request manifest — NEW in this stage
6. sanitized output schema — NEW in this stage
7. fake response fixture — NEW in this stage
8. fake Qwen replay — NEW in this stage
9. parser candidate audit — NEW in this stage
10. one-shot real-call runner fail-closed — NEW in this stage
11. raw response guard — NEW in this stage
12. base64 guard — NEW in this stage
13. API key guard — NEW in this stage
14. output cleanup policy — NEW in this stage

## 缺失能力 (本轮补齐)
- SingleQwenTrialConfig
- Single prompt builder v2
- Single request manifest + CLI
- Fake single Qwen response fixtures (7 files)
- Sanitized output schema + validator
- Sanitizer (strips key/header/base64)
- Parser v2 (invalid option / missing ID / unexpected ID / identity)
- Parser candidate audit (ready_for_grading always false)
- Fake replay pipeline + CLI
- One-shot real-call runner (default fail-closed)
- Not-executed report
- Output policy
- Guards: raw response, base64, API key, prompt schema

## 禁止真实 API 的原因
1. 没有匿名真实图片
2. 没有 QWEN_API_KEY
3. 当前阶段是 R361-R440: Controlled Single Qwen Trial Gate WITHOUT Calling Real API
4. 真实 API 只能在拿到匿名图片、确认所有 gate 通过后，单张显式 allow
