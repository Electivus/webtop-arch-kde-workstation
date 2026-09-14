# Requires Windows, Chrome and the installed playwright-cli.
[CmdletBinding()]
param([Parameter(Mandatory)][string]$ProfileDirectory)
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$cli = Join-Path $repo 'scripts/Workstation.ps1'
$ProfileDirectory = [IO.Path]::GetFullPath($ProfileDirectory)
$status = & $cli status -ProfileDirectory $ProfileDirectory | ConvertFrom-Json
if ($status.container -notmatch '^ew-test-' -or -not $status.healthy) {
    throw 'Use the running dedicated installation created by Test-Lifecycle.ps1 -KeepResources.'
}
$session = 'ew-browser-' + [guid]::NewGuid().ToString('N').Substring(0, 8)
$savedEndpoint = $env:PLAYWRIGHT_MCP_CDP_ENDPOINT
$certificate = & $cli certificate -ProfileDirectory $ProfileDirectory | ConvertFrom-Json
$trustedBefore = Test-Path -LiteralPath "Cert:/CurrentUser/Root/$($certificate.thumbprint)"
function Invoke-Browser([string[]]$BrowserArguments) {
    $output = & playwright-cli "-s=$session" @BrowserArguments
    if ($LASTEXITCODE -ne 0) { throw "Browser command failed: $output" }
    $output | Add-Content -LiteralPath (Join-Path $ProfileDirectory 'browser.log') -Encoding utf8
}
Push-Location $repo
try {
    $null = & $cli trust -ProfileDirectory $ProfileDirectory
    # Isolate this test from any globally configured personal browser endpoint.
    $env:PLAYWRIGHT_MCP_CDP_ENDPOINT = $null
    Invoke-Browser @('open', $status.url, '--browser=chrome')
    Invoke-Browser @('run-code', '--filename=tests/Browser-Session.js')
    $typed = docker exec --user abc $status.container cat /config/t01-typing.txt
    if ($LASTEXITCODE -ne 0 -or $typed -ne 'ação ç áéíóú ãõ ê ü @ / ? |') { throw "Keyboard round trip failed: $typed" }
    $probe = @'
set -eu
task_pid=$(cat /config/t01-task.pid)
kill -0 "$task_pid"
test "$(ps -p "$task_pid" -o lstart=)" = "$(cat /config/t01-task.start)"
before=$(cat /config/t01-task.tick)
sleep 2
after=$(cat /config/t01-task.tick)
test "$after" -gt "$before"
printf 'pid=%s before=%s after=%s\n' "$task_pid" "$before" "$after"
'@
    $task = docker exec --user abc $status.container bash -c $probe
    if ($LASTEXITCODE -ne 0) { throw 'The original terminal task did not survive closing and reopening the browser tab.' }
    $result = [ordered]@{ test = 'desktop-browser'; result = 'passed'; typed = $typed; task = $task; status = $status; screenshots = @('.local/t01-before-disconnect.png', '.local/t01-after-reconnect.png') }
} finally {
    & playwright-cli "-s=$session" close | Out-Null
    $env:PLAYWRIGHT_MCP_CDP_ENDPOINT = $savedEndpoint
    if (-not $trustedBefore) { $null = & $cli untrust -ProfileDirectory $ProfileDirectory }
    Pop-Location
}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $ProfileDirectory 'browser-result.json') -Encoding utf8
$result | ConvertTo-Json -Depth 8
