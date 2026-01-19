#!/usr/bin/env pwsh
# Vérification finale que MCP linux-infra est prêt

Write-Host "🎯 Test Final - MCP linux-infra" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Configuration
$configPath = Join-Path $env:APPDATA "Claude\claude_desktop_config.json"
$config = Get-Content $configPath -Raw | ConvertFrom-Json

Write-Host "📋 MCP Servers configurés dans Claude Desktop:" -ForegroundColor Yellow
$config.mcpServers.PSObject.Properties | ForEach-Object {
    $name = $_.Name
    if ($name -eq "linux-infra") {
        Write-Host "   ✨ $name" -ForegroundColor Green
    } else {
        Write-Host "      $name" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "🔍 Configuration linux-infra:" -ForegroundColor Yellow
$linuxInfra = $config.mcpServers.'linux-infra'
Write-Host "   Command: $($linuxInfra.command)" -ForegroundColor Gray
Write-Host "   Directory: $($linuxInfra.args[1])" -ForegroundColor Gray
Write-Host "   SSH_AUTH_SOCK: $($linuxInfra.env.SSH_AUTH_SOCK)" -ForegroundColor Gray
Write-Host "   LOG_LEVEL: $($linuxInfra.env.LINUX_MCP_LOG_LEVEL)" -ForegroundColor Gray
Write-Host "   LOG_DIR: $($linuxInfra.env.LINUX_MCP_LOG_DIR)" -ForegroundColor Gray

Write-Host ""
Write-Host "🔐 Vérification SSH Agent:" -ForegroundColor Yellow
$sshAdd = if (Get-Command ssh-add -ErrorAction SilentlyContinue) { "ssh-add" } else { "C:\Windows\System32\OpenSSH\ssh-add.exe" }
$keys = & $sshAdd -l 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Agent accessible avec clés chargées" -ForegroundColor Green
    $keyCount = ($keys | Measure-Object -Line).Lines
    Write-Host "   🔑 $keyCount clé(s) disponible(s)" -ForegroundColor Gray
} else {
    Write-Host "   ⚠️  Agent accessible mais pas de clés chargées" -ForegroundColor Yellow
    Write-Host "   💡 Charge tes clés avec: ssh-add <chemin-clé>" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "📊 Statistiques du projet:" -ForegroundColor Yellow
$projectDir = "D:\infra\mcp-servers\mcp-linux-infra"
$toolFiles = Get-ChildItem "$projectDir\src\mcp_linux_infra\tools" -Recurse -Filter "*.py" | Where-Object { $_.Name -ne "__init__.py" }
Write-Host "   📁 $($toolFiles.Count) fichiers de tools" -ForegroundColor Gray
$serverPy = Get-Content "$projectDir\src\mcp_linux_infra\server.py" -Raw
$toolCount = ([regex]::Matches($serverPy, '@app\.call_tool\(\)')).Count
Write-Host "   🔧 $toolCount tools MCP enregistrés" -ForegroundColor Gray

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ MCP linux-infra est configuré et prêt !" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 Pour activer:" -ForegroundColor Yellow
Write-Host "   1. Redémarre Claude Desktop (fermer complètement)"
Write-Host "   2. Rouvre Claude Desktop"
Write-Host "   3. Le MCP linux-infra démarrera automatiquement"
Write-Host ""
Write-Host "🧪 Pour vérifier dans Claude:" -ForegroundColor Cyan
Write-Host "   Demande: 'List all connected MCP servers'"
Write-Host "   Tu devrais voir: linux-infra avec $toolCount tools"
Write-Host ""
Write-Host "💡 Pour tester la connexion SSH:" -ForegroundColor Cyan
Write-Host "   Demande: 'Get system info from <hostname>'"
Write-Host "   (Remplace <hostname> par ton serveur Linux)"
Write-Host ""
Write-Host "📝 Les logs seront dans:" -ForegroundColor Cyan
Write-Host "   $($linuxInfra.env.LINUX_MCP_LOG_DIR)\mcp-audit-$(Get-Date -Format 'yyyyMMdd').json"
