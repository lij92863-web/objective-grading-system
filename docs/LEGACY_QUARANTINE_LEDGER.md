# Legacy Quarantine Ledger

## 当前 legacy 文件列表

```
legacy/
  __init__.py
  ARCHITECTURE.md
  objective_grader_legacy.py   — 旧判分核心 + 报告生成 + CSV/HTML/Excel
  old_modules/
    analysis/                  — 旧 item_analysis, knowledge_profile, practice_recommend, validation
    core/                      — 旧 answer_normalizer, grader, models, scoring
    io/                        — 旧 csv_io, xlsx_writer
    workflow/                  — 旧 grading_runner, archive
  old_outputs/                 — 历史输出存档（只读）
```

## legacy 当前承担哪些职责

| 职责 | 状态 |
|------|------|
| 判分核心 (QuestionSpec, AnswerKey, score_answer, grade_all) | **已迁出** → app/domain/grading/ |
| 识别草稿 (AnswerDraft, DraftAnswerItem) | **已迁出** → app/domain/grading/answer_draft.py |
| 判分预检 (PrecheckReport, run_grading_precheck) | **已迁出** → app/domain/grading/precheck.py |
| 识别 mock (RecognizedAnswerDraft, pipeline) | **已迁出** → app/recognition/ |
| 千问适配 (QwenClient, FakeQwenClient, RealQwenClient) | **已迁出** → app/recognition/qwen_adapter/ |
| 报告生成 (summary, detail, item_analysis, class_report) | **仍在 legacy** |
| Excel/HTML 输出 (write_workbook, write_advanced_dashboard) | **仍在 legacy** |
| 学生报告、讲评计划、补救建议 | **仍在 legacy** |
| 旧 CLI 兼容 (objective_grader.py) | **仍在 legacy** |
| CSV 加载 (load_answer_key, load_submissions) | **仍在 legacy** |
| validation report (build_validation_report) | **仍在 legacy** |

## 禁止新增到 legacy 的内容

- 新判分规则
- 新 OCR 逻辑
- 新千问 API 调用
- 新题库接入
- 新 UI 组件
- 新报告体系
- 新数据模型

## 后续迁移路线

| 内容 | 目标位置 |
|------|---------|
| 报告生成 (summary, detail, item_analysis) | app/infrastructure/exporters |
| Excel 导出 (write_workbook) | app/infrastructure/exporters |
| HTML 报告 (advanced_dashboard, simple_report) | app/infrastructure/exporters |
| CSV 加载 (load_answer_key, load_submissions) | app/infrastructure/importers |
| 归档逻辑 (archive_exam_reports) | app/infrastructure/storage |

## 兼容策略

1. 不直接删除 legacy
2. 先迁出目标功能到 infrastructure
3. 测试保护
4. 旧入口 (objective_grader.py, web_app.py) facade 调新模块
5. 最后瘦身 legacy

## 当前冻结状态

- legacy 允许 import app.domain.grading（STAGE1 兼容桥）
- legacy 不允许 import app.recognition / app.application / app.infrastructure
- 新模块不允许 import legacy（app/core.py 白名单除外）
