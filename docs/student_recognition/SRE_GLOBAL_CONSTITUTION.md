# SRE 全局宪法（SRE_GLOBAL_CONSTITUTION）

> 文件定位：学生识别引擎（Student Recognition Engine，SRE）的最高约束文件。
> 所有阶段（SRE000、SRE001–120、SRE121–220、SRE221–340、…、SRE-FINAL-CODE-AUDIT）的实现、测试、文档**必须**遵守本宪法。
> 本文件与 `NO_DIRECT_GRADING_RULES.md` 互为引用；与 `SRE_FINAL_CODE_AUDIT_SPEC.md` 构成「开发约束 + 审计约束」双闭环。
> 任何代码、测试、文档若与本宪法冲突，以本宪法为准；冲突须记录并在审计阶段披露，不得擅自绕过。

---

## §0 序言与适用范围

0.1 本宪法约束的目录范围严格限定为：
- `app/student_recognition/**`（识别引擎全部业务代码）
- `tests/student_recognition/**`（识别引擎全部测试）
- `scripts/student_recognition/**`（识别引擎全部脚本）
- `docs/student_recognition/**`（识别引擎全部文档）

0.2 本宪法**不**修改、不依赖、不重写以下既有路径（除非在 SRE-FINAL-CODE-AUDIT 阶段发现阻断性问题并书面披露）：
`app/workflow.py`、`objective_grader.py`、`app/domain/grading/**`、`app/answer_extraction/**`、`requirements.txt`、`package.json`、`package-lock.json`、`.env`。

0.3 本宪法的效力高于任何单次 Dispatch、任何阶段报告、任何临时代码决策。修复冲突时优先选择「最稳方案」，禁止为赶进度放松下述硬边界。

0.4 宪法条文分为：§1–§18 全局宪法正文、§19 五个产品化补丁层总览、§20 调整后执行顺序、§21 SRE-FINAL-CODE-AUDIT 独立终段。

---

## §1 十条不可破坏硬边界（CORE BOUNDARIES）

以下十条为**不可破坏硬边界**。任何实现违反任一条，即判定为「不合格」，必须在进入下一阶段前修复。

**B1 四层数据模型严格分离**
`CaptureJob` / `RecognitionDraft` / `TeacherConfirmedSubmission` / `OfficialGradingInput` 四层对象在内存、磁盘、API 中必须严格分离，禁止跨层复用同一对象、禁止同一字段同时承担两个层级的语义。详见 §2。

**B2 识别草稿绝不自动变成正式成绩**
`RecognitionDraft` 是候选，不是成绩。任何代码路径都不得在未经教师确认 + 双闸门的情况下，将草稿内容写入正式成绩（`OfficialGradingInput` / 官方报告）。

**B3 教师确认 + 双闸门**
草稿进入正式批改前，必须依次通过：
- 闸门一：`RecognitionDraftGate`（草稿无 blocking、无未解决 review、身份已确认）
- 闸门二：`GradingBridgeGate`（`TeacherConfirmedSubmission` → `ExamOfficialReportGate`）
缺少任一闸门，禁止生成 official report。

**B4 零新依赖**
本项目不得新增任何 pip / requirements / package.json 依赖。所有算法使用标准库 + 已存在的依赖实现。新增第三方库视为违规。

**B5 真实学生图片不进 git**
真实课堂拍摄的学生答题卡图片（含 original.jpg 及其衍生物）不得纳入版本控制；`.gitignore` 已忽略 `data/captures/` 等目录，必须遵守，不得新增白名单放行真实图片。

**B6 错误码与原因码枚举化（禁止 freeform）**
所有 `blocking_errors` 条目、所有 `review_items.reason_code` 只能使用 `ErrorCode` 枚举（`app/student_recognition/errors/error_codes.py`）。**严禁**自由字符串（如 `blocking_errors.append("识别失败")` 或 `review_items.append({"reason": "不确定"})`）。详见 §10、§18 与 SRE-FINAL-CODE-AUDIT §10。

**B7 设备边界：仅浏览器摄像头**
仅允许浏览器 `getUserMedia()` / `enumerateDevices()` 采集。禁止 USB 手机直连、禁止 ADB、禁止 iOS 原生摄像头调用、禁止任何需要安装驱动的硬件通道。详见 §5。

**B8 保守 OMR**
OMR 阈值集中在 `omr_policy.py`；仅「强涂」可成为自动候选（accepted）；「弱涂 / 半涂 / 多涂 / 擦除」一律进入 `review`，**绝不**自动 accepted。详见 §7。

**B9 严格身份**
身份缺失 / 冲突 / 重复 → `blocked`；`student_id` 优先；遵守「1李明」（学号+姓名）契约。仅姓名不得自动 confirmed；身份冲突不得放行。详见 §8。

**B10 依赖方向：底层不依赖上层**
`app/student_recognition/**` 不得 import `app.workflow` / `objective_grader` / `web_app`。底层模块（common/errors/state/capture/image/template/omr/identity）不得依赖上层（drafts/review/grading_bridge/pipeline/api）。详见 §13。

---

## §2 四层模型精确定义（CAPTURE / DRAFT / CONFIRMED / OFFICIAL）

2.1 **CaptureJob（采集层）**：只负责接收、校验、归一化原始图像并落盘。它**只存图、不识别、不批改**。产出：`original.jpg`、`original.sha256`、`manifest.json`、`normalized/`、`crops/`。
2.2 **RecognitionDraft（识别草稿层）**：消费 CaptureJob 的产物，运行 OMR / 身份候选，产出候选答案与 review_items。它是**候选，不是成绩**，不得写入 `submissions.csv`、不得生成 official report。
2.3 **TeacherConfirmedSubmission（教师确认层）**：教师确认后的草稿。它是通过 `RecognitionDraftGate` 的单一来源，成为 Grading Bridge 的唯一合法输入。
2.4 **OfficialGradingInput（正式批改层）**：由 `GradingBridgeGate` 从已确认提交生成，进入正式评分与 official report。**只有这一层**允许产出正式成绩。
2.5 四层关系单向向下引用：Official ← Confirmed ← Draft ← Capture。反向引用（上层 import 下层允许；下层 import 上层禁止）见 §13。
2.6 任何 API / 文档 / UI 文案必须区分这四层的状态词：识别草稿只写「识别草稿已生成，等待确认」，禁止写「成绩已生成」（详见 SRE-FINAL-CODE-AUDIT §14）。

---

## §3 扩展状态机（~30 状态 + 合法/禁止跳转）

3.1 全部状态来自 `app/student_recognition/state_model.py`（SRE001–120 阶段落地），禁止散落字符串状态（`"done" / "ok" / "finished" / "recognised"` 一律非法）。
3.2 状态全集（共 30 个），分四层：

采集层（CaptureJob）：
- `capture_created`
- `image_uploaded`
- `image_validated`
- `image_quality_failed`
- `page_located`
- `page_locate_failed`
- `normalized`
- `crops_generated`

识别层（RecognitionDraft）：
- `recognition_in_progress`
- `recognition_partial`
- `draft_created`
- `draft_clean`（无 blocking、无 review）
- `draft_has_review_items`（存在 review_items）
- `draft_blocked`（存在 blocking_errors）

确认层（TeacherConfirmedSubmission）：
- `needs_review`（有待处理 review）
- `teacher_reviewing`
- `teacher_confirmed`
- `teacher_overridden`
- `teacher_rejected`

批改层（Grading Bridge / Official）：
- `grading_ready`
- `grading_in_progress`
- `grading_completed`（provisional 试算）
- `provisional_graded`
- `exam_official_report_pending`
- `official_report_generated`
- `official_graded`

聚合与生命周期：
- `bundle_assembled`
- `bundle_conflict`
- `cancelled`
- `archived`

3.3 **合法跳转（示例）**：
- `capture_created → image_uploaded → image_validated → page_located → normalized → crops_generated → recognition_in_progress → draft_created`
- `draft_created → draft_clean | draft_has_review_items | draft_blocked`
- `draft_has_review_items → needs_review → teacher_reviewing → teacher_confirmed | teacher_overridden | teacher_rejected`
- `draft_clean → teacher_confirmed`（无 review 仍需教师确认闸门）
- `teacher_confirmed → grading_ready → grading_in_progress → grading_completed → provisional_graded → exam_official_report_pending → official_report_generated → official_graded`
- `draft_blocked → cancelled | archived`
- 任意状态 → `cancelled` / `archived`（终态）

3.4 **禁止跳转（HARD FORBIDDEN）**：
- **F1**：`draft_blocked`（blocked）**不可直跳** `grading_ready`。
- **F2**：`needs_review` **不可绕过** `teacher_confirmed` 直达 `grading_ready` 或 `official_graded`。
- **F3**：**禁止任何状态直接跳** `official_graded`（必须经由 `grading_ready → … → official_graded` 完整链路）。
- **F4**：`teacher_rejected` 不得跳 `grading_ready`，须回到 `needs_review` 或 `cancelled`。
- **F5**：worker / pipeline **不得一次改多个状态**；每次状态变更只能通过 `state_model.transition()` 单步推进，并写事件到 `events.jsonl`。
- **F6**：`draft_created` / `draft_clean` 不得直接到 `official_report_generated`（缺确认闸门）。
- **F7**：`provisional_graded` 不得伪装为 `official_graded`；二者状态词严格区分。
3.5 状态机必须提供 `is_legal_transition(from, to)` 与 `transition(job, to, actor)`；非法跳转抛 `IllegalStateTransitionError`。测试必须覆盖全部合法 & 非法跳转（见 SRE-FINAL-CODE-AUDIT §9）。

---

## §4 固定持久化树（PERSISTENCE TREE）

4.1 每个 CaptureJob 落盘于固定路径：
```
data/captures/jobs/<job_id>/
  original.jpg            # 原始采集图（不进 git）
  original.sha256         # 原始图 sha256（去重）
  manifest.json           # 元数据（禁止内嵌 base64 图像）
  events.jsonl            # 事件溯源日志（每行一条 JSON 事件）
  normalized/             # 透视归一化图
  crops/                  # ROI 裁剪图
  recognition/            # 识别候选与证据
  review/                 # review_items 与教师处理记录
  confirmed/              # TeacherConfirmedSubmission 产物
```
4.2 `manifest.json` 不得包含 base64 图像数据；图像始终以文件路径引用。
4.3 `events.jsonl` 为追加写、不可变；崩溃恢复依赖其重放（见 §6）。
4.4 `<job_id>` 由唯一生成器产出（UUID + 时序前缀），全局唯一。

---

## §5 设备边界（仅浏览器摄像头）

5.1 采集设备仅限浏览器提供的 `navigator.mediaDevices.getUserMedia()` 与 `enumerateDevices()`。
5.2 **明确禁止**：
- USB 手机直连 / MTP / PTP 通道；
- Android ADB 截图或推流；
- iOS 原生摄像头 / AVFoundation / 任何需原生 SDK 的通道；
- 任何需安装驱动或系统级权限的硬件采集。
5.3 后端只接收浏览器上传的图像字节流（已由 CaptureJob 接收），**不主动连接任何设备**。
5.4 若前端检测到非 `getUserMedia` 来源，后端必须以 `ErrorCode.DEVICE_UNSUPPORTED`（归入 Image/设备类，后续 SRE001–120 落地；本阶段占位于 Image 类别说明）拒绝，且不得进入识别流程。

---

## §6 幂等与崩溃恢复（IDEMPOTENCY / EVENT SOURCING）

6.1 同一原始图像通过 `sha256` 去重：已存在的 `original.sha256` 命中则复用既有 job，不重复建 job。
6.2 全局唯一 `job_id`；并发处理使用 worker 锁（文件锁 / 原子 rename），防止双写。
6.3 所有状态变更、关键决策写入 `events.jsonl`（事件溯源）。进程崩溃后可通过重放 `events.jsonl` 恢复到最近一致状态，不得丢失已确认结果。
6.4 同一 job 的重复提交必须幂等：第二次提交返回既有结果，不产生新副作用。

---

## §7 保守 OMR 原则（CONSERVATIVE OMR）

7.1 OMR 阈值集中在 `omr_policy.py`（SRE001–120 落地），业务函数不得散落魔法阈值。
7.2 仅「强涂」（dark_ratio / center_density / 连通域指标均超过强涂阈值）可成为自动候选（accepted）。
7.3 以下情形**一律进入 review，绝不自动 accepted**：
- 弱涂（低于强涂但高于空白阈值）
- 半涂（覆盖率不足）
- 多涂单选（OMR_MULTI_MARK_SINGLE_CHOICE）
- 擦除痕迹（OMR_ERASURE_DETECTED）
- 边框噪声高 / 低置信度 / 歧义多选
7.4 每个 OMR 候选必须携带 ROI crop 证据（图像路径或 base64-free 特征），不得「只看黑像素最多」或「top_score 最大就判」。
7.5 空白选项不得乱判为已选；无明确强涂则归为「未作答 / review」。

---

## §8 严格身份原则（STRICT IDENTITY）

8.1 `student_id` 优先；身份以「学号+姓名」契约（即「1李明」）为基准。
8.2 以下情形 → `blocked`（blocking_errors）：
- 身份缺失（IDENTITY_MISSING）
- 学号与名单姓名冲突（IDENTITY_CONFLICT）
- 重复身份（IDENTITY_DUPLICATE）
- 学号在名单中找不到（IDENTITY_ROSTER_NOT_FOUND）
8.3 仅姓名、无学号（IDENTITY_NAME_ONLY）→ `review`，**不得自动 confirmed**。
8.4 学号存在但与名单不匹配（IDENTITY_STUDENT_ID_ONLY_UNMATCHED）→ `blocked` / `review`，不得放行进入正式批改。
8.5 教师修改身份必须写 audit log，且不得覆盖原始识别证据。
8.6 同名学生出现两张 confirmed 提交必须阻断（去重约束，见 §9 Bundle）。

---

## §9 正式 Review Queue 模型与枚举（REVIEW QUEUE）

9.1 存在正式的 Review Queue 数据模型（SRE001–120 落地），每个 `ReviewItem` 至少含：
- `reason_code: ErrorCode`（枚举，禁止 freeform）
- `evidence`（图像/指标路径或引用）
- `teacher_resolution`（pending / accepted / overridden / rejected）
- `teacher_note`（教师备注）
- `audit`（处理记录）
9.2 Review Queue 状态枚举：`PENDING / IN_PROGRESS / RESOLVED / ESCALATED`。
9.3 `unresolved review` 不得进入 official report（与 §3 F2、§10 闸门联动）。
9.4 教师处理 review 不得覆盖原始识别结果；覆盖须显式 `teacher_overridden` 并留痕。

---

## §10 双闸门 Grading Bridge（GRADING BRIDGE / DUAL GATES）

10.1 闸门一 `RecognitionDraftGate`：输入 `RecognitionDraft`，仅当
- 无 blocking_errors，且
- 无 unresolved review_items，且
- 身份已确认（teacher_confirmed）
时，输出 `TeacherConfirmedSubmission`。否则拒绝并给出对应 `ErrorCode`（GRADING_* 系列）。
10.2 闸门二 `GradingBridgeGate`（`ExamOfficialReportGate`）：输入 `TeacherConfirmedSubmission` 集合（≥1 份，组成 `SubmissionBundle`），仅当
- 草稿均已确认（GRADING_DRAFT_NOT_CONFIRMED 校验通过）
- 身份均已确认（GRADING_IDENTITY_NOT_CONFIRMED 校验通过）
- 无 blocking errors（GRADING_BLOCKING_ERRORS_EXIST）
- 无未解决 review（GRADING_UNRESOLVED_REVIEW_ITEMS）
- 考试无重复学生（GRADING_EXAM_HAS_DUPLICATE_STUDENT）
- 考试无缺失学生（GRADING_EXAM_HAS_MISSING_STUDENTS）
- 答案密钥已 accepted（GRADING_ANSWER_KEY_NOT_ACCEPTED）
时，生成 `OfficialGradingInput` 并产出 official report。
10.3 **provisional（试算）vs official（正式）严格区分**：
- `provisional_graded` 仅供教师预览，不得标「正式」；
- `official_graded` 才是正式成绩，UI 必须明确标注「正式」。
10.4 Grading Bridge **只收 confirmed，不收 draft**；任何从 draft 直连 official 的路径非法。

---

## §11 OCR/Qwen 兜底原则（OCR / LLM FALLBACK）

11.1 OCR 与 Qwen（多模态大模型）**仅作最后兜底**，且只使用 `FakeClient`（桩实现），不调用真实外部 API。
11.2 兜底产出的候选**永不自动 accepted**；它们只能进入 review，由教师最终判定。
11.3 真实 Qwen / 真实 OCR 默认禁止；若未来需要，必须新增独立阶段、独立审批、独立 guard，不在本阶段启用。
11.4 任何「识别」结果若源自 OCR/Qwen 兜底，必须打标 `source="fallback_fake"`，并在 review 中显式提示。

---

## §12 隐私与 .gitignore（PRIVACY）

12.1 真实学生图片（含 original.jpg 及其 normalized/crops/recognition 衍生图）不进 git；`.gitignore` 已忽略 `data/captures/`、`data/uploads/`、`data/reports/` 等。
12.2 不得新增 `.gitignore` 白名单放行 `data/captures/**` 或任何真实图片目录。
12.3 `manifest.json` 不含 base64 图像；仅存路径与元数据，降低隐私泄露面。
12.4 测试只能用合成 / 桩数据；不得提交任何真实学生图片到仓库。

---

## §13 依赖方向约束（DEPENDENCY DIRECTION）

13.1 允许方向（单向向下）：
`common / errors / state` ← `capture / image / template / omr / identity` ← `drafts / review` ← `grading_bridge` ← `pipeline / api`。
13.2 **禁止依赖（加 guard 测试）**：
- `app/student_recognition/**` 不得 import `app.workflow` / `objective_grader` / `web_app`；
- `omr/**` 不得 import `grading_bridge/**`；
- `capture/**` 不得 import `omr/**`；
- `image/**` 不得 import `grading_bridge/**`；
- `benchmark/**` 不得修改生产数据。
13.3 循环依赖一律禁止；发现即修（重构或小步拆分）。
13.4 底层模块不得反向引用上层模型（如 ConfirmedSubmission 不得 import web_app）。

---

## §14 测试分类（5 类测试 + 10 个 guard 测试）

14.1 **5 类测试**（每核心模块至少覆盖四类：正常 / 失败 / 边界 / 反向安全）：
- 单元（unit）：单函数 / 单类行为；
- 集成（integration）：模块间协作（capture→draft→confirmed）；
- 状态机（state-machine）：合法 & 非法跳转、恢复、retry、cancelled；
- 反向安全（negative-safety）：确认冲突不能进 grade、未确认 draft 不能进 official、多涂进 review 等；
- 审计/guard（audit-guard）：本宪法硬边界的静态/运行期守护。

14.2 **10 个 guard 测试分类**（至少覆盖，本阶段先落地 6 个全局 guard）：
1. 无 `import app.workflow`（在 student_recognition 上下文）；
2. 无 `import objective_grader`；
3. 源码不含 `grade_all`；
4. 无代码写 `submissions.csv`；
5. 无代码写 `data/reports`；
6. 宪法与 NO_DIRECT_GRADING_RULES 明确区分四层模型；
7.（后续）状态全部来自 state_model，无 freeform 状态字符串；
8.（后续）错误码全部来自 error_codes，无 freeform reason 字符串；
9.（后续）OMR 阈值来自 omr_policy，无散落魔法阈值；
10.（后续）manifest 无 base64，无真实图片进 git。
14.3 低价值测试定义（`assertIsNotNone` / `assertTrue` / `assertEqual(status,"ok")` 等）除非同时断言具体答案 / 错误码 / 状态 / evidence / 具体禁止行为未发生，否则不计入有效覆盖（见 SRE-FINAL-CODE-AUDIT §12）。

---

## §15 固定最终报告格式（FINAL REPORT FORMAT）

下列格式为各阶段执行器**必须**使用的汇报骨架（字段顺序固定）。本阶段（SRE000 + SRE1091 部分）汇报即套用此格式（仅覆盖本轮范围）：

```
【<阶段名> 完成】
当前分支：
起始 commit：
最新 commit：
是否 push：否（按主理人要求不 push）
git status --short：

## 1. 总体结论
代码质量等级：
架构状态：
功能落实状态：
是否存在幻觉报告：
是否存在屎山风险：
是否允许进入下一阶段：

## 2. 已创建/修改文件清单
（逐行列绝对路径）

## 3. 测试
unittest discover / student_recognition tests / guard tests / 本论新增 tests：
低价值测试：
缺失测试：

## 4. 安全边界
是否调用真实 API：否
是否写 submissions.csv：否
是否调用 grade_all：否
是否生成 official report：否
是否允许 unconfirmed draft：否
是否保存 base64：否
是否提交真实图片：否

## 5. 遗留 / 待办
- ...
```

---

## §16 十条 STOP 条件（STOP CONDITIONS）

出现以下任一情形，执行器**必须停止**并书面汇报，不得自行绕过：

1. 必须修改 forbidden path（如 `app/workflow.py`、`objective_grader.py`、`requirements.txt`、`.env` 等）才能继续；
2. 发现直连批改绕过且无法在允许路径内修复；
3. 身份冲突可到达 official report；
4. 未确认 draft 可到达 official report；
5. 真实学生图片在 git 中；
6. `run_tests.py` / `unittest discover` 失败且无法在允许路径内修复；
7. 修复需要大规模未计划重写；
8. 出现循环依赖且无法在小步重构内消解；
9. 出现 freeform 错误码 / 原因码且无法枚举化；
10. 文档声称的能力无代码 + 测试 + 运行证据支撑（幻觉）且无法补全。

---

## §17 执行纪律与优先级总则（DISCIPLINE）

17.1 用户休眠期间，执行器自主拍板，选最稳方案，不提问、不等确认。
17.2 冲突优先级：宪法硬边界 > 测试通过 > 功能进度 > 文档美观。
17.3 任何偏离宪法的临时决策，必须写入该阶段报告「遗留 / 待办」，并在 SRE-FINAL-CODE-AUDIT 披露。
17.4 不在本地 push 到远程；仅本地写文件 + 跑测试；用户醒后自行复核。

---

## §18 修订、解释与合规判定（AMENDMENT）

18.1 本宪法由主理人（齐活林）维护；修订须显式版本号与日期。
18.2 合规判定以「可自动化验证」为准：能写 guard 测试的硬边界，必须有对应 guard 测试。
18.3 解释冲突时，以最保守（最不利于「自动放行 / 直连批改」）的解读为准。
18.4 B6（枚举化）与 §10（双闸门）为最高频违规点，审计阶段重点核查。

---

## §19 五个产品化补丁层总览（PRODUCTIZATION PATCH LAYERS）

以下五层为**非可选**的产品化补丁，分别在不同执行段落落地（详见 §20 顺序）：

- **SRE945–SRE980 Template Builder & Calibration**：模板构建与标定工具，使 ROI / 选项格可可视化标定，而非手写 JSON。
- **SRE981–SRE1020 Recognition Benchmark & Metrics**：识别基准与指标计算（真实指标，非仅脚本），量化 OMR / 身份准确率。
- **SRE1021–SRE1060 Multi-page Submission Assembly**：多页提交聚合（Bundle），含缺页 / 重页 / 顺序未知校验。
- **SRE1061–SRE1090 Data Retention & Cleanup**：数据保留与清理（含真实图片生命周期、隐私清理）。
- **SRE1091–SRE1120 Failure Taxonomy & Error Code Standardization**：失败分类与错误码标准化（本阶段先落地 SRE1091 部分的 ErrorCode 骨架）。

---

## §20 调整后执行顺序（EXECUTION ORDER）

逐行列出（注意 SRE1091 部分提前到 SRE001 之前）：

```
SRE000
  → SRE1091 部分（ErrorCode 骨架）
    → SRE001-120
      → SRE121-220
        → SRE945-980
          → SRE221-340
            → SRE341-480
              → SRE981-1020
                → SRE481-560
                  → SRE561-660
                    → SRE661-740
                      → SRE1021-1060
                        → SRE741-840
                          → SRE1061-1090
                            → SRE841-940
                              → SRE-FINAL-CODE-AUDIT
                                → SRE-FINAL-SELF-CHECK
                                  → 真实课堂样本试跑
```

---

## §21 SRE-FINAL-CODE-AUDIT（独立终段）

21.1 SRE-FINAL-CODE-AUDIT 是**独立阶段**，不与任何功能开发阶段混在一起。
21.2 执行位置：完整 SRE 主链实现之后、真实样本测试之前（见 §20）。
21.3 完整协议已落盘 `docs/student_recognition/SRE_FINAL_CODE_AUDIT_SPEC.md`（主理人已建）。执行器到该阶段直接读取此文件作业，按其中 §19–§22 的强制 PASS 闸门与汇报格式执行。
21.4 该阶段目标：确认代码真实实现需求、报告无幻觉、测试非假通过、架构未腐化、无草稿直连正式批改、代码可读可维护可扩展；必要时小范围重构（仅降臃肿 / 解耦）。
21.5 若审计不通过，不允许进入真实课堂样本试跑。

---

> 宪法结束。任何阶段实现须逐条回指本文件对应条文。
