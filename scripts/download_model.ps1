# Download the Qwen3-4B-Instruct-2507 Q4_K_M GGUF model.
# Requires huggingface_hub:  py -m pip install -U huggingface_hub

param(
    [string]$Repo = "unsloth/Qwen3-4B-Instruct-2507-GGUF",
    [string]$Filename = "Qwen3-4B-Instruct-2507-Q4_K_M.gguf",
    [string]$LocalDir = ".\models"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command huggingface-cli -ErrorAction SilentlyContinue)) {
    Write-Host "Installing huggingface_hub..." -ForegroundColor Yellow
    py -m pip install -U huggingface_hub
}

Write-Host "Downloading $Filename from $Repo ..." -ForegroundColor Cyan

huggingface-cli download `
    $Repo `
    $Filename `
    --local-dir $LocalDir

Write-Host ""
Write-Host "Download complete. Verifying..." -ForegroundColor Green
Get-ChildItem $LocalDir
