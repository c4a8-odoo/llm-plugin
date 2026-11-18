<#
.SYNOPSIS
  Thin PowerShell wrapper around automation.py (the real implementation).
  Usage is identical, e.g.:
    powershell -NoProfile -File automation.ps1 check-scope --version 19.0 --repo partner-contact --module partner_firstname
#>
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $python) { Write-Error 'python not found on PATH; install Python 3 to use the automation helper'; exit 3 }
& $python.Source (Join-Path $PSScriptRoot 'automation.py') @args
exit $LASTEXITCODE
