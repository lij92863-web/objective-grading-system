# Stage R361-R440 Preflight Report

- **当前分支**: main
- **当前 commit**: 825b49b feat prepare single anonymous image trial readiness
- **git status**: clean
- **测试结果**: 792 tests OK (skipped=5)
- **qwen sample 默认 fail-closed**: ✅
- **qwen sample --check-only**: ✅ (real_api_called=false)
- **single image manifest validator**: ✅
- **single image ROI validator**: ✅
- **single image dry-run**: ✅
- **single image qwen readiness check-only**: ✅
- **single image trial report**: ✅
- **single image snapshot**: ✅
- **real paper readiness**: ✅ (correctly blocked)
- **small batch gate**: ✅ (correctly blocked)

## 本轮确认
- 本轮没有真实试卷
- 本轮没有真实图片
- 本轮不执行真实 API
- allowed paths: app/recognition/**, tests/**, scripts/**, docs/recognition/**
- forbidden paths: legacy/**, app/compat/**, grading core, workflow.py, objective_grader.py, web/**, dependency files
- 上一轮已完成: manifest schema, ROI schema, dry-run, check-only, trial report, artifact guard, readiness gate, small batch gate
- 本轮目标: single Qwen trial config, prompt builder, request manifest, fake response fixtures, sanitizer, parser, parser audit, fake replay, real-call gate, not-executed report, guards, docs
