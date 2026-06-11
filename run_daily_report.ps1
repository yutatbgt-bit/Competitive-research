# run_daily_report.ps1
# スタートアップから非表示で起動され、本日未実行である間、オンラインになるまで10分おきに監視・実行します。
# 実行に成功すると自動的にコミットし、自身を終了（自動終了）します。

$workDir = "C:\Users\yutat\Documents\antigravity\agitated-galileo"
Set-Location $workDir

$logFile = Join-Path $workDir "report\auto_runner.log"

function Write-Log {
    param([string]$message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $message" | Out-File -FilePath $logFile -Append -Encoding utf8
}

Write-Log "AutoRunner monitor loop started."

while ($true) {
    $today = Get-Date -Format "yyyy-MM-dd"
    $lastSuccessFile = Join-Path $workDir "report\last_success.txt"
    
    # 1. 本日実行済みかチェック
    if (Test-Path $lastSuccessFile) {
        $lastSuccess = (Get-Content $lastSuccessFile -Raw).Trim()
        if ($lastSuccess -eq $today) {
            Write-Log "Today's report is already generated. Exiting AutoRunner."
            break
        }
    }
    
    # 2. ネットワーク接続のチェック (OSMサーバーへのHEADリクエスト)
    $pingSuccess = $false
    try {
        $headers = @{ "User-Agent" = "IkariCompetitiveMapBot/0.2 (antigravity)" }
        # -UseBasicParsing を追加してIEエンジンの初期化ハングを防ぎます
        # 疎通確認先を安定した google.com に変更
        $response = Invoke-WebRequest -Uri "https://www.google.com" -Method Head -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop

        if ($response.StatusCode -eq 200) {
            $pingSuccess = $true
        }
    } catch {
        $pingSuccess = $false
    }
    
    if ($pingSuccess) {
        Write-Log "Online detected. Starting daily report generation..."
        
        # main.py の実行 (カレントディレクトリを明示)
        $process = Start-Process -FilePath "uv" -ArgumentList "run main.py" -WorkingDirectory $workDir -NoNewWindow -PassThru -Wait
        
        if ($process.ExitCode -eq 0) {
            Write-Log "Report generated successfully. Committing to Git..."
            # git add & commit
            & git add report/2026_06_08_competitive_report.pptx report/last_success.txt report/2026_06_08_competitive_map.html
            & git commit -m "chore: automatic daily report recovery via startup runner"
            Write-Log "Git commit completed. Exiting AutoRunner."
            break
        } else {
            Write-Log "Error: uv run main.py failed with exit code $($process.ExitCode). Will retry in 10 minutes."
        }
    } else {
        Write-Log "Offline. Will check again in 10 minutes..."
    }
    
    # 10分間待機 (600秒)
    Start-Sleep -Seconds 600
}
