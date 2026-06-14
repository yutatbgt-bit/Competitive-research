# run_daily_report.ps1
# タスクスケジューラから毎日AM5時（または遅延起動時）に呼び出されます。
$ErrorActionPreference = "Stop"

$workDir = "C:\Users\yutat\Documents\antigravity\agitated-galileo"
Set-Location $workDir

$logFile = Join-Path $workDir "report\auto_runner.log"

function Write-Log {
    param([string]$message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $message" | Out-File -FilePath $logFile -Append -Encoding utf8
}

Write-Log "Scheduled task started."

$today = Get-Date -Format "yyyy-MM-dd"
$lastSuccessFile = Join-Path $workDir "report\last_success.txt"

# 1. 本日実行済みかチェック
if (Test-Path $lastSuccessFile) {
    $lastSuccess = (Get-Content $lastSuccessFile -Raw).Trim()
    if ($lastSuccess -eq $today) {
        Write-Log "Today's report is already generated. Exiting."
        exit
    }
}

# 2. ネットワーク接続を待機 (PC起動直後のため最大10分間待機)
$networkReady = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "https://www.google.com" -Method Head -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $networkReady = $true
            break
        }
    } catch {
        # ignore error and retry
    }
    Start-Sleep -Seconds 10
}

if (-not $networkReady) {
    Write-Log "Failed to connect to network after 10 minutes. Exiting."
    exit
}

Write-Log "Online detected. Updating report via AI..."
$updateProcess = Start-Process -FilePath "uv" -ArgumentList "run update_report.py" -WorkingDirectory $workDir -NoNewWindow -PassThru -Wait
if ($updateProcess.ExitCode -ne 0) {
    Write-Log "Warning: update_report.py failed. Proceeding with main.py anyway."
}

Write-Log "Running main.py..."

# 3. レポート作成
$process = Start-Process -FilePath "uv" -ArgumentList "run main.py" -WorkingDirectory $workDir -NoNewWindow -PassThru -Wait

if ($process.ExitCode -eq 0) {
    Write-Log "Report generated successfully. Committing to Git..."
    
    # 以前の特定日付ハードコードのバグを修正し、生成された全ファイルを動的に追加
    & git add report/
    & git commit -m "chore: automatic daily report generation"
    
    Write-Log "Git commit completed. Exiting."
} else {
    Write-Log "Error: uv run main.py failed with exit code $($process.ExitCode)."
}
