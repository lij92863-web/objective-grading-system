# 客观题批改系统产品与架构总规划

## 1. 项目最终目标

客观题批改系统的最终目标不是做一个简单的选择题判分工具，而是形成“题库 + 批改 + 学情分析 + 练习推荐 + 数据回流”的教师工作流闭环。

最终闭环应是：

题库录题 -> 选题 / 组卷 -> 客观题批改 -> 班级学情分析 -> 学生个人诊断 -> 讲评建议 -> 推送对应练习 -> 批改数据回流题库 -> 题库越来越懂学生。

系统分工应清晰：

- 题库系统负责题目录入、题干、选项、答案、解析、图片、知识点、预估难度和组卷。
- 批改系统负责班级、学生、考试、作答、规则判分、统计分析、报告导出。
- 分析系统负责高错题、易错选项、薄弱知识点、学生风险、讲评优先级。
- 后续练习推荐只读取已确认的统计结果和题库数据，不反向污染原始分数。
- 题库回流只更新统计字段，不允许批改系统直接修改题库原题。

第一阶段的核心不是“功能很多”，而是先把稳定闭环做扎实：

班级 -> 学生 -> 考试 -> 标准答案 -> 学生答案 -> 判分 -> 班级报告 -> 学生报告 -> Excel 导出。

## 2. 用户画像与核心痛点

### 不太懂电脑的老师

这类老师不想理解技术名词，不想配置复杂参数，不想面对大量表格。他们关心的是：

- 这次考试整体怎么样；
- 哪几道题错得最多；
- 哪些知识点没掌握好；
- 哪些学生需要重点关注；
- 能不能一键导出成绩表；
- 能不能直接拿去开讲评课。

产品要给他们“快速批改”和“班级简报”：

- 首页用大按钮和少量入口；
- 向导步骤短，每一步只问一个核心问题；
- 报告先给结论，不先堆明细；
- 错误提示必须是老师能看懂的话；
- 技术术语隐藏到更多设置或工程层。

### 会电脑、愿意细看的老师

这类老师希望看到更完整的数据：

- 每题正确率和得分率；
- 每个选项选择人数；
- 每个学生的错题和薄弱知识点；
- 班级知识点掌握情况；
- 分数段、排名、异常答案；
- 详细 Excel；
- 题库回流数据。

产品要给他们“详细分析”和“导出中心”：

- 明细可筛选、可导出；
- 题目、学生、知识点三条分析线并存；
- 支持题库题目 ID，便于长期追踪；
- 数据模型和报告字段要稳定。

## 3. 产品设计原则

1. 教师优先，不是程序员优先。界面说“导入学生答案”，代码可以叫 `submission`；界面说“从题库导入试卷”，代码可以叫 `paperPackage`。
2. 操作步骤越少越好。不会电脑的老师理想流程是：选择班级 -> 新建考试 -> 导入答案 -> 导入学生作答 -> 开始批改 -> 查看报告 -> 导出 Excel。
3. 先给结论，再给细节。报告首页先显示平均分、高错题、薄弱知识点、重点关注学生和讲评顺序。
4. 简洁报告和详尽报告并存。简洁报告服务快速使用，详尽报告服务深入分析。
5. 数据准确性优先于自动化。标准答案、学生作答、OCR 结果、AI 建议都必须有确认边界。
6. AI 不能判分。AI 只能读取确定数据生成讲评建议或练习建议。
7. OCR 不能直写成绩。OCR 只能生成“待确认作答草稿”。
8. 先闭环，再增强。OCR、AI、复杂图表、自动推荐都必须建立在稳定判分和稳定协议之上。

## 4. 推荐产品页面

### 首页：我的批改

目标：老师打开系统后立刻知道下一步该做什么。

主要内容：

- “新建一次批改”大按钮；
- 最近考试列表；
- 最近一次班级报告摘要；
- 常用班级入口；
- “3 步完成批改”的轻提示：导入答案、导入学生作答、开始批改。

推荐按钮：

- 新建一次批改；
- 查看历史报告；
- 管理班级；
- 从题库导入试卷。

避免名称：

- Dashboard；
- Exam Manager；
- Data Center；
- Paper Package Import。

### 新建批改向导

采用分步向导，不要一次展示所有配置。

第 1 步：选择班级  
老师看到：“这次批改哪个班？”  
功能包括选择已有班级、新建班级、导入学生名单。

第 2 步：填写考试信息  
老师看到：“这次考试叫什么？”  
字段包括考试名称、考试日期、总分、题目数量、题型分布。总分和题目数量可选，系统能从答案导入中推断时不要强迫填写。

第 3 步：导入标准答案  
老师看到：“把正确答案放进来。”  
方式包括手动输入、Excel 导入、从题库导入试卷。界面不显示 `paper-package.json`，只显示“从题库导入试卷”。

第 4 步：导入学生答案  
老师看到：“把学生作答放进来。”  
方式包括表格录入、Excel 导入、后续拍照识别。拍照识别结果进入待确认状态。

第 5 步：检查并批改  
系统显示学生人数、题目数量、标准答案完整性、空答、异常选项、未匹配学生、是否可以开始批改。主按钮叫“开始批改”。

第 6 步：查看报告  
批改完成后给出四个清楚入口：看班级情况、看学生情况、导出成绩表、生成讲评建议。

### 班级管理页

页面名称建议：“我的班级”。

功能：

- 班级列表；
- 学生名单；
- 导入名单；
- 添加学生；
- 修改学生；
- 删除学生；
- 查看该班历史考试。

避免显示 `roster`、`student repository` 等术语。

### 报告中心

报告中心分五层，先简后详。

第一层：班级总览  
显示平均分、最高分、最低分、及格人数、优秀人数、错得最多的题、最薄弱知识点、重点关注学生。

第二层：哪些题错得多  
显示每题正确率、平均得分、错误人数、选项分布、是否高错、是否与预估难度偏差大。

第三层：每个学生的问题  
显示学生总分、错题号、薄弱知识点、与班级平均差距、建议补救方向。

第四层：哪些知识点没掌握好  
显示知识点得分率、涉及题目、错误学生数量、薄弱程度排序、推荐讲评顺序。

第五层：这节课怎么讲  
显示必讲题、略讲题、重点知识点、课后跟进学生、针对性练习建议。

### 导出中心

按钮名称：

- 导出成绩表；
- 导出班级报告；
- 导出学生报告；
- 导出讲评建议；
- 导出题库回流数据。

“导出题库回流数据”属于详细或更多设置入口，不要打扰普通老师的主流程。

## 5. 功能命名规范

### 界面推荐名称

- 我的批改；
- 新建一次批改；
- 选择班级；
- 导入学生名单；
- 导入标准答案；
- 从题库导入试卷；
- 导入学生答案；
- 检查数据；
- 开始批改；
- 班级简报；
- 班级详细报告；
- 哪些题错得多；
- 每个学生的问题；
- 哪些知识点没掌握好；
- 讲评建议；
- 导出成绩表；
- 导出题库回流数据。

### 不建议直接出现在普通界面的专业名

- assessment-result；
- paper-package；
- difficultyGap；
- optionDistribution；
- Knowledge Profile；
- Submission Matrix；
- schemaVersion；
- questionId；
- actualDifficulty。

这些可以在代码、协议、开发文档、导出文件中使用，但普通老师主界面要翻译成教师语言。

## 6. 报告体系设计

### 班级简报

用途：给不会电脑的老师快速使用，控制在一个屏幕或一页内。

内容：

1. 本次考试基本情况；
2. 班级平均分、最高分、最低分；
3. 错得最多的 5 道题；
4. 最薄弱的 3 个知识点；
5. 需要关注的学生；
6. 讲评建议顺序；
7. 导出成绩表按钮。

### 班级详细报告

用途：给愿意细看的老师做教学分析。

内容：

1. 每题正确率；
2. 每题得分率；
3. 每个选项选择人数；
4. 分数段分布；
5. 知识点得分率；
6. 高错题分析；
7. 难度偏差分析；
8. 讲评建议；
9. 后续练习建议。

### 学生个人报告

内容：

1. 学生总分；
2. 班级排名；
3. 错题列表；
4. 薄弱知识点；
5. 与班级平均相比；
6. 推荐复习内容；
7. 推荐练习题。

### 讲评建议

内容：

1. 必讲题；
2. 略讲题；
3. 学生普遍问题；
4. 易错选项；
5. 推荐讲评顺序；
6. 课后补救建议。

AI 后续可以辅助生成讲评语言，但必须只读取确定统计数据。

### 题库回流数据

这是高级导出，不作为普通报告主入口。

字段：

- `questionId`；
- `paperId`；
- `questionNumber`；
- `correctRate`；
- `wrongRate`；
- `averageScoreRate`；
- `optionDistribution`；
- `actualDifficulty`；
- `estimatedDifficulty`；
- `difficultyGap`；
- `usageCount`；
- `lastUsedAt`。

## 7. 总体架构原则

1. UI 只负责展示和交互，不负责判分。
2. 判分逻辑必须是纯函数、可测试、可复用。
3. 数据导入和数据校验必须分离。
4. 题库协议和批改内部模型必须分离。
5. AI 只能做建议层，不能进入判分层。
6. OCR 只能进入“待确认作答”，不能直接进入最终成绩。
7. 题库系统和批改系统通过协议连接，不互相硬改内部文件。
8. 所有核心规则必须有测试。
9. 所有跨系统数据必须有 schema / validator。
10. 不把流程、UI、数据、判分、报告写在一个文件里。

## 8. 推荐代码结构

如果未来采用 TypeScript / React，可参考：

```text
src/
  domain/
    grading/
      models.ts
      normalizeAnswer.ts
      scoreSingleChoice.ts
      scoreMultipleChoice.ts
      scoreTrueFalse.ts
      scoreEngine.ts
    exam/
      examModels.ts
      examService.ts
    roster/
      studentModels.ts
      classModels.ts
      rosterService.ts
    report/
      reportModels.ts
      classReportService.ts
      studentReportService.ts
      teachingAdviceService.ts
    question-bank/
      paperPackageModels.ts
      paperPackageMapper.ts
      assessmentResultModels.ts
      assessmentResultMapper.ts
  application/
    use-cases/
      createClass.ts
      importStudents.ts
      createExam.ts
      importAnswerKey.ts
      importStudentAnswers.ts
      gradeExam.ts
      generateReports.ts
      exportExcel.ts
      importPaperPackage.ts
      exportAssessmentResult.ts
  infrastructure/
    storage/
      localRepository.ts
      indexedDbRepository.ts
      fileRepository.ts
    importers/
      excelStudentImporter.ts
      excelAnswerImporter.ts
      paperPackageImporter.ts
    exporters/
      excelExporter.ts
      assessmentResultExporter.ts
    ocr/
      ocrDraftAdapter.ts
    ai/
      teachingAdviceAdapter.ts
  presentation/
    pages/
      HomePage.tsx
      ClassPage.tsx
      NewGradingWizard.tsx
      AnswerKeyPage.tsx
      StudentAnswersPage.tsx
      ReviewPage.tsx
      ReportPage.tsx
    components/
      SimpleReportCard.tsx
      QuestionErrorTable.tsx
      StudentWeaknessTable.tsx
      KnowledgePointChart.tsx
      ExportButtons.tsx
  shared/
    validation/
    errors/
    utils/
    constants/
```

如果继续使用当前 Python + Web，也应保留同样边界：

```text
app/
  domain/
    grading/
    roster/
    exam/
    submission/
    analysis/
    report/
    question_bank/
  application/
    use_cases/
  infrastructure/
    storage/
    importers/
    exporters/
    ocr/
    ai/
  shared/
    validation/
    errors/
web/
  pages_or_templates/
  static/
    api/
    state/
    views/
    wizard/
    camera/
    reports/
```

核心思想：

- `domain` 放纯业务规则；
- `application` 放用例流程；
- `infrastructure` 放文件、Excel、存储、OCR、AI；
- `presentation` / `web` 放页面和交互；
- `shared` 放通用校验、错误、工具、常量。

## 9. 核心模块边界

### grading

职责：

- 标准化答案；
- 单选判分；
- 多选判分；
- 判断题判分；
- 每题得分；
- 学生总分；
- 判分状态，如 correct、wrong、partial、blank、invalid。

不得做：

- UI 渲染；
- Excel 导出；
- AI 分析；
- 题库回流；
- OCR 识别；
- HTML 报告。

### roster

职责：

- 班级；
- 学生；
- 学生编号；
- 导入学生名单；
- 学生数据校验。

不得做判分、报告生成、题库回流。

### exam

职责：

- 考试信息；
- 题目列表；
- 标准答案；
- 分值；
- 题型；
- 知识点；
- 题库题目 ID 映射。

不得做学生作答识别、AI 讲评、UI 展示。

### submission

职责：

- 学生答案；
- 空答；
- 异常答案；
- 待确认答案；
- 作答校验；
- OCR 草稿转人工确认数据。

不得做判分规则、报告生成、题库修改。

### analysis

职责：

- 班级平均分；
- 每题正确率；
- 每题得分率；
- 选项分布；
- 知识点得分率；
- 学生薄弱点；
- 高错题；
- 难度偏差。

不得做原始判分、UI 渲染、文件导入。

### report

职责：

- 班级简报；
- 班级详细报告；
- 学生个人报告；
- 讲评建议；
- 导出数据准备。

不得改分、改答案、直接调用 OCR。

### question-bank

职责：

- 导入 `paper-package.json`；
- 校验题库题目包；
- 将题库题目包映射成考试；
- 导出 `assessment-result.json`；
- 为题库回流准备统计数据。

不得直接修改题库项目源码，不得直接改题库原题，不得绕过 `questionId`，不得只靠 `questionNumber` 关联题目。

### OCR / 拍照

职责：

- 识别学生答案草稿；
- 给出置信度；
- 标记不确定项；
- 进入人工确认流程。

不得直接进入最终成绩，不得直接写入题库，不得自动覆盖老师确认过的数据。

### AI 讲评

职责：

- 根据确定统计数据生成讲评建议；
- 生成补救练习建议；
- 解释错因可能性；
- 帮老师组织语言。

不得判分、改标准答案、改学生答案、改题库原题。

## 10. 题库系统连接协议

### `paper-package.json`

界面名称：从题库导入试卷。  
代码名称：`paper-package.json`。

目标格式：

```json
{
  "schemaVersion": "1.0",
  "paperId": "paper_001",
  "paperName": "函数单元测试",
  "source": "qisi-math-pro",
  "createdAt": "2026-07-08",
  "questions": [
    {
      "questionId": "q_001",
      "questionNumber": 1,
      "type": "single_choice",
      "stem": "题干",
      "options": ["A", "B", "C", "D"],
      "correctAnswer": ["B"],
      "score": 5,
      "knowledgePoints": ["函数单调性"],
      "estimatedDifficulty": 0.65,
      "images": []
    }
  ]
}
```

规则：

- `questionId` 是题库题目唯一 ID。
- `questionNumber` 是本试卷题号。
- 不能用 `questionNumber` 替代 `questionId`。
- `correctAnswer` 必须结构化为数组。
- `knowledgePoints` 允许为空，但字段应保留。
- `estimatedDifficulty` 可选。
- `images` 可选。
- 导入后生成考试标准答案和题目映射，但不能修改题库原数据。
- schema 必须校验，错误要转换成老师能理解的话。

### `assessment-result.json`

界面名称：导出题库回流数据。  
代码名称：`assessment-result.json`。

目标格式：

```json
{
  "schemaVersion": "1.0",
  "examId": "exam_001",
  "paperId": "paper_001",
  "classId": "class_01",
  "generatedAt": "2026-07-08",
  "summary": {
    "studentCount": 50,
    "averageScore": 78.5,
    "maxScore": 98,
    "minScore": 42
  },
  "questionStats": [
    {
      "questionId": "q_001",
      "questionNumber": 1,
      "correctRate": 0.82,
      "wrongRate": 0.18,
      "averageScoreRate": 0.82,
      "optionDistribution": {
        "A": 5,
        "B": 41,
        "C": 3,
        "D": 1,
        "blank": 0
      },
      "actualDifficulty": 0.82,
      "estimatedDifficulty": 0.65,
      "difficultyGap": 0.17
    }
  ]
}
```

规则：

- `assessment-result.json` 不能包含修改题库原题的指令。
- 它只提供统计结果。
- 题库系统读取后只能更新统计字段。
- 批改系统不能直接写题库数据库。
- 必须保留 `paperId` 和 `questionId`。
- `correctRate`、`wrongRate`、`averageScoreRate` 使用 0-1 数值，不使用百分号字符串。
- `optionDistribution.blank` 必须保留。
- `actualDifficulty` 的含义建议与正确率同向：越高表示越容易；如需“难度越高越难”，必须另设字段，不能混用。

## 11. 完整数据流

### 普通批改流

班级名单 -> 考试信息 -> 标准答案 -> 学生作答 -> 答案校验 -> 规则判分 -> 统计分析 -> 报告生成 -> Excel 导出。

关键控制点：

- 标准答案必须确认；
- 学生作答必须校验；
- 异常答案不能静默通过；
- 判分结果必须可追溯到每题；
- 报告只读取判分结果，不反向改分。

### 题库联动流

题库系统 -> 导出 `paper-package.json` -> 批改系统导入试卷 -> 批改系统完成判分 -> 导出 `assessment-result.json` -> 题库系统读取统计数据 -> 更新题目实测表现 -> 后续辅助选题、讲评、练习推荐。

关键控制点：

- 题库和批改系统只通过协议通信；
- 批改系统不直接改题库；
- `paperId`、`questionId`、`questionNumber` 全程保留；
- 回流数据只包含统计，不包含改题指令。

### OCR 流

学生答题卡图片 -> OCR 识别草稿 -> 标记置信度 -> 老师人工确认 -> 进入正式作答 -> 判分。

关键控制点：

- 低置信度高亮；
- 未确认数据不能进入正式成绩；
- OCR 原图和识别草稿要可追溯；
- 老师修改后以老师确认结果为准。

### AI 讲评流

确定的判分结果 -> 统计分析 -> AI 读取统计摘要 -> 生成讲评建议 -> 老师确认 -> 导出报告。

关键控制点：

- AI 不读取未确认作答；
- AI 不改成绩；
- AI 输出必须标记为建议；
- 老师可编辑或忽略 AI 建议。

## 12. 技术路线判断

1. 当前是否建议完全推倒重写：不建议。当前已有可运行 Web 壳、批改流程、报告输出和测试，应该保留可用资产。
2. 是否建议保留现有 Web 产品壳：建议保留，但要逐步拆分前端职责，避免 `app.js` 继续膨胀。
3. 是否建议先迁出判分核心：建议。判分是最稳定、最需要测试保护的核心，应先从 legacy 中迁出。
4. 是否建议先建立数据协议：建议。`paper-package.json` 和 `assessment-result.json` 是题库联动的地基。
5. 是否建议马上接 OCR：不建议。先做待确认数据模型和作答校验，再接 OCR。
6. 是否建议马上接 AI：不建议。先稳定统计摘要和讲评报告结构，再让 AI 读取确定数据。
7. 是否建议马上做复杂图表：不建议。先做简洁报告和稳定表格。
8. 是否建议先做简洁报告：建议。它最贴近普通老师的使用价值。
9. 是否建议再做详细报告：建议，在简洁报告稳定后分层增加。
10. 是否建议优先做题库联动：建议作为核心中期目标，但顺序应在判分核心和数据模型稳定之后。

总体路线：不盲目推倒重写，保留现有可用产品壳；但必须重新规划边界，先稳定核心判分、数据模型、题库协议，再做 UI 美化、报告优化、OCR、AI。

## 13. 分阶段开发路线

### Phase 0：产品与架构冻结

目标：

- 输出本总规划文档；
- 输出数据协议草案；
- 明确模块边界；
- 明确禁止事项。

范围：

- 只写文档和协议草案；
- 不改业务规则；
- 不改 UI。

验收标准：

- 文档说明产品页面、模块边界、数据协议和阶段路线；
- 后续任务必须先读本文档；
- `git status --short` 清楚；
- 说明是否运行测试和测试结果。

### Phase 1：核心判分模块独立

目标：

- 从 legacy 迁出判分核心；
- 单选、多选、判断题规则纯函数化；
- 保持现有行为不变；
- 补充测试。

范围：

- `grading` 模块；
- 判分模型；
- 判分测试。

验收标准：

- 单选、多选、判断题、空答、异常答案均有测试；
- 多选 2 个和 3 个正确答案的部分得分测试完整；
- 原有 `python run_tests.py` 通过；
- 明确说明没有改变既有判分规则，除非任务明确要求。

### Phase 2：数据模型稳定

目标：

- 班级、学生、考试、题目、标准答案、作答、结果模型稳定；
- 减少散乱 dict/list；
- 建立基础 validator。

范围：

- domain models；
- validators；
- mapper。

验收标准：

- 每个核心模型有字段说明；
- 外部输入先校验再进入内部模型；
- 错误消息能给老师看懂；
- 测试覆盖模型校验。

### Phase 3：基础批改闭环产品化

目标：

- 新建批改向导；
- 导入学生；
- 导入答案；
- 导入学生作答；
- 检查异常；
- 开始批改；
- 班级简报；
- Excel 导出。

范围：

- 现有 Web 壳；
- 应用用例；
- 报告基础输出。

验收标准：

- 一个不会电脑的老师能按向导完成一次批改；
- 所有异常可读；
- 可导出成绩表；
- 不调用真实 OCR / AI。

### Phase 4：报告系统分层

目标：

- 班级简报；
- 班级详细报告；
- 学生个人报告；
- 题目分析；
- 知识点分析；
- 讲评建议。

范围：

- report 模块；
- analysis 模块；
- 报告 UI。

验收标准：

- 简洁报告一屏可读；
- 详细报告字段稳定；
- 每题、每学生、每知识点均可追溯；
- Excel 导出字段有说明。

### Phase 5：题库系统打通

目标：

- 导入 `paper-package.json`；
- 导出 `assessment-result.json`；
- 保留 `questionId` / `paperId` / `questionNumber`；
- 支持题目实测数据回流。

范围：

- question-bank 模块；
- protocol schema；
- importer / exporter；
- validator。

验收标准：

- 示例 `paper-package.json` 可导入；
- 生成内部考试和标准答案；
- 批改后可导出 `assessment-result.json`；
- 回流结果不包含修改题库原题的指令；
- 协议测试通过。

### Phase 6：UI 简化与美化

目标：

- 大按钮；
- 分步向导；
- 少术语；
- 简洁报告优先；
- 支持详细分析入口；
- 适配普通老师真实使用场景。

范围：

- presentation / web；
- 前端状态拆分；
- 页面文案。

验收标准：

- 普通老师主流程不出现专业协议名；
- 页面入口少而清楚；
- `app.js` 职责开始拆分；
- UI 改动不影响判分测试。

### Phase 7：OCR / 拍照识别

目标：

- 拍照识别只生成草稿；
- 老师确认后才判分；
- 不确定项高亮；
- 不直接污染成绩。

范围：

- OCR adapter；
- draft model；
- confirmation UI；
- audit trail。

验收标准：

- 未确认 OCR 结果不能进入成绩；
- 每条识别结果有置信度；
- 老师修改后以确认结果为准；
- 可追溯原图和识别草稿。

### Phase 8：AI 讲评与练习推荐

目标：

- AI 只读统计结果；
- 生成讲评建议；
- 推荐补救练习；
- 不参与判分；
- 不修改题库原题。

范围：

- AI adapter；
- prompt templates；
- teaching advice report；
- practice recommendation integration。

验收标准：

- AI 输入是脱敏或必要最小统计摘要；
- AI 输出标记为建议；
- 老师可编辑；
- 判分结果不受 AI 影响；
- 可关闭 AI 功能。

## 14. 长期代码规范

### 文件职责单一

一个文件只做一类事。禁止一个文件同时做 UI、判分、Excel、HTML、AI、OCR。

### 核心规则必须有测试

必须有测试的模块：

- `scoreSingleChoice`；
- `scoreMultipleChoice`；
- `scoreTrueFalse`；
- `normalizeAnswer`；
- `gradeExam`；
- `questionStats`；
- `knowledgeStats`；
- `paperPackageImporter`；
- `assessmentResultExporter`。

### 数据协议必须有版本号

`paper-package.json` 和 `assessment-result.json` 必须包含 `schemaVersion`。以后升级协议必须兼容旧版本或提供迁移器。

### 禁止直接信任外部输入

所有导入数据必须校验：

- 学生名单；
- 标准答案；
- 学生作答；
- 题库题目包；
- OCR 识别结果；
- AI 返回文本。

### 所有异常必须让老师看得懂

不要只显示 `ValidationError`、`NullReference`、`Schema mismatch`。

应该显示：

- 第 3 题没有标准答案；
- 张三第 5 题答案包含异常选项 E；
- 第 8 题是多选题，但学生答案为空；
- 导入文件缺少学生姓名列。

### 不要把显示名称和代码字段混在一起

界面给老师看的名字可以简单：从题库导入试卷、导出题库回流数据。  
代码内部必须规范：`paperPackage`、`assessmentResult`、`questionId`、`actualDifficulty`、`optionDistribution`。

### 禁止继续扩大 legacy

legacy 只能逐步减少，不能新增核心功能。迁移时必须先写测试保护行为，再小步移动。

### 禁止 `app.js` 继续膨胀

前端必须逐步拆分：

- state；
- api；
- views；
- table；
- camera；
- report；
- wizard。

### 每个阶段必须有验收标准

每个任务完成后必须说明：

- 改了哪些文件；
- 影响范围；
- 测试命令；
- 测试结果；
- 是否改业务规则；
- 是否改 UI；
- 是否调用 AI / OCR / API；
- 是否可回滚。

## 15. 给后续 Codex / Workbuddy 的执行守则

1. 每次任务先读本文档和当前任务文件。
2. 只执行当前任务，不顺手重构。
3. 修改代码前必须说明影响范围。
4. 不把 UI 和业务规则写在一起。
5. 不让 AI 判分。
6. 不让 OCR 直写成绩。
7. 不直接改题库原题。
8. 不新增 legacy 核心逻辑。
9. 不把失败测试改成通过。
10. 不绕过 `questionId`，不能只靠 `questionNumber` 关联题库题目。
11. 不把未确认数据写入正式成绩。
12. 不把技术术语直接暴露给普通老师。
13. 每次任务必须汇报当前分支、最新 commit、`git status --short`、修改文件、测试命令、测试结果、是否调用 AI / OCR / API。
14. 如果任务边界不清楚，必须停止并询问。

## 16. 总结判断

下一步不应该马上大改 UI，也不应该马上接 OCR 或 AI。最稳的路线是：

1. 保留当前可运行的 Web 产品壳；
2. 冻结产品方向和模块边界；
3. 先迁出判分核心并补强测试；
4. 稳定班级、考试、题目、作答、结果数据模型；
5. 建立 `paper-package.json` 和 `assessment-result.json` 协议；
6. 再分层做简洁报告、详细报告、题库联动；
7. 最后接 OCR 和 AI。

最重要的判断：不推倒重写，但必须停止继续把核心逻辑堆进 legacy 和前端大文件；从下一阶段开始，每一次开发都要围绕“判分纯净、协议稳定、老师易用、数据可追溯”推进。
