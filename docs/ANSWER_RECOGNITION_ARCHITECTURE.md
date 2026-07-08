# 答题识别与复杂填空判分架构设计

## 1. 最新需求结论

### 1.1 核心决策

| 决策项 | 结论 |
|--------|------|
| 是否改模板 | **不改**。系统必须适配用户当前已有的普通试卷答题框，不允许要求增加四角定位点、改成标准答题卡或让学生涂黑选项 |
| 学号字段 | **不单独开"学号"字段**。姓名栏内容 = 学号/序号数字 + 姓名（如 `1李明`、`23张三`） |
| 联网能力 | **可以联网**。本项目不是纯离线项目，可以接千问 API（Qwen-OCR / Qwen-VL） |
| AI 参与判分 | **可以参与复杂填空判分**。方程、表达式、区间、不等式等本地规则难以完全覆盖的答案，可交千问做结构化判定 |
| 高置信自动入分 | **支持**。千问输出高置信、理由完整、无冲突时自动入分，不弹给老师 |
| 复核机制 | **异常复核**，不是全部复核。老师只处理少数不确定项 |
| AI 限制 | AI 不能无条件直接改最终成绩；必须有结构化输出、置信度、理由、trace、异常闸门 |

### 1.2 当前模板特点

用户当前使用的普通试卷答题模板具有以下特征：

- 顶部有标题
- 有"班级、姓名、评分"区域
- 1—11 题选择题答案在一个表格里
- 表格有"题号 / 答案"两行
- 12—14 题是横线填空
- 下面是题目正文

系统必须围绕这个普通模板做识别架构，**不强求四角定位点**。

### 1.3 与现有系统的关系

本架构文档描述的是**识别与复杂判分层的设计**，位于现有批改系统之上：

- 现有 `app/domain/grading/` 判分核心（单选、多选、判断、填空基础判分）**保持不变**
- 现有 `exam_recognizer.py` 的 exam manifest 流程**保持不变**
- 现有 `web_app.py` + `web/` 网页端**保持不变**
- 现有 `roster_manager.py` 班级名单管理**保持不变**
- 本架构新增的是：**图像预处理 → 千问识别 → 结构化草稿 → 本地校验 → 异常队列** 这一整条识别链路

## 2. 总体架构

### 2.1 四层结构

系统不是"单一 OCR 识别系统"，而是**三引擎协同 + 异常队列**的四层结构：

```
┌─────────────────────────────────────────────────────┐
│                  第四层：异常队列                      │
│  老师只处理少数不确定项，不逐题复核                      │
│  · 姓名/序号冲突  · 选择题 unclear  · 非法选项          │
│  · OCR 低置信  · 多候选  · 千问低置信                  │
│  · 千问与本地规则冲突  · needs_review  · 强制复核       │
└─────────────────────────────────────────────────────┘
                         ↑
┌─────────────────────────────────────────────────────┐
│               第三引擎：本地规则算法                     │
│  · 学号姓名正则拆分  · 班级名单校验  · 选择题合法性校验    │
│  · 单选/多选/判断判分  · 数值填空题等价判定              │
│  · 分数/小数/根式/集合等价  · 千问结果校验               │
│  · 异常项分类  · 最终分数落地                           │
└─────────────────────────────────────────────────────┘
                         ↑
┌─────────────────────────────────────────────────────┐
│             第二引擎：千问 / Qwen-OCR / Qwen-VL         │
│  · 姓名栏数字+姓名识别  · 选择题格子手写选项识别          │
│  · 填空题横线手写答案识别  · LaTeX 结构化数学表达式输出    │
│  · 复杂方程/不等式/区间等价判定  · 置信度+理由           │
│  · 必须结构化 JSON 输出，不允许自由文本                   │
└─────────────────────────────────────────────────────┘
                         ↑
┌─────────────────────────────────────────────────────┐
│              第一引擎：OpenCV / 图像处理                │
│  · 页面矫正（倾斜/透视）  · 答案表格检测                 │
│  · 表格网格线检测  · 姓名栏定位                         │
│  · 选择题答案格定位  · 填空题横线区域定位                │
│  · ROI 裁剪  · 降级策略（边缘检测失败时的备选方案）        │
└─────────────────────────────────────────────────────┘
```

### 2.2 各引擎职责边界

**OpenCV 不允许做**：数学判分、语义判断、学号姓名最终确认、复杂表达式等价判断。

**千问不允许做**：自由文本输出后让系统自己猜、绕过本地规则直接写最终成绩、在无上下文的情况下判分。

**本地规则不允许做**：原始图像识别、复杂数学表达式的语义等价判断（方程、不等式、区间等超出确定性规则范围的）。

### 2.3 数据流向

```
拍照图片
  → OpenCV 页面矫正 + 区域定位 + ROI 裁剪
  → 千问 OCR / 视觉识别（姓名栏、选择题格、填空横线）
  → 生成 RecognizedAnswerDraft（结构化草稿，不是最终成绩）
  → 本地规则校验（正则拆分、名单匹配、合法性检查、简单等价判定）
  → 低风险：自动确认 / 本地规则自动判分
  → 中风险：千问结构化判定 → 高置信自动入分
  → 高风险：进入异常队列 → 老师复核
  → 确认后的结果进入现有 grading pipeline（answer_key + submissions → grade_all）
```

## 3. 不改模板下的页面定位方案

### 3.1 设计原则

由于用户不接受改模板，不强求四角定位点。应使用**现有版式锚点 + AI 粗定位**共同完成定位。

### 3.2 可用锚点

| 优先级 | 锚点 | 用途 |
|--------|------|------|
| 1 | 标题文字 | 确定页面上边界和方向 |
| 2 | "班级 / 姓名 / 评分"区域 | 定位姓名栏 |
| 3 | "题号 / 答案"表格 | 定位选择题答案区域 |
| 4 | 表格网格线 | 切分每道选择题的答案格 |
| 5 | "一、单选题"等文字 | 辅助确认答案表格位置 |
| 6 | 12、13、14 题号 | 定位填空区域起始位置 |
| 7 | 填空横线 | 定位每道填空的答案区域 |

### 3.3 定位流程

```
拍照图片
  → 页面边缘估计（Canny + 轮廓检测 + 最大四边形逼近）
  → 透视矫正（四点透视变换）
  → 检测答案表格网格线（HoughLines / 形态学操作）
  → 定位"题号 / 答案"行
  → 定位"答案"行中各题答案格（按列切分）
  → 定位姓名栏（"姓名"文字下方/右侧区域）
  → 定位填空题横线区域（12/13/14 题号 + 横线检测）
  → 裁剪 ROI 小图
  → 送入千问 / OCR 识别
```

### 3.4 降级策略

如果页面边缘检测失败，按以下优先级降级：

1. **用表格线定位**：以检测到的表格网格线为锚点推算页面范围
2. **用"题号 / 答案"文字定位**：以 OCR 检测到的特定文字区域为锚点
3. **让千问视觉模型粗定位**：将整张图片传给千问 VL，让其输出答案表格和姓名栏的 bounding box
4. **让老师手动框选一次**：在网页端提供框选工具，老师框选答案区域
5. **保存模板坐标偏移**：将该模板的坐标偏移保存，下次同模板的试卷自动复用

### 3.5 模板坐标记忆机制

当老师手动框选或系统成功定位后：

- 记录该试卷模板的特征（如标题文字、表格行列数、关键文字位置）
- 保存 ROI 坐标偏移到模板配置文件
- 下次识别同模板试卷时优先使用已保存的坐标
- 若偏移后检测不到预期内容，回退到完整检测流程

## 4. 姓名栏"数字+姓名"识别方案

### 4.1 识别规则

姓名栏内容格式：**学号/序号数字 + 姓名**

示例：
- `1李明` → 序号 1，姓名 李明
- `23张三` → 序号 23，姓名 张三
- `05王小明` → 序号 05（即 5），姓名 王小明

### 4.2 识别流程

```
裁剪姓名栏 ROI
  → 千问 OCR 识别姓名栏文本
  → 正则拆分：开头连续数字 = 序号，后面中文 = 姓名
  → 班级名单校验（roster_manager.load_roster）
  → 输出匹配结果和置信度
```

### 4.3 正则拆分规则

```python
import re

def parse_name_field(text: str) -> dict:
    """
    从姓名栏文本中拆出序号和姓名。
    示例：
      "1李明"    → {"student_number": "1",  "name": "李明", "status": "parsed"}
      "23张三"   → {"student_number": "23", "name": "张三", "status": "parsed"}
      "李明"     → {"student_number": "",    "name": "李明", "status": "no_number"}
      "1李朋"    → {"student_number": "1",  "name": "李朋", "status": "parsed"}
    """
    text = (text or "").strip()
    match = re.match(r'^(\d+)\s*(.+)', text)
    if match:
        return {
            "student_number": match.group(1),
            "name": match.group(2).strip(),
            "status": "parsed"
        }
    # 只有中文，没有数字
    if re.search(r'[一-鿿]', text):
        return {
            "student_number": "",
            "name": text,
            "status": "no_number"
        }
    return {
        "student_number": "",
        "name": text,
        "status": "unclear"
    }
```

### 4.4 班级名单校验规则

| 场景 | 识别结果 | 名单数据 | 判定 | 动作 |
|------|----------|----------|------|------|
| 序号+姓名完全匹配 | `1李明` | 1: 李明 | confirmed | 自动确认 |
| 姓名匹配但序号不匹配 | `7李明` | 1: 李明, 7: 王强 | conflict | 进入异常队列 |
| 只有姓名没有数字 | `李明` | 1: 李明 | needs_review | 姓名能匹配但缺少序号，进入异常队列 |
| 序号匹配但姓名疑似错误 | `1李朋` | 1: 李明 | needs_review | 疑似识别错误，进入异常队列 |
| 序号和姓名都不匹配 | `9赵六` | 无匹配 | invalid | 进入异常队列 |
| 无法解析 | `???` | — | invalid | 进入异常队列 |
| 数字不清楚 | `1?明` | — | low_confidence | 进入异常队列 |

### 4.5 校验流程

```
识别文本 → parse_name_field()
  → roster_manager.load_roster(class_name)
  → 如果序号存在且姓名匹配 → confirmed
  → 如果姓名存在但序号不匹配 → conflict（列出名单中该姓名的序号）
  → 如果只有姓名 → needs_review（尝试模糊匹配名单）
  → 如果序号不存在 → invalid
  → 如果无法解析 → invalid
```

### 4.6 关键约束

- 系统**不能只靠 AI 说"这是某某同学"**，必须结合班级名单做校验
- 名单来源：`roster_manager.load_roster()`，返回 `Dict[student_id, name]`
- 校验逻辑是确定性规则，不由 AI 决定

## 5. 选择题表格识别方案

### 5.1 当前题型

当前试卷 1—11 题在同一个答案表格中，表格结构为：

```
┌──────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
│ 题号  │ 1  │ 2  │ 3  │ 4  │ 5  │ 6  │ 7  │ 8  │ 9  │ 10 │ 11 │
├──────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┤
│ 答案  │ A  │ B  │ C  │ D  │ A  │ B  │ C  │ D  │ AC │ BD │    │
└──────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
```

### 5.2 识别流程

```
定位答案表格（通过网格线 + "题号/答案"文字锚点）
  → 定位"答案"行
  → 按列切分 1—11 题答案格（通过竖线检测或等分推算）
  → 每格单独裁剪为小图（如 100×60 px）
  → 每格单独送千问识别
  → 千问返回结构化 JSON
  → 本地规则校验
  → 低置信或非法进入异常队列
```

### 5.3 千问 Prompt 设计（选择题格识别）

发送给千问的 prompt：

```
你只识别这个答案格中的手写选择题答案。
答案只能是 A、B、C、D 的组合，或者 blank、unclear。
不要解释，不要补充。
如果看不清，输出 unclear。
如果没有作答，输出 blank。
请只输出 JSON：
{
  "answer": "A|B|C|D|AB|AC|AD|BC|BD|CD|ABC|ABD|ACD|BCD|ABCD|blank|unclear|invalid",
  "confidence": 0.0
}
```

### 5.4 本地规则校验

| 情况 | 处理 |
|------|------|
| 单选题（标准答案只有 1 个选项）识别出多个选项 | invalid，得 0，进入异常队列或按设置自动算错 |
| 多选题含错误选项 | 得 0（现有 `choice_scoring.score_choice_answer` 已处理） |
| blank（千问返回空答） | 空答，得 0 |
| unclear（千问返回不清楚） | 进入异常队列 |
| 非 A-D 字符 | invalid |
| 选项顺序无关（如 BA → AB） | 本地规则自动标准化（`normalize_answer` 已处理） |

### 5.5 选择题识别结果映射到现有系统

识别结果先生成 `RecognizedAnswerDraft`，确认后通过 `draft_to_submission()` 转为 `Submission`，再进入现有 `grade_all()` 流程。现有 `score_choice_answer` 和 `score_answer_detail` 保持不变。

## 6. 填空题横线识别方案

### 6.1 当前题型

12—14 题是横线填空，每道题有一条或多条横线供学生手写作答。

### 6.2 识别流程

```
通过题号（12/13/14）和横线定位填空区域
  → 裁剪每道填空的答案区域（横线上下各留适当边距）
  → 传给千问 OCR 识别
  → 千问输出 raw_text 和 latex
  → 本地规则先尝试简单等价（分数/小数/根式/集合）
  → 本地规则无法确定时 → 调用千问做数学等价判定
  → 高置信自动入分
  → 低置信或冲突进入异常队列
```

### 6.3 千问 OCR Prompt（填空题横线识别）

```
请只识别该填空题横线上的手写答案。
不要解题，不要判断对错。
尽量输出数学表达式。
如果能转成 LaTeX，请同时给出 LaTeX。
看不清输出 unclear，空白输出 blank。
请只输出 JSON：
{
  "raw_text": "...",
  "latex": "...",
  "confidence": 0.0,
  "status": "recognized|blank|unclear"
}
```

### 6.4 本地规则优先判定

以下情况本地规则可直接判定，不必调用千问判分（千问最多参与 OCR 识别原始答案）：

| 类型 | 示例 | 处理方式 |
|------|------|----------|
| 分数/小数等价 | 1/2 = 0.5 | `blank_scoring._fraction()` 数值比较 |
| 小数等价 | 0.25 = 1/4 | `blank_scoring._same_single()` |
| 整数等价 | 2.0 = 2 | 数值比较 |
| 根式文本等价 | √2 = 根号2 = sqrt(2) | `blank_scoring._looks_like_root()` |
| 集合乱序等价 | {1,2} = {2,1} | `blank_scoring._parse_set()` |
| 多选题选项顺序无关 | AB = BA | `normalize_answer` 自动排序 |
| 空答 | — | `score_answer_detail` 返回 blank |
| 明显非法答案 | 乱码、无关内容 | 标记 invalid |

以上所有处理已在 `app/domain/grading/blank_scoring.py` 中实现，无需额外开发。

### 6.5 现有填空题判分覆盖范围

| 已支持 | 未支持（需千问辅助） |
|--------|---------------------|
| 数值等价（分数/小数/整数） | 方程等价判定 |
| 集合乱序等价 | 不等式/区间等价 |
| 根式文本等价 | 函数表达式等价 |
| 文本别名/容差 | 三角表达式等价 |
| 空答检测 | 因式分解结果等价 |
| 需要人工复核标记 | 带参数答案等价 |
| | 向量/坐标形式等价 |

## 7. 复杂填空题 AI 判定方案

### 7.1 千问参与判定的题型

以下情况本地规则不容易完全处理，可调用千问进行结构化判定：

- 方程（如 `x² - 1 = 0` vs `x = ±1`）
- 不等式（如 `x > 1` vs `(1, +∞)`）
- 区间（如 `[0, 1)` vs `0 ≤ x < 1`）
- 解集（如 `{1, 2}` vs `x = 1 或 x = 2`）
- 函数表达式（如 `f(x) = x²` vs `y = x²`）
- 三角表达式（如 `sin²x + cos²x = 1` vs `1`）
- 因式分解结果（如 `(x+1)(x-1)` vs `x² - 1`）
- 等价表达式
- 带参数答案
- 向量表达式
- 坐标形式
- 题意相关的数学表达

### 7.2 千问判分 Prompt（复杂填空判定）

```
你是高中数学填空题判分助手。
请根据题目、标准答案、学生答案判断是否数学等价。
不要重新解题，只判断学生答案是否可接受。
如果无法确定，请返回 needs_review。

题目原文：{stem}
题型：填空题
分值：{points} 分
标准答案：{correct_answer}
学生答案：{student_answer}
识别置信度：{ocr_confidence}
是否来自 OCR：是
评分要求：只判断数学等价性
是否允许不同形式答案：是
是否需要考虑答案形式要求：{format_required}

只输出 JSON：
{
  "verdict": "correct|wrong|partial|needs_review|invalid",
  "confidence": 0.0,
  "reason": "...",
  "normalized_standard": "...",
  "normalized_student": "...",
  "equivalence_type": "same_value|same_solution_set|same_expression|format_mismatch|unknown",
  "requires_review": true
}
```

### 7.3 千问必须传入的完整上下文

不能只传标准答案和学生答案让千问判断对错，必须传入：

1. 题目原文（stem）
2. 题型（question_type）
3. 分值（points）
4. 标准答案（correct_answer）
5. 学生答案（student_answer / raw_text / latex）
6. 识别置信度（ocr_confidence）
7. 是否来自 OCR
8. 评分要求（只判断数学等价 / 需考虑答案形式）
9. 是否允许不同形式答案
10. 是否需要考虑答案形式要求

### 7.4 千问结构化输出规范

`verdict` 只能是以下值之一：

| verdict | 含义 |
|---------|------|
| `correct` | 学生答案与标准答案数学等价，给满分 |
| `wrong` | 学生答案与标准答案不等价，得 0 分 |
| `partial` | 部分正确，按比例给分 |
| `needs_review` | 千问无法确定，需要老师判断 |
| `invalid` | 学生答案格式异常，无法判定 |

**不允许千问输出自由文本后系统自己猜。**

### 7.5 千问高置信自动入分条件

以下条件**全部满足**时，可以自动入分，不弹给老师：

1. 千问 verdict 是 `correct` / `wrong` / `partial`
2. confidence ≥ 0.90（阈值可配置）
3. reason 不为空
4. normalized_standard 和 normalized_student 不为空
5. OCR 识别本身不是 `low_confidence` 或 `unclear`
6. 不存在多个候选答案
7. 本地规则没有检测到冲突
8. 题目没有被标记为"必须人工确认"

### 7.6 必须进入异常队列的情况

以下任一情况**不能**自动入最终成绩：

1. OCR 识别不清（status = unclear）
2. AI 输出多个候选答案（candidateAnswers 长度 > 1）
3. 千问 confidence < 阈值（默认 0.90）
4. 千问 verdict = `needs_review`
5. 千问 reason 为空或前后矛盾
6. 本地规则和千问结论冲突（如本地判定 wrong 但千问判定 correct）
7. 学生答案缺少关键变量
8. 学生答案多解或少解（与标准答案的解的数量不一致）
9. 题目要求特定答案形式，但学生写成另一种形式
10. 姓名 / 序号与学生名单不匹配
11. 选择题识别出非法选项
12. 填空题 blank 但图像疑似有笔迹（千问 status = blank 但 confidence 中等）
13. 老师设置该题必须人工确认（`QuestionSpec.status = "manual_review"`）

## 8. 自动入分与异常队列规则

### 8.1 三级风险分层

| 风险等级 | 判定方式 | 动作 |
|----------|----------|------|
| **低风险** | 本地规则可直接判定（单选/多选/判断/简单填空等价） | **自动判分**，不入异常队列 |
| **中风险** | 千问高置信判定（confidence ≥ 0.90，reason 完整，无冲突） | **自动入分**，但保留 aiTrace 可追踪 |
| **高风险** | 低置信、冲突、needs_review、识别不清、多候选 | **进入异常队列**，老师复核 |

### 8.2 异常队列内容

异常队列包含以下类型：

- 姓名 / 序号冲突（识别结果与名单不一致）
- 选择题 unclear（千问看不清）
- 选择题非法选项（超出 A-D 范围）
- OCR 低置信（confidence < 阈值）
- 填空题多个候选答案
- 千问判定低置信（confidence < 0.90）
- 千问与本地规则冲突
- verdict = `needs_review`
- 老师设置强制复核
- 图像疑似有字但识别为 blank

### 8.3 老师操作

- 老师可以在异常队列界面逐条处理
- 老师可以批量确认同类型的低风险异常
- 老师可以抽查自动判分结果（随机展示已自动判分的题目）
- 老师可以设置某道填空题"强制复核"
- 所有自动判分保留可追踪理由

### 8.4 与现有 grading pipeline 的集成

异常队列处理后，确认的结果通过 `confirm_draft_answer()` 将 `DraftAnswerItem` 标记为 `confirmed`，再通过 `draft_to_submission()` 转为 `Submission`，进入现有的 `grade_all()` 流程。千问自动入分的题目也会生成对应的 `GradingDecision`，其中 `decidedBy = "qwen"`，`aiTrace` 记录完整判定过程。

## 9. 数据结构设计

### 9.1 RecognizedAnswerDraft（识别草稿）

这是 AI / OCR 识别后的草稿，**不是最终成绩**。

```python
@dataclasses.dataclass(frozen=True)
class RecognizedAnswerDraft:
    student_id: str = ""              # 匹配后的学号
    student_number: str = ""          # 从姓名栏解析出的序号
    student_name: str = ""            # 从姓名栏解析出的姓名
    question_number: int = 0          # 题号
    question_type: str = ""           # 题型：single_choice/multiple_choice/blank/true_false
    raw_image_ref: str = ""           # 裁剪后的小图路径或 base64 引用
    roi_box: tuple = ()               # ROI 边界框坐标 (x, y, w, h)
    raw_text: str = ""                # 千问 OCR 原始输出文本
    normalized_text: str = ""         # 本地规则标准化后文本
    latex: str = ""                   # LaTeX 格式（填空/数学表达式）
    candidate_answers: list = None    # 多个候选答案（如有歧义）
    confidence: float = 0.0           # 识别置信度 0.0-1.0
    source: str = ""                  # 识别来源：qwen_ocr/qwen_vl/tesseract/manual
    status: str = "draft"             # 见下方状态列表
    message: str = ""                 # 附加信息或警告
    needs_review: bool = False        # 是否需要老师复核

# status 取值：
# - draft: 初始草稿
# - confirmed: 已确认（可进入判分）
# - low_confidence: 低置信度
# - conflict: 存在冲突（如姓名与名单不匹配）
# - blank: 空答
# - invalid: 非法答案
# - unclear: 识别不清
# - needs_review: 需要复核
# - auto_accepted: 自动接受（高置信且校验通过）
```

### 9.2 GradingDecision（判分决策）

这是判分决策，记录谁判的、为什么判、可追踪。

```python
@dataclasses.dataclass(frozen=True)
class GradingDecision:
    question_number: int = 0          # 题号
    question_type: str = ""           # 题型
    correct_answer: str = ""          # 标准答案
    student_answer: str = ""          # 学生答案
    normalized_correct_answer: str = ""  # 标准化标准答案
    normalized_student_answer: str = ""  # 标准化学生答案
    score: float = 0.0                # 得分
    max_score: float = 0.0            # 满分
    verdict: str = ""                 # correct/wrong/partial/needs_review/invalid
    confidence: float = 0.0           # 判定置信度
    reason: str = ""                  # 判定理由
    decided_by: str = ""              # 判定者：local_rule/qwen/teacher/mixed
    requires_review: bool = False     # 是否需要复核
    ai_trace: dict = None             # 千问判定完整记录（如果 decided_by = qwen）
    rule_trace: dict = None           # 本地规则判定记录（如果 decided_by = local_rule）
    teacher_decision: dict = None     # 老师修改记录（如果老师修改过）

# decided_by 取值：
# - local_rule: 本地确定性规则判定
# - qwen: 千问 AI 判定
# - teacher: 老师人工判定
# - mixed: 多引擎共同判定
```

### 9.3 与现有数据模型的关系

- `RecognizedAnswerDraft` → 确认后 → `DraftAnswerItem`（`answer_draft.py`）→ `draft_to_submission()` → `Submission`（`models.py`）
- `GradingDecision` → 对应现有 `QuestionResult`（`models.py`），在其基础上增加了 `decided_by`、`ai_trace`、`rule_trace`、`teacher_decision` 等追踪字段
- 现有 `SingleQuestionScore` 和 `QuestionResult` 已经包含 `needs_review` 字段，可直接对接异常队列

## 10. Prompt 设计汇总

### 10.1 姓名栏识别 Prompt

```
请识别这张图片中姓名栏的手写内容。
姓名栏中可能包含数字（学号/序号）和中文姓名。
请原样输出，不要修改或补充。
如果看不清，输出 unclear。
请只输出 JSON：
{
  "raw_text": "...",
  "confidence": 0.0,
  "status": "recognized|unclear"
}
```

### 10.2 选择题格识别 Prompt

```
你只识别这个答案格中的手写选择题答案。
答案只能是 A、B、C、D 的组合，或者 blank、unclear。
不要解释，不要补充。
如果看不清，输出 unclear。
如果没有作答，输出 blank。
请只输出 JSON：
{
  "answer": "A|B|C|D|AB|AC|AD|BC|BD|CD|ABC|ABD|ACD|BCD|ABCD|blank|unclear|invalid",
  "confidence": 0.0
}
```

### 10.3 填空题 OCR Prompt

```
请只识别该填空题横线上的手写答案。
不要解题，不要判断对错。
尽量输出数学表达式。
如果能转成 LaTeX，请同时给出 LaTeX。
看不清输出 unclear，空白输出 blank。
请只输出 JSON：
{
  "raw_text": "...",
  "latex": "...",
  "confidence": 0.0,
  "status": "recognized|blank|unclear"
}
```

### 10.4 复杂填空判定 Prompt

```
你是高中数学填空题判分助手。
请根据题目、标准答案、学生答案判断是否数学等价。
不要重新解题，只判断学生答案是否可接受。
如果无法确定，请返回 needs_review。

题目原文：{stem}
题型：填空题
分值：{points} 分
标准答案：{correct_answer}
学生答案：{student_answer}
识别置信度：{ocr_confidence}
是否来自 OCR：是
评分要求：只判断数学等价性
是否允许不同形式答案：是
是否需要考虑答案形式要求：{format_required}

只输出 JSON：
{
  "verdict": "correct|wrong|partial|needs_review|invalid",
  "confidence": 0.0,
  "reason": "...",
  "normalized_standard": "...",
  "normalized_student": "...",
  "equivalence_type": "same_value|same_solution_set|same_expression|format_mismatch|unknown",
  "requires_review": true
}
```

## 11. 安全边界

### 11.1 AI 可以做的事

- 识别姓名栏中的数字和姓名
- 识别选择题格子中的手写选项
- 识别填空题横线上的手写答案
- 输出 LaTeX 或结构化数学表达式
- 对复杂方程、不等式、区间做结构化数学等价判定
- 输出置信度和判定理由
- 帮助老师粗定位答案区域（降级策略）

### 11.2 AI 不能做的事

- **不能**输出自由文本后让系统自己猜（必须结构化 JSON）
- **不能**绕过本地规则直接写最终成绩
- **不能**在无上下文的情况下判分（必须传题目原文、标准答案、题型、分值等）
- **不能**直接修改 `answer_key.csv` 或 `submissions.csv`
- **不能**决定学生姓名（必须经过班级名单校验）
- **不能**在低置信时强行判定
- **不能**无条件自动入分（必须满足高置信自动入分条件）

### 11.3 安全闸门

```
千问输出 → 本地规则校验 → 冲突检测 → 置信度检查 → 异常闸门
                                                      ↓
                                          ┌─ 通过 → 自动入分（保留 trace）
                                          └─ 不通过 → 异常队列 → 老师复核
```

### 11.4 可追踪性要求

- 千问自动判分的题目必须保存完整的 `aiTrace`（输入 prompt、输出 JSON、时间戳、模型版本）
- 本地规则判分必须保存 `ruleTrace`（匹配的规则名称、输入输出）
- 老师修改过的判分必须保存 `teacher_decision`（修改前后的值、时间戳）
- 所有自动入分结果必须能在报告中追溯到判定来源

## 12. 阶段路线

### Stage R1：文档与架构冻结
- **目标**：明确不改模板、千问参与、异常复核、高置信自动判分
- **产出**：本文档（`docs/ANSWER_RECOGNITION_ARCHITECTURE.md`）
- **不写代码**

### Stage R2：图片预处理与 ROI 裁剪
- **目标**：基于现有模板定位姓名栏、答案表格、填空横线
- **内容**：OpenCV 页面矫正、表格检测、ROI 裁剪、降级策略
- **输出**：裁剪后的小图文件 + ROI 坐标数据

### Stage R3：姓名栏"数字+姓名"解析
- **目标**：识别 `1李明` / `23张三`，并和班级名单校验
- **内容**：正则拆分 + `roster_manager` 名单匹配
- **输出**：`RecognizedAnswerDraft`（student info 部分）

### Stage R4：选择题格子识别 mock
- **目标**：先用 mock 模拟千问返回，验证格子识别数据流
- **内容**：mock 返回 `{"answer": "A", "confidence": 0.95}` 等，打通从 ROI → mock 识别 → `RecognizedAnswerDraft` → 本地校验的数据流
- **不接真实千问 API**

### Stage R5：填空题识别 mock
- **目标**：模拟 `raw_text` / `latex` / `confidence`，接入本地判分
- **内容**：mock 返回填空识别结果，验证本地 `blank_scoring` 等价判定 + 千问复杂判定 mock 的数据流
- **不接真实千问 API**

### Stage R6：复杂填空 AI 判定 mock
- **目标**：模拟千问判断方程、表达式、区间是否等价
- **内容**：mock 返回 `GradingDecision`（verdict + confidence + reason），验证异常队列分流逻辑

### Stage R7：异常队列机制
- **目标**：只把低置信、冲突、needs_review 推给老师
- **内容**：异常队列数据结构、老师复核界面、批量确认、抽查机制

### Stage R8：接千问真实 API
- **目标**：真实调用 Qwen-OCR / Qwen-VL，但只生成草稿和判定，不直接绕过安全闸门
- **内容**：千问 API 调用封装、prompt 管理、结构化输出解析、错误处理/重试

### Stage R9：接入正式批改流程
- **目标**：confirmed / auto_accepted 的结果进入正式判分
- **内容**：`RecognizedAnswerDraft` → `DraftAnswerItem` → `Submission` → `grade_all()` 的完整链路

### Stage R10：识别准确率迭代
- **目标**：积累错例，优化 prompt、ROI、阈值和规则
- **内容**：错例收集、prompt 调优、置信度阈值校准、ROI 定位精度提升

## 13. 下一步建议

### 13.1 立即开始的工作

**下一步不是立刻接真实千问 API**，而是先做 mock 数据流：

1. **ROI 裁剪结构**：基于现有模板图片，用 OpenCV 检测表格和横线，输出裁剪坐标
2. **姓名栏解析**：实现正则拆分 + 班级名单校验 + 结果分类（confirmed / conflict / needs_review / invalid）
3. **选择题识别 mock**：模拟千问返回，验证从裁剪 → mock 识别 → `RecognizedAnswerDraft` → 本地校验的完整数据流
4. **填空题识别 mock**：模拟 OCR 返回 raw_text + latex + confidence，接入 `blank_scoring` 判定
5. **复杂判定 mock**：模拟千问返回 `GradingDecision`，验证与本地规则的协同
6. **异常队列**：定义异常项数据结构和分流逻辑

### 13.2 不建议现在做的事

- 不建议立刻接真实千问 API（数据流未通，接了也无法验证）
- 不建议改 UI（现有 `web/index.html` + `web/static/app.js` 保持不变）
- 不建议改判分核心（`app/domain/grading/` 已稳定，保持不变）
- 不建议动 legacy 代码（保持兼容）
- 不建议做题库联动（`paper-package.json` / `assessment-result.json` 后置）

### 13.3 与现有系统的对接点

| 本架构模块 | 对接的现有模块 |
|-----------|---------------|
| 姓名栏解析 + 名单校验 | `roster_manager.load_roster()` / `match_student()` |
| 选择题识别草稿 | `app/domain/grading/answer_draft.py` → `draft_to_submission()` |
| 选择题本地校验 | `app/domain/grading/choice_scoring.score_choice_answer()` |
| 填空基础等价判定 | `app/domain/grading/blank_scoring.blank_answer_matches()` |
| 判分决策 | `app/domain/grading/scoring.score_answer_detail()` |
| 预检 | `app/domain/grading/precheck.run_grading_precheck()` |
| 正式批改 | `app/workflow.run_grading()` |
| 照片采集 | `web_app.py` → `data/captures/` |
| 考试识别入口 | `exam_recognizer.py` → exam manifest 流程 |

---

**文档状态**：架构设计阶段（Stage R1）
**最后更新**：2026-07-09
**关联文档**：
- `docs/ARCHITECTURE_AUDIT_001.md` — 现有系统架构审计
- `docs/STAGE1_GRADING_FOUNDATION_LONG_RUN.md` — 判分底座长期任务
- `docs/PRODUCT_ARCHITECTURE_MASTER_PLAN.md` — 产品与架构总规划
- `docs/GRADING_SOFTWARE_PRODUCTIZATION_PLAN.md` — 产品化改造计划
- `legacy/ARCHITECTURE.md` — 历史架构文档
