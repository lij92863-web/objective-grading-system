# SRE945–SRE980 Template Builder & Calibration — 系统设计与任务分解（修订版 v2）

> 阶段：SRE945–SRE980｜设计基线：`cd5a9e285dd3d695112aab601a22b29c87438d4b`
> **修订说明**：本版对齐用户补充要求。相对首版关键变更：
> 1. **主坐标由 pixel 改为 normalized（0–1，origin=top_left）**；pixel 仅在运行时由 `runtime = norm * runtime_size` 转换；synthetic 的 pixel 几何经 **adapter** 兼容。
> 2. 首版 `CalibratedTemplate` 概念**升级为 `TemplateProfile` v2**（正式、validator-passed 协议产物）；其冻结 OMR 接口为 `get_option_cells / get_identity_roi / get_blank_roi`。
> 3. 新增 **TemplateDraft / TemplateValidator / 三层 Builder（L0/L1/L2）/ 版本化 / Synthetic v1→v2 adapter**。
> 配套文件：`SRE945_TEMPLATE_PROFILE_V2_SCHEMA.md`、`SRE945_TASK_BREAKDOWN.md`、`SRE945_TEST_PLAN.md`、本文件 mermaid（类图/时序图）。

---

## §1 Scope（范围）

**本阶段做**：模板标定与模板协议层——定义"每题每选项/身份/空白区的坐标从哪来、如何版本化/校验/复用/迁移"。
**本阶段不做**（边界锁死令）：OMR 识别、判断学生答案、图像矫正/page locator、OCR、Qwen、web_app、grading、写 submissions.csv、生成 official report、新增依赖、PIL/OpenCV/numpy、读/提交真实学生图。

---

## §2 Existing Context（现有上下文）

**读取的现有文件**：
- `docs/student_recognition/SRE_GLOBAL_CONSTITUTION.md`
- `docs/student_recognition/NO_DIRECT_GRADING_RULES.md`
- `docs/student_recognition/STUDENT_RECOGNITION_ARCHITECTURE.md`
- `docs/student_recognition/SRE_FINAL_CODE_AUDIT_SPEC.md`
- `app/student_recognition/state_model.py`
- `app/student_recognition/synthetic/template_profile.py`（`TemplateProfile`，pixel 几何，SCHEMA_VERSION=1）
- `app/student_recognition/synthetic/{ground_truth,generator,corpus}.py`
- `app/student_recognition/errors/{error_codes,error_catalog,error_policy,error_message}.py`
- `tests/student_recognition/test_synthetic_*.py`
- `tests/student_recognition/fixtures/synthetic/{template_profile,corpus_manifest}.json`

交接要求中的 `docs/student_recognition/SRE_FINAL_SELF_CHECK_PROTOCOL.md`、仓库根目录 `MEMORY.md`、`2026-07-10.md` 在本次审计时不存在；本设计不臆测其内容。`SRE_PATCH_LAYERS_SPEC.md` 同样不存在。

**现有 synthetic `TemplateProfile` schema 摘要**（pixel，须向后兼容）：
`{schema_version:1, template_id, template_version, canvas:{width,height}, bubble_grid:{rows,cols,option_labels,cell_w,cell_h,origin_x,origin_y,bubble_radius}, questions, identity_roi:{x,y,w,h}}`；方法 `cell_center(q,o)`（pixel）、`option_index(label)`、`to_dict/from_dict`。校验抛 `SyntheticProfileError(ErrorCode)`。

**宪法约束摘要**：B1 四层分离；B4 零新依赖（仅 stdlib + 既有 errors/synthetic/common）；B5 真实图不进 git（空白参考图须 synthetic 渲染）；B6 错误码枚举化；B10/§13 依赖方向（`template/**` 不得 import `drafts/review/grading_bridge/pipeline/api/web_app`，**允许** `synthetic`/`errors`/`common`/`state`）。

---

## §3 TemplateProfile v2 Schema（详见 `SRE945_TEMPLATE_PROFILE_V2_SCHEMA.md`）

要点：
- `schema_version: "2.0"`（字符串，贴合用户示例；v1 int 由 adapter 升级）。
- 顶层：`template_id` / `template_name` / `template_version` / `created_at` / `updated_at` / `coordinate_system` / `reference_canvas` / `pages[]`。
- `coordinate_system`: `{type:"normalized", origin:"top_left", unit:"ratio", x_range:[0,1], y_range:[0,1]}`。
- `reference_canvas`: `{width, height, source}`（source = `"synthetic:<id>"` 或相对路径；**不得真实学生图**）。
- `pages[]`: `{template_page_id, page_no, anchors[], identity{}, question_blocks[], blank_rois[]}`。
- 所有 ROI 为 normalized `{x,y,w,h}`。
- 完整 JSON 示例、字段表、兼容策略见配套 schema 文档。

---

## §4 Coordinate System（三种坐标，强制区分）

| 坐标 | 定义 | 存储 | 转换 |
|------|------|------|------|
| **A. Reference Canvas** | synthetic/标定参考画布（如 240×360） | `reference_canvas.{width,height}` | —— |
| **B. Normalized** | 正式坐标，x/y/w/h∈[0,1]，origin=top_left | **TemplateProfile 落盘坐标** | —— |
| **C. Runtime Pixel** | 运行时实际归一化图像像素 | OMR/ImageNorm 运行时 | `runtime_x = norm_x * runtime_w`；`runtime_y = norm_y * runtime_h` |

- `coordinates.to_runtime_pixels(norm_roi, W, H)` 为唯一 pixel 转换入口（纯 stdlib `math`，无 PIL）。
- 浮点边界校验使用固定 `epsilon=1e-9`；裁剪边界采用 `left=floor(xW), top=floor(yH), right=ceil((x+w)W), bottom=ceil((y+h)H)` 并 clamp 到画布。Profile 查询仍返回 normalized ROI，转换由 template/coordinates 层完成。
- TemplateProfile **只存 normalized**；ROI cropper 运行时转换；**OMR 不允许自己猜坐标**。

---

## §5 Anchor + BubbleGrid 设计

**层级**：Anchor → QuestionBlock → OptionGrid → OptionCell ROI。禁止孤立硬编码每题坐标（整块平移只改 anchor/grid 参数）。
- **Anchor**：`{anchor_id, x, y, description}`（normalized），是相对坐标唯一真源。
- **QuestionBlock**：`{block_id, question_type, question_range, options, anchor_id, layout{row_gap,option_gap,cell_w,cell_h}, blank_roi}`。
- **展开（确定性纯 math）**：对 `question_range`（连续 `[s,e]` 或显式列表预留非连续）：
  ```
  cell_y = anchor.y + r*row_gap
  cell_x = anchor.x + c*option_gap
  option_cell[q][label] = {x:cell_x, y:cell_y, w:cell_w, h:cell_h}
  blank_roi[q] = {x: anchor.x+blank.dx, y: cell_y+blank.dy, w:blank.w, h:blank.h}
  ```
- 支持 `single_choice`（须含 A/B/C/D）、`multi_choice`（options 非空）；多列 `layout.columns` 与**非连续题号仅 schema 预留**，本阶段先实现连续区间。
- 展开越界→`TEMPLATE_ROI_OUT_OF_BOUNDS`；题号重复→`TEMPLATE_DUPLICATE_QUESTION_NO`；label 非法→`TEMPLATE_INVALID_OPTION_LABEL`；cell 缺失→`TEMPLATE_OPTION_CELL_MISSING`。

---

## §6 TemplateDraft vs TemplateProfile

| 维度 | TemplateDraft | TemplateProfile (v2) |
|------|---------------|----------------------|
| 校验 | 未校验/可不完整 | 已通过 Validator |
| 可编辑 | 是 | 否（不可变产物） |
| 可用于 OMR/SRE221 | **否** | 是 |
| 可进 CaptureJob | **否** | 是（须记 `template_ref`） |
| 状态 | `draft` | `validated` |

- `TemplateDraft.finalize() → TemplateProfile`：经 Validator，invalid 抛 `TemplateValidationError(report)`（report 全 `ErrorCode`，禁 freeform）。
- 测试覆盖：`draft_cannot_be_used_for_recognition` / `valid_draft_can_be_finalized` / `invalid_draft_cannot_finalize`。

---

## §7 TemplateValidator

- **流程**：`TemplateDraft → TemplateValidator.validate() → ValidationReport → TemplateProfile`（status=valid 时才 finalize）。
- **校验项（全）**：schema_version/template_id/template_version/page 缺失；coordinate_system 非法；ROI 越界/宽高≤0/NaN/null；identity ROI 缺失；question_no 重复；option cell 缺失；option label 非法；单选缺 A/B/C/D；多选缺 options；题块空；展开越界；ROI 重叠过量（warning）；template_page_id/page_no 重复。
- **输出**：`{status:"valid"|"invalid", errors:[{code,message,path}], warnings:[...]}`。
  - `code` 必为 `ErrorCode`；`message` 一律 `error_message.message_for(code)`（catalog 驱动，**禁 freeform**，对齐 B6）；`path` 为 JSON 指针。
  - v2 对象采用严格字段集合：未知字段一律 blocking，不得静默丢弃。实现前先复用现有 `TEMPLATE_*` 枚举；只有确无对应语义时才同步补齐 `ErrorCode` 与 catalog。
  - `errors`=blocking（fail-closed），`warnings`=不阻断。

---

## §8 Versioning（版本化）

- `template_id`（逻辑模板）+ `template_version`（≥1，单调递增）。
- 修改模板必须产生**新 version**；旧 version **不得覆盖**（`TemplateStore.save` 检测同 `(id,version)` 已存在即拒 `TEMPLATE_VERSION_CONFLICT`）。
- `CaptureJob`/`RecognitionDraft` 须记录 `template_ref`：`{template_id, template_version}`（本阶段不接 CaptureJob，但 `TemplateRef` 数据类在 `template/` 定义，供 SRE221/SRE341 引用——接口声明）。

---

## §9 Synthetic Compatibility（v1→v2 adapter）

- **不改** `synthetic/template_profile.py`，**不重写** synthetic fixtures → SRE121 的 123 测试不破。
- `template/compatibility.py`：`adapt_synthetic_to_v2(synthetic_profile) -> TemplateProfile`：
  - `norm = pixel / canvas`；由 `origin_x/origin_y` 推导单一锚点 `choice_block_top_left`；由 `rows/cols/option_labels` 推导单 `question_block`（range `[1,rows]`）；由 `identity_roi` 推导 `combined_identity_roi`。
  - `reference_canvas = synthetic.canvas`，`source="synthetic:<id>"`，`schema_version="2.0"`。
- `TemplateProfile.from_dict` 遇 v1(int 1) 自动经 adapter 升级 → "旧 template_profile.json 能被 SRE945 识别"。
- 自动升级只接受已知 synthetic v1 形状且 `schema_version == 1`；其它版本或混合形状 fail-closed。v1 reader 继续服务原 generator，适配过程不回写旧 fixture。
- 兼容测试：`test_synthetic_template_profile_still_valid` / `test_synthetic_fixtures_still_generate` / `test_sre121_tests_still_pass`（CI 守卫）。

---

## §10 Future OMR Interface（冻结，OMR 不得自行解释模板）

`TemplateProfile`（v2）对外暴露（返回 **normalized ROI**）：
- `get_option_cells(question_no) -> List[OptionCell]`（`{question_no, option_label, roi}`）
- `get_identity_roi() -> Dict`（优先 combined，否则 student_id∪name）
- `get_blank_roi(question_no) -> Dict`
- 便利：`get_all_option_cells()`、`get_page_anchors(page_no)`

**OMR 禁止**：自己解析 JSON、硬编码模板路径/坐标、自行维护 question layout、猜坐标。Template module 是 ROI 唯一来源；OMR 是消费者，不是模板解释器（SRE341 须加反向测试守护"硬编码 origin/cell_w 即违规"）。

---

## §11 Implementation Task Breakdown（SRE945-A … H，详见 `SRE945_TASK_BREAKDOWN.md`）

- **A** 数据模型+坐标+冻结OMR接口：`template/{__init__,template_profile,coordinates}.py` + schema/roi 测试。
- **B** Draft+Validator+错误码：`template/{template_draft,template_validator}.py` + `errors/{error_codes,error_catalog}.py` + validator/draft 测试。
- **C** Anchor+BubbleGrid 展开：`template/anchor_layout.py` + 题目/选项/身份测试。
- **D** Synthetic v1→v2 adapter：`template/compatibility.py` + 兼容测试。
- **E** TemplateStore 版本化：`template/template_store.py` + 版本化/import-export 测试 + fixtures/.gitkeep。
- **F** Calibrator(L1)+L0 JSON+L2 接口：`template_builder/{__init__,calibrator,level0_json,level2_interface}.py` + 标定测试。
- **G** CLI：`scripts/student_recognition/build_template.py` + 生成 fixture JSON/PNG。
- **H** 测试+守卫收口：`test_template_builder_guards.py` + `test_template_integration.py`，全量 `unittest discover` 绿。

依赖 DAG：A→{B,C,D,E}；{B,C,D}→F；{E,F}→G；A..G→H。

---

## §12 Tests（详见 `SRE945_TEST_PLAN.md`）

覆盖 §15 全部 9 类（Schema/ROI/题目选项/身份/Draft-Profile/版本化/Import-Export/Synthetic兼容/Guard）+ 集成 + 契约测试。每个测试断言具体 `ErrorCode`/坐标值/禁止行为（宪法 §14.3 低价值红线）。

---

## §13 Acceptance Criteria（验收标准，对应 §16）

1. v2 schema 文档完整；2. Draft/Profile 边界明确；3. Validator 拒非法；4. Anchor+Grid 生成 ROI；5. Identity 必存在；6. 版本不覆盖旧版；7. Import/Export/Roundtrip 通过；8. Synthetic v1 兼容、不破 SRE121；9. OMR 接口冻结；10. 无 OMR/Image/Qwen/Grading/web_app 越界；11. 无新依赖；12. 全量 run_tests 通过；13. student_recognition 测试通过。

---

## §14 Risks / Frozen Decisions

1. v2 的 `schema_version` 固定为字符串 `"2.0"`；synthetic v1 保持整数 `1`，仅经 adapter 提升。
2. Level 1 只实现调用方显式提供 anchor/grid/identity 的确定性几何标定，不检测图像内容，也不实现 four-corner/page locator。
3. 非连续题号与多列布局仅冻结 schema 扩展位；首个实现只承诺连续区间与单列，遇未支持布局必须 fail-closed。
4. guard 独立落在 `test_template_builder_guards.py`；模板 fixture 落在 `tests/student_recognition/fixtures/templates/`。
5. Validator 文案由 catalog 解析；`path` 只承载结构位置。
6. 最大风险是 v1 像素几何与 v2 normalized 几何双源漂移。防线是单向 adapter、不可变版本、canonical roundtrip 与逐 cell 等价测试。
7. Level 2 不在 SRE945 实现范围内；当前不得声称支持教师可视化拖拽标定。

---

## 附：类图 / 时序图

- 类图：`SRE945_class_diagram.mermaid`（TemplateProfile v2 / TemplateDraft / TemplateValidator / TemplateStore / AnchorLayout / Compatibility / Calibrator / Level2Interface / Coordinates，及既有 SyntheticProfile/ErrorCode）。
- 时序图：`SRE945_sequence_diagram.mermaid`（CLI→SyntheticSheetGenerator→Calibrator→Draft→Validator→Profile→Store→fixtures，及测试加载校验路径）。
