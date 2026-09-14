#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0)]
    [ValidateSet('install', 'start', 'stop', 'status', 'certificate', 'trust', 'untrust')]
    [string]$Command,
    [string]$ProfileDirectory = (Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'Electivus/Workstation/base'),
    [ValidatePattern('^[a-z][a-z0-9-]{2,47}$')][string]$Name = 'electivus-workstation-base',
    [string]$Image = 'electivus/webtop-arch-kde-base:stable',
    [ValidateRange(1024, 65535)][int]$Port = 3001,
    [ValidateRange(1024, 65536)][int]$MemoryMiB = 6144,
    [ValidateRange(1, 64)][int]$Cpus = 4,
    [switch]$NoShortcut,
    [switch]$OpenBrowser
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Import-Module (Join-Path $PSScriptRoot 'Workstation.Core.psm1') -Force
$profilePath = [IO.Path]::GetFullPath($ProfileDirectory)
switch ($Command) {
    'install' { $result = Install-Workstation -Directory $profilePath -Name $Name -Image $Image -Port $Port -MemoryMiB $MemoryMiB -Cpus $Cpus -NoShortcut:$NoShortcut }
    'start' { $result = Start-Workstation -Directory $profilePath -OpenBrowser:$OpenBrowser }
    'stop' { $result = Stop-Workstation -Directory $profilePath }
    'status' { $result = Get-WorkstationStatus -Directory $profilePath }
    'certificate' { $result = Get-WorkstationCertificate -Directory $profilePath }
    'trust' { $result = Add-WorkstationCertificateTrust -Directory $profilePath }
    'untrust' { $result = Remove-WorkstationCertificateTrust -Directory $profilePath }
}
$result | ConvertTo-Json -Depth 10
