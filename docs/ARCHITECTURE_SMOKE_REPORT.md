# Architecture Smoke Report

## 测试命令

```
python run_tests.py
python -m unittest discover -s tests -p "test*.py"
```

## 测试结果

226 tests passed, OK. 包含原有 197 + 新增 29 架构测试。

## CLI 样例执行

```
python objective_grader.py --answer-key samples/demo_exam/answer_key_sample.csv --submissions samples/demo_exam/submissions_sample.csv --out-dir data/reports/architecture_smoke_cli --no-archive
```

结果：批改完成。输出到 `data/reports/architecture_smoke_cli/index.html`。

## 输出目录

`data/reports/architecture_smoke_cli/` — 包含 summary.csv, detail.csv, item_analysis.csv, exam_report.xlsx, index.html 等完整报告。

## web_app 是否能启动

`import web_app` 模块导入成功，无 import error。

## 是否有 import error

无。所有入口点 (`objective_grader`, `web_app`, `app.core`, `legacy.objective_grader_legacy`, `roster_manager`, `exam_recognizer`) import 正常。

## 是否调用真实 API

否。所有测试默认禁用真实 API。`test_no_uncontrolled_external_effects` 测试已验证无外部调用泄漏。

## 是否修改 UI

否。`web/` 目录未改动。

## 发现的问题

无阻塞问题。已知风险：

- `web/static/app.js` 仍是大文件（~2000+ 行），需要拆分为 state/api/views/table/camera 等模块
- legacy 报告生成仍未被完全替代
- report/Excel workflow 仍在 legacy

## 下一步建议

1. 保持当前架构边界，所有新功能进新模块
2. 逐步将报告生成从 legacy 迁到 `app/infrastructure/exporters`
3. 前端 app.js 拆分放到独立任务
4. 持续运行边界测试防止回归
