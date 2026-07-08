$ErrorActionPreference = "Stop"

$pythonCommand = $null

foreach ($candidate in @("python", "py")) {
    $command = Get-Command $candidate -ErrorAction SilentlyContinue
    if (-not $command) {
        continue
    }

    try {
        & $command.Source --version *> $null
        if ($LASTEXITCODE -eq 0) {
            $pythonCommand = $command.Source
            break
        }
    }
    catch {
        continue
    }
}

if (-not $pythonCommand) {
    Write-Host "Python 3.7+ could not be started."
    Write-Host "On Windows, install Python from python.org and disable the Microsoft Store python alias if needed."
    exit 1
}

& $pythonCommand ".\objective_grader.py" `
    --answer-key ".\samples\demo_exam\answer_key_sample.csv" `
    --submissions ".\samples\demo_exam\submissions_sample.csv" `
    --question-bank ".\samples\demo_exam\question_bank_sample.csv" `
    --exam-name "demo_exam" `
    --class-name "demo_class" `
    --subject "math" `
    --out-dir ".\data\reports\demo_run"
