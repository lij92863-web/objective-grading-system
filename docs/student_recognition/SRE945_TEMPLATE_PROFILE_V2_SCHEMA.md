# SRE945 TemplateProfile v2 Schema 规范

> 本文件定义 SRE945 的**正式模板协议**（TemplateProfile v2）。它是后续 OMR(SRE341) / Image Norm(SRE221) / Identity / Review / Grading Bridge 的**唯一坐标基座**。
> 宪法硬边界：B4 零新依赖、B5 真实图不进 git、B6 错误码枚举化、B10/§13 依赖方向。本 schema 不引入任何运行时依赖。

---

## 1. 设计原则

1. **主坐标为 normalized（0–1，origin=top_left，unit=ratio）**。像素仅在运行时由 `runtime_x = normalized_x * runtime_width` 转换（见 `SRE945_TEMPLATE_BUILDER_DESIGN.md` §4）。
2. **Anchor + Grid 驱动**，禁止孤立硬编码每个题坐标（见 §5）。
3. **Draft → Validator → Profile** 三段式，非法模板 fail-closed（见 `SRE945_TEMPLATE_BUILDER_DESIGN.md` §6/§7）。
4. **版本化**：`template_id` + `template_version`，旧版本不可覆盖（见 §8）。
5. **向后兼容 SRE121**：提供 v1→v2 adapter，不破 123 测试、不改写 synthetic fixtures（见 §9）。
6. **冻结 OMR 接口**：`get_option_cells / get_identity_roi / get_blank_roi`，OMR 不得自行解析 JSON 或硬编码坐标（见 `SRE945_TEMPLATE_BUILDER_DESIGN.md` §10）。

---

## 2. 完整 JSON 示例（v2，以 synthetic 提升为蓝本）

```json
{
  "schema_version": "2.0",
  "template_id": "objective_sheet_v1",
  "template_name": "高一数学客观题答题卡模板",
  "template_version": 1,
  "created_at": "2026-07-10T10:00:00",
  "updated_at": "2026-07-10T10:00:00",
  "coordinate_system": {
    "type": "normalized",
    "origin": "top_left",
    "unit": "ratio",
    "x_range": [0.0, 1.0],
    "y_range": [0.0, 1.0]
  },
  "reference_canvas": {
    "width": 240,
    "height": 360,
    "source": "synthetic:synthetic-v1"
  },
  "pages": [
    {
      "template_page_id": "page_1",
      "page_no": 1,
      "anchors": [
        {
          "anchor_id": "choice_block_top_left",
          "x": 0.15,
          "y": 0.1333,
          "description": "选择题区域左上角"
        }
      ],
      "identity": {
        "student_id_roi": { "x": 0.0833, "y": 0.0333, "w": 0.8333, "h": 0.0667 },
        "name_roi":       { "x": 0.0833, "y": 0.0333, "w": 0.8333, "h": 0.0667 },
        "combined_identity_roi": { "x": 0.0833, "y": 0.0333, "w": 0.8333, "h": 0.0667 }
      },
      "question_blocks": [
        {
          "block_id": "choice_block_1",
          "question_type": "single_choice",
          "question_range": [1, 12],
          "options": ["A", "B", "C", "D"],
          "anchor_id": "choice_block_top_left",
          "layout": {
            "row_gap": 0.0722,
            "option_gap": 0.1833,
            "cell_w": 0.1833,
            "cell_h": 0.0722
          },
          "blank_roi": { "dx": 0.0, "dy": 0.09, "w": 0.1833, "h": 0.03 }
        }
      ],
      "blank_rois": []
    }
  ]
}
```

> `created_at`/`updated_at` 使用带时区的 ISO 8601 UTC；canonical export 固定一种表示。import/export 不得擅自刷新时间戳。

---

## 3. 字段逐条解释

### 3.1 顶层字段

| 字段 | 类型 | 必填 | 可空 | 消费者 | 说明 |
|------|------|------|------|--------|------|
| `schema_version` | `str` | ✅ | 否 | Validator/Store | v2 固定 `"2.0"`；v1(int 1) 由 adapter 升级。缺失/不符→`TEMPLATE_VERSION_MISSING`/`TEMPLATE_VERSION_MISMATCH`。 |
| `template_id` | `str` | ✅ | 否 | 全部下游 | 稳定标识（如 `objective_sheet_v1`）。缺失→`TEMPLATE_MISSING`。 |
| `template_name` | `str` | 否 | 可 | 文档/UI | 人类可读名，不参与校验。 |
| `template_version` | `int` | ✅ | 否 | Store/版本化 | ≥1；修改模板必须 +1，旧版不可覆盖。缺失→`TEMPLATE_VERSION_MISSING`。 |
| `created_at` / `updated_at` | `str`(ISO8601 UTC) | ✅ | 否 | 审计 | Profile 必填；Draft 可缺，由 finalize 一次性补齐。读取和导出不得刷新。 |
| `coordinate_system` | `object` | ✅ | 否 | 全部 | 必须 `type=normalized, origin=top_left, unit=ratio`；否则→`TEMPLATE_COORDINATE_SYSTEM_INVALID`。 |
| `reference_canvas` | `object` | ✅ | 否 | Adapter/ImageNorm | `{width,height}` 参考画布（synthetic 或标定图尺寸）；`source` 为 `"synthetic:<id>"` 或相对路径（**不得为真实学生图**，B5）。 |
| `pages` | `array` | ✅ | 否（但须≥1） | 全部 | 至少 1 页；缺失/空→`TEMPLATE_PAGE_MISSING`；`template_page_id`/`page_no` 重复→对应重复码。 |

### 3.2 `coordinate_system`

| 子字段 | 取值 | 说明 |
|--------|------|------|
| `type` | `"normalized"` | 唯一合法值；其它→`TEMPLATE_COORDINATE_SYSTEM_INVALID`。 |
| `origin` | `"top_left"` | 原点左上，x 右、y 下。 |
| `unit` | `"ratio"` | 单位为比例（非像素、非百分比）。 |
| `x_range` / `y_range` | `[0.0, 1.0]` | 归一化有效区间；ROI 越界→`TEMPLATE_ROI_OUT_OF_BOUNDS`。 |

### 3.3 `pages[]` 子字段

| 子字段 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `template_page_id` | `str` | ✅ | 页唯一 ID；重复→`TEMPLATE_DUPLICATE_PAGE_ID`。 |
| `page_no` | `int` | ✅ | 页序号（1-based）；重复→`TEMPLATE_DUPLICATE_PAGE_NO`。 |
| `anchors` | `array` | ✅（可为空数组） | 锚点定义（见 §5.1）。 |
| `identity` | `object` | ✅ | 至少含 `student_id_roi` / `name_roi` / `combined_identity_roi` 之一；全缺→`TEMPLATE_IDENTITY_ROI_MISSING`。 |
| `question_blocks` | `array` | ✅（可为空数组） | 选择题块（见 §5.2）；空数组且模板声明含题→`TEMPLATE_QUESTION_BLOCK_EMPTY`。 |
| `blank_rois` | `array` | ✅（可为空） | 独立空白 ROI（如填空题区）；通常随 question_block 展开。 |

### 3.4 `identity` 子字段（均 normalized ROI `{x,y,w,h}`，可空但至少 1 个存在）

| 子字段 | 说明 |
|--------|------|
| `student_id_roi` | 学号区；越界→`TEMPLATE_ROI_OUT_OF_BOUNDS`。 |
| `name_roi` | 姓名区。 |
| `combined_identity_roi` | 合并身份区（学号+姓名）。`student_id_roi` 与 `name_roi` 可分开或合并，但**至少存在一个**身份 ROI。 |

### 3.5 ROI 矩形统一形状

任意 ROI（`identity.*`、`question_blocks[].blank_roi`、展开后的 OptionCell）均为：
```json
{ "x": 0.15, "y": 0.1333, "w": 0.1833, "h": 0.0722 }
```
约束（Validator 全检）：
- `x,y,w,h` 必须为有限数（非 `null`/非 `NaN`）→ 否则 `TEMPLATE_ROI_INVALID`；
- `w > 0` 且 `h > 0`（≤0→`TEMPLATE_ROI_INVALID`）；
- 归一化下 `0.0 ≤ x` 且 `x + w ≤ 1.0`（`y` 同理）→ 否则 `TEMPLATE_ROI_OUT_OF_BOUNDS`；
- 重叠过量（IoU 超过阈值）→ `TEMPLATE_ROI_OVERLAP_WARNING`（warning，不阻断）。

首版阈值冻结为 `IoU > 0.50`。同一 identity 组中 combined ROI 与子 ROI 的预期包含关系、以及显式父/子 ROI 不参与此 warning；其它 option cell/blank ROI 对参与检查。

---

## 4. Coordinate System（三坐标，强制区分）

| 坐标 | 定义 | 存储位置 | 转换 |
|------|------|----------|------|
| **A. Reference Canvas** | synthetic/标定参考画布（如 240×360） | `reference_canvas.{width,height}` | —— |
| **B. Normalized** | 正式坐标，x/y/w/h ∈ [0,1]，origin=top_left | **TemplateProfile 落盘坐标** | —— |
| **C. Runtime Pixel** | 运行时实际归一化图的像素坐标 | OMR/ImageNorm 运行时 | `runtime_x = norm_x * runtime_w`；`runtime_y = norm_y * runtime_h` |

- TemplateProfile **只存 normalized**；
- ROI cropper 在运行时用 `runtime_w/h` 转换成像素；
- OMR **不允许**自己猜坐标（见 §10 / `SRE945_TEMPLATE_BUILDER_DESIGN.md` §4,§10）。

---

## 5. Anchor + BubbleGrid 设计

### 5.1 Anchor（`pages[].anchors[]`）

```json
{ "anchor_id": "choice_block_top_left", "x": 0.15, "y": 0.1333, "description": "选择题区域左上角" }
```
- 锚点是**相对坐标的唯一真源**；整块区域整体平移只需改锚点，不必逐题改坐标（防屎山）。
- 一个 block 通过 `anchor_id` 引用一个锚点。

### 5.2 QuestionBlock（`pages[].question_blocks[]`）

```json
{
  "block_id": "choice_block_1",
  "question_type": "single_choice",
  "question_range": [1, 12],
  "options": ["A", "B", "C", "D"],
  "anchor_id": "choice_block_top_left",
  "layout": { "row_gap": 0.0722, "option_gap": 0.1833, "cell_w": 0.1833, "cell_h": 0.0722 },
  "blank_roi": { "dx": 0.0, "dy": 0.09, "w": 0.1833, "h": 0.03 }
}
```

### 5.3 展开规则（确定性几何，纯 math）

对 `question_range`（含 [start,end] 连续，或显式整数列表以预留非连续）：
```
for r, q_no in enumerate(question_range):
    cell_y = anchor.y + r * layout.row_gap
    for c, label in enumerate(options):
        cell_x = anchor.x + c * layout.option_gap
        option_cell[q_no][label] = {x: cell_x, y: cell_y, w: layout.cell_w, h: layout.cell_h}
    blank_roi[q_no] = {x: anchor.x + blank_roi.dx,
                       y: anchor.y + r*layout.row_gap + blank_roi.dy,
                       w: blank_roi.w, h: blank_roi.h}
```
- 支持 `single_choice`（options 须含 A/B/C/D，否则 `TEMPLATE_SINGLE_CHOICE_MISSING_OPTIONS`）、`multi_choice`（options 非空，否则 `TEMPLATE_MULTI_CHOICE_MISSING_OPTIONS`）。
- 多列布局：预留 `layout.columns`（本阶段默认 1 列；非连续题号用显式列表预留）。
- 展开后任一 cell 越界→`TEMPLATE_ROI_OUT_OF_BOUNDS`；`question_no` 重复→`TEMPLATE_DUPLICATE_QUESTION_NO`；option label 非法（非字符串/不在 options）→`TEMPLATE_INVALID_OPTION_LABEL`；option cell 缺失→`TEMPLATE_OPTION_CELL_MISSING`。

### 5.4 限制

- 本阶段仅实现**连续区间 + 单/多选 + 单/多列（columns 预留）**；填空题块、非连续区间以 schema 字段预留但不强制实现 UI。
- “预留”不等于静默支持：首版遇非连续列表或 `columns > 1` 必须返回 blocking report，直到扩展实现完成。
- 不允许孤立硬编码单个题坐标；一切 ROI 须由 anchor+grid 推导（fail-closed 校验）。

---

## 6. TemplateDraft vs TemplateProfile（边界）

| 维度 | TemplateDraft | TemplateProfile (v2) |
|------|---------------|----------------------|
| 校验 | 未校验/可不完整 | 已通过 Validator |
| 可编辑 | 是 | 否（不可变产物） |
| 可用于 OMR/SRE221 | **否** | 是 |
| 可进 CaptureJob | **否** | 是（须记 `template_ref`） |
| 字段 | 同 v2 结构但允许缺失 | 同 v2 且全必填齐全 |
| 状态 | `draft` | `validated`（内部标记） |

- `TemplateDraft.finalize() → TemplateProfile`：经 Validator，invalid 则抛 `TemplateValidationError(report)`（携带 ErrorCode，禁 freeform）。
- 测试必须覆盖：`draft_cannot_be_used_for_recognition` / `valid_draft_can_be_finalized` / `invalid_draft_cannot_finalize`。

---

## 7. TemplateValidator 输出（结构化报告）

```json
{
  "status": "valid",
  "errors": [],
  "warnings": [
    { "code": "TEMPLATE_ROI_OVERLAP_WARNING", "message": "<catalog default>", "path": "pages[0].question_blocks[0]" }
  ]
}
```
- `status`: `"valid"` | `"invalid"`。
- `errors` / `warnings`: 每项 `{code: ErrorCode, message: str, path: str}`。
- **`message` 必须来自错误码目录**（`error_message.message_for(code)`），**不得手写 freeform**（B6 对齐；用户示例中的英文 message 仅为示意，实现时一律用 catalog 中文默认文案）。
- `path` 为 JSON 指针（如 `pages[0].identity`）。
- v2 使用严格字段集合：未知字段、类型错误、未知 schema 均 blocking，不得静默忽略。

### 7.1 Import / Export / Roundtrip

- `export_template(profile) -> JSON` 使用 UTF-8、稳定 key 顺序和固定数字序列化策略；
- `import_template(JSON) -> TemplateProfile` 先识别 schema，再走 v2 validator 或已注册 v1 adapter；
- roundtrip 的规范等价为“反序列化对象逐字段相等，第二次 canonical export 字节相等”；时间戳和坐标不得刷新、舍入或丢失。

---

## 8. 版本化

- `template_id`（逻辑模板）+ `template_version`（≥1，单调递增）。
- **修改模板必须产生新 version，旧 version 不得覆盖**（`TemplateStore.save` 检测到同 `(id, version)` 已存在即拒绝，`TEMPLATE_VERSION_CONFLICT`）。
- `CaptureJob` / `RecognitionDraft` 必须记录 `template_ref`：
```json
{ "template_ref": { "template_id": "objective_sheet_v1", "template_version": 1 } }
```
- 本阶段**不接 CaptureJob**，但 `TemplateRef` 作为数据类在 `template/` 中定义，供 SRE221/SRE341 引用（接口声明）。

---

## 9. Synthetic（SRE121）兼容策略（v1 → v2 adapter）

- **现有 `synthetic/template_profile.py` 不改**，其 pixel 几何（canvas/origin_x/cell_w/identity_roi）继续被 synthetic 生成器与 SRE121 测试使用 → **123 测试不破、fixtures 不重写**。
- 新增 **compatibility 层**（`template/compatibility.py`）：`adapt_synthetic_to_v2(synthetic_profile: TemplateProfile) -> TemplateProfile`：
  - `normalized_x = pixel_x / canvas.width`；`normalized_y = pixel_y / canvas.height`；`w/h` 同理。
  - 由 `bubble_grid.origin_x/origin_y` 推导单一锚点 `choice_block_top_left`；由 `rows/cols/option_labels` 推导一个 `question_block`（question_range `[1, rows]`）。
  - 由 `identity_roi` 推导 `combined_identity_roi`（normalized）。
  - 设 `reference_canvas = synthetic.canvas`，`source = "synthetic:<template_id>"`，`schema_version = "2.0"`。
- v1 reader：保留 `synthetic.TemplateProfile.from_dict`（int schema_version=1）原样；adapter 在 `TemplateProfile.from_dict` 检测到 v1 时自动升级，保证"旧 template_profile.json 能被 SRE945 识别"。
- 兼容测试：`test_synthetic_template_profile_still_valid` / `test_synthetic_fixtures_still_generate` / `test_sre121_tests_still_pass`（CI 守卫）。

---

## 10. 冻结未来 OMR 接口（SRE945 不实现 OMR，只定义契约）

`TemplateProfile`（v2）对外暴露（返回 **normalized ROI**，消费者自行 runtime 转换）：
- `get_option_cells(question_no: int) -> List[OptionCell]` — 该题所有选项的 `{question_no, option_label, roi}`。
- `get_identity_roi() -> Dict` — 优先 `combined_identity_roi`，否则 `student_id_roi ∪ name_roi`。
- `get_blank_roi(question_no: int) -> Dict` — 该题空白/书写区 ROI。
- 便利：`get_all_option_cells() -> List[OptionCell]`、`get_page_anchors(page_no)`。

**OMR 禁止**：自己解析 JSON、硬编码模板路径/坐标、自行维护 question layout、猜坐标。Template module 是 ROI 唯一来源；OMR 是消费者，不是模板解释器（SRE341 须加反向测试守护）。

---

## 11. Template ErrorCode 冻结表

下列枚举在当前 `error_codes.py` 中已存在，实施时优先复用并核对 catalog；只有出现确切语义缺口时才允许同步新增枚举和 catalog 条目。

| ErrorCode | 用途 | 严重度 |
|-----------|------|--------|
| `TEMPLATE_COORDINATE_SYSTEM_INVALID` | coordinate_system 非法 | blocking |
| `TEMPLATE_ROI_INVALID` | ROI NaN/null/宽高≤0 | blocking |
| `TEMPLATE_DUPLICATE_QUESTION_NO` | 题号重复 | blocking |
| `TEMPLATE_INVALID_OPTION_LABEL` | 选项标签非法 | blocking |
| `TEMPLATE_SINGLE_CHOICE_MISSING_OPTIONS` | 单选缺 A/B/C/D | blocking |
| `TEMPLATE_MULTI_CHOICE_MISSING_OPTIONS` | 多选缺 options | blocking |
| `TEMPLATE_QUESTION_BLOCK_EMPTY` | 题块为空 | blocking |
| `TEMPLATE_ROI_OVERLAP_WARNING` | ROI 重叠过量 | warning |
| `TEMPLATE_DUPLICATE_PAGE_ID` | 页 ID 重复 | blocking |
| `TEMPLATE_DUPLICATE_PAGE_NO` | 页号重复 | blocking |
| `TEMPLATE_CALIBRATION_ANCHOR_INVALID` | 标定锚点非法 | blocking |
| `TEMPLATE_VERSION_CONFLICT` | 同版本覆盖被拒 | blocking |
| `TEMPLATE_DRAFT_NOT_FINALIZED` | 草稿未校验即被当 Profile 用 | blocking |

> 均追加到 `error_codes.py` + `error_catalog.py`（category=template）；`error_policy.py`/`error_message.py` 经 catalog 自动驱动，无需改动。
