# Configuration SSH Agent pour MCP Linux Infra

**MCP Linux Infra v0.3.0** utilise une approche intelligente pour l'authentification SSH:

```
Priorité 1: SSH Agent (RECOMMANDÉ) ✅ Sécurité maximale
Priorité 2: Clés directes (FALLBACK) ⚠️  Avec warning
Priorité 3: Aucune méthode (ERREUR) ❌
```

## 🔐 Pourquoi utiliser SSH Agent?

### ✅ Avantages
- **Sécurité maximale**: Les clés privées restent chiffrées en mémoire
- **Pas de clés sur disque**: Pas besoin de stocker les clés déchiffrées
- **Single Sign-On**: Une seule authentification pour toutes les connexions
- **Compatibilité**: Fonctionne avec tous les outils SSH
- **Audit**: Logs centralisés des accès

### ⚠️ Mode fallback (clés directes)
Si l'agent n'est pas disponible, MCP utilise les clés directes:
- Requiert `LINUX_MCP_SSH_KEY_PATH` et `LINUX_MCP_PRA_KEY_PATH`
- Warning dans les logs
- Moins sécurisé (clés lisibles sur disque)

---

## 🚀 Configuration Rapide (5 minutes)

### Windows (Pageant + PuTTY)

#### 1. Installer PuTTY
```powershell
# Via Chocolatey
choco install putty

# Ou télécharger depuis https://www.putty.org/
```

#### 2. Générer les clés (si nécessaire)
```powershell
# Avec PuTTYgen
puttygen.exe

# Générer une clé ED25519
# Sauvegarder: mcp-reader.ppk et mcp-reader.pub
# Générer une seconde clé pour pra-runner.ppk
```

#### 3. Démarrer Pageant (SSH Agent Windows)
```powershell
# Démarrer Pageant
pageant.exe

# Ou l'ajouter au démarrage
# Win+R -> shell:startup -> créer raccourci vers pageant.exe
```

#### 4. Charger les clés dans Pageant
```powershell
# Clic droit sur l'icône Pageant dans le systray
# "Add Key" -> Sélectionner mcp-reader.ppk
# "Add Key" -> Sélectionner pra-runner.ppk
# Entrer les passphrases si demandé
```

#### 5. Vérifier
```powershell
# Avec PuTTY
putty -agent mcp-reader@server1

# Avec OpenSSH (si installé)
ssh -A mcp-reader@server1
```

### Windows (OpenSSH natif) - Recommandé pour MCP

#### 1. Activer OpenSSH Authentication Agent
```powershell
# En tant qu'administrateur
Get-Service ssh-agent | Set-Service -StartupType Automatic
Start-Service ssh-agent
```

#### 2. Générer les clés (si nécessaire)
```powershell
# Générer clé ED25519 pour mcp-reader
ssh-keygen -t ed25519 -f "$HOME\.ssh\mcp-reader" -C "mcp-reader"

# Générer clé ED25519 pour pra-runner
ssh-keygen -t ed25519 -f "$HOME\.ssh\pra-runner" -C "pra-runner"

# Entrer une passphrase forte pour chaque clé
```

#### 3. Ajouter les clés à l'agent
```powershell
# Ajouter mcp-reader
ssh-add "$HOME\.ssh\mcp-reader"

# Ajouter pra-runner
ssh-add "$HOME\.ssh\pra-runner"

# Entrer les passphrases
```

#### 4. Vérifier les clés chargées
```powershell
# Lister les clés
ssh-add -l

# Output attendu:
# 256 SHA256:xxxx... mcp-reader (ED25519)
# 256 SHA256:yyyy... pra-runner (ED25519)
```

#### 5. Distribuer les clés publiques
```powershell
# Copier sur les serveurs cibles
type "$HOME\.ssh\mcp-reader.pub" | ssh root@server1 "cat >> /home/mcp-reader/.ssh/authorized_keys"
type "$HOME\.ssh\pra-runner.pub" | ssh root@server1 "cat >> /home/pra-runner/.ssh/authorized_keys"
```

### Linux / macOS

#### 1. Générer les clés
```bash
# Générer clé ED25519 pour mcp-reader
ssh-keygen -t ed25519 -f ~/.ssh/mcp-reader -C "mcp-reader"

# Générer clé ED25519 pour pra-runner
ssh-keygen -t ed25519 -f ~/.ssh/pra-runner -C "pra-runner"
```

#### 2. Démarrer SSH Agent (si pas déjà actif)
```bash
# Vérifier si agent actif
echo $SSH_AUTH_SOCK

# Si vide, démarrer l'agent
eval $(ssh-agent -s)

# Optionnel: ajouter au ~/.bashrc ou ~/.zshrc
echo 'eval $(ssh-agent -s) > /dev/null' >> ~/.bashrc
```

#### 3. Ajouter les clés à l'agent
```bash
# Ajouter mcp-reader
ssh-add ~/.ssh/mcp-reader

# Ajouter pra-runner
ssh-add ~/.ssh/pra-runner
```

#### 4. Vérifier
```bash
# Lister les clés chargées
ssh-add -l

# Tester la connexion
ssh -T mcp-reader@server1
```

#### 5. Distribuer les clés publiques
```bash
# Copier avec ssh-copy-id (plus simple)
ssh-copy-id -i ~/.ssh/mcp-reader.pub mcp-reader@server1
ssh-copy-id -i ~/.ssh/pra-runner.pub pra-runner@server1

# Ou manuellement
cat ~/.ssh/mcp-reader.pub | ssh root@server1 \
  "mkdir -p /home/mcp-reader/.ssh && cat >> /home/mcp-reader/.ssh/authorized_keys"
```

---

## 🔧 Configuration MCP

### Mode Agent (Recommandé)

**MCP détecte automatiquement l'agent SSH** et l'utilise si disponible.

Aucune variable d'environnement nécessaire:
```bash
# L'agent est détecté automatiquement via SSH_AUTH_SOCK
# Pas besoin de LINUX_MCP_SSH_KEY_PATH
```

### Mode Fallback (Clés directes)

Si l'agent n'est pas disponible ou désactivé:

```bash
# Variables d'environnement nécessaires
export LINUX_MCP_SSH_KEY_PATH="$HOME/.ssh/mcp-reader"
export LINUX_MCP_PRA_KEY_PATH="$HOME/.ssh/pra-runner"

# Optionnel: passphrases (NON RECOMMANDÉ - utiliser l'agent à la place)
export LINUX_MCP_KEY_PASSPHRASE="..."
export LINUX_MCP_PRA_KEY_PASSPHRASE="..."
```

### Forcer un mode

```bash
# Forcer l'utilisation de l'agent (échec si pas dispo)
export LINUX_MCP_FORCE_AUTH_MODE="agent"

# Forcer les clés directes (désactiver l'agent)
export LINUX_MCP_DISABLE_SSH_AGENT="true"
export LINUX_MCP_SSH_KEY_PATH="$HOME/.ssh/mcp-reader"
export LINUX_MCP_PRA_KEY_PATH="$HOME/.ssh/pra-runner"
```

---

## 🧪 Tests de validation

### Test 1: Vérifier l'agent SSH

**Windows (OpenSSH):**
```powershell
# Vérifier le service
Get-Service ssh-agent

# Vérifier les clés chargées
ssh-add -l
```

**Linux/macOS:**
```bash
# Vérifier la socket
echo $SSH_AUTH_SOCK

# Vérifier les clés chargées
ssh-add -l
```

### Test 2: Tester les connexions SSH

```bash
# Test mcp-reader (read-only)
ssh mcp-reader@server1 'ls -la'

# Test pra-runner (actions)
ssh pra-runner@server1 'sudo systemctl status nginx'
```

### Test 3: Tester avec MCP

```python
# Test Python direct
import sys
sys.path.insert(0, 'src')

from mcp_linux_infra.connection.smart_ssh import SmartSSHManager

manager = SmartSSHManager()
print(f"Auth mode: {manager._auth_mode.value}")

# Devrait afficher "agent" si tout est configuré
```

---

## 🔍 Troubleshooting

### Problème: "No SSH agent found"

**Cause**: L'agent SSH n'est pas démarré ou pas accessible

**Solution Windows:**
```powershell
# Démarrer le service
Start-Service ssh-agent

# Vérifier
Get-Service ssh-agent
```

**Solution Linux/macOS:**
```bash
# Démarrer l'agent
eval $(ssh-agent -s)

# Vérifier
echo $SSH_AUTH_SOCK
```

### Problème: "Permission denied (publickey)"

**Cause**: Clé publique non installée sur le serveur cible

**Solution:**
```bash
# Vérifier que la clé est dans l'agent
ssh-add -l

# Copier la clé sur le serveur
ssh-copy-id -i ~/.ssh/mcp-reader.pub mcp-reader@server1

# Vérifier les permissions sur le serveur
ssh root@server1 'chmod 700 /home/mcp-reader/.ssh && chmod 600 /home/mcp-reader/.ssh/authorized_keys'
```

### Problème: "Could not open a connection to your authentication agent"

**Cause**: Variable SSH_AUTH_SOCK non définie

**Solution:**
```bash
# Trouver la socket
ls -la /tmp/ssh-*/agent.*

# Définir manuellement
export SSH_AUTH_SOCK=/tmp/ssh-xxxx/agent.xxxx

# Ou redémarrer l'agent
eval $(ssh-agent -s)
```

### Problème: MCP utilise les clés directes au lieu de l'agent

**Vérifier:**
```bash
# Logs MCP
tail -f logs/*.log | grep "auth_mode"

# Devrait afficher: "auth_mode: agent"
# Si "auth_mode: direct" -> agent non détecté
```

**Forcer l'agent:**
```bash
export LINUX_MCP_FORCE_AUTH_MODE="agent"
# MCP échouera si agent non disponible (bon pour debug)
```

---

## 📋 Checklist de sécurité

### ✅ Configuration recommandée (Production)

- [ ] SSH Agent activé et démarré
- [ ] Clés ED25519 (plus sécurisées que RSA)
- [ ] Passphrases fortes sur toutes les clés
- [ ] Clés chargées dans l'agent au démarrage
- [ ] Pas de clés non chiffrées sur disque
- [ ] `LINUX_MCP_SSH_KEY_PATH` **non défini** (utilise l'agent)
- [ ] `SSH_AUTH_SOCK` correctement configuré
- [ ] Forced-command configuré sur les serveurs cibles
- [ ] Audit logs activés (`/var/log/auth.log`)

### ⚠️ À éviter (Risques de sécurité)

- [ ] Clés sans passphrase
- [ ] Passphrases en variables d'environnement
- [ ] Clés avec permissions 644 (doivent être 600)
- [ ] Même clé pour mcp-reader et pra-runner
- [ ] Clés dans des scripts non chiffrés
- [ ] Agent désactivé en production

---

## 🎯 Configuration recommandée finale

### Windows (OpenSSH) - Optimal

```powershell
# 1. Activer et démarrer le service
Set-Service ssh-agent -StartupType Automatic
Start-Service ssh-agent

# 2. Générer les clés (une seule fois)
ssh-keygen -t ed25519 -f "$HOME\.ssh\mcp-reader" -C "mcp-reader"
ssh-keygen -t ed25519 -f "$HOME\.ssh\pra-runner" -C "pra-runner"

# 3. Ajouter au démarrage (PowerShell profile)
notepad $PROFILE
# Ajouter:
#   ssh-add "$HOME\.ssh\mcp-reader" 2>$null
#   ssh-add "$HOME\.ssh\pra-runner" 2>$null

# 4. Charger maintenant
ssh-add "$HOME\.ssh\mcp-reader"
ssh-add "$HOME\.ssh\pra-runner"

# 5. Distribuer les clés
ssh-copy-id -i "$HOME\.ssh\mcp-reader.pub" mcp-reader@server1
ssh-copy-id -i "$HOME\.ssh\pra-runner.pub" pra-runner@server1

# 6. Tester MCP (détection automatique)
cd /d/infra/mcp-servers/mcp-linux-infra
python -c "from mcp_linux_infra.connection.smart_ssh import SmartSSHManager; m = SmartSSHManager(); print(f'Mode: {m._auth_mode.value}')"

# Devrait afficher: "Mode: agent" ✅
```

### Linux/macOS - Optimal

```bash
# 1. Ajouter au ~/.bashrc ou ~/.zshrc
echo 'eval $(ssh-agent -s) > /dev/null' >> ~/.bashrc
echo 'ssh-add ~/.ssh/mcp-reader 2>/dev/null' >> ~/.bashrc
echo 'ssh-add ~/.ssh/pra-runner 2>/dev/null' >> ~/.bashrc

# 2. Recharger
source ~/.bashrc

# 3. Générer les clés (une seule fois)
ssh-keygen -t ed25519 -f ~/.ssh/mcp-reader -C "mcp-reader"
ssh-keygen -t ed25519 -f ~/.ssh/pra-runner -C "pra-runner"

# 4. Distribuer
ssh-copy-id -i ~/.ssh/mcp-reader.pub mcp-reader@server1
ssh-copy-id -i ~/.ssh/pra-runner.pub pra-runner@server1

# 5. Tester
python3 -c "from mcp_linux_infra.connection.smart_ssh import SmartSSHManager; m = SmartSSHManager(); print(f'Mode: {m._auth_mode.value}')"
```

---

## 📚 Ressources

- [OpenSSH Agent Forwarding](https://www.ssh.com/academy/ssh/agent)
- [PuTTY Pageant](https://www.chiark.greenend.org.uk/~sgtatham/putty/docs.html)
- [Windows OpenSSH](https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_keymanagement)
- [SSH Best Practices](https://infosec.mozilla.org/guidelines/openssh)

---

**Version**: 0.3.0
**Date**: 2026-01-19
**Status**: ✅ Production Ready
