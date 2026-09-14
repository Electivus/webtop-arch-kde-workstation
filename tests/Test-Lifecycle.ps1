# Run against a locally built image, using disposable resources only.
[CmdletBinding()]
param(
    [string]$Image = 'electivus/webtop-arch-kde-base:t01',
    [int]$Port = 13401,
    [int]$MemoryMiB = 2560,
    [int]$Cpus = 2,
    [switch]$KeepResources
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repo = Split-Path $PSScriptRoot -Parent
$cli = Join-Path $repo 'scripts/Workstation.ps1'
$testId = 'ew-test-' + [guid]::NewGuid().ToString('N').Substring(0, 10)
$testDirectory = Join-Path $repo ".local/$testId"
$testResult = $null
function Assert-That($Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}
try {
    $installed = & $cli install -ProfileDirectory $testDirectory -Name $testId -Image $Image -Port $Port -MemoryMiB $MemoryMiB -Cpus $Cpus -NoShortcut | ConvertFrom-Json
    Assert-That ($installed.state -eq 'installed') 'The install command must prepare a profile.'
    $started = & $cli start -ProfileDirectory $testDirectory | ConvertFrom-Json
    Assert-That ($started.state -eq 'running' -and $started.healthy) 'The start command must reach a healthy desktop.'
    $endpoint = Invoke-WebRequest -Uri "http://127.0.0.1:$Port" -MaximumRedirection 0 -SkipHttpErrorCheck
    Assert-That ($endpoint.StatusCode -eq 400) 'The published port must require HTTPS.'
    $info = docker inspect $started.container | ConvertFrom-Json
    Assert-That ($LASTEXITCODE -eq 0) 'Container inspection failed.'
    $bindings = @($info[0].NetworkSettings.Ports.'3001/tcp')
    Assert-That ($bindings.Count -eq 1 -and $bindings[0].HostIp -eq '127.0.0.1') 'The desktop must bind only to IPv4 loopback.'
    $auth = docker exec $started.container curl --fail --silent --output /dev/null --write-out '%{http_code}' http://127.0.0.1:3000/
    Assert-That ($LASTEXITCODE -eq 0 -and $auth -eq '200') 'Desktop entry must not require another password.'
    $locale = docker exec --user abc $started.container locale
    Assert-That ($LASTEXITCODE -eq 0 -and $locale -contains 'LANG=en_US.UTF-8' -and $locale -contains 'LC_TIME=pt_BR.UTF-8') 'The shell must use English messages and Brazilian formats.'
    $timezone = docker exec $started.container date '+%Z,%z'
    Assert-That ($LASTEXITCODE -eq 0 -and $timezone -eq '-03,-0300') 'The workstation clock must use the Bahia UTC offset.'
    $certificate = & $cli certificate -ProfileDirectory $testDirectory | ConvertFrom-Json
    Assert-That ($certificate.dnsName -eq 'localhost' -and $certificate.sha256.Length -eq 64) 'The local certificate must identify localhost and have a verifiable fingerprint.'
    $same = & $cli start -ProfileDirectory $testDirectory | ConvertFrom-Json
    Assert-That ($same.containerId -eq $started.containerId) 'Starting an already running workstation must keep the session.'
    $stopped = & $cli stop -ProfileDirectory $testDirectory | ConvertFrom-Json
    Assert-That ($stopped.state -eq 'stopped') 'Stop must end execution.'
    $restarted = & $cli start -ProfileDirectory $testDirectory | ConvertFrom-Json
    Assert-That ($restarted.healthy -and $restarted.containerId -eq $started.containerId) 'Start must reuse the stopped workstation.'
    $testResult = [ordered]@{ test = 'lifecycle'; result = 'passed'; profile = $testDirectory; status = $restarted }
    $testResult | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $testDirectory 'lifecycle-result.json') -Encoding utf8
    $testResult | ConvertTo-Json -Depth 8
} finally {
    if (-not $KeepResources) {
        # Names are generated in this process; never enumerate or delete other resources.
        docker container rm --force $testId 2>$null | Out-Null
        docker volume rm "$testId-home" 2>$null | Out-Null
    }
}
