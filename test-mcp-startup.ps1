#!/usr/bin/env pwsh
# Test de démarrage du MCP server linux-infra

$ErrorActionPreference = "Stop"

Write-Host "🧪 Test de démarrage MCP linux-infra" -ForegroundColor Cyan

# Variables d'environnement
$env:SSH_AUTH_SOCK = "\\.\pipe\openssh-ssh-agent"
$env:LINUX_MCP_LOG_LEVEL = "INFO"
$env:LINUX_MCP_LOG_DIR = "D:\infra\mcp-servers\mcp-linux-infra\logs"

Write-Host "`n📋 Configuration:" -ForegroundColor Yellow
Write-Host "   SSH_AUTH_SOCK: $env:SSH_AUTH_SOCK"
Write-Host "   LOG_LEVEL: $env:LINUX_MCP_LOG_LEVEL"
Write-Host "   LOG_DIR: $env:LINUX_MCP_LOG_DIR"

Write-Host "`n🚀 Démarrage du serveur (10 secondes max)..." -ForegroundColor Yellow
Write-Host "   (Le serveur attend des commandes MCP sur stdin)" -ForegroundColor Gray

# Changer de répertoire
Set-Location "D:\infra\mcp-servers\mcp-linux-infra"

# Test de démarrage avec timeout
$job = Start-Job -ScriptBlock {
    param($authSock, $logLevel, $logDir)
    $env:SSH_AUTH_SOCK = $authSock
    $env:LINUX_MCP_LOG_LEVEL = $logLevel
    $env:LINUX_MCP_LOG_DIR = $logDir

    Set-Location "D:\infra\mcp-servers\mcp-linux-infra"

    # Envoyer un message JSON vide pour tester
    "" | uv run mcp-linux-infra 2>&1
} -ArgumentList $env:SSH_AUTH_SOCK, $env:LINUX_MCP_LOG_LEVEL, $env:LINUX_MCP_LOG_DIR

# Attendre 5 secondes
$completed = Wait-Job $job -Timeout 5

if ($completed) {
    $output = Receive-Job $job
    Write-Host "`n📄 Output:" -ForegroundColor Cyan
    Write-Host $output

    if ($output -match "error|exception|failed") {
        Write-Host "`n❌ Erreur détectée dans l'output" -ForegroundColor Red
        Remove-Job $job -Force
        exit 1
    } else {
        Write-Host "`n✅ Serveur démarré (pas d'erreur critique)" -ForegroundColor Green
    }
} else {
    Write-Host "`n✅ Serveur tourne (timeout attendu pour serveur MCP)" -ForegroundColor Green
    Stop-Job $job
}

Remove-Job $job -Force

# Vérifier les logs
Write-Host "`n📝 Vérification des logs..." -ForegroundColor Yellow
$logFile = Join-Path $env:LINUX_MCP_LOG_DIR "mcp-audit-$(Get-Date -Format 'yyyyMMdd').json"

if (Test-Path $logFile) {
    Write-Host "   ✅ Fichier de log créé: $logFile" -ForegroundColor Green
    $logLines = Get-Content $logFile | Select-Object -First 5
    if ($logLines) {
        Write-Host "`n   📋 Premières lignes:" -ForegroundColor Cyan
        $logLines | ForEach-Object {
            try {
                $json = $_ | ConvertFrom-Json
                Write-Host "      [$($json.event_type)] $($json.status)" -ForegroundColor Gray
            } catch {
                Write-Host "      $_" -ForegroundColor Gray
            }
        }
    }
} else {
    Write-Host "   ⚠️  Pas encore de fichier de log (normal si pas d'événement)" -ForegroundColor Yellow
}

Write-Host "`n" + ("="*70)
Write-Host "✅ Test terminé" -ForegroundColor Green
Write-Host "`n💡 Pour tester complètement:" -ForegroundColor Yellow
Write-Host "   1. Redémarrer Claude Desktop"
Write-Host "   2. Utiliser le MCP depuis Claude"
Write-Host "   3. Vérifier les logs dans: $env:LINUX_MCP_LOG_DIR"
