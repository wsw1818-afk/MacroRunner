# MacroRunner code signing certificate helper.
# Usage: powershell -ExecutionPolicy Bypass -File create_cert.ps1

$ErrorActionPreference = 'Stop'

$existing = Get-ChildItem Cert:\CurrentUser\My |
    Where-Object { $_.Subject -like '*MacroRunner*' } |
    Sort-Object NotAfter -Descending |
    Select-Object -First 1

if ($existing) {
    Write-Host "Existing certificate found: $($existing.Thumbprint)" -ForegroundColor Green
    Write-Host "Expires: $($existing.NotAfter)"
    $response = Read-Host "Create a new certificate? (y/N)"
    if ($response -ne 'y') {
        Write-Host "Keeping existing certificate."
    } else {
        Remove-Item "Cert:\CurrentUser\My\$($existing.Thumbprint)"
        Write-Host "Existing certificate removed."
        $existing = $null
    }
}

if (-not $existing) {
    $cert = New-SelfSignedCertificate `
        -Subject "CN=MacroRunner Publisher" `
        -Type CodeSigningCert `
        -CertStoreLocation Cert:\CurrentUser\My `
        -NotAfter (Get-Date).AddYears(5) `
        -HashAlgorithm SHA256
    Write-Host "New certificate created: $($cert.Thumbprint)" -ForegroundColor Green
    $existing = $cert
}

$cerPath = Join-Path $PSScriptRoot "MacroRunner_Publisher.cer"
Export-Certificate -Cert $existing -FilePath $cerPath | Out-Null

# Trust the certificate for the current Windows user so local signatures validate.
Import-Certificate -FilePath $cerPath -CertStoreLocation Cert:\CurrentUser\Root | Out-Null
Import-Certificate -FilePath $cerPath -CertStoreLocation Cert:\CurrentUser\TrustedPublisher | Out-Null

Write-Host ""
Write-Host "Certificate exported: $cerPath" -ForegroundColor Cyan
Write-Host "Trusted for CurrentUser Root and TrustedPublisher stores."
Write-Host ""
Write-Host "For another PC:"
Write-Host "1. Copy MacroRunner_Publisher.cer to that PC."
Write-Host "2. Install it for Local Machine or Current User."
Write-Host "3. Place it in Trusted Publishers and Trusted Root Certification Authorities."
