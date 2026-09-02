# Windows Task Scheduler Unregistration Script for Ikari Competitive Research

$taskName = "IkariCompetitiveReportDailyRunner"

Write-Host "Unregistering scheduled task '$taskName'..." -ForegroundColor Yellow

& schtasks.exe /delete /tn $taskName /f

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] Scheduled task '$taskName' has been successfully removed." -ForegroundColor Green
} else {
    Write-Host "`n[INFO] Task '$taskName' does not exist or has already been removed." -ForegroundColor Yellow
}
