# 防直连批改规则（NO_DIRECT_GRADING_RULES）

> 本文件是 `SRE_GLOBAL_CONSTITUTION.md` §1(B1/B2/B3)、§2、§3(F1–F7)、§10 的操作化细则。
> 任何实现、测试、代码评审都必须遵守以下规则。**识别草稿绝不直连正式批改。**

---

## 1. 四层模型不可混淆

必须严格区分以下四个独立对象（宪法 §2）：

| 层 | 对象 | 职责 | 是否可产出成绩 |
|----|------|------|----------------|
| 采集层 | `CaptureJob` | 接收 / 校验 / 归一化原始图并落盘 | 否（只存图） |
| 识别草稿层 | `RecognitionDraft` | 运行 OMR / 身份候选，产出候选 + review_items | 否（仅候选） |
| 教师确认层 | `TeacherConfirmedSubmission` | 教师确认后的草稿（过闸门一） | 否（过桥前） |
| 正式批改层 | `OfficialGradingInput` | 由 Grading Bridge 生成（过闸门二） | **是（唯一正式来源）** |

- `CaptureJob ≠ RecognitionDraft ≠ TeacherConfirmedSubmission ≠ OfficialGradingInput`。
- 四层对象不得复用同一实例；同一字段不得同时承担两个层级的语义。
- 下层可向上提供数据，上层不得反向改写下层原始证据。

---

## 2. 识别草稿绝不自动变正式成绩

2.1 `RecognitionDraft` 永远是候选，**不是成绩**。
2.2 禁止以下行为（硬违规）：
- `RecognitionDraft` 直接写入 `submissions.csv`；
- `RecognitionDraft` 直接生成 official report；
- 跳过教师确认，将草稿内容当作正式成绩返回给前端 / UI；
- 用 `provisional_graded`（试算）伪装 `official_graded`（正式）。

---

## 3. 教师确认 + 双闸门（必经路径）

草稿进入正式批改的**唯一合法路径**：

```
RecognitionDraft
  → [闸门一: RecognitionDraftGate]
     条件：无 blocking_errors + 无 unresolved review_items + 身份已确认
  → TeacherConfirmedSubmission
  → [闸门二: GradingBridgeGate / ExamOfficialReportGate]
     条件：草稿均已确认 + 身份已确认 + 无 blocking + 无 unresolved review
           + 考试无重复/缺失学生 + 答案密钥已 accepted
  → OfficialGradingInput → official report
```

3.1 缺少任一闸门，禁止生成 official report。
3.2 教师修改身份 / review 必须写 audit log，且不得覆盖原始识别结果。

---

## 4. 禁止的状态跳转（对应宪法 §3 F1–F7）

- **blocked**（`draft_blocked`）不可直跳 `grading_ready`；
- **needs_review** 不可绕过 `teacher_confirmed` 直达 `grading_ready` / `official_graded`；
- 禁止任何状态**直接跳** `official_graded`；
- worker / pipeline 不得一次改多个状态（每次只能单步 `transition()`）；
- `draft_created` / `draft_clean` 不得直接到 `official_report_generated`。

---

## 5. 静态 / 运行期守护（guard）

下列 guard 测试（见 `tests/student_recognition/test_sre_global_guards.py`）持续守护上述规则：

- G1：`app/student_recognition/**` 不得 import `app.workflow`；
- G2：不得 import `objective_grader`；
- G3：源码不得含 `grade_all`；
- G4：不得写 `submissions.csv`；
- G5：不得写 `data/reports`；
- G6：宪法与本文档明确区分 CaptureJob / RecognitionDraft / TeacherConfirmedSubmission / OfficialGradingInput 四层。

任何 guard 失败即判定防直连批改被破坏，必须立即修复并披露。

---

> 本文档与 `SRE_GLOBAL_CONSTITUTION.md` 冲突时，以宪法为准。
