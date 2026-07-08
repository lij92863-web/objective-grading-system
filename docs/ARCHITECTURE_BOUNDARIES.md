# Architecture Boundaries

## 当前推荐分层

```
presentation/         web/ (index.html, app.js, app.css), web_app.py
application/          app/application/use_cases/
domain/               app/domain/grading/
recognition/          app/recognition/, app/recognition/qwen_adapter/
infrastructure/       app/infrastructure/importers, exporters, storage
shared/               app/shared/errors.py
legacy/               legacy/ (隔离区, 只减不增)
```

## 依赖方向（自顶向下）

```
presentation → application → domain
                           → recognition
                           → infrastructure
domain 不允许依赖上层
recognition 不允许依赖 presentation
infrastructure 只依赖 shared 和标准库
legacy 是隔离区, 不允许被新模块依赖
```

## domain 层职责

- `app/domain/grading/`: 判分核心模型和算法
- 不允许 import legacy, web_app, recognition, infrastructure
- 不允许 HTTP 请求、文件 I/O、环境变量读取
- 纯业务核心

## recognition 层职责

- `app/recognition/`: 识别草稿、mock 流水线、异常队列
- 不允许 import legacy, web_app, web
- 可 import app.domain.grading（读取判分结果结构）
- 不直接写成绩、不直接接正式批改

## qwen_adapter 层职责

- `app/recognition/qwen_adapter/`: 千问 API 适配安全壳
- 除 real_client.py 外不允许 HTTP
- 不允许读取 .env、不允许硬编码 API key
- 不允许直接判分、写成绩、接 UI

## application/use_cases 层职责（预留）

- 协调 domain + recognition + infrastructure 完成教师工作流
- 一个用例一个类或函数

## infrastructure 层职责（预留）

- importers: 文件读取（roster, answer_key, submissions）
- exporters: CSV / Excel / HTML 报告生成
- storage: data/ 目录布局、归档、元数据

## presentation/web 层职责

- web_app.py: HTTP server
- web/index.html + app.js: 单页 UI
- 当前 app.js 仍是大文件（遗留风险，待拆分）

## legacy 冻结规则

- 只减不增
- 新判分、新 OCR、新千问、新题库、新 UI 一律不进 legacy
- 兼容 facade（app/core.py, objective_grader.py）可临时 import legacy
- 最终迁移路线: reports → infrastructure/exporters, Excel → infrastructure/exporters, 文件读取 → infrastructure/importers

## app/core.py 兼容 facade 规则

- 当前可 import legacy (白名单)
- 不允许 import recognition
- 作为旧入口到新核心的过渡层存在

## 禁止依赖方向

| 层 | 禁止依赖 |
|----|---------|
| domain | legacy, web_app, recognition, infrastructure, application |
| recognition | legacy, web_app, web, infrastructure, application |
| qwen_adapter | legacy, web_app, web, infrastructure, application |
| legacy | recognition.qwen_adapter, application, infrastructure |

## 后续所有任务必须先读本文档

任何新增模块必须符合以上分层规则。边界测试 `tests/test_architecture_boundaries.py` 会持续检查违规。
