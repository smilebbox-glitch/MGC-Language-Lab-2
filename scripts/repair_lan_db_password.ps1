param(
    [string]$EnvFile = ".env.lan",
    [string]$ComposeFile = "docker-compose.lan.yml"
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

function Get-EnvValue([string]$Path, [string]$Key) {
    if (-not (Test-Path -LiteralPath $Path)) { return "" }
    $line = Get-Content -LiteralPath $Path |
        Where-Object { $_ -match ("^\s*" + [Regex]::Escape($Key) + "\s*=") } |
        Select-Object -Last 1
    if (-not $line) { return "" }
    return (($line -split "=", 2)[1]).Trim().Trim('"').Trim("'")
}

$EnvPath = if ([IO.Path]::IsPathRooted($EnvFile)) { $EnvFile } else { Join-Path $Root $EnvFile }
$ComposePath = if ([IO.Path]::IsPathRooted($ComposeFile)) { $ComposeFile } else { Join-Path $Root $ComposeFile }

if (-not (Test-Path -LiteralPath $EnvPath)) {
    throw "LAN environment file not found: $EnvPath"
}
if (-not (Test-Path -LiteralPath $ComposePath)) {
    throw "LAN compose file not found: $ComposePath"
}

$DbUser = Get-EnvValue $EnvPath "POSTGRES_USER"
$DbName = Get-EnvValue $EnvPath "POSTGRES_DB"
$DbPassword = Get-EnvValue $EnvPath "POSTGRES_PASSWORD"
if ([string]::IsNullOrWhiteSpace($DbUser)) { $DbUser = "mgc_languages" }
if ([string]::IsNullOrWhiteSpace($DbName)) { $DbName = "mgc_languages" }
if ([string]::IsNullOrWhiteSpace($DbPassword)) {
    throw "POSTGRES_PASSWORD is missing from $EnvPath"
}

$ComposeArgs = @("compose", "--env-file", $EnvPath, "-f", $ComposePath)

Write-Host "Checking persistent PostgreSQL credentials..." -ForegroundColor DarkGray
& docker @ComposeArgs up -d db
if ($LASTEXITCODE -ne 0) {
    throw "Unable to start the LAN PostgreSQL service for credential reconciliation."
}

$Ready = $false
$Deadline = (Get-Date).AddSeconds(90)
while ((Get-Date) -lt $Deadline) {
    & docker @ComposeArgs exec -T db pg_isready -U $DbUser -d $DbName *> $null
    if ($LASTEXITCODE -eq 0) {
        $Ready = $true
        break
    }
    Start-Sleep -Seconds 2
}
if (-not $Ready) {
    throw "PostgreSQL did not become ready for credential reconciliation."
}

# The official PostgreSQL image keeps local Unix-socket access available to the
# bootstrap database role. Re-apply the password from the current .env.lan so a
# persistent volume created by an older folder/config remains usable. This does
# not drop the database, recreate the volume, or modify application data.
$EscapedUser = $DbUser.Replace('"', '""')
$EscapedPassword = $DbPassword.Replace("'", "''")
$Sql = "ALTER ROLE `"$EscapedUser`" WITH PASSWORD '$EscapedPassword';"
$Sql | & docker @ComposeArgs exec -T db psql -v ON_ERROR_STOP=1 -U $DbUser -d $DbName
if ($LASTEXITCODE -ne 0) {
    throw "Unable to reconcile the PostgreSQL role password with the current .env.lan. Existing data was left untouched."
}

# Verify the exact TCP authentication path used by SQLAlchemy/app containers.
& docker @ComposeArgs exec -T -e "PGPASSWORD=$DbPassword" db psql -h 127.0.0.1 -U $DbUser -d $DbName -v ON_ERROR_STOP=1 -tAc "SELECT 1" *> $null
if ($LASTEXITCODE -ne 0) {
    throw "PostgreSQL password reconciliation completed but TCP authentication still failed."
}

Write-Host "PostgreSQL credentials: synchronized with current .env.lan" -ForegroundColor Green
