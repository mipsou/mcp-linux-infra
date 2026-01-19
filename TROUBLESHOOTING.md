# 🔧 Troubleshooting - linux-infra MCP

## 🚨 Erreurs Communes

### 1. "MCP server not found" ou "Tool not available"

**Symptôme**: Claude ne trouve pas le serveur `linux-infra`

**Causes possibles**:
- Claude Desktop n'a pas été redémarré
- Erreur dans `claude_desktop_config.json`
- Serveur ne démarre pas

**Diagnostic**:
```bash
# Vérifier config Claude Desktop
cat ~/AppData/Roaming/Claude/claude_desktop_config.json | grep -A 10 "linux-infra"

# Tester le serveur manuellement
cd D:\infra\mcp-servers\mcp-linux-infra
~/.local/bin/uv.exe run mcp-linux-infra

# Vérifier les logs
tail -n 50 logs/mcp-linux-infra.log
```

**Solution**:
1. Redémarrer Claude Desktop
2. Vérifier que `uv.exe` est dans `C:\Users\chpuj\.local\bin\`
3. Vérifier le fichier `.env`

---

### 2. "SSH connection failed" ou "Connection refused"

**Symptôme**: Impossible de se connecter aux hosts

**Causes possibles**:
- SSH Agent non démarré
- Clé SSH non chargée dans l'agent
- Host inaccessible
- User SSH incorrect

**Diagnostic**:
```bash
# Vérifier SSH Agent (Windows)
Get-Service ssh-agent

# Vérifier les clés chargées
ssh-add -l

# Tester connexion SSH directe
ssh -i C:/Users/chpuj/.ssh/id_ed25519 ansible@coreos-11.local

# Vérifier named pipe
ls -la \\.\pipe\openssh-ssh-agent
```

**Solution**:
```powershell
# Démarrer SSH Agent
Start-Service ssh-agent

# Charger la clé
ssh-add C:\Users\chpuj\.ssh\id_ed25519

# Vérifier
ssh-add -l
```

---

### 3. "Command authorization failed" ou "BLOCKED"

**Symptôme**: Une commande est refusée

**Causes possibles**:
- Commande dangereuse (whitelist BLOCKED)
- Nécessite approbation manuelle (MANUAL)
- Typo dans la commande

**Diagnostic**:
```
# Voir la whitelist
show_command_whitelist

# Voir les commandes en attente
list_pending_approvals
```

**Solution**:
- Utiliser une commande de la whitelist AUTO
- Approuver avec `approve_command(approval_id)`
- Modifier la commande pour utiliser une variante safe

---

### 4. "PRA action requires approval"

**Symptôme**: Action PRA bloquée en attente d'approbation

**Causes possibles**:
- `LINUX_MCP_REQUIRE_APPROVAL_FOR_PRA=true` dans `.env`
- Action non auto-approuvée

**Diagnostic**:
```
# Lister actions en attente
list_pending_actions
```

**Solution**:
```
# Approuver l'action
approve_pra_action(action_id=<ID>, approved=True)

# Ou modifier .env pour auto-approve (DANGEREUX)
LINUX_MCP_REQUIRE_APPROVAL_FOR_PRA=false
```

---

### 5. "Module import error" ou "ImportError"

**Symptôme**: Erreur d'import Python au démarrage

**Causes possibles**:
- Dépendances manquantes
- Virtualenv corrompu
- Erreur de syntaxe Python

**Diagnostic**:
```bash
cd D:\infra\mcp-servers\mcp-linux-infra

# Vérifier dépendances
~/.local/bin/uv.exe pip list

# Tester imports
.venv/Scripts/python.exe -c "
import sys
sys.path.insert(0, 'src')
from mcp_linux_infra.server import mcp
print('OK')
"

# Vérifier syntaxe
./test-integrity.sh
```

**Solution**:
```bash
# Réinstaller dépendances
~/.local/bin/uv.exe pip install -e .

# Ou recréer venv
rm -rf .venv
~/.local/bin/uv.exe venv
~/.local/bin/uv.exe pip install -e .
```

---

### 6. "Timeout" ou "No response"

**Symptôme**: Commande timeout, pas de réponse

**Causes possibles**:
- Host down
- Firewall bloque SSH
- Commande trop lente
- Deadlock asyncio

**Diagnostic**:
```bash
# Tester connectivité
ping coreos-11.local

# Tester SSH direct
ssh ansible@coreos-11.local 'echo OK'

# Vérifier logs en temps réel
tail -f logs/mcp-linux-infra.log
```

**Solution**:
- Augmenter timeout dans le code
- Vérifier connectivité réseau
- Relancer le serveur MCP

---

### 7. "Permission denied" sur SSH

**Symptôme**: Permission refusée lors de l'exécution de commandes

**Causes possibles**:
- User `ansible` n'a pas les droits
- Sudo requis mais pas configuré
- SELinux/AppArmor bloque

**Diagnostic**:
```bash
# Vérifier droits sudo
ssh ansible@coreos-11.local 'sudo -l'

# Vérifier user
ssh ansible@coreos-11.local 'whoami'

# Vérifier groups
ssh ansible@coreos-11.local 'groups'
```

**Solution**:
- Ajouter `ansible` à sudoers avec NOPASSWD
- Utiliser un user avec plus de droits
- Modifier la commande pour ne pas nécessiter sudo

---

## 📊 Logs et Debugging

### Activer DEBUG logs
```bash
# Dans .env
LINUX_MCP_LOG_LEVEL=DEBUG
```

### Localisation des logs
```
D:\infra\mcp-servers\mcp-linux-infra\logs\mcp-linux-infra.log
```

### Consulter logs en temps réel
```bash
tail -f D:\infra\mcp-servers\mcp-linux-infra\logs\mcp-linux-infra.log
```

### Filtrer erreurs
```bash
grep ERROR D:\infra\mcp-servers\mcp-linux-infra\logs\mcp-linux-infra.log
```

---

## 🛠️ Outils de Diagnostic

### Test d'intégrité complet
```bash
cd D:\infra\mcp-servers\mcp-linux-infra
./test-integrity.sh
```

### Test connexion SSH
```bash
ssh -vvv ansible@coreos-11.local
```

### Test SSH Agent
```powershell
Get-Service ssh-agent
ssh-add -l
```

### Test serveur MCP manuel
```bash
cd D:\infra\mcp-servers\mcp-linux-infra
~/.local/bin/uv.exe run mcp-linux-infra
```

---

## 🔄 Reset Complet

Si tout échoue :

```bash
# 1. Arrêter Claude Desktop

# 2. Nettoyer venv
cd D:\infra\mcp-servers\mcp-linux-infra
rm -rf .venv

# 3. Réinstaller
~/.local/bin/uv.exe venv
~/.local/bin/uv.exe pip install -e .

# 4. Vérifier
./test-integrity.sh

# 5. Nettoyer logs
rm logs/*.log

# 6. Redémarrer Claude Desktop
```

---

## 📞 Support

### Documentation
- `README.md` - Architecture générale
- `TEST-LINUX-INFRA.md` - Tests détaillés
- `INTEGRITY-CHECK-LINUX-INFRA.md` - Rapport d'intégrité
- `QUICK-START-LINUX-INFRA.md` - Quick start

### Fichiers Clés
- `claude_desktop_config.json` - Config Claude Desktop
- `.env` - Variables d'environnement
- `pyproject.toml` - Dépendances Python
- `src/mcp_linux_infra/server.py` - Serveur MCP

### Commandes Utiles
```bash
# Status complet
systemctl status ssh-agent     # Windows: Get-Service ssh-agent
ssh-add -l                      # Clés chargées
uv pip list                     # Packages Python
grep @mcp.tool server.py | wc -l  # Nombre de tools
```

---

**Dernière mise à jour**: 2026-01-19
**Version**: 0.1.0
