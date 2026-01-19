# MCP Linux Infra v0.3.0 - Configuration SSH Agent Windows
# Script PowerShell pour configurer l'agent SSH sur Windows

param(
    [switch]$Force,
    [switch]$SkipKeyGen,
    [string]$TargetHost = ""
)

$ErrorActionPreference = "Continue"

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "       MCP Linux Infra - Configuration SSH Agent Windows             " -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Vérifier si exécuté en tant qu'admin (nécessaire pour configurer le service)
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[1/6] " -NoNewline
    Write-Host "PRIVILÈGES: " -ForegroundColor Yellow -NoNewline
    Write-Host "Non administrateur (OK pour usage, mais limité pour configuration service)"
} else {
    Write-Host "[1/6] " -NoNewline
    Write-Host "PRIVILÈGES: " -ForegroundColor Green -NoNewline
    Write-Host "Administrateur détecté"
}
Write-Host ""

# Test 2: Vérifier le service SSH Agent
Write-Host "[2/6] " -NoNewline
Write-Host "SERVICE SSH AGENT" -ForegroundColor Cyan
$sshAgent = Get-Service ssh-agent -ErrorAction SilentlyContinue

if ($null -eq $sshAgent) {
    Write-Host "  " -NoNewline
    Write-Host "ERREUR: " -ForegroundColor Red -NoNewline
    Write-Host "Service ssh-agent non trouvé"
    Write-Host "  Installation: Activer 'OpenSSH Authentication Agent' dans les fonctionnalités Windows"
    exit 1
}

Write-Host "  Service trouvé: $($sshAgent.Status)"

if ($sshAgent.Status -ne "Running") {
    if ($isAdmin) {
        Write-Host "  Démarrage du service..." -ForegroundColor Yellow
        Set-Service ssh-agent -StartupType Automatic
        Start-Service ssh-agent
        Write-Host "  " -NoNewline
        Write-Host "OK: " -ForegroundColor Green -NoNewline
        Write-Host "Service démarré"
    } else {
        Write-Host "  " -NoNewline
        Write-Host "ACTION REQUISE: " -ForegroundColor Yellow -NoNewline
        Write-Host "Exécuter en tant qu'admin pour démarrer le service:"
        Write-Host "  Start-Service ssh-agent" -ForegroundColor Cyan
        exit 1
    }
} else {
    Write-Host "  " -NoNewline
    Write-Host "OK: " -ForegroundColor Green -NoNewline
    Write-Host "Service actif"
}
Write-Host ""

# Test 3: Générer les clés si nécessaire
Write-Host "[3/6] " -NoNewline
Write-Host "CLÉS SSH" -ForegroundColor Cyan

$sshDir = "$HOME\.ssh"
if (-not (Test-Path $sshDir)) {
    New-Item -ItemType Directory -Path $sshDir | Out-Null
    Write-Host "  Création du répertoire $sshDir"
}

$keysToGenerate = @(
    @{Name="mcp-reader"; Path="$sshDir\mcp-reader"; Comment="mcp-reader@mcp-linux-infra"},
    @{Name="pra-runner"; Path="$sshDir\pra-runner"; Comment="pra-runner@mcp-linux-infra"}
)

foreach ($key in $keysToGenerate) {
    if (Test-Path $key.Path) {
        Write-Host "  " -NoNewline
        Write-Host "OK: " -ForegroundColor Green -NoNewline
        Write-Host "Clé existe: $($key.Name)"
    } elseif (-not $SkipKeyGen) {
        Write-Host "  Génération de la clé $($key.Name)..." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  IMPORTANT: Entrez une passphrase forte pour sécuriser cette clé" -ForegroundColor Yellow
        Write-Host ""

        $keygenArgs = @(
            "-t", "ed25519",
            "-f", $key.Path,
            "-C", $key.Comment
        )

        & ssh-keygen @keygenArgs

        if ($LASTEXITCODE -eq 0) {
            Write-Host "  " -NoNewline
            Write-Host "OK: " -ForegroundColor Green -NoNewline
            Write-Host "Clé générée: $($key.Name)"
        } else {
            Write-Host "  " -NoNewline
            Write-Host "ERREUR: " -ForegroundColor Red -NoNewline
            Write-Host "Échec génération: $($key.Name)"
        }
    } else {
        Write-Host "  " -NoNewline
        Write-Host "SKIP: " -ForegroundColor Yellow -NoNewline
        Write-Host "Clé manquante: $($key.Name) (utilisez -SkipKeyGen:$false)"
    }
}
Write-Host ""

# Test 4: Ajouter les clés à l'agent
Write-Host "[4/6] " -NoNewline
Write-Host "CHARGEMENT DANS L'AGENT" -ForegroundColor Cyan

$keysToAdd = @(
    "$sshDir\mcp-reader",
    "$sshDir\pra-runner"
)

foreach ($keyPath in $keysToAdd) {
    if (Test-Path $keyPath) {
        Write-Host "  Ajout de $(Split-Path -Leaf $keyPath)..." -ForegroundColor Yellow

        # Vérifier si déjà chargée
        $keyFingerprint = & ssh-keygen -lf $keyPath 2>$null
        $loadedKeys = & ssh-add -l 2>$null

        if ($loadedKeys -match ($keyFingerprint -split " ")[1]) {
            Write-Host "    " -NoNewline
            Write-Host "OK: " -ForegroundColor Green -NoNewline
            Write-Host "Déjà chargée"
        } else {
            & ssh-add $keyPath

            if ($LASTEXITCODE -eq 0) {
                Write-Host "    " -NoNewline
                Write-Host "OK: " -ForegroundColor Green -NoNewline
                Write-Host "Clé ajoutée à l'agent"
            } else {
                Write-Host "    " -NoNewline
                Write-Host "ERREUR: " -ForegroundColor Red -NoNewline
                Write-Host "Échec de l'ajout"
            }
        }
    } else {
        Write-Host "  " -NoNewline
        Write-Host "SKIP: " -ForegroundColor Yellow -NoNewline
        Write-Host "Clé non trouvée: $(Split-Path -Leaf $keyPath)"
    }
}
Write-Host ""

# Test 5: Vérifier les clés chargées
Write-Host "[5/6] " -NoNewline
Write-Host "VÉRIFICATION" -ForegroundColor Cyan

$loadedKeys = & ssh-add -l 2>$null
if ($LASTEXITCODE -eq 0 -and $loadedKeys) {
    Write-Host "  Clés chargées dans l'agent:" -ForegroundColor Green
    $loadedKeys | ForEach-Object {
        Write-Host "    • $_"
    }
} else {
    Write-Host "  " -NoNewline
    Write-Host "AVERTISSEMENT: " -ForegroundColor Yellow -NoNewline
    Write-Host "Aucune clé dans l'agent"
}
Write-Host ""

# Test 6: Tester MCP
Write-Host "[6/6] " -NoNewline
Write-Host "TEST MCP" -ForegroundColor Cyan

$mcpTest = python -c @"
import sys
sys.path.insert(0, 'src')
try:
    from mcp_linux_infra.connection.smart_ssh import SmartSSHManager
    manager = SmartSSHManager()
    print(manager._auth_mode.value)
except Exception as e:
    print(f'error:{e}')
"@ 2>$null

if ($mcpTest -eq "agent") {
    Write-Host "  " -NoNewline
    Write-Host "OK: " -ForegroundColor Green -NoNewline
    Write-Host "MCP détecte le mode agent"
} elseif ($mcpTest -eq "direct") {
    Write-Host "  " -NoNewline
    Write-Host "FALLBACK: " -ForegroundColor Yellow -NoNewline
    Write-Host "MCP utilise les clés directes"
} else {
    Write-Host "  " -NoNewline
    Write-Host "INFO: " -ForegroundColor Cyan -NoNewline
    Write-Host "Test MCP: $mcpTest"
}
Write-Host ""

# Distribution des clés (optionnel)
if ($TargetHost) {
    Write-Host "=====================================================================" -ForegroundColor Cyan
    Write-Host "DISTRIBUTION DES CLÉS" -ForegroundColor Cyan
    Write-Host "=====================================================================" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "Serveur cible: $TargetHost" -ForegroundColor Yellow
    Write-Host ""

    $pubKeys = @(
        @{User="mcp-reader"; Path="$sshDir\mcp-reader.pub"},
        @{User="pra-runner"; Path="$sshDir\pra-runner.pub"}
    )

    foreach ($pub in $pubKeys) {
        if (Test-Path $pub.Path) {
            Write-Host "Copie de la clé $($pub.User)..." -ForegroundColor Yellow
            Write-Host "Commande à exécuter:" -ForegroundColor Cyan
            Write-Host "  type `"$($pub.Path)`" | ssh root@$TargetHost `"cat >> /home/$($pub.User)/.ssh/authorized_keys`"" -ForegroundColor Gray
            Write-Host ""

            $confirm = Read-Host "Exécuter maintenant? (o/N)"
            if ($confirm -eq "o" -or $confirm -eq "O") {
                Get-Content $pub.Path | ssh root@$TargetHost "mkdir -p /home/$($pub.User)/.ssh && cat >> /home/$($pub.User)/.ssh/authorized_keys && chmod 700 /home/$($pub.User)/.ssh && chmod 600 /home/$($pub.User)/.ssh/authorized_keys"

                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  " -NoNewline
                    Write-Host "OK: " -ForegroundColor Green -NoNewline
                    Write-Host "Clé distribuée pour $($pub.User)"
                } else {
                    Write-Host "  " -NoNewline
                    Write-Host "ERREUR: " -ForegroundColor Red -NoNewline
                    Write-Host "Échec de la distribution"
                }
            }
        }
    }
    Write-Host ""
}

# Résumé et instructions
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "RÉSUMÉ ET PROCHAINES ÉTAPES" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Configuration terminée!" -ForegroundColor Green
Write-Host ""
Write-Host "Pour rendre la configuration permanente:" -ForegroundColor Yellow
Write-Host "  1. Le service ssh-agent démarre automatiquement au boot" -ForegroundColor Cyan
Write-Host "  2. Ajouter au profil PowerShell:" -ForegroundColor Cyan
Write-Host ""
Write-Host "     notepad `$PROFILE" -ForegroundColor Gray
Write-Host ""
Write-Host "     # Ajouter ces lignes:" -ForegroundColor Gray
Write-Host "     ssh-add `"$HOME\.ssh\mcp-reader`" 2>`$null" -ForegroundColor Gray
Write-Host "     ssh-add `"$HOME\.ssh\pra-runner`" 2>`$null" -ForegroundColor Gray
Write-Host ""

Write-Host "Distribution des clés sur les serveurs:" -ForegroundColor Yellow
Write-Host "  1. Manuellement:" -ForegroundColor Cyan
Write-Host "     type `"$HOME\.ssh\mcp-reader.pub`" | ssh root@server1 `"cat >> /home/mcp-reader/.ssh/authorized_keys`"" -ForegroundColor Gray
Write-Host "     type `"$HOME\.ssh\pra-runner.pub`" | ssh root@server1 `"cat >> /home/pra-runner/.ssh/authorized_keys`"" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Avec ce script:" -ForegroundColor Cyan
Write-Host "     .\setup-ssh-agent-windows.ps1 -TargetHost server1" -ForegroundColor Gray
Write-Host ""

Write-Host "Tester la configuration:" -ForegroundColor Yellow
Write-Host "  .\test-ssh-agent.sh" -ForegroundColor Cyan
Write-Host ""

Write-Host "Documentation complète:" -ForegroundColor Yellow
Write-Host "  Get-Content SSH-AGENT-SETUP.md" -ForegroundColor Cyan
Write-Host ""

Write-Host "=====================================================================" -ForegroundColor Green
Write-Host "  CONFIGURATION SSH AGENT TERMINÉE" -ForegroundColor Green
Write-Host "=====================================================================" -ForegroundColor Green
