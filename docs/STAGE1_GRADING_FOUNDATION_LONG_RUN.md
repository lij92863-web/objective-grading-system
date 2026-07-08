# Stage 1 Grading Foundation Long Run

## 本次目标

本次长任务只推进“客观题批改系统”的工程化底座，不接入真实 OCR、AI 或外部 API，不改 UI，不改题库协议，不实现 paper-package.json 或 assessment-result.json。

## 已完成内容

1. 新增独立批改核心模块 `app/domain/grading/`。
2. 保留旧入口兼容：`objective_grader.py`、`legacy/objective_grader_legacy.py`、`app/core.py` 仍可按原方式调用。
3. 稳定单选、多选、判断题判分边界。
4. 新增填空题确定性判分基础，包括分数/小数、集合乱序、根式等价和复杂表达式人工复核。
5. 新增答案草稿 intake 模型，区分 confirmed、blank、low_confidence、conflict、needs_review 等状态。
6. 新增批改前预检引擎，区分 blocking、warnings、review_required。
7. 扩展 `run_tests.py`，使其同时运行原轻量测试和 `tests/` 下的 unittest 用例。

## 新增核心文件

- `app/domain/grading/models.py`
- `app/domain/grading/normalize.py`
- `app/domain/grading/scoring.py`
- `app/domain/grading/choice_scoring.py`
- `app/domain/grading/true_false_scoring.py`
- `app/domain/grading/blank_scoring.py`
- `app/domain/grading/answer_draft.py`
- `app/domain/grading/precheck.py`

## 新增测试

- `tests/test_grading_core.py`
- `tests/test_choice_true_false_scoring.py`
- `tests/test_blank_scoring.py`
- `tests/test_answer_draft_intake.py`
- `tests/test_grading_precheck.py`

## 判分边界

单选题：

- 正确答案给满分。
- 错选给 0 分。
- 选项超出允许范围标记为 invalid。
- 多选填在单选题中保持 wrong，不额外猜测。

多选题：

- 全对给满分。
- 漏选且无错选时按比例或配置的 partial_points 给部分分。
- 有错选时给 0 分。

判断题：

- 支持 T/F、true/false、对/错、√/× 等常见写法。
- 无法识别的判断题答案标记为 invalid。

填空题：

- 支持文本别名、数值容差、分数/小数等价。
- 支持简单集合乱序等价。
- 支持 `根号2`、`√2`、`sqrt(2)` 这类确定性根式等价。
- 区间、复杂函数、含不等号等表达式不交给 AI 猜测，标记为 needs_review。

## 兼容关系

- `app/core.py` 优先导出新的 grading core。
- legacy 模块在文件末尾用新 grading core 覆盖核心模型和判分函数，旧报表、CSV 加载和工作流仍沿用原实现。
- `objective_grader.py` 仍通过 legacy 对外暴露，现有调用方不需要改导入路径。

## 未做事项

- 未接入真实 OCR。
- 未调用真实 AI。
- 未调用任何外部 API。
- 未接入奇思数学 Pro 题库系统。
- 未实现 paper-package.json 导入。
- 未实现 assessment-result.json 导出。
- 未重构 UI。
- 未删除 legacy 代码。

## 风险和后续建议

1. 旧 CSV 加载、报表和 workflow 仍在 legacy 中，应在后续阶段逐步迁移到 `app/domain/` 与 `app/workflow.py` 的清晰边界。
2. 填空题复杂数学表达式当前只做确定性匹配和人工复核，后续可增加受控的符号化解析，但不能让 AI 决定分数。
3. 答案草稿 intake 已有状态模型，但尚未接入 UI 或真实识别结果。
4. 预检引擎目前可独立调用，后续可接入批改按钮前置流程。
5. `questionId`、paper-package.json 和 assessment-result.json 仍应放到下一阶段协议任务中单独推进。

## 验证命令

- `python run_tests.py`
- `python -m unittest discover -s tests -p "test*.py"`
