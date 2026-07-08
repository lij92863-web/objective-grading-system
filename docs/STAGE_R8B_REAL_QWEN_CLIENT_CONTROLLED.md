# Stage R8B Real Qwen Client — Controlled Access

## 本次目标

实现 `RealQwenClient`，默认禁用真实 API 调用，通过环境变量显式启用。不写死 API key，不读取 .env，不做批量识别。

## 为什么默认禁用真实 API

1. 安全：防止误操作意外产生 API 费用
2. 测试隔离：所有自动化测试仍使用 FakeQwenClient
3. 显式启用：只有明确设置 `QWEN_API_ENABLED=true` 才会发起网络请求
4. 不影响现有 mock 数据流和 168 个通过的测试

## RealQwenClient 结构

```
app/recognition/qwen_adapter/real_client.py
  RealQwenClient(QwenClient)
    ├── _is_enabled()        — 检查 QWEN_API_ENABLED
    ├── _check_config()      — 验证 API key / base / model
    ├── _resolve_image()     — 解析图片 (path → base64 或直接传 base64)
    ├── _call_api()          — HTTP POST (urllib, OpenAI-compatible)
    ├── recognize_name_field()
    ├── recognize_choice_cell()
    ├── recognize_blank_answer()
    └── judge_complex_blank()

app/recognition/qwen_adapter/prompt_builder.py
  build_prompt(request) → str
    ├── name_field           → NAME_FIELD_RECOGNITION_PROMPT
    ├── choice_cell          → CHOICE_CELL_RECOGNITION_PROMPT
    ├── blank_answer         → BLANK_ANSWER_RECOGNITION_PROMPT
    ├── complex_blank_judgment → COMPLEX_BLANK_JUDGMENT_PROMPT (动态填充)
    └── other                → raise QwenAdapterError
```

## 环境变量

| 变量 | 用途 | 缺失时行为 |
|------|------|-----------|
| `QWEN_API_ENABLED` | 总开关 | 抛 `api_disabled` |
| `QWEN_API_KEY` | API 密钥 | 抛 `missing_api_key` |
| `QWEN_API_BASE` | API base URL | 抛 `missing_api_base` |
| `QWEN_MODEL` | 模型名称 | 抛 `missing_model` |
| `QWEN_TIMEOUT_SECONDS` | HTTP 超时（默认 30s）| 使用默认值 |

启用条件：`QWEN_API_ENABLED=true` 且三个必填变量均非空。

## 安全边界

1. **不写死 API key** — 所有配置从环境变量或构造函数参数注入
2. **不读取 .env** — 只读 `os.environ`
3. **不打印 API key** — 错误消息不含密钥
4. **不打印 base64** — 日志中显示 `<base64 omitted>`
5. **image_path 检查存在性** — 不存在抛 `image_not_found`
6. **不扫描目录** — 只处理显式传入的单个图片
7. **不绕过 R8A 安全壳** — 所有响应经过 `parse_qwen_response` + validators + mapping

## 单图 Smoke 脚本用法

```bash
# dry-run（默认，不发送请求）
python scripts/qwen_single_image_smoke.py --image crop.png --prompt-type choice_cell

# 真实调用（需要环境变量）
python scripts/qwen_single_image_smoke.py --image crop.png --prompt-type choice_cell --no-dry-run

# 复杂填空判定
python scripts/qwen_single_image_smoke.py --image crop.png \
    --prompt-type complex_blank_judgment \
    --standard-answer "x>1" --student-answer "(1,+inf)"

# 提示类型
name_field | choice_cell | blank_answer | complex_blank_judgment
```

## Dry-run 输出示例

```
=== DRY-RUN (no API call) ===
  request_id      : 63ee07d61974
  prompt_type     : choice_cell
  image           : data/captures/smoke_capture/answer_sheet_001.jpg
  image_base64    : <not loaded in dry-run>
  prompt length   : 220 chars
  [OK] dry-run complete — request was NOT sent.
```

## Prompt 构造

`prompt_builder.py` 复用 `app.recognition.prompts` 常量：

- `name_field` / `choice_cell` / `blank_answer` — 直接使用常量
- `complex_blank_judgment` — 从 `request.metadata` 取 `standard_answer`、`student_answer` 等动态填充
- 不支持的 `prompt_type` → 抛出 `QwenAdapterError(unsupported_prompt_type)`

## 新增错误码

| 错误码 | 场景 |
|-------|------|
| `api_disabled` | QWEN_API_ENABLED 未设置或不为 true |
| `missing_api_key` | QWEN_API_KEY 缺失 |
| `missing_api_base` | QWEN_API_BASE 缺失 |
| `missing_model` | QWEN_MODEL 缺失 |
| `image_not_found` | 图片文件不存在 |
| `http_error` | HTTP 非 200 响应 |

## 测试覆盖

| 测试文件 | 测试数 | 覆盖内容 |
|---------|--------|---------|
| test_qwen_real_client_config | 7 | disabled/env false/missing key/base/model/no dotenv/explicit override |
| test_qwen_real_client_safety | 5 | image not found, no image, base64 omitted, API key not leaked, disabled message |
| test_qwen_real_client_request_building | 7 | 4 prompt types + no-metadata + unsupported + request_id |
| test_qwen_single_image_smoke_script | 10 | dry-run default/id/has no key/has no base64, missing image/type, complex args, all types |

新增 29 个测试，全部通过。总计 197 tests passed。

## 本次未做内容

- 未真实调用千问 API（需手动设置环境变量后使用 smoke 脚本）
- 未批量识别
- 未接入正式批改流程
- 未修改 UI
- 未修改判分规则
- 未读取 .env

## 进入 R8C 的条件

R8C 可以做**一次**真实受控调用：
1. 设置 `QWEN_API_ENABLED=true` + key/base/model
2. 使用单张裁剪小图（如 `data/captures/smoke_capture/answer_sheet_001.jpg`）
3. 运行 `scripts/qwen_single_image_smoke.py --no-dry-run`
4. 手动确认返回结果的结构和内容
5. 确认后继续迭代，仍不接入正式批改

---

**关联文档**：
- `docs/STAGE_R8A_QWEN_ADAPTER_SHELL.md` — R8A 适配层
- `docs/STAGE_R8A_ACCEPTANCE_HARDENING.md` — R8A 验收加固
- `app/recognition/qwen_adapter/` — 实现代码
