#!/usr/bin/env pwsh
# Test d'accès SSH Agent depuis différents contextes

Write-Host "🔍 Test d'accès SSH Agent" -ForegroundColor Cyan

# Test 1: Variable SSH_AUTH_SOCK
Write-Host "`n1. Variable SSH_AUTH_SOCK:"
if ($env:SSH_AUTH_SOCK) {
    Write-Host "   ✅ Définie: $env:SSH_AUTH_SOCK" -ForegroundColor Green
} else {
    Write-Host "   ❌ Non définie" -ForegroundColor Red
    Write-Host "   💡 Définition pour Windows OpenSSH..." -ForegroundColor Yellow
    $env:SSH_AUTH_SOCK = "\\.\pipe\openssh-ssh-agent"
    Write-Host "   ✅ Définie: $env:SSH_AUTH_SOCK" -ForegroundColor Green
}

# Test 2: Accès agent
Write-Host "`n2. Connexion à l'agent:"
$sshAdd = Get-Command ssh-add -ErrorAction SilentlyContinue
if (-not $sshAdd) {
    $sshAdd = "C:\Windows\System32\OpenSSH\ssh-add.exe"
}

$result = & $sshAdd -l 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Agent accessible" -ForegroundColor Green
    Write-Host "`n   📋 Clés dans l'agent:"
    & $sshAdd -l | ForEach-Object { Write-Host "      $_" -ForegroundColor Gray }
} elseif ($result -match "no identities") {
    Write-Host "   ⚠️  Agent accessible mais aucune clé chargée" -ForegroundColor Yellow
} else {
    Write-Host "   ❌ Agent non accessible: $result" -ForegroundColor Red
}

# Test 3: Service Windows
Write-Host "`n3. Service Windows ssh-agent:"
$service = Get-Service ssh-agent -ErrorAction SilentlyContinue
if ($service) {
    Write-Host "   Status: $($service.Status)" -ForegroundColor $(if ($service.Status -eq 'Running') { 'Green' } else { 'Red' })
    Write-Host "   StartType: $($service.StartType)"
} else {
    Write-Host "   ❌ Service non trouvé" -ForegroundColor Red
}

# Test 4: asyncssh Python
Write-Host "`n4. Test Python asyncssh:"
$pythonTest = @"
import os
import sys
os.environ['SSH_AUTH_SOCK'] = r'\\.\pipe\openssh-ssh-agent'

try:
    import asyncssh
    print('   ✅ asyncssh importé')

    # Vérifier agent
    if asyncssh.load_keypairs():
        print('   ✅ Agent détecté par asyncssh')
    else:
        print('   ⚠️  Aucune clé détectée')
except Exception as e:
    print(f'   ❌ Erreur: {e}')
"@

uv run python -c $pythonTest

Write-Host "`n" + ("="*60)
Write-Host "💡 Recommandation:" -ForegroundColor Yellow
Write-Host "   Pour Claude Desktop, définir dans claude_desktop_config.json:"
Write-Host '   "env": {' -ForegroundColor Gray
Write-Host '     "SSH_AUTH_SOCK": "\\\\.\\pipe\\openssh-ssh-agent"' -ForegroundColor Gray
Write-Host '   }' -ForegroundColor Gray
