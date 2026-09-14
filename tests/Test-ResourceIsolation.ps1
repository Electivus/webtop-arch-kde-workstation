[CmdletBinding()]
param([string]$Image = 'electivus/webtop-arch-kde-base:t01')
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$cli = Join-Path $repo 'scripts/Workstation.ps1'
$testId = 'ew-isolation-' + [guid]::NewGuid().ToString('N').Substring(0, 8)
$directory = Join-Path $repo ".local/$testId"
$containerName = "$testId-container"
$volumeName = "$testId-volume-home"
try {
    $containerId = docker create --name $containerName --entrypoint /bin/true $Image
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the isolated foreign-container fixture.' }
    $refused = $false
    try {
        $null = & $cli install -ProfileDirectory "$directory/container" -Name $containerName -Image $Image -MemoryMiB 2048 -Cpus 2 -NoShortcut
    } catch {
        if ($_.Exception.Message -notlike '*belongs to another installation*') { throw }
        $refused = $true
    }
    if (-not $refused) { throw 'Installation accepted a container owned by someone else.' }
    $stillPresent = docker inspect --format '{{.Id}}' $containerName
    if ($LASTEXITCODE -ne 0 -or $stillPresent -ne $containerId) { throw 'The foreign container was modified.' }

    $null = docker volume create $volumeName
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the isolated foreign-volume fixture.' }
    $volumeBefore = docker volume inspect $volumeName
    $null = & $cli install -ProfileDirectory "$directory/volume" -Name "$testId-volume" -Image $Image -MemoryMiB 2048 -Cpus 2 -NoShortcut
    $refused = $false
    try { $null = & $cli start -ProfileDirectory "$directory/volume" }
    catch {
        if ($_.Exception.Message -notlike '*volume belongs to another installation*') { throw }
        $refused = $true
    }
    if (-not $refused) { throw 'Startup accepted a volume owned by someone else.' }
    $volumeAfter = docker volume inspect $volumeName
    if ($LASTEXITCODE -ne 0 -or ($volumeAfter -join "`n") -ne ($volumeBefore -join "`n")) { throw 'The foreign volume was modified.' }
    @{ test = 'resource-isolation'; result = 'passed' } | ConvertTo-Json
} finally {
    docker container rm $containerName 2>$null | Out-Null
    docker volume rm $volumeName 2>$null | Out-Null
}
