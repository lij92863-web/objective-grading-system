# Stage R8A Acceptance & Hardening

## 验收目标

在不接真实千问 API 的前提下，对 R8A 适配层进行格式检查、安全加固和边界测试补齐。

## 文件格式检查结果

- 所有 `app/recognition/qwen_adapter/*.py` 文件使用标准换行（LF），无超长行（全部 < 120 字符）
- `tests/test_qwen_adapter_*.py` 格式正常
- `docs/STAGE_R8A_QWEN_ADAPTER_SHELL.md` Markdown 可读

均无需格式修复。

## request_id 追踪修复

| 修改 | 文件 | 内容 |
|------|------|------|
| 新增字段 | `models.py` | `QwenParsedResult.request_id: str` |
| 传播逻辑 | `parser.py` | 所有返回路径填充 `resolved_id = request_id or response.request_id or ""` |

优先级：显式传入 `request_id` > `response.request_id` > 空字符串。

## mapping error guard

所有 4 个 mapping 函数新增硬门禁 `_guard(result, label)`：

- `result.status != "ok"` 或 `result.errors` 非空 → 抛出 `QwenAdapterError(unsafe_response, ...)`
- 不允许把 error result 静默转成 draft
- `_guard` 在 mapping 函数第一行执行

## requires_review bool 安全

- 新增 `_safe_bool(value, default)` 函数
- `None` → 返回 `default`（True）
- 已是 `bool` → 直接返回
- 其他类型（包括字符串 `"false"`）→ 抛出 `QwenAdapterError(invalid_verdict, ...)`
- 替换了 `parse_complex_judgment_response` 中原来的 `bool(result.data.get(...))`

## FakeQwenClient 注入语义

改为 **one-shot**：

- `_consume_injections()` 取出当前注入值并立即清零
- `inject_error`：只影响下一次调用
- `inject_custom_payload`：只影响下一次调用
- `clear_injection`：仍有效，可在 one-shot 前手动清除
- 文档已更新，明确标注 "one-shot"

## Validator 修复

`validate_choice_cell_response`：不再使用固定合法值集合校验。改为：
- `blank`/`unclear`/`invalid` 直接通过
- 纯 A-D 字母组合通过（兼容 `BA` 等未排序形式）
- 含非 A-D 字符 → `INVALID_VERDICT`

## 测试覆盖

| 测试文件 | 新增测试 | 覆盖内容 |
|---------|---------|---------|
| test_qwen_adapter_fake_client | +4 | one-shot error/custom, clear_injection after one-shot, consecutive injections |
| test_qwen_adapter_parser | +3 | request_id from response, explicit override, request_id on error |
| test_qwen_adapter_mapping | +8 | error guard × 4 funcs, non-ok status guard, string "false" raises, True/False/missing bool |
| test_qwen_adapter_validation | 已有 | E illegal, lowercase handled 仍通过 |

总计新增 15 个测试，全部通过。现有测试无回归。

## 测试结果

```
Ran 168 tests in 0.100s
OK
```

34 原始 + 66 R2-R7 + 50 R8A 原始 + 18 R8A 加固 = 168 tests, all passed.

## 未做内容

- 未接真实千问 API
- 未读取 .env / API key
- 未改 UI
- 未改判分规则
- 未接题库

## 是否可以进入 R8B

**可以。** 适配层已具有：
1. request_id 全链路追踪
2. mapping error 硬门禁（error result 不可能被静默映射）
3. requires_review 严格 bool（`bool("false")` 不再被静默接受）
4. FakeQwenClient one-shot 注入语义清晰
5. 完整测试覆盖（168 tests）

R8B 实现 `RealQwenClient` 时可安全复用 parser → validator → mapping 链路。

---

**关联文档**：
- `docs/STAGE_R8A_QWEN_ADAPTER_SHELL.md` — R8A 适配层原始设计
- `docs/ANSWER_RECOGNITION_ARCHITECTURE.md` — 总体架构
- `app/recognition/qwen_adapter/` — 实现代码
