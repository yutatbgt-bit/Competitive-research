# Windows Task Scheduler Registration Script for Ikari Competitive Research
# This registers a daily scheduled task to run `src/run_daily_report.sh` via WSL.

$taskName = "IkariCompetitiveReportDailyRunner"
$time = "05:00"

# Detect default WSL distro cleanly
$distro = "Ubuntu"
try {
    $rawDistro = (& wsl.exe -l -q 2>$null | Select-Object -First 1)
    if ($rawDistro) {
        $clean = ($rawDistro -replace "[^\x20-\x7E]", "").Trim()
        if ($clean) { $distro = $clean }
    }
} catch {
    # fallback to Ubuntu
}

# Resolve WSL path for the project root
$windowsScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$windowsProjectDir = Split-Path -Parent $windowsScriptDir

try {
    $wslProjectDir = (& wsl.exe -d $distro -e bash -c "cd `$(wslpath '$windowsProjectDir') 2>/dev/null && pwd").Trim()
} catch {
    $wslProjectDir = ""
}

if (-not $wslProjectDir) {
    # Fallback to current directory inside WSL if already executed inside WSL
    $wslProjectDir = "/home/$env:USERNAME/projects/Competitive-research"
}

Write-Host "Target WSL Distribution:     $distro" -ForegroundColor Cyan
Write-Host "Project Directory (WSL):     $wslProjectDir" -ForegroundColor Cyan

$command = "wsl.exe -d $distro bash -lic 'cd `"$wslProjectDir`" && bash src/run_daily_report.sh'"

Write-Host "`nRegistering scheduled task '$taskName'..." -ForegroundColor Yellow

# Use schtasks.exe to register the task
& schtasks.exe /create /tn $taskName /tr $command /sc daily /st $time /f

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] Scheduled task '$taskName' has been successfully registered!" -ForegroundColor Green
    Write-Host "Trigger: Daily at $time (and runs in background via WSL)" -ForegroundColor Green
} else {
    Write-Host "`n[ERROR] Failed to register task." -ForegroundColor Red
}
