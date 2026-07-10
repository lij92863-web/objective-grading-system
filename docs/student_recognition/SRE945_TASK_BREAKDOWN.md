# SRE945–SRE980 Template Builder & Calibration — 任务分解（SRE945-A … H）

> 配套：`SRE945_TEMPLATE_BUILDER_DESIGN.md`、`SRE945_TEMPLATE_PROFILE_V2_SCHEMA.md`、`SRE945_TEST_PLAN.md`。
> 约束：仅设计 + 任务分解；不写实现代码（实现交工程师，测试交 QA）。
> 边界锁死：不做 OMR / 图像矫正 / 批改 / Qwen-OCR / web_app / 真实图 / 新依赖（B4/B5/B10/§13/锁死令）。

---

## 依赖总览（DAG）

```
SRE945-A (数据模型+坐标+冻结OMR接口)
   ├─> SRE945-B (Draft + Validator + 错误码)
   ├─> SRE945-C (Anchor + BubbleGrid 展开)
   ├─> SRE945-D (Synthetic v1→v2 adapter)
   └─> SRE945-E (TemplateStore 版本化)
SRE945-B,C,D ─> SRE945-F (Calibrator L1 + L0 JSON + L2 接口)
SRE945-E,F ─> SRE945-G (CLI build_template.py)
SRE945-A..G ─> SRE945-H (测试 + 守卫)
```

---

## SRE945-A — TemplateProfile v2 数据模型 + 坐标系统 + 冻结 OMR 接口

- **产出文件**
  - `app/student_recognition/template/__init__.py`
  - `app/student_recognition/template/template_profile.py`  （v2，`TemplateProfile` + `OptionCell` + `TemplateRef`）
  - `app/student_recognition/template/coordinates.py`      （normalized ↔ runtime pixel 转换）
  - `tests/student_recognition/test_template_profile_schema.py`（§15.1）
  - `tests/student_recognition/test_template_roi.py`（§15.2）
- **验收点**
  1. `TemplateProfile` 落盘坐标全为 normalized（0–1，origin=top_left）；`from_dict` 拒绝非 `"2.0"` 版本（v1 自动走 adapter，见 D）。
  2. `coordinates.to_runtime_pixels(norm_roi, W, H)` = `norm * (W,H)`，纯 stdlib，无 PIL。
  3. 冻结接口存在：`get_option_cells(question_no)` / `get_identity_roi()` / `get_blank_roi(question_no)` / `get_all_option_cells()`，返回 normalized ROI。
  4. `TemplateRef(template_id, template_version)` 数据类定义完成（供 CaptureJob/RecognitionDraft 后续引用）。
  5. 错误码枚举化，无 freeform（B6）。

---

## SRE945-B — TemplateDraft + TemplateValidator + 错误码追加

- **依赖**：SRE945-A
- **产出文件**
  - `app/student_recognition/template/template_draft.py`     （`TemplateDraft`，可编辑、可不完整）
  - `app/student_recognition/template/template_validator.py` （`TemplateValidator` + `ValidationReport` + `TemplateValidationError`）
  - `app/student_recognition/errors/error_codes.py`          （优先复用既有 `TEMPLATE_*`；仅缺口时追加）
  - `app/student_recognition/errors/error_catalog.py`        （审计既有码；新增码必须同步登记）
  - `tests/student_recognition/test_template_validator.py`   （§15.1/15.2/15.3/15.4 校验项）
  - `tests/student_recognition/test_template_draft_profile.py`（§15.5）
- **验收点**
  1. `TemplateDraft.finalize()` → 经 Validator → `TemplateProfile`；invalid 抛 `TemplateValidationError(report)`，report 的 `errors[]` 全为 `ErrorCode`。
  2. Validator 覆盖 §7.1 全部校验项（schema_version/template_id/template_version/page 缺失、coordinate_system 非法、ROI 越界/≤0/NaN/null、identity 缺失、question_no 重复、option cell 缺失、option label 非法、单选缺 ABC、多选缺 options、题块空、展开越界、ROI 重叠警告、page_id/page_no 重复）。
  3. `ValidationReport.status ∈ {valid, invalid}`；`message` 一律来自 `error_message.message_for(code)`（禁 freeform）。
  4. `test_template_draft_cannot_be_used_for_recognition` / `valid_draft_can_be_finalized_to_profile` / `invalid_draft_cannot_finalize` 通过。

---

## SRE945-C — Anchor + BubbleGrid 展开

- **依赖**：SRE945-A
- **产出文件**
  - `app/student_recognition/template/anchor_layout.py`  （`Anchor` + `QuestionBlock` 展开为 OptionCell/blank ROI）
  - `tests/student_recognition/test_template_questions_options.py`（§15.3）
  - `tests/student_recognition/test_template_identity.py`（§15.4，identity 解析部分）
- **验收点**
  1. `expand_block(block, anchors)` 由 anchor + layout 确定性展开 Q1..Qn 的 A/B/C/D ROI（纯 math）。
  2. 支持 `single_choice`/`multi_choice`；`question_range` 连续区间 `[1,12]` 展开正确；非连续列表与 `layout.columns>1` 仅预留，首版明确拒绝，不得接受后忽略。
  3. 展开后 ROI 越界→`TEMPLATE_ROI_OUT_OF_BOUNDS`；题号重复→`TEMPLATE_DUPLICATE_QUESTION_NO`；option label 非法→`TEMPLATE_INVALID_OPTION_LABEL`。
  4. `test_template_expands_choice_grid` / `test_template_expanded_grid_rois_are_in_bounds` 通过。

---

## SRE945-D — Synthetic v1→v2 兼容层（adapter）

- **依赖**：SRE945-A, SRE945-C
- **产出文件**
  - `app/student_recognition/template/compatibility.py`（`adapt_synthetic_to_v2`）
  - `tests/student_recognition/test_template_synthetic_compat.py`（§15.8）
- **验收点**
  1. `adapt_synthetic_to_v2(synthetic.TemplateProfile)` → v2 `TemplateProfile`：pixel 几何 ÷ canvas 得 normalized，单一锚点 + 单 question_block + combined_identity_roi。
  2. **不修改** `synthetic/template_profile.py`，**不重写** synthetic fixtures。
  3. `test_synthetic_template_profile_still_valid`（adapter 产物过 Validator）/ `test_synthetic_fixtures_still_generate`（synthetic 生成器仍可产图）/ 间接保证 `test_sre121_tests_still_pass`（CI 守卫，不破 123 测试）。

---

## SRE945-E — TemplateStore 版本化落盘

- **依赖**：SRE945-A, SRE945-B
- **产出文件**
  - `app/student_recognition/template/template_store.py`（`save/load/list_templates`，版本化）
  - `tests/student_recognition/test_template_versioning.py`（§15.6）
  - `tests/student_recognition/test_template_import_export.py`（§15.7）
  - `tests/student_recognition/fixtures/templates/.gitkeep`
- **验收点**
  1. `save(profile)` 经 `common.atomic_io`（temp+rename）；同 `(template_id, template_version)` 已存在→拒绝（`TEMPLATE_VERSION_CONFLICT`），**旧版不覆盖**。
  2. `load` → `from_dict`；`list_templates(dir)` 返回 `(path, template_id, template_version)`；显式 load 损坏 JSON 必须 fail-closed，list 可返回结构化诊断但不得把损坏模板列为可用。
  3. `test_template_update_increments_version` / `test_template_old_version_not_overwritten` / `test_template_ref_contains_id_and_version`。
  4. `test_template_export_import_roundtrip`（保存→读取→再保存稳定）/ `test_template_import_rejects_unknown_schema_without_adapter` / `test_template_import_preserves_coordinates`。

---

## SRE945-F — Calibrator（Level 1 无头 anchor）+ Level 0 JSON + Level 2 接口预留

- **依赖**：SRE945-B, SRE945-C, SRE945-D
- **产出文件**
  - `app/student_recognition/template_builder/__init__.py`
  - `app/student_recognition/template_builder/calibrator.py`（Level 1：blank reference + anchors + grid + identity + question range → Draft → Validator → Profile + report）
  - `app/student_recognition/template_builder/level0_json.py`（Level 0：纯 JSON 模板读写/校验入口）
  - `app/student_recognition/template_builder/level2_interface.py`（Level 2：`VisualCalibrator` Protocol/ABC 接口预留，**无 UI 实现**）
  - `tests/student_recognition/test_template_builder_calibrator.py`（标定提升 + 锚点解析正确性）
- **验收点**
  1. `Calibrator.calibrate_from_synthetic(profile_v1)` → 经 adapter(D) + Validator(B) → `TemplateProfile`，report.status=valid。
  2. `Calibrator.calibrate_from_anchors(canvas, anchors, blocks, identity, question_range)`（调用方显式提供 grid_origin 等锚点）→ 确定性 normalized ROI；锚点非法→`TEMPLATE_CALIBRATION_ANCHOR_INVALID`。不检测 four-corner，不做 page locator 或图像识别。
  3. Level 0：手写/脚本 `template_profile.json` 可直接经 `level0_json` + Validator 成为 Profile。
  4. Level 2：`VisualCalibrator` 仅定义抽象方法（`start_session/define_anchor/draw_roi/commit`），**明确注释"未来阶段实现，本阶段不实现 UI"**，不得 import web/flask。
  5. 全程 ErrorCode，无 freeform；不碰 OMR/Image/Grading/web_app。

---

## SRE945-G — CLI 构建脚本（build_template.py）

- **依赖**：SRE945-E, SRE945-F
- **产出文件**
  - `scripts/student_recognition/build_template.py`（纯 `argparse`+stdlib）
  - `tests/student_recognition/fixtures/templates/template-objective_sheet_v1.json`（CLI 生成、提交）
  - `tests/student_recognition/fixtures/templates/blank-objective_sheet_v1.png`（synthetic 渲染，允许入库，B5）
- **验收点**
  1. `python scripts/student_recognition/build_template.py --template-id objective_sheet_v1` 跑通：用 `SyntheticSheetGenerator` 渲染无标记空白卡 → `Calibrator.calibrate_from_synthetic` → `TemplateStore.save` 到 fixtures。
  2. **不得** import `web_app`/`flask`/`omr`/`image`/`grading_bridge`（G 守卫覆盖）。
  3. 产出 `template_profile.json` 可用 `TemplateProfile.from_dict` 读回且通过 Validator。

---

## SRE945-H — 测试套件 + 依赖守卫（收尾）

- **依赖**：SRE945-A … G
- **产出文件**
  - `tests/student_recognition/test_template_builder_guards.py`（§15.9）
  - `tests/student_recognition/test_template_integration.py`（CLI→标定→落盘→重载 端到端）
  - （前述 A–G 各测试文件已随任务产出；本任务负责集成与守卫收口）
- **验收点（§15.9 守卫）**
  1. `test_template_builder_does_not_import_omr` / `_does_not_import_image` / `_does_not_import_grading` / `_does_not_import_web_app`：扫描 `app/student_recognition/template/**` 与 `template_builder/**` 无禁止 import（**允许** import `synthetic`/`errors`/`common`/`state`）。
  2. `test_template_builder_has_no_pil_opencv_numpy_dependency`：源码不含 `import PIL`/`cv2`/`numpy`（B4 守卫）。
  3. 全仓 `unittest discover -s tests/student_recognition`（或 `run_tests.py`）在 123 现有测试基础上**新增全绿、无回退**；SRE121 测试仍 pass。

---

## 测试落地归属一览（对应 §15 / SRE945_TEST_PLAN.md）

| §15 类别 | 测试文件 | 归属任务 |
|----------|----------|----------|
| 15.1 Schema | test_template_profile_schema.py | A |
| 15.2 ROI | test_template_roi.py | A/B |
| 15.3 题目/选项 | test_template_questions_options.py | C |
| 15.4 身份 | test_template_identity.py | C |
| 15.5 Draft/Profile | test_template_draft_profile.py | B |
| 15.6 版本化 | test_template_versioning.py | E |
| 15.7 Import/Export | test_template_import_export.py | E |
| 15.8 Synthetic 兼容 | test_template_synthetic_compat.py | D |
| 15.9 Guard | test_template_builder_guards.py | H |
| 校验项全集 | test_template_validator.py | B |
| 标定/展开 | test_template_builder_calibrator.py | F |
| 端到端 | test_template_integration.py | H |

---

## 已冻结实现决策

`schema_version="2.0"`；显式 anchor 的无头 L1；不做 four-corner 检测；guard 新建独立文件；fixture 使用 `tests/student_recognition/fixtures/templates/`；非连续题号和多列仅预留且首版 fail-closed；复用现有 ErrorCode，缺口才连同 catalog 一起新增。工程师不得自行改变这些协议决策。
