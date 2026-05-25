# MacroRunner artifact signing helper.
# Usage: powershell -ExecutionPolicy Bypass -File sign_installer.ps1

$ErrorActionPreference = 'Stop'

$cert = Get-ChildItem Cert:\CurrentUser\My |
    Where-Object { $_.Subject -like '*MacroRunner*' } |
    Sort-Object NotAfter -Descending |
    Select-Object -First 1

if (-not $cert) {
    Write-Error "MacroRunner signing certificate was not found. Run create_cert.ps1 first."
    exit 1
}

$exePath = "dist\MacroRunner\MacroRunner.exe"
$installerPath = "installer_output\MacroRunner_Setup.exe"

if (-not (Test-Path $installerPath)) {
    Write-Error "Installer was not found: $installerPath"
    exit 1
}

$filesToSign = @($installerPath)
if (Test-Path $exePath) {
    $filesToSign = @($exePath) + $filesToSign
}

$resultFolderName = ([string][char]0xACB0) + ([string][char]0xACFC) + ([string][char]0xBB3C)
$codeWorkName = ([string][char]0xCF54) + ([string][char]0xB4DC) + ([string][char]0xC791) + ([string][char]0xC5C5)
$resultDir = Join-Path (Join-Path "D:\OneDrive" $codeWorkName) $resultFolderName

Push-Location $PSScriptRoot
try {
    $failed = $false
    $signedAny = $false

    foreach ($file in $filesToSign) {
        if (Test-Path $file) {
            $result = Set-AuthenticodeSignature -FilePath $file -Certificate $cert -TimestampServer 'http://timestamp.digicert.com' -HashAlgorithm SHA256
            if ($result.Status -eq 'Valid') {
                Write-Host "OK: $file" -ForegroundColor Green
                $signedAny = $true
            } else {
                Write-Host "FAIL: $file ($($result.Status))" -ForegroundColor Red
                $failed = $true
            }
        }
    }

    if ($failed -or -not $signedAny) {
        exit 1
    }

    $installerFullPath = Join-Path $PSScriptRoot $installerPath
    if (Test-Path $installerFullPath) {
        New-Item -ItemType Directory -Force -Path $resultDir | Out-Null
        Copy-Item -LiteralPath $installerFullPath -Destination (Join-Path $resultDir "MacroRunner_Setup.exe") -Force
        Write-Host "Copied installer to: $resultDir" -ForegroundColor Green
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "Signing complete."
