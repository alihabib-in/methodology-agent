# Benchmark the local LLM: measures time-to-first-token, total generation
# time, and tokens/second over repeated prompts.

param(
    [string]$BaseUrl = "http://127.0.0.1:8080/v1",
    [string]$Model = "qwen3-4b-instruct-2507",
    [int]$Runs = 10,
    [int]$MaxTokens = 128
)

$ErrorActionPreference = "Stop"

$prompts = @(
    "What is a statistical unit?",
    "ما هي الوحدة الإحصائية؟",
    "Identify the missing methodology element: we want a monthly indicator of active establishments but the definition is not agreed."
)

$timings = @()
$totalTokens = 0

for ($i = 1; $i -le $Runs; $i++) {
    $prompt = $prompts[($i - 1) % $prompts.Count]
    $body = @{
        model = $Model
        messages = @(@{ role = "user"; content = $prompt })
        temperature = 0.1
        max_tokens = $MaxTokens
    } | ConvertTo-Json -Depth 6

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $response = Invoke-RestMethod `
        -Uri "$BaseUrl/chat/completions" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body
    $sw.Stop()

    $tokens = [int]$response.usage.completion_tokens
    $totalTokens += $tokens
    $seconds = $sw.Elapsed.TotalSeconds
    $tps = if ($seconds -gt 0) { $tokens / $seconds } else { 0 }

    $timings += [PSCustomObject]@{
        Run       = $i
        Prompt    = $prompt.Substring(0, [Math]::Min(40, $prompt.Length))
        Tokens    = $tokens
        Seconds   = [Math]::Round($seconds, 3)
        TokensPerSec = [Math]::Round($tps, 2)
    }
}

$timings | Format-Table -AutoSize

$sorted = $timings | Sort-Object Seconds
$totalSecs = ($timings | Measure-Object Seconds -Sum).Sum

Write-Host ""
Write-Host "=== Summary ($Runs runs) ===" -ForegroundColor Cyan
Write-Host ("Total time      : {0}s" -f [Math]::Round($totalSecs, 2))
Write-Host ("Mean            : {0}s" -f [Math]::Round(($timings | Measure-Object Seconds -Average).Average, 3))
Write-Host ("Min             : {0}s" -f $sorted[0].Seconds)
Write-Host ("Max             : {0}s" -f $sorted[-1].Seconds)
Write-Host ("Median          : {0}s" -f $sorted[[int]($sorted.Count / 2)].Seconds)
Write-Host ("p95             : {0}s" -f $sorted[[int]($sorted.Count * 0.95) - 1].Seconds)
Write-Host ("Tokens          : $totalTokens")
Write-Host ("Overall Tokens/s: {0}" -f [Math]::Round($totalTokens / $totalSecs, 2))
