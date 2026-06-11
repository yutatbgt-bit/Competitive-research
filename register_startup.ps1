$workDir = "C:\Users\yutat\Documents\antigravity\agitated-galileo"
$scriptPath = Join-Path $workDir "run_daily_report.ps1"
$registryPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$valueName = "IkariCompetitiveReportAutoRunner"
$command = "powershell.exe -NoProfile -WindowStyle Hidden -File `"$scriptPath`""

# Register startup command in Registry HKCU\Run
Set-ItemProperty -Path $registryPath -Name $valueName -Value $command

Write-Output "Startup registry entry added successfully!"
