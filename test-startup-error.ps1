#!/usr/bin/env pwsh
# Test de démarrage pour identifier l'erreur

$ErrorActionPreference = "Continue"

Write-Host "🔍 Test de démarrage MCP linux-infra" -ForegroundColor Cyan
Write-Host ""

# Configuration env
$env:SSH_AUTH_SOCK = "\\.\pipe\openssh-ssh-agent"
$env:LINUX_MCP_LOG_LEVEL = "INFO"
$env:LINUX_MCP_LOG_DIR = "D:\infra\mcp-servers\mcp-linux-infra\logs"

Set-Location "D:\infra\mcp-servers\mcp-linux-infra"

Write-Host "📋 Test 1: Import des modules..." -ForegroundColor Yellow
$result = uv run python -c "from mcp_linux_infra.server import app, run; print('Import OK')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Import réussi" -ForegroundColor Green
} else {
    Write-Host "   ❌ Erreur d'import:" -ForegroundColor Red
    Write-Host $result
    exit 1
}

Write-Host ""
Write-Host "📋 Test 2: Démarrage du serveur (2 secondes)..." -ForegroundColor Yellow
Write-Host "   (Appuie sur Ctrl+C si ça bloque)" -ForegroundColor Gray

# Lancer le serveur et envoyer une initialisation MCP
$initMessage = @'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
'@

$job = Start-Job -ScriptBlock {
    param($authSock, $logLevel, $logDir)
    $env:SSH_AUTH_SOCK = $authSock
    $env:LINUX_MCP_LOG_LEVEL = $logLevel
    $env:LINUX_MCP_LOG_DIR = $logDir

    Set-Location "D:\infra\mcp-servers\mcp-linux-infra"

    $process = Start-Process -FilePath "uv" -ArgumentList "run","mcp-linux-infra" -NoNewWindow -PassThru -RedirectStandardInput "input.txt" -RedirectStandardOutput "output.txt" -RedirectStandardError "error.txt"

    Start-Sleep -Seconds 2

    if ($process.HasExited) {
        $stderr = Get-Content "error.txt" -Raw
        return @{Status="Failed"; Error=$stderr}
    } else {
        Stop-Process -Id $process.Id -Force
        return @{Status="Running"}
    }
} -ArgumentList $env:SSH_AUTH_SOCK, $env:LINUX_MCP_LOG_LEVEL, $env:LINUX_MCP_LOG_DIR

Wait-Job $job -Timeout 5 | Out-Null
$result = Receive-Job $job

if ($result.Status -eq "Failed") {
    Write-Host "   ❌ Erreur au démarrage:" -ForegroundColor Red
    Write-Host $result.Error -ForegroundColor Red
} elseif ($result.Status -eq "Running") {
    Write-Host "   ✅ Serveur démarre correctement" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Timeout ou état inconnu" -ForegroundColor Yellow
}

Remove-Job $job -Force

Write-Host ""
Write-Host "💡 Si erreur, vérifie:" -ForegroundColor Cyan
Write-Host "   1. Le service ssh-agent est Running"
Write-Host "   2. La commande 'uv' est dans le PATH"
Write-Host "   3. Les dépendances Python sont installées"
