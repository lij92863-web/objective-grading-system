# 客观题批改助手

## 最常用的打开方式

- 打开网页：双击 `启动网页.bat`
- 运行测试：双击 `运行测试.bat`
- 数据保存位置：`data/`
- 报告保存位置：`data/reports/`
- 考试归档位置：`data/exams/`

这个软件定位为“教师客观题批改、班级诊断、讲评决策、分层补救助手”。普通老师建议只使用网页端，不需要使用命令行。

## 老师的使用流程

1. 双击 `启动网页.bat`。
2. 在首页进入“班级管理”，导入学生名单。
3. 进入“新建考试”。
4. 填写班级、考试名称、日期和科目。
5. 导入或填写标准答案。
6. 检查标准答案草稿，点击“确认标准答案”。
7. 导入学生作答，或使用摄像头/手机摄像头拍照保存答题卡图片。
8. 点击“检查数据”，处理未匹配学生和严重错误。
9. 无严重错误后点击“开始批改”。
10. 查看完整报告、讲评建议和历史考试。

## 项目结构

```text
客观题批改/
├── 启动网页.bat
├── 运行测试.bat
├── web_app.py
├── objective_grader.py
├── exam_recognizer.py
├── roster_manager.py
├── README.md
├── app/
│   ├── core.py
│   ├── data_io.py
│   ├── analysis.py
│   ├── reports.py
│   ├── workflow.py
│   └── validators.py
├── web/
│   ├── templates/
│   └── static/
│       ├── app.css
│       └── app.js
├── data/
│   ├── classes/
│   ├── exams/
│   ├── uploads/
│   ├── captures/
│   └── reports/
├── samples/
├── tests/
└── legacy/
```

## 标准答案导入

网页端支持：

- 上传表格：`.xlsx`、`.xls`、`.csv`
- 上传 Word / PDF：`.docx`、`.pdf`
- 拍照 / 上传图片：`.jpg`、`.jpeg`、`.png`、`.webp`
- 手动填写：可粘贴 `1.A`、`2.B`、`3.CD` 这类文本

所有来源都会先生成“标准答案草稿”。老师必须在网页里确认后，系统才会生成正式 `answer_key` 并进入批改。

## 拍照录入

“新建考试”的学生作答步骤里有“拍照录入答题卡”。

它支持：

- 电脑自带摄像头
- 外接 USB 摄像头 / 高拍仪
- 手机作为摄像头

软件不会直接控制手机，只会使用电脑系统已经识别出的摄像头设备。手机需要先通过数据线或摄像头工具让电脑识别为摄像头。

## 报告内容

系统报告重点面向教师讲评和班级补救：

- 成绩统计
- 每题分析
- 班级薄弱知识点
- 讲评优先级
- 学生错题清单
- 班级统一补救练习
- 分层补救建议

核心输出：

- `teaching_plan.csv / .html`
- `class_remedial_package.csv / .html`
- `layered_remedial_plan.csv / .html`
- `student_wrong_list.csv`
- `exam_report.xlsx`

## 高级命令行用法

普通老师不需要使用命令行。高级用户仍可运行：

```powershell
python objective_grader.py --answer-key .\samples\demo_exam\answer_key_sample.csv --submissions .\samples\demo_exam\submissions_sample.csv --out-dir .\data\reports\manual_run
```

## 测试

双击 `运行测试.bat`，或运行：

```powershell
python run_tests.py
```

