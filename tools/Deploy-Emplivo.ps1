#Requires -Version 5.1
[CmdletBinding()]
param(
    [string] $IdentityFile
)

$ErrorActionPreference = 'Stop'
$ssh = (Get-Command ssh -CommandType Application | Select-Object -First 1).Source
$scp = (Get-Command scp -CommandType Application | Select-Object -First 1).Source
$destination = 'emplivo@emplivo.ftp.tools'
$siteDirectory = '/home/emplivo/emplivo.com.ua'
$archive = Join-Path $PSScriptRoot 'emplivo-design-release.zip'
$checksum = Join-Path $PSScriptRoot 'emplivo-design-release.zip.sha256'

$expected = ((Get-Content -LiteralPath $checksum -TotalCount 1) -split '\s+')[0]
if ($expected -notmatch '^[a-fA-F0-9]{64}$' -or (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $expected) {
    throw 'The release ZIP does not match its SHA-256 checksum.'
}

$sshOptions = @('-o', 'ConnectTimeout=15', '-o', 'IdentitiesOnly=yes', '-o', 'StrictHostKeyChecking=yes')
if ($IdentityFile) {
    $keyPath = (Resolve-Path -LiteralPath $IdentityFile).Path
    $sshOptions += @('-i', $keyPath)
}

Write-Host 'Connecting to Emplivo hosting...'
$stageId = [Guid]::NewGuid().ToString('N')
$stage = "$siteDirectory/.design-$stageId"
$confirmation = "EMPLIVO_STAGE_READY=$stageId"
$createStage = "umask 077 && mkdir -- '$stage' && printf '%s\n' '$confirmation'"
$stageOutput = & $ssh @sshOptions $destination $createStage
$stageExit = $LASTEXITCODE
$stageLines = @($stageOutput | ForEach-Object { ([string] $_).Trim() })
if ($stageExit -ne 0 -or $stageLines -notcontains $confirmation) {
    $stageLines | ForEach-Object { Write-Host $_ }
    if ($stageExit -eq 255) {
        throw 'SSH connection or authentication failed (exit 255). See the SSH message above.'
    }
    throw "The hosting server did not confirm creation of $stage (SSH exit $stageExit). See the server message above."
}

Write-Host 'Uploading the design release...'
& $scp @sshOptions $archive "${destination}:$stage/release.zip"
if ($LASTEXITCODE -ne 0) {
    throw "SCP upload failed. Staging directory: $stage"
}

Write-Host 'Creating a backup, installing the design and checking the website...'
$checkLine = "$($expected.ToLowerInvariant())  release.zip"
$install = "umask 077 && cd '$stage' && echo '$checkLine' | sha256sum -c - && unzip -q release.zip && bash deploy.sh"
& $ssh @sshOptions $destination $install
if ($LASTEXITCODE -ne 0) {
    throw "Check the deployment output above. Staging directory: $stage"
}

& $ssh @sshOptions $destination "rm -rf -- '$stage'"
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Deployment succeeded. Could not clean up the staging directory: $stage"
}
