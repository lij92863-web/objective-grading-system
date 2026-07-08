# 客观题批改系统架构审计报告 001

## 1. 当前项目概况

当前项目已经具备一个本地网页端和命令行批改链路，面向教师完成班级名单导入、考试信息录入、标准答案导入/确认、学生作答导入、自动判分、数据质量检查、统计报告和 Excel/HTML/CSV 导出。主要入口包括 `web_app.py`、`web/index.html`、`web/static/app.js`、`objective_grader.py`、`run_tests.py`。

- 是否已有网页端：有。`web_app.py` 使用 `ThreadingHTTPServer` 暴露本地接口，`web/index.html` 和 `web/static/app.js` 组成单页式界面。
- 是否已有班级管理：有。`roster_manager.py` 管理 `data/classes/`、`classes_index.json`、`class_metadata.json`、`roster.csv`。
- 是否已有考试创建：有。网页端“新建考试”流程收集班级、考试名、日期、科目，并在 `web_app.py` 的 session 中保存。
- 是否已有标准答案导入：有。`app/data_io.py` 支持 CSV/XLSX/DOCX/PDF/TXT/图片入口，最终生成教师确认草稿；确认后写 `confirmed_answer_key.csv`。
- 是否已有学生作答导入：有。`web_app.py` 支持上传 CSV/XLSX/XLS，并转换为 CSV 后预览/批改。
- 是否已有拍照录入入口：有入口。`web/static/app.js` 调用摄像头并上传图片，`web_app.py` 保存到 `data/captures/`，但当前没有真实 OCR 识别。
- 是否已有自动判分：有。核心在 `legacy/objective_grader_legacy.py` 的 `score_answer`、`grade_submission`、`grade_all`。
- 是否已有统计报告：有。输出 summary/detail/item_analysis/knowledge_profile/teaching_plan/class_remedial/layered_remedial 等。
- 是否已有 Excel 导出：有。`app/workflow.py` 调用 `write_enhanced_workbook` 生成 `exam_report.xlsx`，legacy 也有 `write_workbook`。
- 是否已经是产品级完成态：不是。原因是核心仍依赖 legacy 大文件、前端单文件耦合重、数据协议尚未正式支持 `paper-package.json` 和 `assessment-result.json`、OCR/AI 仍是占位或保存入口。

## 2. 当前目录结构

- `app/`：当前业务门面和流程编排。`core.py`、`analysis.py` 主要 re-export legacy；`workflow.py` 负责批改流程和报告生成；`data_io.py` 负责标准答案来源解析；`validators.py` 负责阻塞错误判断。
- `web/`：网页前端。`index.html` 是页面结构，`static/app.js` 是前端状态、API、渲染、摄像头和流程控制集中实现。
- `legacy/`：历史遗留核心。`objective_grader_legacy.py` 仍包含模型、判分、统计、报告、HTML、Excel、校验等关键能力。
- `data/`：本地运行数据。包含 `classes/`、`exams/`、`uploads/`、`captures/`、`reports/`。
- `samples/`：样例输入，包括 `sample_exam_manifest.json`、示例 answer_key、submissions、question_bank。
- `tests/`：测试代码。`run_tests.py` 是统一测试入口，`tests/test_enhanced_grading.py` 是轻量规则测试脚本。

核心业务目前横跨 `app/`、`web_app.py`、`roster_manager.py`、`legacy/objective_grader_legacy.py`；历史遗留集中在 `legacy/`；样例和测试分别在 `samples/`、`tests/`。

## 3. 当前运行方式

- 网页端启动：README 指向双击启动网页批处理，也可从代码看出 `web_app.py` 启动本地 HTTP 服务，默认 `127.0.0.1:8765`。
- 命令行工具启动：README 给出 `python objective_grader.py --answer-key ... --submissions ... --out-dir ...`。
- 测试运行：`python run_tests.py`。
- 数据保存位置：班级在 `data/classes/`，上传临时文件在 `data/uploads/`，拍照图片在 `data/captures/`，报告在 `data/reports/`，考试归档在 `data/exams/`。
- 是否依赖本地文件：是。CSV/XLSX/JSON/HTML/XLSX 报告均落本地文件系统。
- 是否依赖外部 API：当前审计未发现真实外部 API 调用。OCR/AI 相关逻辑明确为未接入或 mock/占位。

## 4. 核心业务流程

1. 班级 / 学生名单：`roster_manager.import_roster` 读取 CSV/XLSX，规范化 `student_id`、`name`，写入 `data/classes/<class_id>/roster.csv`、`class_metadata.json`、`roster_validation_report.csv`，并更新 `classes_index.json`。
2. 新建考试：`web/index.html` 的 wizard 收集班级、考试名称、考试日期、科目，`web/static/app.js` 保存在前端状态并提交到 `web_app.py`。
3. 标准答案：`web_app.py.handle_answer_parse` 调用 `app.data_io.parse_answer_source` 生成草稿；`handle_answer_confirm` 调用 `review_rows_to_answer_key_csv` 写 `confirmed_answer_key.csv`。
4. 学生作答：`web_app.py.handle_preview` 接收作答文件，必要时 `table_file_to_csv` 转成 CSV；拍照入口仅保存图片和 `capture_manifest.json`。
5. 数据检查：`preview_session` 调用 `objective_grader.load_answer_key`、`load_submissions`、`grade_all` 以及 validation 逻辑，返回阻塞错误、未匹配学生、预览行。
6. 自动批改：`web_app.py.handle_grade` 调用 `app.workflow.run_grading`；后者调用 legacy 的 `load_answer_key`、`load_submissions`、`grade_all`。
7. 报告生成：`app.workflow.run_grading` 写 summary、detail、item_analysis、knowledge_profile、practice、class_report、student_report、teaching_plan、class_remedial、layered_remedial、HTML dashboard、Excel workbook。
8. 历史记录或数据保存：`run_grading` 输出到 `data/reports/...`，并通过 `archive_exam_reports`/归档逻辑进入 `data/exams/...`；`web_app.py.history_items` 读取历史供前端展示。

## 5. 判分逻辑审计

- `score_answer` 在 `legacy/objective_grader_legacy.py` 第 380 行。
- `grade_all` 在 `legacy/objective_grader_legacy.py` 第 449 行。
- `AnswerKey`、`QuestionSpec`、`StudentResult` 在 `legacy/objective_grader_legacy.py` 第 50、66、101 行；`app/core.py` 只是 re-export。
- 单选判分：`score_answer` 先判空答、文本等价，再判断 `actual == spec.answers` 满分；若标准答案只有 1 个且不相等，返回 `wrong`。
- 多选判分：如果 `partial_credit=True` 且标准答案数量大于 1，含错误选项返回 0；只选正确子集则按 `points * 选中正确数 / 正确答案数` 计算部分分。
- 判断题是否支持：没有独立 true/false 模型；如果用 A/B 或 0/1 作为答案，可被现有 choice/text 规则处理，但未发现专门题型。
- 填空题是否支持：部分支持。`score_answer` 支持 `answer_text`、`answer_aliases`、`tolerance`，`exam_recognizer.py` 中 blank 可标为 auto_gradable；但核心仍不是独立填空模型。
- 是否支持部分得分：支持多选按比例部分得分；`QuestionSpec.partial_points` 字段存在，但当前 `score_answer` 实际按比例计算，未使用 `partial_points`。
- 是否支持空答：支持，空集合且 raw 空返回 `(0.0, "blank")`。
- 是否支持异常答案：支持，选择题实际答案超出允许选项返回 `invalid`；`unrecognized` 文本返回 `unrecognized`。

多选规则核对：

- 正确答案 2 个时，测试 `run_tests.py` 覆盖选 1 个正确得一半、含错误选项得 0；`tests/test_enhanced_grading.py` 还覆盖全对、两个单独正确选项、空答。
- 正确答案 3 个时，`tests/test_enhanced_grading.py` 覆盖选 1 个得 1/3、选 2 个得 2/3、全对满分、含错误选项得 0。
- `run_tests.py` 当前只覆盖 2 个正确答案的多选部分得分，未覆盖 3 个正确答案场景。

## 6. 测试覆盖审计

`run_tests.py` 包含 13 个 unittest 测试，覆盖判分规则、文件流程、名单导入、阻塞错误、归档不覆盖、识别作答转换。`tests/test_enhanced_grading.py` 是额外轻量脚本，覆盖更细的多选规则、排名、掌握等级、别名/容差、非法选择。

- 是否测试了单选：是，`run_tests.py` 和 `tests/test_enhanced_grading.py` 均覆盖。
- 是否测试了多选部分得分：是。
- 是否测试了含错误选项得 0：是。
- 是否测试了空答：`tests/test_enhanced_grading.py` 覆盖多选空答；`run_tests.py` 覆盖空 submissions，但未直接断言每题 blank。
- 是否测试了排名：`tests/test_enhanced_grading.py` 覆盖 `competition_ranks`；`run_tests.py` 未直接覆盖排名。
- 是否测试了知识点分析：`tests/test_enhanced_grading.py` 覆盖 `mastery_level`，`run_tests.py` 在流程测试中间接生成 `knowledge_profile.csv`，但缺少字段级断言。
- 是否测试了 `paper-package.json`：否，未发现正式导入测试。
- 是否测试了 `assessment-result.json`：否，未发现正式导出测试。
- 当前测试缺口：正式题库协议、正式结果协议、前端行为、摄像头保存流程、OCR/AI 禁用边界、`partial_points` 字段行为、判断题专门语义、报告字段稳定性。

## 7. 数据模型审计

- 学生数据结构：`roster_manager.py` 使用 `student_id,name` CSV；`load_roster` 返回 `Dict[str, str]`；`Submission` dataclass 含 `student_id`、`name`、`answers`、`raw_answers`、`extra_questions`、`row_number`。
- 班级数据结构：`data/classes/classes_index.json` 存 `classes` 列表；`class_metadata.json` 字段包括 `class_id`、`class_name`、`created_at`、`updated_at`、`student_count`、`source_file`、`notes`；默认班级在 `default_class.json`。
- 考试数据结构：网页 session JSON 含 `class_name`、`exam_name`、`exam_date`、`subject`、`answer_key`、`submissions`、`question_bank`、`created_at`；`ExamMeta` dataclass 含 `exam_name`、`class_name`、`subject`、`exam_date`。
- 标准答案数据结构：`AnswerKey` 包含 `QuestionSpec` tuple；`QuestionSpec` 字段有 `number`、`answers`、`points`、`partial_credit`、`partial_points`、`tags`、`source_id`、`difficulty`、`answer_text`、`answer_aliases`、`tolerance`、`status`。
- 学生作答数据结构：CSV 表头为 `student_id,name,Q1,Q2...`；加载后是 `Submission.answers: Dict[int, FrozenSet[str]]` 和 `raw_answers: Dict[int, str]`。
- 批改结果数据结构：`StudentResult` 包含总分、百分比、计数和 `QuestionResult` 明细；`QuestionResult` 包含 `number`、`expected`、`actual`、`raw_actual`、`score`、`max_score`、`status`。
- 报告数据结构：大多是 CSV/HTML/XLSX，没有统一 JSON 模型。`summary.csv`、`detail.csv`、`item_analysis.csv`、`knowledge_profile.csv` 等由 legacy/app.workflow 以 dict/list 写出。

部分结构是稳定 dataclass，报告和网页 session 仍是隐式 dict/list，协议稳定性不足。

## 8. legacy 依赖审计

- `app/core.py` 是否只是转发 legacy：是。它从 `legacy.objective_grader_legacy` re-export `AnswerKey`、`QuestionSpec`、`StudentResult`、`score_answer`、`grade_all` 等。
- `app/analysis.py` 是否只是转发 legacy：是。它 re-export `basic_stats`、`build_class_report`、`build_knowledge_profiles`、`item_stats` 等。
- `app/workflow.py` 是否调用 legacy：是。`run_grading` 调用 `legacy.load_answer_key`、`legacy.load_submissions`、`legacy.grade_all`、`legacy.build_knowledge_profiles`、`legacy.write_*`。
- `objective_grader.py` 是否调用 legacy：是。它 `from legacy.objective_grader_legacy import *`，并以兼容 API 暴露历史实现。
- `web_app.py` 是否间接依赖 legacy：是。它 import `objective_grader`，而 `objective_grader.py` re-export legacy；它也通过 `app.workflow.run_grading` 间接依赖 legacy。

仍来自 `legacy/objective_grader_legacy.py` 的关键函数、类、数据结构包括：`QuestionSpec`、`AnswerKey`、`Submission`、`QuestionResult`、`StudentResult`、`BankQuestion`、`KnowledgeProfile`、`ExamMeta`、`normalize_answer`、`load_answer_key`、`load_submissions`、`score_answer`、`grade_submission`、`grade_all`、`build_knowledge_profiles`、`item_stats`、`basic_stats`、`build_validation_report`、各类 `write_*` 报告函数。

明确判断：当前 `app/` 还不是真正的现代模块化核心。`app/data_io.py`、`app/workflow.py`、`app/validators.py` 有新增编排和输入能力，但判分、模型、分析、报告核心仍主要在 legacy；`app/core.py` 和 `app/analysis.py` 是门面层。

## 9. 前端耦合审计

`web/static/app.js` 当前同时承担：

- 全局状态管理：顶部 `state` 对象。
- API 调用：`api()`、`fetch("/api/exams/grade")` 等。
- DOM 渲染：`renderStepper`、`renderStudents`、`renderHistory`、`renderReports`、`renderAnswerRows`、`renderValidation`、`renderResult`。
- 页面导航：`showView` 和侧边栏事件。
- 摄像头逻辑：`refreshCameras`、`openCamera`、`closeCamera`、`switchCamera`、`capturePhoto`。
- 文件上传：班级导入、答案解析、作答预览、拍照上传。
- 表格编辑：答案草稿行的渲染、收集、添加、删除。
- 批改流程控制：wizard step、preview、grade、allow_errors。
- 报告展示：历史列表、报告卡片、结果页链接。

判断：存在明显“大文件耦合风险”。这个文件把状态、网络、视图、设备、业务流程揉在一起，后续接入 `paper-package.json`、OCR 或报告新视图时很容易互相影响。

## 10. 题库系统打通现状

- 是否已有 `paper-package.json` 导入：否。当前有 `samples/sample_exam_manifest.json` 和 `exam_recognizer.py` 的 `exam_manifest.json`/`confirmed_exam_manifest.json` 流程，但未发现正式 `paper-package.json` 导入器。
- 是否已有 `assessment-result.json` 导出：否。当前输出 CSV/HTML/XLSX 和元数据 JSON，但未发现正式结果包导出。
- 是否保留 `paperId`：否。
- 是否保留 `questionId`：部分保留。`answer_key.csv` 支持 `question_id`/`bank_id`，进入 `QuestionSpec.source_id`，报告中输出 `question_id`。
- 是否保留 `questionNumber`：部分保留。当前主要字段叫 `question` 或 `number`，不是正式 `questionNumber`。
- 是否区分 `questionId` 和 `questionNumber`：内部可区分 `QuestionSpec.number` 和 `source_id`，但协议层尚未正式化。
- 是否支持 `estimatedDifficulty`：否。当前有 `difficulty`，取值 1-5。
- 是否支持 `actualDifficulty`：否。当前有 accuracy/wrong_rate，可推导，但未导出正式字段。
- 是否支持 `correctRate`：部分支持。`item_analysis.csv` 有 `accuracy` 百分数，但不是 `correctRate` 0-1。
- 是否支持 `optionDistribution`：部分支持。`item_analysis.csv` 有 `option_distribution` JSON 字符串，但键名和 blank 规则未对齐目标协议。
- 是否能把批改结果回流题库系统：当前不能直接回流，需要新增正式导出。

`samples/sample_exam_manifest.json` 与未来正式 `paper-package.json` 的差距：

- 当前 manifest 使用 `exam_name`、`class_name`、`subject`、`exam_date`、`question_count`、`questions[].question`、`questions[].answer`、`questions[].points`、`questions[].tags`、`questions[].difficulty`。
- 目标 `paper-package.json` 需要 `paperId`、`paperName`、`source`、`questions[].questionId`、`questionNumber`、`stem`、`options`、`correctAnswer` 数组、`score`、`knowledgePoints`、`estimatedDifficulty`、`images`。
- 当前 manifest 更像“识别出的考试结构”，不是题库系统标准题包；缺题干、选项、图片、稳定 paperId、标准 questionId 和难度语义。

## 11. 产品级重构风险

- legacy 继续膨胀风险：`legacy/objective_grader_legacy.py` 同时包含模型、判分、统计、报告、HTML、Excel、校验，继续堆功能会让风险集中。
- `app.js` 前端巨石风险：任何 UI、API、摄像头、表格或流程变更都可能影响同一文件中的其他功能。
- 判分逻辑和 UI 耦合风险：目前判分核心不直接在 UI，但前端流程字段、answer draft 字段和 legacy CSV 字段隐式绑定，协议变更容易断裂。
- 数据协议不稳定风险：大量数据以 CSV/dict/list 隐式流动，字段名如 `question`、`question_id`、`difficulty` 与未来协议不完全一致。
- 题库系统打通困难风险：没有正式 `paper-package.json` 导入和 `assessment-result.json` 导出，现有 manifest 不是题库协议。
- OCR / AI 功能提前接入导致污染数据的风险：当前拍照只保存图片，若在判分协议未稳定前直接接 AI/OCR，可能把不可靠识别结果当正式答案或作答。

## 12. 下一阶段建议

Stage A：补架构边界文档  
目标：明确当前真实结构和禁止事项。记录哪些模块仍是 legacy，哪些字段是临时 CSV 字段，哪些功能禁止 AI 决定分数。

Stage B：迁出 core/scoring  
目标：把 `QuestionSpec`、`AnswerKey`、`Submission`、`QuestionResult`、`StudentResult`、`normalize_answer`、`score_answer`、`grade_all` 从 legacy 中迁出到独立 scoring 模块，并用现有测试保护。

Stage C：补 `paper-package.json` 导入  
目标：支持从奇思数学 Pro 题库系统导入标准题目包，明确 `paperId`、`questionId`、`questionNumber`、`correctAnswer`、`score` 到内部 `QuestionSpec` 的映射。

Stage D：补 `assessment-result.json` 导出  
目标：批改完成后导出可以回流题库系统的结果包，包括 `summary`、`questionStats`、`correctRate`、`optionDistribution`、`actualDifficulty`、`difficultyGap`。

Stage E：整理前端 `app.js`  
目标：逐步拆分 API、状态、视图、摄像头、表格编辑，不一次性大改。先按职责拆文件，再改功能。

Stage F：再做拍照识别和 AI 讲评  
目标：在判分和数据协议稳定后，再接 OCR / AI。AI 只能生成讲评建议或识别草稿，不能决定学生分数。

## 13. 本次测试结果

- 执行的测试命令：`python run_tests.py`
- 测试是否通过：通过。
- 失败详情：无。输出显示 `Ran 13 tests in 0.099s`，结果 `OK`。
- 是否调用真实 AI / OCR / API：否。
- 是否修改业务代码：否。

## 14. 本次结论摘要

1. 不建议推倒重写，当前已有可运行的网页端、批改流程和报告输出壳。
2. 建议保留现有功能壳，先用测试保护关键行为。
3. 建议优先迁出判分核心，避免继续依赖 `legacy/objective_grader_legacy.py`。
4. 多选部分得分规则已经实现，且测试覆盖了关键场景。
5. 当前 `app/` 不是完整现代核心，主要仍是 legacy 门面和流程编排。
6. 前端 `web/static/app.js` 存在明显大文件耦合风险。
7. 当前尚未正式支持 `paper-package.json` 导入。
8. 当前尚未正式支持 `assessment-result.json` 导出。
9. 建议优先打通题库数据协议，再做 OCR / AI。
10. 建议暂缓真实 OCR / AI 接入，先稳定判分规则、题目 ID 和结果回流格式。
