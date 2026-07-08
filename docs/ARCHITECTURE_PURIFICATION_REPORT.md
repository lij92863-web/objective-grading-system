# Architecture Purification Report

## 本次任务目标

不做新产品功能，只做架构净化、边界锁定、兼容检查、测试补强、文档固化。

## 完成阶段列表

| 阶段 | 内容 | 状态 |
|------|------|------|
| 0 | 预检 (git status, tests) | 通过 |
| 1 | 架构边界测试 | 完成 (11 tests) |
| 2 | 外部副作用禁令 | 完成 (6 tests) |
| 3 | 代码可读性 guard | 完成 (3 tests) |
| 4 | 新架构骨架 + ARCHITECTURE_BOUNDARIES.md | 完成 |
| 5 | legacy 隔离 + LEGACY_QUARANTINE_LEDGER.md | 完成 (3 tests) |
| 6 | 旧流程回归 smoke + ARCHITECTURE_SMOKE_REPORT.md | 完成 (6 tests) |
| 7 | 净化总结报告 (本文档) | 完成 |

## 新增架构边界测试 (11 tests)

- `test_architecture_boundaries.py`:
  - domain 不 import legacy (1 test)
  - domain 不 import web/cli (1 test)
  - domain 不 import recognition (1 test)
  - recognition 不 import legacy (1 test)
  - recognition 不 import web/cli (1 test)
  - qwen_adapter 不 import legacy (1 test)
  - qwen_adapter 不 import web (1 test)
  - legacy 不 import recognition (1 test)
  - legacy 不 import qwen_adapter (1 test)
  - app/core.py 不 import recognition (1 test)
  - 白名单 facade 确认 (1 test)

## 外部副作用禁令 (6 tests)

- `test_no_uncontrolled_external_effects.py`:
  - 测试文件不 import HTTP client (1 test)
  - 测试不读取 .env (1 test)
  - 测试不要求 QWEN_API_KEY (1 test)
  - app 无硬编码 API key (1 test)
  - app 不 print base64 (1 test)
  - smoke 脚本默认 dry-run (1 test)

## 代码可读性 Guard (3 tests)

- `test_code_readability_guard.py`:
  - 无超长物理行 (>200 chars, prompts/real_client 白名单) (1 test)
  - Markdown 文档非单行 dump (1 test)
  - 文件 UTF-8 编码 (1 test)

## 新架构骨架

```
app/application/__init__.py + use_cases/__init__.py
app/infrastructure/__init__.py + importers/ + exporters/ + storage/
app/shared/__init__.py + errors.py
```

## legacy 隔离

- `test_legacy_quarantine.py` (3 tests)
- `docs/LEGACY_QUARANTINE_LEDGER.md`
- legacy 允许 import app.domain.grading（STAGE1 兼容桥）
- legacy 不允许 import recognition/application/infrastructure
- 新模块不允许 import legacy（白名单除外）

## 旧流程 Smoke

- CLI demo 样例：批改完成，输出完整报告
- web_app import：无错误
- 所有入口点 import 正常
- `test_legacy_entrypoints_import.py` (6 tests)

## 当前仍然存在的隐藏炸弹

| 炸弹 | 风险等级 | 说明 |
|------|---------|------|
| `web/static/app.js` | 高 | ~2000+ 行单文件，职责混杂（state/api/views/camera/wizard） |
| legacy 报告生成 | 中 | summary/detail/item_analysis/class_report 等仍在 legacy |
| legacy Excel/HTML | 中 | write_workbook, write_advanced_dashboard 仍在 legacy |
| app/workflow.py 依赖 legacy | 中 | run_grading 直接调用 legacy.write_* 函数 |
| web_app.py 文件长度 | 中 | web_app.py ~530 行，可拆分为路由和业务 |

## 哪些炸弹已经拆掉

| 已拆 | 说明 |
|------|------|
| 判分核心 | 从 legacy 迁到 app/domain/grading/ |
| 识别草稿 | answer_draft / precheck 迁到 app/domain/grading/ |
| 识别 mock | 新建 app/recognition/（不依赖 legacy） |
| 千问适配 | 新建 app/recognition/qwen_adapter/（安全壳） |
| 架构边界 | 226 测试锁死分层依赖 |
| API 泄漏 | 禁止测试检查硬编码 key / .env / base64 print |
| legacy 膨胀 | 新功能禁入 legacy，反向依赖被测试锁死 |

## 哪些地方仍不能碰

- `web/static/app.js`: 不改（UI 任务独立）
- 题库接入: 不改（独立任务）
- 真实千问调用: 只允许通过 smoke 脚本手动触发
- legacy 删除: 先迁出再瘦身

## 下一阶段建议

1. 将报告生成从 legacy 迁到 `app/infrastructure/exporters`
2. Excel/HTML 导出迁到 `app/infrastructure/exporters`
3. 文件读取迁到 `app/infrastructure/importers`
4. 前端 app.js 拆分（state/api/views/table/camera）
5. 每次架构变更前运行 `test_architecture_boundaries` 检查违规

---

**新底座已经被 226 个测试锁边界。后续迁移不能绕过 ARCHITECTURE_BOUNDARIES.md。**
