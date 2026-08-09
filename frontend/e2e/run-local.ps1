$ErrorActionPreference = "Stop"

$frontendDirectory = Split-Path $PSScriptRoot -Parent
$projectDirectory = Split-Path $frontendDirectory -Parent
$backendDirectory = Join-Path $projectDirectory "backend"
$testResultsDirectory = Join-Path $frontendDirectory "test-results"
$backendPort = 8100
$frontendPort = 3100

foreach ($port in @($backendPort, $frontendPort)) {
    if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) {
        throw "Port $port is already in use. Stop the existing service or choose another port."
    }
}

$testDatabaseLine = Get-Content -LiteralPath (Join-Path $backendDirectory ".env") -Encoding UTF8 |
    Where-Object { $_ -like "TEST_DATABASE_URL=*" } |
    Select-Object -First 1
if (-not $testDatabaseLine) {
    throw "TEST_DATABASE_URL is missing from backend/.env"
}

$testDatabaseUrl = $testDatabaseLine.Substring("TEST_DATABASE_URL=".Length)
$runId = [guid]::NewGuid().ToString("N").Substring(0, 12)
$env:E2E_FAMILY_LOGIN_NAME = "e2e-family-$runId"
$env:E2E_OWNER_LOGIN_NAME = "e2e-owner-$runId"
$env:E2E_FAMILY_PASSWORD = [guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N")
$env:E2E_OWNER_PASSWORD = [guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N")
$env:E2E_BASE_URL = "http://127.0.0.1:$frontendPort"
$env:APP_ENV = "test"
$env:APP_ORIGIN = $env:E2E_BASE_URL
$env:DATABASE_URL = $testDatabaseUrl

New-Item -ItemType Directory -Path $testResultsDirectory -Force | Out-Null
$backendOutput = Join-Path $testResultsDirectory "backend.out.log"
$backendError = Join-Path $testResultsDirectory "backend.err.log"
$frontendOutput = Join-Path $testResultsDirectory "frontend.out.log"
$frontendError = Join-Path $testResultsDirectory "frontend.err.log"
$backendJob = $null
$frontendJob = $null
$exitCode = 1

try {
    Push-Location $backendDirectory
    & ".\.venv\Scripts\python.exe" "scripts\prepare_e2e.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to prepare E2E accounts"
    }

    $backendJob = Start-Job -ScriptBlock {
        param($directory, $port, $outputPath, $errorPath)
        Set-Location $directory
        & ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port $port 1> $outputPath 2> $errorPath
    } -ArgumentList $backendDirectory, $backendPort, $backendOutput, $backendError
    Pop-Location

    Remove-Item Env:DATABASE_URL
    $env:BACKEND_API_ORIGIN = "http://127.0.0.1:$backendPort"
    $frontendJob = Start-Job -ScriptBlock {
        param($directory, $port, $outputPath, $errorPath)
        Set-Location $directory
        & npm.cmd run dev -- --hostname 127.0.0.1 --port $port 1> $outputPath 2> $errorPath
    } -ArgumentList $frontendDirectory, $frontendPort, $frontendOutput, $frontendError

    $backendReady = $false
    $frontendReady = $false
    for ($attempt = 0; $attempt -lt 90; $attempt++) {
        if (-not $backendReady) {
            try {
                $backendReady = (Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$backendPort/api/v1/health" -TimeoutSec 2).StatusCode -eq 200
            } catch {}
        }
        if (-not $frontendReady) {
            try {
                $frontendReady = (Invoke-WebRequest -UseBasicParsing -Uri $env:E2E_BASE_URL -TimeoutSec 3).StatusCode -eq 200
            } catch {}
        }
        if ($backendReady -and $frontendReady) {
            break
        }
        Start-Sleep -Seconds 1
    }
    if (-not $backendReady -or -not $frontendReady) {
        throw "E2E services did not become ready"
    }

    Push-Location $frontendDirectory
    & npm.cmd run test:e2e
    $exitCode = $LASTEXITCODE
    Pop-Location
} catch {
    Write-Error $_
    Write-Output "Backend errors:"
    Get-Content -LiteralPath $backendError -ErrorAction SilentlyContinue | Select-Object -Last 40
    Write-Output "Frontend errors:"
    Get-Content -LiteralPath $frontendError -ErrorAction SilentlyContinue | Select-Object -Last 40
    $exitCode = 1
} finally {
    foreach ($port in @($frontendPort, $backendPort)) {
        Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue |
            ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    }
    foreach ($job in @($frontendJob, $backendJob)) {
        if ($null -ne $job) {
            Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
        }
    }
    foreach ($name in @(
        "E2E_FAMILY_LOGIN_NAME",
        "E2E_OWNER_LOGIN_NAME",
        "E2E_FAMILY_PASSWORD",
        "E2E_OWNER_PASSWORD",
        "E2E_BASE_URL",
        "BACKEND_API_ORIGIN",
        "APP_ENV",
        "APP_ORIGIN",
        "DATABASE_URL"
    )) {
        Remove-Item "Env:$name" -ErrorAction SilentlyContinue
    }
}

exit $exitCode
