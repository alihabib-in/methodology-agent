# Check the health of the LLM and the API services.

param(
    [string]$LlmUrl = "http://127.0.0.1:8080/health",
    [string]$ApiUrl = "http://127.0.0.1:8000/health"
)

$ErrorActionPreference = "Continue"

Write-Host "LLM health:" -ForegroundColor Cyan
try {
    $llm = Invoke-RestMethod -Uri $LlmUrl -Method GET -TimeoutSec 10
    Write-Host "  OK: $llm" -ForegroundColor Green
} catch {
    Write-Host "  FAILED: $LlmUrl" -ForegroundColor Red
}

Write-Host ""
Write-Host "API health:" -ForegroundColor Cyan
try {
    $api = Invoke-RestMethod -Uri $ApiUrl -Method GET -TimeoutSec 10
    Write-Host "  OK: $($api | ConvertTo-Json -Compress)" -ForegroundColor Green
} catch {
    Write-Host "  FAILED: $ApiUrl" -ForegroundColor Red
}
