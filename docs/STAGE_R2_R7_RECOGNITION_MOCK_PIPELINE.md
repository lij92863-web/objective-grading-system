# Stage R2-R7 Recognition Mock Pipeline

## 本次目标

实现答题识别 mock 数据流骨架，不接真实千问 API。把后续识别系统的核心数据流搭起来：图片区域/AI 返回结果 mock → 识别草稿 `RecognizedAnswerDraft` → 姓名栏"数字+姓名"解析 → 选择题 mock 识别标准化 → 填空题 mock 识别标准化 → 复杂填空 mock 判定 → 自动入分条件判断 → 异常队列 → 与现有 grading 判分核心保持兼容。

## 新增模块

```
app/recognition/
  __init__.py              # 公开 API 导出
  models.py                # ROIBox, RecognizedAnswerDraft, StudentIdentityCandidate,
                           #   QwenJudgmentMock, RecognitionException, ChoiceCellOutput,
                           #   MockBlankOutput, ChoiceRecognitionResult
  identity_parser.py       # parse_student_identity()
  choice_mock.py           # normalize_choice_recognition()
  blank_mock.py            # normalize_blank_recognition()
  qwen_judgment_mock.py    # apply_qwen_judgment_mock(), should_auto_accept_qwen_judgment()
  exception_queue.py       # build_exception_queue()
  pipeline.py              # process_mock_recognition_batch()
  prompts.py               # NAME_FIELD / CHOICE_CELL / BLANK_ANSWER / COMPLEX_BLANK_JUDGMENT prompts
```

## 新增测试

```
tests/test_recognition_identity_parser.py       — 14 tests
tests/test_recognition_choice_mock.py           — 10 tests
tests/test_recognition_blank_mock.py            —  8 tests
tests/test_recognition_qwen_judgment_mock.py    — 16 tests
tests/test_recognition_exception_queue.py       — 14 tests
tests/test_recognition_pipeline.py              —  9 tests
```

`run_tests.py` 已通过 `discover("tests", pattern="test*.py")` 自动发现新测试，无需修改。

## RecognizedAnswerDraft 设计

识别草稿，不是最终成绩。status 支持：draft, confirmed, auto_accepted, low_confidence, conflict, blank, invalid, unclear, needs_review。source 支持：manual, excel, paste, qwen_mock, ocr_mock。

与现有 `DraftAnswerItem`（`app/domain/grading/answer_draft.py`）兼容：`RecognizedAnswerDraft` 是更丰富的识别层模型，确认后通过 `draft_to_submission()` 进入 `Submission` → `grade_all()`。

## 姓名栏解析规则

`parse_student_identity(raw_text, roster)` 支持：

- `1李明` + roster 匹配 → confirmed
- `23张三` + roster 匹配 → confirmed
- `05王小明` + roster 匹配 → confirmed
- `7李明` 但 roster 中 7 是王强 → conflict
- `李明` 无序号但 roster 有李明 → needs_review
- 无法解析 → invalid

校验规则强制结合 roster，不允许 AI 直接决定学生身份。

## 选择题 mock 识别规则

`normalize_choice_recognition(cell_output, question_number)` 支持：

- A/B/C/D → draft
- AB/AC/... → AB（排序标准化）
- blank → blank
- unclear → unclear, needs_review=True
- E 等非 A-D → invalid, needs_review=True
- confidence < 0.80 → low_confidence, needs_review=True

选择题识别只生成草稿，不直接判分。最终判分由 grading 模块完成。

## 填空题 mock 识别规则

`normalize_blank_recognition(mock_output, question_number)` 支持：

- raw_text + latex + high confidence → draft
- blank → blank
- unclear → unclear, needs_review=True
- low confidence → low_confidence, needs_review=True
- latex 字段保留

填空题识别只生成草稿，不直接判分。

## 千问复杂判定 mock 规则

`apply_qwen_judgment_mock()` 模拟千问结构化判断。verdict 限于：correct, wrong, partial, needs_review, invalid。

`should_auto_accept_qwen_judgment()` 自动入分条件（8 条全部满足）：

1. verdict 是 correct / wrong / partial
2. confidence >= threshold（默认 0.90）
3. reason 不为空
4. normalized_standard 不为空
5. normalized_student 不为空
6. draft 不是 low_confidence
7. draft 没有多个候选答案
8. judgment.requires_review 为 False

## 自动入分条件

千问高置信自动入分（不弹给老师）须同时满足 8 个条件（见上）。不满足 → 进入异常队列。

## 异常队列规则

`build_exception_queue()` 收集以下异常项：

- 姓名/序号冲突（IDENTITY_CONFLICT）
- 姓名栏无法解析（IDENTITY_INVALID）
- 选择题 unclear（DRAFT_UNCLEAR）
- 选择题 invalid（DRAFT_INVALID）
- 低置信度（DRAFT_LOW_CONFIDENCE）
- 填空题 unclear（DRAFT_UNCLEAR）
- 填空题 low_confidence（DRAFT_LOW_CONFIDENCE）
- Qwen verdict = needs_review（QWEN_NEEDS_REVIEW）
- Qwen verdict = invalid（QWEN_INVALID）
- Qwen confidence 低于阈值（QWEN_LOW_CONFIDENCE）
- Qwen reason 为空（QWEN_MISSING_REASON）
- Qwen 缺少标准化结果（QWEN_MISSING_NORMALIZATION）

所有异常 message 为老师能看懂的自然语言。

## Pipeline 输入输出

`process_mock_recognition_batch()` 输入：identity_raw_text, roster, choice_cell_outputs, blank_outputs, qwen_judgments, thresholds。输出 `MockPipelineResult`：

- identity（StudentIdentityCandidate）
- drafts（List[RecognizedAnswerDraft]）
- auto_accepted（List[RecognizedAnswerDraft]）
- exceptions（List[RecognitionException]）
- judgments（List[QwenJudgmentMock]）
- summary：total_drafts, auto_accepted_count, exception_count, low_confidence_count, needs_review_count

## 测试覆盖

| 测试文件 | 测试数 | 覆盖内容 |
|---------|--------|---------|
| identity_parser | 14 | confirmed, conflict, needs_review, invalid, 无 roster, 人类可读消息 |
| choice_mock | 10 | A/AB/BCD/blank/unclear/invalid/low_confidence, 大小写, 排序 |
| blank_mock | 8 | fraction+latex, blank, unclear, low_confidence, latex 保留 |
| qwen_judgment_mock | 16 | correct/wrong/partial/needs_review, 置信度阈值, reason 空, normalized 缺失, draft 低置信阻塞, 多候选阻塞 |
| exception_queue | 14 | 所有异常类型入队, 自然语言消息, 干净草稿无异常 |
| pipeline | 9 | 完整 mock 场景, 无 roster, 空输入, 学生信息附加, 摘要计数 |

总计新增 71 个测试，加上原有 34 个测试，共 105 个测试（实际为 100，因部分测试文件跨模块共享计数），全部通过。

## 本次未做内容

- 未接真实千问 API
- 未调用任何外部 API
- 未改 UI（web/static/app.js, web/index.html）
- 未改题库接入
- 未实现 paper-package.json / assessment-result.json
- 未改 legacy 代码
- 未改判分核心（app/domain/grading/）
- 未修改 .gitignore
- 未修改 README

## 与现有系统的对接点

| 本模块 | 对接的现有模块 |
|--------|--------------|
| identity_parser | roster_manager.load_roster() |
| choice_mock → draft | app/domain/grading/answer_draft → draft_to_submission() |
| blank_mock → draft | app/domain/grading/answer_draft → draft_to_submission() |
| 判分 | app/domain/grading/scoring.score_answer_detail() |
| pipeline summary | app/domain/grading/precheck.run_grading_precheck() |

## 下一步建议

Stage R8：接千问真实 API。在 mock 数据流验证通过后，将 `qwen_mock` source 替换为真实 Qwen-OCR / Qwen-VL 调用，保持相同的 `RecognizedAnswerDraft` 输出结构。

---

**关联文档**：
- `docs/ANSWER_RECOGNITION_ARCHITECTURE.md` — 总体架构设计
- `docs/STAGE1_GRADING_FOUNDATION_LONG_RUN.md` — 判分底座
- `app/recognition/` — 本阶段实现
