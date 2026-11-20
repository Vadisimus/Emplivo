#Requires -Version 5.1
[CmdletBinding()]
param(
    [string] $Repository = '.',
    [string] $Archive,
    [string] $WorkerOrigin,
    [string] $TurnstileSiteKey,
    [switch] $Push
)

$ErrorActionPreference = 'Stop'
$branch = 'refactor/modernization'
$git = (Get-Command git -CommandType Application | Select-Object -First 1).Source
$repo = (Resolve-Path -LiteralPath $Repository).Path
$archivePath = if ($Archive) { (Resolve-Path -LiteralPath $Archive).Path }
$temporary = $null

function Invoke-Git {
    & $git -C $repo @args
    if ($LASTEXITCODE -ne 0) {
        throw "Git stopped (exit $LASTEXITCODE). See its message above."
    }
}

try {
    $null = Invoke-Git rev-parse --show-toplevel
    if (Invoke-Git status --porcelain --untracked-files=no) {
        throw 'Commit or stash your tracked changes before importing the modernization branch.'
    }
    if ([bool] $WorkerOrigin -ne [bool] $TurnstileSiteKey) {
        throw 'Set both -WorkerOrigin and -TurnstileSiteKey, or leave both empty.'
    }
    Invoke-Git fetch origin main
    if ($archivePath) {
        $temporary = Join-Path ([IO.Path]::GetTempPath()) ('emplivo-source-' + [Guid]::NewGuid().ToString('N'))
        Expand-Archive -LiteralPath $archivePath -DestinationPath $temporary
        $bundle = Join-Path $temporary 'modernization.bundle'
        Invoke-Git bundle verify $bundle
        Invoke-Git fetch $bundle "refs/heads/$branch"
    } else {
        Invoke-Git fetch origin "refs/heads/$branch"
    }
    $import = Invoke-Git rev-parse FETCH_HEAD

    & $git -C $repo show-ref --verify --quiet "refs/heads/$branch"
    if ($LASTEXITCODE -eq 0) {
        Invoke-Git switch $branch
        Invoke-Git merge --ff-only $import
    } else {
        Invoke-Git switch -c $branch $import
    }

    if ($WorkerOrigin) {
        Push-Location -LiteralPath $repo
        try {
            $pythonCommand = Get-Command py -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
            $options = @('tools/configure_intake.py', '--worker-origin', $WorkerOrigin, '--site-key', $TurnstileSiteKey)
            if ($pythonCommand) {
                & $pythonCommand.Source -3 @options
            } else {
                $pythonCommand = Get-Command python -CommandType Application | Select-Object -First 1
                & $pythonCommand.Source @options
            }
            if ($LASTEXITCODE -ne 0) { throw 'Could not configure the public form settings.' }
        } finally {
            Pop-Location
        }
        if (Invoke-Git status --porcelain -- intake-config.mjs) {
            Invoke-Git add -- intake-config.mjs CHECKSUMS.json
            Invoke-Git commit -m 'Configure the public Emplivo intake endpoint'
        }
    }

    if ($Push) { Invoke-Git push --set-upstream origin $branch }
    Invoke-Git log -5 --oneline
} finally {
    if ($temporary -and (Test-Path -LiteralPath $temporary)) {
        Remove-Item -LiteralPath $temporary -Recurse -Force
    }
}
