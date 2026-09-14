Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:Owner = 'io.electivus.workstation.installation'

function Invoke-Docker {
    param([string[]]$Arguments, [string]$Context)
    $dockerArguments = @()
    if ($Context) { $dockerArguments += @('--context', $Context) }
    $dockerArguments += $Arguments
    # PowerShell 5.1 turns stderr into ErrorRecords; keep successful warnings
    # separate from stdout so callers can parse the Docker JSON reliably.
    $stderr = [IO.Path]::GetTempFileName()
    try {
        $nativePreference = $ErrorActionPreference
        try {
            $ErrorActionPreference = 'Continue'
            $output = & docker @dockerArguments 2> $stderr
            $dockerExitCode = $LASTEXITCODE
        } finally { $ErrorActionPreference = $nativePreference }
        if ($dockerExitCode -ne 0) {
            $detail = Get-Content -LiteralPath $stderr -Raw
            throw "Docker failed ($dockerExitCode): $detail"
        }
        if (Test-Path -LiteralPath $stderr) {
            $warningText = Get-Content -LiteralPath $stderr -Raw
            if ($warningText) { Write-Verbose $warningText.Trim() }
        }
        return ($output -join "`n")
    } finally { Remove-Item -LiteralPath $stderr -Force }
}

function Read-Profile([string]$Directory) {
    $file = Join-Path $Directory 'profile.json'
    if (-not (Test-Path -LiteralPath $file)) { throw "No installation at $Directory. Run install first." }
    $profile = Get-Content -LiteralPath $file -Raw | ConvertFrom-Json
    if ($profile.schema -ne 1) { throw 'Unsupported installation profile schema.' }
    return $profile
}

function Get-OwnedContainer($Profile) {
    $id = Invoke-Docker -Context $Profile.dockerContext -Arguments @('container', 'ls', '--all', '--filter', "name=^/$($Profile.name)$", '--format', '{{.ID}}')
    if (-not $id) { return $null }
    $container = (Invoke-Docker -Context $Profile.dockerContext -Arguments @('container', 'inspect', $id) | ConvertFrom-Json)[0]
    $ownerProperty = if ($container.Config.Labels) { $container.Config.Labels.PSObject.Properties[$script:Owner] } else { $null }
    if (-not $ownerProperty -or $ownerProperty.Value -ne $Profile.installationId) {
        throw "Container $($Profile.name) belongs to another installation. Choose another name."
    }
    return $container
}

function Get-Engine($Profile) {
    $engine = Invoke-Docker -Context $Profile.dockerContext -Arguments @('info', '--format', '{{json .}}') | ConvertFrom-Json
    if ($engine.OSType -ne 'linux' -or $engine.Architecture -notin @('x86_64', 'amd64')) {
        throw 'This profile requires Docker Desktop with Linux amd64 containers.'
    }
    $backend = 'unknown'
    $settingsPath = if ($env:APPDATA) { Join-Path $env:APPDATA 'Docker/settings-store.json' } else { $null }
    if ($settingsPath -and (Test-Path -LiteralPath $settingsPath)) {
        $settings = Get-Content -LiteralPath $settingsPath -Raw | ConvertFrom-Json
        $vmm = $settings.PSObject.Properties['UseLibkrun']
        $wsl = $settings.PSObject.Properties['WslEngineEnabled']
        if ($vmm -and $vmm.Value) { $backend = 'VMM (Docker Desktop setting)' }
        elseif ($wsl -and $wsl.Value) { $backend = 'WSL2 (Docker Desktop setting)' }
        elseif ($wsl -and -not $wsl.Value) { $backend = 'Hyper-V (Docker Desktop setting; validate on destination)' }
    }
    return [ordered]@{ context = $Profile.dockerContext; os = $engine.OperatingSystem; kernel = $engine.KernelVersion; cpus = $engine.NCPU; memoryMiB = [math]::Floor($engine.MemTotal / 1MB); backend = $backend }
}

function Install-Workstation {
    param([string]$Directory, [string]$Name, [string]$Image, [int]$Port, [int]$MemoryMiB, [int]$Cpus, [switch]$NoShortcut)
    if (Test-Path -LiteralPath (Join-Path $Directory 'profile.json')) { throw 'This profile is already installed. Use start or another profile directory.' }
    $profile = [ordered]@{
        schema = 1; installationId = [guid]::NewGuid().ToString(); name = $Name
        image = $Image; port = $Port; memoryMiB = $MemoryMiB; cpus = $Cpus
        homeVolume = "$Name-home"; dockerContext = (Invoke-Docker -Arguments @('context', 'show'))
    }
    $context = (Invoke-Docker -Arguments @('context', 'inspect', $profile.dockerContext) | ConvertFrom-Json)[0]
    $endpoint = $context.Endpoints.docker.Host
    if ($endpoint -notmatch '^npipe:////\./pipe/' -and $endpoint -notmatch '^unix:///') {
        throw 'Choose a local Docker Desktop context. A remote daemon cannot provide the notebook-only desktop.'
    }
    $engine = Get-Engine ([pscustomobject]$profile)
    $null = Get-OwnedContainer ([pscustomobject]$profile)
    if ($MemoryMiB -gt $engine.memoryMiB -or $Cpus -gt $engine.cpus) {
        throw "Requested limits exceed the Docker VM ($($engine.memoryMiB) MiB, $($engine.cpus) CPUs). Adjust Docker Desktop or use -MemoryMiB/-Cpus."
    }
    $null = New-Item -ItemType Directory -Path $Directory -Force
    $toolsDirectory = Join-Path $Directory 'tools'
    $null = New-Item -ItemType Directory -Path $toolsDirectory -Force
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Workstation.ps1'), (Join-Path $PSScriptRoot 'Workstation.Core.psm1') -Destination $toolsDirectory
    $shortcutPath = $null
    if (-not $NoShortcut) {
        if ($env:OS -ne 'Windows_NT') { throw 'Windows shortcuts require Windows. Use -NoShortcut for CI.' }
        $shortcutPath = Join-Path $Directory 'Start Workstation.lnk'
        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = Join-Path $env:SystemRoot 'System32/WindowsPowerShell/v1.0/powershell.exe'
        $shortcut.Arguments = '-NoProfile -ExecutionPolicy RemoteSigned -File "' + (Join-Path $toolsDirectory 'Workstation.ps1') + '" start -ProfileDirectory "' + $Directory + '" -OpenBrowser'
        $shortcut.WorkingDirectory = $Directory
        $shortcut.Description = 'Start the local Electivus workstation'
        $shortcut.Save()
    }
    $profile | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $Directory 'profile.json') -Encoding UTF8
    return [ordered]@{ state = 'installed'; profile = $Directory; shortcut = $shortcutPath; url = "https://localhost:$Port/"; engine = $engine }
}

function Get-WorkstationStatus([string]$Directory) {
    $profile = Read-Profile $Directory
    $container = Get-OwnedContainer $profile
    $state = 'installed'; $healthy = $false; $id = $null; $imageId = $null; $version = $null; $baseDigest = $null
    if ($container) {
        $state = if ($container.State.Running) { 'running' } else { 'stopped' }
        $healthy = $container.State.Running -and $container.State.PSObject.Properties['Health'] -and $container.State.Health.Status -eq 'healthy'
        $id = $container.Id
        $imageId = $container.Image
        $version = $container.Config.Labels.'org.opencontainers.image.version'
        $baseDigest = $container.Config.Labels.'org.opencontainers.image.base.digest'
    }
    return [ordered]@{
        state = $state; healthy = [bool]$healthy; container = $profile.name; containerId = $id
        homeVolume = $profile.homeVolume; image = $profile.image; imageId = $imageId; version = $version; upstreamDigest = $baseDigest
        url = "https://localhost:$($profile.port)/"; engine = (Get-Engine $profile)
        limits = @{ memoryMiB = $profile.memoryMiB; cpus = $profile.cpus }
    }
}

function Start-Workstation {
    param([string]$Directory, [switch]$OpenBrowser)
    $profile = Read-Profile $Directory
    $engine = Get-Engine $profile
    if ($profile.memoryMiB -gt $engine.memoryMiB -or $profile.cpus -gt $engine.cpus) { throw 'Profile resources exceed the current Docker VM allocation.' }
    $container = Get-OwnedContainer $profile
    if (-not $container) {
        $images = Invoke-Docker -Context $profile.dockerContext -Arguments @('image', 'ls', '--quiet', $profile.image)
        if (-not $images) {
            Write-Host "Downloading $($profile.image)..."
            $null = Invoke-Docker -Context $profile.dockerContext -Arguments @('pull', '--platform', 'linux/amd64', $profile.image)
        }
        $image = (Invoke-Docker -Context $profile.dockerContext -Arguments @('image', 'inspect', $profile.image) | ConvertFrom-Json)[0]
        $variant = if ($image.Config.Labels) { $image.Config.Labels.PSObject.Properties['io.electivus.workstation.variant'] } else { $null }
        if ($image.Os -ne 'linux' -or $image.Architecture -ne 'amd64' -or -not $variant -or $variant.Value -notin @('base', 'salesforce')) {
            throw 'The selected image is not an Electivus Linux amd64 workstation.'
        }
        $volumeName = Invoke-Docker -Context $profile.dockerContext -Arguments @('volume', 'ls', '--quiet', '--filter', "name=^$($profile.homeVolume)$")
        if ($volumeName) {
            $volume = (Invoke-Docker -Context $profile.dockerContext -Arguments @('volume', 'inspect', $volumeName) | ConvertFrom-Json)[0]
            $volumeOwner = if ($volume.Labels) { $volume.Labels.PSObject.Properties[$script:Owner] } else { $null }
            if (-not $volumeOwner -or $volumeOwner.Value -ne $profile.installationId) { throw 'The home volume belongs to another installation.' }
        } else {
            $null = Invoke-Docker -Context $profile.dockerContext -Arguments @('volume', 'create', '--label', "$script:Owner=$($profile.installationId)", $profile.homeVolume)
        }
        $null = Invoke-Docker -Context $profile.dockerContext -Arguments @(
            'run', '--detach', '--name', $profile.name, '--platform', 'linux/amd64', '--restart', 'no',
            '--label', "$script:Owner=$($profile.installationId)",
            '--publish', "127.0.0.1:$($profile.port):3001/tcp", '--mount', "type=volume,src=$($profile.homeVolume),dst=/config",
            '--memory', "$($profile.memoryMiB)m", '--cpus', "$($profile.cpus)", '--shm-size', '1g',
            '--env', 'PUID=1000', '--env', 'PGID=1000', $profile.image
        )
    } elseif (-not $container.State.Running) {
        $null = Invoke-Docker -Context $profile.dockerContext -Arguments @('container', 'start', $profile.name)
    }
    $deadline = [DateTime]::UtcNow.AddMinutes(4)
    do {
        $container = Get-OwnedContainer $profile
        if (-not $container.State.Running) { throw "Desktop stopped during startup. Inspect: docker --context $($profile.dockerContext) logs $($profile.name)" }
        if ($container.State.PSObject.Properties['Health'] -and $container.State.Health.Status -eq 'healthy') {
            if ($OpenBrowser) { Start-Process "https://localhost:$($profile.port)/" }
            return Get-WorkstationStatus $Directory
        }
        Start-Sleep -Seconds 2
    } while ([DateTime]::UtcNow -lt $deadline)
    throw "Desktop did not become healthy in four minutes. Inspect: docker --context $($profile.dockerContext) logs $($profile.name)"
}

function Stop-Workstation([string]$Directory) {
    $profile = Read-Profile $Directory
    $container = Get-OwnedContainer $profile
    if ($container -and $container.State.Running) {
        $null = Invoke-Docker -Context $profile.dockerContext -Arguments @('container', 'stop', '--time', '30', $profile.name)
    }
    return Get-WorkstationStatus $Directory
}

function Get-WorkstationCertificate([string]$Directory) {
    $profile = Read-Profile $Directory
    $container = Get-OwnedContainer $profile
    if (-not $container) { throw 'Start the workstation once to generate its local certificate.' }
    $file = Join-Path $Directory 'localhost.crt'
    $null = Invoke-Docker -Context $profile.dockerContext -Arguments @('cp', "$($profile.name):/config/ssl/cert.pem", $file)
    $certificate = New-Object Security.Cryptography.X509Certificates.X509Certificate2($file)
    $hash = [Security.Cryptography.SHA256]::Create()
    try { $sha256 = ([BitConverter]::ToString($hash.ComputeHash($certificate.RawData))).Replace('-', '') }
    finally { $hash.Dispose() }
    return [ordered]@{ file = $file; dnsName = $certificate.GetNameInfo([Security.Cryptography.X509Certificates.X509NameType]::DnsName, $false); subject = $certificate.Subject; thumbprint = $certificate.Thumbprint; sha256 = $sha256; expires = $certificate.NotAfter.ToUniversalTime().ToString('o') }
}

function Add-WorkstationCertificateTrust([string]$Directory) {
    if ($env:OS -ne 'Windows_NT') { throw 'The trust command installs the localhost certificate for the current Windows user.' }
    $details = Get-WorkstationCertificate $Directory
    $certificate = New-Object Security.Cryptography.X509Certificates.X509Certificate2($details.file)
    $constraints = @($certificate.Extensions | Where-Object { $_.Oid.Value -eq '2.5.29.19' })
    $alternativeNames = @($certificate.Extensions | Where-Object { $_.Oid.Value -eq '2.5.29.17' })
    # DER for exactly DNS:localhost and IP:127.0.0.1, with no additional names.
    $localhostNames = 'MBGCCWxvY2FsaG9zdIcEfwAAAQ=='
    if ($certificate.Subject -ne 'CN=localhost' -or $certificate.Issuer -ne 'CN=localhost' -or $details.dnsName -ne 'localhost' -or $constraints.Count -ne 1 -or $constraints[0].CertificateAuthority -or $alternativeNames.Count -ne 1 -or [Convert]::ToBase64String($alternativeNames[0].RawData) -ne $localhostNames -or $certificate.NotAfter -le [DateTime]::Now) {
        throw 'Refusing to trust a certificate that is not the installation localhost leaf.'
    }
    $store = New-Object Security.Cryptography.X509Certificates.X509Store('Root', 'CurrentUser')
    try { $store.Open('ReadWrite'); $store.Add($certificate) }
    finally { $store.Close() }
    return [ordered]@{ state = 'trusted'; store = 'CurrentUser/Root'; certificate = $details }
}

function Remove-WorkstationCertificateTrust([string]$Directory) {
    if ($env:OS -ne 'Windows_NT') { throw 'The untrust command removes the installation certificate for the current Windows user.' }
    $details = Get-WorkstationCertificate $Directory
    $certificate = New-Object Security.Cryptography.X509Certificates.X509Certificate2($details.file)
    $store = New-Object Security.Cryptography.X509Certificates.X509Store('Root', 'CurrentUser')
    try { $store.Open('ReadWrite'); $store.Remove($certificate) }
    finally { $store.Close() }
    return [ordered]@{ state = 'untrusted'; store = 'CurrentUser/Root'; certificate = $details }
}

Export-ModuleMember -Function Install-Workstation, Start-Workstation, Stop-Workstation, Get-WorkstationStatus, Get-WorkstationCertificate, Add-WorkstationCertificateTrust, Remove-WorkstationCertificateTrust
