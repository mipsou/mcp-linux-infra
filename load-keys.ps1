#!/usr/bin/env pwsh
#
# Charger les clés SSH dans l'agent
#

$ErrorActionPreference = "Stop"

Write-Host "🔐 Chargement des clés SSH dans l'agent..." -ForegroundColor Cyan

# Vérifier que le service tourne
$service = Get-Service ssh-agent
if ($service.Status -ne "Running") {
    Write-Host "❌ Service ssh-agent arrêté. Démarrage..." -ForegroundColor Red
    Start-Service ssh-agent
    Start-Sleep -Seconds 2
}

Write-Host "✅ Service ssh-agent: $($service.Status)" -ForegroundColor Green

# Définir la variable d'environnement pour cette session
$env:SSH_AUTH_SOCK = "\\.\pipe\openssh-ssh-agent"

# Charger les clés
Write-Host "`nChargement des clés..."

try {
    # Détecter ssh-add
    $sshAdd = Get-Command ssh-add -ErrorAction SilentlyContinue
    if (-not $sshAdd) {
        $sshAdd = "C:\Windows\System32\OpenSSH\ssh-add.exe"
    }

    # Clé read-only (diagnostics)
    Write-Host "  📄 mcp-reader.key..." -NoNewline
    & $sshAdd keys\mcp-reader.key 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✅" -ForegroundColor Green
    } else {
        Write-Host " ❌" -ForegroundColor Red
    }

    # Clé PRA (actions)
    Write-Host "  📄 pra-exec.key..." -NoNewline
    & $sshAdd keys\pra-exec.key 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✅" -ForegroundColor Green
    } else {
        Write-Host " ❌" -ForegroundColor Red
    }

    # Lister les clés chargées
    Write-Host "`n📋 Clés chargées dans l'agent:" -ForegroundColor Cyan
    & $sshAdd -l

    Write-Host "`n✅ Clés chargées avec succès!" -ForegroundColor Green
    Write-Host "`n💡 Pour les utiliser dans Claude Desktop:" -ForegroundColor Yellow
    Write-Host "   1. Redémarrer Claude Desktop"
    Write-Host "   2. Les clés seront automatiquement détectées"

} catch {
    Write-Host "`n❌ Erreur lors du chargement des clés:" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}
