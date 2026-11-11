<#
.SYNOPSIS
  Runs one command at a time across all agents and terminals on this PC.

.DESCRIPTION
  Building the Unreal project and running the game are heavy (several GB of RAM, all CPU cores).
  When several people or agents work in parallel, wrap every heavy command in this script so that
  they take turns instead of running together and thrashing the machine:

    powershell -NoProfile -ExecutionPolicy Bypass -File Tools\exclusive.ps1 -Command "& 'C:\...\Build.bat' InstagibArenaEditor Win64 Development ..."

  Light commands (git, reading files, editing) do not need it.

.PARAMETER Command
  The PowerShell command line to run once it is your turn.
.PARAMETER TimeoutMinutes
  How long to wait for your turn before giving up (default 90).
#>
param(
    [Parameter(Mandatory = $true)][string]$Command,
    [int]$TimeoutMinutes = 90
)

$mutex = New-Object System.Threading.Mutex($false, "Global\InstagibArenaHeavyJob")
$acquired = $false
try {
    Write-Host "[exclusive] waiting for my turn..."
    try {
        $acquired = $mutex.WaitOne([TimeSpan]::FromMinutes($TimeoutMinutes))
    } catch [System.Threading.AbandonedMutexException] {
        $acquired = $true   # the previous owner died; the lock is ours now
    }
    if (-not $acquired) {
        Write-Error "[exclusive] gave up waiting after $TimeoutMinutes minutes."
        exit 2
    }
    Write-Host "[exclusive] my turn, running."
    $global:LASTEXITCODE = 0
    Invoke-Expression $Command
    exit $LASTEXITCODE
}
finally {
    if ($acquired) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
