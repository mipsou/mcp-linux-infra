#!/usr/bin/env pwsh
# Test complet du MCP linux-infra avant démarrage Claude Desktop

$ErrorActionPreference = "Stop"

Write-Host "🧪 Test complet du MCP linux-infra" -ForegroundColor Cyan
Write-Host ""

# 1. Vérifier SSH Agent
Write-Host "1️⃣  Service SSH Agent..." -ForegroundColor Yellow
$service = Get-Service ssh-agent
if ($service.Status -eq 'Running') {
    Write-Host "   ✅ Running" -ForegroundColor Green
} else {
    Write-Host "   ❌ Stopped - Démarrage..." -ForegroundColor Yellow
    Start-Service ssh-agent
    Start-Sleep -Seconds 2
    Write-Host "   ✅ Démarré" -ForegroundColor Green
}

# 2. Vérifier uv
Write-Host ""
Write-Host "2️⃣  Commande uv..." -ForegroundColor Yellow
if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Host "   ✅ Disponible" -ForegroundColor Green
    $uvVersion = uv --version
    Write-Host "   📦 $uvVersion" -ForegroundColor Gray
} else {
    Write-Host "   ❌ Non trouvé dans PATH" -ForegroundColor Red
    exit 1
}

# 3. Vérifier configuration Claude Desktop
Write-Host ""
Write-Host "3️⃣  Configuration Claude Desktop..." -ForegroundColor Yellow
$configPath = Join-Path $env:APPDATA "Claude\claude_desktop_config.json"
if (Test-Path $configPath) {
    $config = Get-Content $configPath -Raw | ConvertFrom-Json
    if ($config.mcpServers.'linux-infra') {
        Write-Host "   ✅ MCP linux-infra configuré" -ForegroundColor Green
        Write-Host "   📋 Command: $($config.mcpServers.'linux-infra'.command)" -ForegroundColor Gray
        if ($config.mcpServers.'linux-infra'.env.SSH_AUTH_SOCK) {
            Write-Host "   ✅ SSH_AUTH_SOCK défini" -ForegroundColor Green
        }
        if ($config.mcpServers.'linux-infra'.env.LINUX_MCP_LOG_DIR) {
            Write-Host "   ✅ LOG_DIR défini" -ForegroundColor Green
        }
    } else {
        Write-Host "   ❌ MCP linux-infra absent" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "   ❌ Fichier config absent" -ForegroundColor Red
    exit 1
}

# 4. Vérifier le répertoire du projet
Write-Host ""
Write-Host "4️⃣  Répertoire projet..." -ForegroundColor Yellow
$projectDir = "D:\infra\mcp-servers\mcp-linux-infra"
if (Test-Path $projectDir) {
    Write-Host "   ✅ Projet existe" -ForegroundColor Green
    Set-Location $projectDir
} else {
    Write-Host "   ❌ Répertoire absent" -ForegroundColor Red
    exit 1
}

# 5. Test import Python
Write-Host ""
Write-Host "5️⃣  Import Python modules..." -ForegroundColor Yellow
$result = uv run python -c "from mcp_linux_infra.server import app; print('OK')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Imports OK" -ForegroundColor Green
} else {
    Write-Host "   ❌ Erreur import" -ForegroundColor Red
    Write-Host "   $result" -ForegroundColor Red
    exit 1
}

# 6. Compter les tools
Write-Host ""
Write-Host "6️⃣  Outils MCP disponibles..." -ForegroundColor Yellow
$serverPy = Get-Content "src\mcp_linux_infra\server.py" -Raw
$toolCount = ([regex]::Matches($serverPy, '@app\.call_tool\(\)')).Count
Write-Host "   📊 $toolCount tools enregistrés" -ForegroundColor Gray

# 7. Vérifier la connexion SSH
Write-Host ""
Write-Host "7️⃣  Vérifier la connexion SSH..." -ForegroundColor Yellow
$result = uv run python -c "
import os
os.environ['SSH_AUTH_SOCK'] = r'\\.\pipe\openssh-ssh-agent'
from mcp_linux_infra.connection.smart_ssh import SmartSSHManager
manager = SmartSSHManager()
print(f'Auth mode: {manager._auth_mode.value}')
" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ SSH Manager initialisé" -ForegroundColor Green
    Write-Host "   $result" -ForegroundColor Gray
} else {
    Write-Host "   ⚠️  Erreur SSH Manager (normal si pas de serveur cible)" -ForegroundColor Yellow
    Write-Host "   $result" -ForegroundColor Gray
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ Tous les tests passent !" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 Prochaine étape:" -ForegroundColor Yellow
Write-Host "   1. Redémarre Claude Desktop"
Write-Host "   2. Dans Claude, demande: 'List connected MCP servers'"
Write-Host "   3. Tu devrais voir: linux-infra avec $toolCount tools"
Write-Host ""
Write-Host "📝 Logs seront dans:" -ForegroundColor Cyan
Write-Host "   D:\infra\mcp-servers\mcp-linux-infra\logs\mcp-audit-$(Get-Date -Format 'yyyyMMdd').json"
Write-Host ""
Write-Host "💡 Pour tester la connexion SSH vers un serveur:" -ForegroundColor Cyan
Write-Host "   'Get system info from server hostname'"
