# SRE945–SRE980 Template Builder & Calibration — 测试计划（Test Plan）

> 对应补充要求 §15（测试清单）、§16（验收标准）。宪法 §14 测试分类：unit / integration / state-machine / negative-safety / audit-guard。
> 本阶段测试目标：证明模板协议不腐化、坐标有统一来源、非法模板 fail-closed、SRE121 兼容不破。

---

## 0. 测试分层与命名约定

- 文件：`tests/student_recognition/test_template_*.py`（模块单测）、`test_template_builder_*.py`（Builder 集成）。
- 函数名直采补充要求 §15 给出的 `test_template_*` 命名（便于审计回溯）。
- 所有 `errors`/`warnings` 断言必须校验 `ErrorCode` 成员（而非字符串匹配），呼应 B6。
- 坐标断言统一在 **normalized** 空间；runtime pixel 仅测转换函数。

---

## 1. Schema 测试（§15.1）— `test_template_profile_schema.py`

| 测试函数 | 断言 |
|----------|------|
| `test_template_profile_requires_schema_version` | 缺 `schema_version` → `TEMPLATE_VERSION_MISSING` |
| `test_template_profile_requires_template_id` | 缺 `template_id` → `TEMPLATE_MISSING` |
| `test_template_profile_requires_template_version` | 缺 `template_version` → `TEMPLATE_VERSION_MISSING` |
| `test_template_profile_rejects_missing_page` | `pages` 缺失/空 → `TEMPLATE_PAGE_MISSING` |
| `test_template_profile_rejects_invalid_coordinate_system` | `coordinate_system.type != "normalized"` 或 `unit != "ratio"` → `TEMPLATE_COORDINATE_SYSTEM_INVALID` |

补充：v1 `schema_version=1`（int）经 `from_dict` 自动走 adapter → 升级为 v2（兼容，不报错）。

---

## 2. ROI 测试（§15.2）— `test_template_roi.py`

| 测试函数 | 断言 |
|----------|------|
| `test_template_rejects_roi_out_of_bounds` | ROI `x+w>1` 或 `y+h>1` 或 `<0` → `TEMPLATE_ROI_OUT_OF_BOUNDS` |
| `test_template_rejects_negative_roi_width` | `w<0` → `TEMPLATE_ROI_INVALID` |
| `test_template_rejects_negative_roi_height` | `h<0` → `TEMPLATE_ROI_INVALID` |
| `test_template_rejects_zero_size_roi` | `w==0` 或 `h==0` → `TEMPLATE_ROI_INVALID` |
| `test_template_rejects_nan_roi` | `x/y/w/h` 为 NaN → `TEMPLATE_ROI_INVALID` |
| `test_template_rejects_null_roi` | ROI 字段为 `null` → `TEMPLATE_ROI_INVALID` |

补充：`coordinates.to_runtime_pixels` 用合成 `runtime_w/h` 验证 `norm*size` 映射（含边界 0/1 不越界）。

---

## 3. 题目 / 选项测试（§15.3）— `test_template_questions_options.py`

| 测试函数 | 断言 |
|----------|------|
| `test_template_rejects_duplicate_question_no` | 同题号出现两次 → `TEMPLATE_DUPLICATE_QUESTION_NO` |
| `test_template_rejects_missing_option_cell` | 某选项 cell 缺失 → `TEMPLATE_OPTION_CELL_MISSING` |
| `test_template_rejects_invalid_option_label` | option label 不在 `options` 或非字符串 → `TEMPLATE_INVALID_OPTION_LABEL` |
| `test_template_expands_choice_grid` | `question_range=[1,10]` + 4 options → 展开 40 个 OptionCell，且 `get_option_cells(q)` 返回 4 个 |
| `test_template_expanded_grid_rois_are_in_bounds` | 展开后所有 cell ROI 均在 [0,1] 内 |

补充：`single_choice` 缺 A/B/C/D → `TEMPLATE_SINGLE_CHOICE_MISSING_OPTIONS`；`multi_choice` 无 options → `TEMPLATE_MULTI_CHOICE_MISSING_OPTIONS`。

---

## 4. 身份区域测试（§15.4）— `test_template_identity.py`

| 测试函数 | 断言 |
|----------|------|
| `test_template_requires_identity_roi` | `identity` 全缺 → `TEMPLATE_IDENTITY_ROI_MISSING` |
| `test_template_accepts_combined_identity_roi` | 仅有 `combined_identity_roi` 即通过；`get_identity_roi()` 返回它 |
| `test_template_rejects_identity_roi_out_of_bounds` | identity ROI 越界 → `TEMPLATE_ROI_OUT_OF_BOUNDS` |

补充：`student_id_roi` 与 `name_roi` 分开时 `get_identity_roi()` 优先返回 combined，否则合并两区。

---

## 5. Draft / Profile 测试（§15.5）— `test_template_draft_profile.py`

| 测试函数 | 断言 |
|----------|------|
| `test_template_draft_cannot_be_used_for_recognition` | `TemplateDraft` 不暴露 `get_option_cells` 等消费接口（或调用即 `TEMPLATE_DRAFT_NOT_FINALIZED`） |
| `test_valid_draft_can_be_finalized_to_profile` | 合法 draft `.finalize()` → `TemplateProfile`，`status=="valid"` |
| `test_invalid_draft_cannot_finalize` | 缺 identity 的 draft `.finalize()` 抛 `TemplateValidationError`，report.status=="invalid" 且含 `TEMPLATE_IDENTITY_ROI_MISSING` |

---

## 6. 版本化测试（§15.6）— `test_template_versioning.py`

| 测试函数 | 断言 |
|----------|------|
| `test_template_update_increments_version` | 修改模板须 `template_version+1` 才能 save |
| `test_template_old_version_not_overwritten` | 同 `(id, version)` 已存在 → `save` 拒绝（`TEMPLATE_VERSION_CONFLICT`） |
| `test_template_ref_contains_id_and_version` | `TemplateRef(id, version)` 序列化含 `template_id`+`template_version` |

---

## 7. Import / Export 测试（§15.7）— `test_template_import_export.py`

| 测试函数 | 断言 |
|----------|------|
| `test_template_export_import_roundtrip` | `export→import→export` 字节/字段稳定 |
| `test_template_import_rejects_unknown_schema_without_adapter` | 未知 `schema_version` 且无 adapter → 拒绝（非静默忽略） |
| `test_template_import_preserves_coordinates` | 往返后 normalized 坐标精度无损（误差 < 1e-9） |

补充：`test_template_import_rejects_unknown_field`（v2 未知字段不得静默忽略）；`test_template_roundtrip_preserves_timestamps`；`test_template_second_canonical_export_is_byte_stable`。

---

## 8. Synthetic 兼容测试（§15.8）— `test_template_synthetic_compat.py`

| 测试函数 | 断言 |
|----------|------|
| `test_synthetic_template_profile_still_valid` | `adapt_synthetic_to_v2(synthetic.TemplateProfile)` 产物过 Validator |
| `test_synthetic_fixtures_still_generate` | `SyntheticSheetGenerator` 仍可渲染 synthetic fixture |
| `test_sre121_tests_still_pass` | 运行既有 SRE121 测试集（123 项）全绿，无回归 |

> 该文件为 CI 守卫：任何破坏 synthetic 兼容的改动在此暴露。

---

## 9. Guard 测试（§15.9）— `test_template_builder_guards.py`

| 测试函数 | 断言 |
|----------|------|
| `test_template_builder_does_not_import_omr` | `template/**`+`template_builder/**` 无 `import ...omr` |
| `test_template_builder_does_not_import_image` | 无 `import ...image` |
| `test_template_builder_does_not_import_grading` | 无 `import ...grading_bridge` |
| `test_template_builder_does_not_import_web_app` | 无 `import web_app` / `flask` |
| `test_template_builder_has_no_pil_opencv_numpy_dependency` | 源码无 `PIL`/`cv2`/`numpy`（B4） |

> 实现方式复用 `test_sre_global_guards.py` 的 AST 扫描手法；**允许** import `synthetic`/`errors`/`common`/`state`（同层/下层叶子）。

补充边界测试：非连续题号和 `columns>1` 在首版返回 blocking report；损坏 JSON 的显式 import/load fail-closed；identity 父子包含不触发重叠 warning，而无关 ROI 的 `IoU>0.50` 触发 `TEMPLATE_ROI_OVERLAP_WARNING`。

---

## 10. 集成测试 — `test_template_integration.py`

- 端到端：CLI(`build_template.py`) → `SyntheticSheetGenerator` 渲染空白卡 → `Calibrator.calibrate_from_synthetic` → `TemplateStore.save` → `TemplateStore.load` → `TemplateProfile.from_dict` → `get_option_cells` 全网格可解析且坐标与 synthetic `cell_center` 映射一致。
- 契约测试（防 OMR 退化）：`get_option_cells/get_identity_roi/get_blank_roi` 返回结构符合 §10 契约；坐标统一 normalized；消费侧不反向依赖标定实现细节。

---

## 11. 验收标准映射（§16 → 测试）

| §16 验收项 | 对应测试 |
|-----------|----------|
| 1. v2 schema 完整 | §1 Schema 测试 + `SRE945_TEMPLATE_PROFILE_V2_SCHEMA.md` |
| 2. Draft/Profile 边界 | §5 |
| 3. Validator 拒非法 | §1–4 + `test_template_validator.py` |
| 4. Anchor+Grid 生成 ROI | §3 |
| 5. Identity 必存在 | §4 |
| 6. 版本不覆盖旧版 | §6 |
| 7. Import/Export/Roundtrip | §7 |
| 8. Synthetic v1 兼容 | §8 |
| 9. OMR 接口冻结 | §10 契约测试 |
| 10. 无越界 | §9 Guard + §1–4 |
| 11. 无新依赖 | §9 `has_no_pil_opencv_numpy` |
| 12. run_tests 全过 | 全量 `unittest discover` |
| 13. student_recognition 测试过 | §8 含 SRE121 回归 |

---

## 12. 低价值测试红线（宪法 §14.3）

- 禁止仅 `assertIsNotNone` / `assertTrue(status)` 之类无具体断言。
- 每个测试必须断言**具体 ErrorCode / 具体坐标值 / 具体禁止行为未发生**。
- 验收/契约类测试须断言"OMR 不自行算坐标"的结构不变量。

## 13. 回归命令与通过门槛

实现阶段依次执行：`python -m unittest discover -s tests/student_recognition`、`python run_tests.py`、synthetic fixture 生成与 truthfulness guard。门槛为零失败、既有 skip 数不无故增加、SRE121 fixtures 不被重写。

交接记录的最近基线是全量 `259 tests OK / skipped=5`、student_recognition `23 tests OK`。文档阶段不得把历史数字冒充本次实测结果；实现报告必须记录当次真实输出。
