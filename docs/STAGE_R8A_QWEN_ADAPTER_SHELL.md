# Stage R8A Qwen Adapter Shell

## 本次目标

为后续接入真实千问 / Qwen-OCR / Qwen-VL API 建立安全、可测试、可替换的适配层。本次不真实调用千问 API，不读取 API key，不访问外网。

## 为什么本次不真实调用 API

1. 数据流未通：调用真实 API 返回的结果无法直接映射到现有 `RecognizedAnswerDraft` 和 `QwenJudgmentMock`，先搭好适配层再接入。
2. 安全边界未设：直接接入可能把 API key、base64 图片数据泄露到日志或错误消息。
3. 测试覆盖为零：没有 adapter 层的测试，直接接 API 无法区分"API 问题"和"代码问题"。
4. 可替换性：有了抽象接口和 fake client，后续换模型或切换 API 供应商只需要换一个实现。

## 新增模块结构

```
app/recognition/qwen_adapter/
  __init__.py      — 公开 API
  errors.py        — QwenAdapterError, QwenAdapterErrorCode (8 种错误码)
  models.py        — QwenImageInput, QwenRequest, QwenRawResponse, QwenParsedResult
  client.py        — QwenClient 抽象接口 (4 个方法)
  fake_client.py   — FakeQwenClient (预设 + 注入异常)
  parser.py        — parse_qwen_response() JSON 解析 + 校验
  validators.py    — 4 种 prompt type 的独立校验器
  mapping.py       — QwenParsedResult → 现有 domain 类型
```

## QwenClient 接口

抽象类，定义 4 个方法：

| 方法 | prompt_type | 返回 |
|------|------------|------|
| `recognize_name_field()` | `name_field` | QwenRawResponse |
| `recognize_choice_cell()` | `choice_cell` | QwenRawResponse |
| `recognize_blank_answer()` | `blank_answer` | QwenRawResponse |
| `judge_complex_blank()` | `complex_blank_judgment` | QwenRawResponse |

## FakeQwenClient 行为

- 默认返回预设合法 JSON（姓名栏"1李明"、选择题"AB"、填空"1/2"、判定 correct 0.96）
- `inject_error(key)` — 注入 6 种异常响应（invalid_json, missing_field, invalid_verdict, invalid_confidence, empty_reason, needs_review_true）
- `inject_custom_payload(dict)` — 自定义响应
- `clear_injection()` — 恢复默认
- 不访问网络，不读取文件

## Parser / Validator 规则

### parse_qwen_response()

1. 尝试 JSON 解析（先检查 `parsed_json`，再尝试解析 `raw_text`）
2. 非 JSON → `INVALID_JSON`
3. 调用对应的 validator
4. 返回 `QwenParsedResult(status, data, confidence, errors, warnings)`

### 四种 validator

| prompt_type | 校验规则 |
|------------|---------|
| name_field | raw_text 必填，confidence 0-1 |
| choice_cell | answer 必填，限 A-D 组合/blank/unclear/invalid，confidence 0-1 |
| blank_answer | raw_text 或 status 至少一个，status 限 recognized/blank/unclear，confidence 0-1 |
| complex_blank_judgment | verdict 限 correct/wrong/partial/needs_review/invalid，confidence 0-1，correct/wrong/partial 时 normalized 必填，requires_review 须为 bool，reason 在 verdict!=invalid 时必填 |

## 映射到 RecognizedAnswerDraft 的方式

| 映射函数 | 输入 | 输出 |
|---------|------|------|
| `parse_name_field_to_identity_candidate()` | QwenParsedResult → parse_student_identity() | StudentIdentityCandidate |
| `parse_choice_response_to_draft()` | QwenParsedResult → ChoiceCellOutput → normalize_choice_recognition() | RecognizedAnswerDraft |
| `parse_blank_response_to_draft()` | QwenParsedResult → MockBlankOutput → normalize_blank_recognition() | RecognizedAnswerDraft |
| `parse_complex_judgment_response()` | QwenParsedResult → QwenJudgmentMock | QwenJudgmentMock |

所有映射函数复用 `app/recognition/models.py` 的现有类型，不制造第二套数据结构。

## 安全边界

1. 不打印 API key
2. 不读取 .env
3. 不把 image_base64 写入日志
4. 错误信息不包含完整图片数据
5. request_id 用于追踪
6. 解析失败时输出安全错误码（不输出 raw response body）
7. 不吞掉异常
8. 不把 invalid response 当成正确识别

## 测试覆盖

| 测试文件 | 测试数 | 覆盖内容 |
|---------|--------|---------|
| test_qwen_adapter_fake_client | 10 | 4 种默认响应, invalid_json, missing_field, custom_payload, clear_injection, request_id, model |
| test_qwen_adapter_parser | 13 | 4 种有效解析, 非JSON, 空字符串, missing_field, confidence越界, invalid_verdict, unsupported_type |
| test_qwen_adapter_validation | 17 | name_field×3, choice_cell×6, blank_answer×5, complex_judgment×7 |
| test_qwen_adapter_mapping | 10 | name→identity(+roster), choice→draft(+blank), blank→draft(+unclear), judgment→mock(+auto_accept/no) |

新增 50 个测试，加上原有 102 个测试，共 152 个测试，全部通过。

## 未完成内容

- 未实现真实 QwenClient（保留给 Stage R8B）
- 未调用任何外部 API
- 未读取 .env 或 API key
- 未修改现有判分规则
- 未修改 UI

## 下一步 R8B 如何接真实 API

1. 实现 `RealQwenClient(QwenClient)`，调用 Qwen API endpoint
2. 默认关闭真实调用，用环境变量 `QWEN_API_ENABLED=true` 显式启用
3. 复用现有的 `parse_qwen_response()` 解析真实 API 返回
4. 复用现有的 mapping 函数映射到 `RecognizedAnswerDraft`
5. API key 通过环境变量 `QWEN_API_KEY` 注入，不写入代码
6. 添加真实 API 调用的集成测试（标记为 slow，默认不跑）

---

**关联文档**：
- `docs/ANSWER_RECOGNITION_ARCHITECTURE.md` — 总体架构设计
- `docs/STAGE_R2_R7_RECOGNITION_MOCK_PIPELINE.md` — R2-R7 mock pipeline
- `app/recognition/` — recognition 主模块
- `app/recognition/qwen_adapter/` — 本阶段实现
