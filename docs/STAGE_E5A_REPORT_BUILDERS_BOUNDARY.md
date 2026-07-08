# Stage E5A Report Builders Boundary

## 目标

建立 `app/application/use_cases/report_builders/` 骨架，定义分析构建层与 exporters、domain、legacy 的边界。

## 为什么先迁分析构建

CSV 写出层 (E2A-H) 已经迁到 `infrastructure/exporters/`，但它们需要数据 rows 输入。这些 rows 原本由 legacy 的 build_* 函数生成。迁出 build_* 逻辑后，CSV exporters 可以完全脱离 legacy 工作。

## 新增模块

```
app/application/use_cases/report_builders/
  __init__.py     — 模块说明
  contracts.py    — ReportBuildResult, ReportRowsBundle dataclasses
```

## 职责边界

| 层 | 职责 | 禁止 |
|----|------|------|
| report_builders | 生成报告数据 rows (dicts) | 不写文件、不 import legacy、不 import web、不调用 exporters |
| exporters | 写 CSV/Excel/HTML | 不计算分析数据、不 import legacy |
| domain/grading | 判分 | 不写文件、不生成报告 |
| legacy | 历史对照 | 不新增逻辑 |

## 测试覆盖

- `test_report_builders_boundaries.py`: 3 tests (不 import legacy, web, exporters)

## 未做内容

- 未迁移具体 builder 逻辑 (E5B-F)
- 未替换 workflow
- 未删除 legacy
