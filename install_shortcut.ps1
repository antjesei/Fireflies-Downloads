# Einmalig ausfuehren: legt Desktop-Verknuepfungen an.
# Ausfuehren: Rechtsklick -> "Mit PowerShell ausfuehren"
# Falls Execution Policy meckert:
#   powershell -ExecutionPolicy Bypass -File install_shortcut.ps1

$ErrorActionPreference = "Stop"

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runBat = Join-Path $projectDir "run.bat"

if (-not (Test-Path $runBat)) {
    Write-Error "run.bat nicht gefunden unter $runBat"
    exit 1
}

$desktop = [Environment]::GetFolderPath("Desktop")
$wsh = New-Object -ComObject WScript.Shell

function New-Shortcut {
    param(
        [string]$Name,
        [string]$Arguments,
        [string]$Description
    )
    $lnkPath = Join-Path $desktop "$Name.lnk"
    $sc = $wsh.CreateShortcut($lnkPath)
    $sc.TargetPath = $runBat
    $sc.Arguments = $Arguments
    $sc.WorkingDirectory = $projectDir
    $sc.Description = $Description
    $sc.IconLocation = "imageres.dll,3"
    $sc.Save()
    Write-Host "[ok] $lnkPath"
}

New-Shortcut -Name "Fireflies abrufen" -Arguments "" -Description "Fireflies - interaktiver Download"
New-Shortcut -Name "Fireflies - letzte 24h" -Arguments "--last 24h" -Description "Fireflies - alle Meetings der letzten 24h"

Write-Host ""
Write-Host "Verknuepfungen auf dem Desktop erstellt."
