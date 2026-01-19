# Configuration Claude Desktop pour MCP Linux Infra

**MCP Linux Infra v0.3.0** - Guide d'intégration avec Claude Desktop

## 📋 Prérequis

Avant de configurer Claude Desktop, assure-toi que:

- ✅ MCP Linux Infra est installé: `pip install -e .`
- ✅ SSH Agent est configuré (voir `SSH-AGENT-SETUP.md`)
- ✅ Les clés SSH sont chargées: `ssh-add -l`
- ✅ Python est accessible dans le PATH

## 🔧 Configuration

### Étape 1: Localiser le fichier de configuration Claude Desktop

Le fichier de configuration se trouve à différents emplacements selon l'OS:

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```
Chemin complet typique:
```
C:\Users\<USERNAME>\AppData\Roaming\Claude\claude_desktop_config.json
```

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

### Étape 2: Éditer la configuration

Ouvre le fichier `claude_desktop_config.json` avec un éditeur de texte et ajoute la configuration MCP:

```json
{
  "mcpServers": {
    "mcp-linux-infra": {
      "command": "python",
      "args": [
        "-m",
        "mcp_linux_infra.server"
      ],
      "cwd": "D:\\infra\\mcp-servers\\mcp-linux-infra",
      "env": {
        "PYTHONPATH": "D:\\infra\\mcp-servers\\mcp-linux-infra\\src",
        "LINUX_MCP_SSH_KEY_PATH": "${HOME}/.ssh/mcp-reader",
        "LINUX_MCP_PRA_KEY_PATH": "${HOME}/.ssh/pra-runner",
        "LINUX_MCP_PRA_USER": "pra-runner",
        "LINUX_MCP_ALLOWED_HOSTS": "*",
        "LINUX_MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**⚠️ IMPORTANT**: Adapter les chemins selon ton installation:
- `cwd`: Chemin vers le répertoire mcp-linux-infra
- `PYTHONPATH`: Chemin vers le sous-répertoire src/

### Étape 3: Configuration avancée (optionnel)

#### Mode SSH Agent (Recommandé)

Si tu utilises SSH Agent, tu peux simplifier la config:

```json
{
  "mcpServers": {
    "mcp-linux-infra": {
      "command": "python",
      "args": ["-m", "mcp_linux_infra.server"],
      "cwd": "D:\\infra\\mcp-servers\\mcp-linux-infra",
      "env": {
        "PYTHONPATH": "D:\\infra\\mcp-servers\\mcp-linux-infra\\src"
      }
    }
  }
}
```

Les clés SSH seront automatiquement récupérées depuis l'agent.

#### Hosts restreints

Pour limiter l'accès à des serveurs spécifiques:

```json
{
  "env": {
    "LINUX_MCP_ALLOWED_HOSTS": "server1,server2,server3"
  }
}
```

#### Logs détaillés (debug)

Pour le troubleshooting:

```json
{
  "env": {
    "LINUX_MCP_LOG_LEVEL": "DEBUG",
    "LINUX_MCP_LOG_DIR": "D:\\infra\\logs"
  }
}
```

### Étape 4: Redémarrer Claude Desktop

1. Ferme complètement Claude Desktop
2. Relance l'application
3. Ouvre une nouvelle conversation

## ✅ Vérification

### Test 1: Vérifier que le serveur MCP est détecté

Dans Claude Desktop, tape:

```
Liste les outils MCP disponibles
```

Tu devrais voir apparaître les 37 outils de MCP Linux Infra:
- `get_system_info`
- `list_services`
- `execute_ssh_command`
- `list_command_plugins`
- `analyze_command`
- etc.

### Test 2: Tester une commande simple

```
Utilise MCP pour lister les informations système du serveur server1
```

Ou:

```
Avec MCP, montre-moi les plugins de commandes disponibles
```

### Test 3: Tester l'analyse de commande

```
Analyse la sécurité de la commande "rm -rf /" avec MCP
```

## 🎯 Exemples de prompts

### Diagnostic système

```
Utilise MCP pour:
1. Obtenir les infos système de server1
2. Lister les services actifs
3. Vérifier l'utilisation du disque
```

### Gestion de services

```
Avec MCP, vérifie le statut du service nginx sur server1
```

### Analyse de commandes

```
J'aimerais exécuter "systemctl restart nginx" sur server1.
Utilise MCP pour analyser cette commande et me dire si elle est sûre.
```

### Plugins et commandes

```
Montre-moi tous les plugins de commandes disponibles dans MCP,
et donne-moi des exemples pour chaque catégorie.
```

### Auto-learning

```
Avec MCP, montre-moi les statistiques d'auto-learning:
- Combien de commandes ont été bloquées?
- Quelles suggestions pour la whitelist?
```

### Workflow complet

```
Je veux diagnostiquer un problème sur server1:

1. Utilise MCP pour obtenir les infos système
2. Vérifie l'état du service nginx
3. Récupère les derniers logs nginx
4. Analyse les erreurs trouvées
5. Propose des actions correctives avec analyse de risque
```

## 🔍 Troubleshooting

### Problème: "MCP server not found"

**Cause**: Claude Desktop ne trouve pas le serveur MCP

**Solution**:
1. Vérifier le chemin dans `cwd`
2. Vérifier que Python est dans le PATH
3. Vérifier les logs Claude Desktop:
   - Windows: `%APPDATA%\Claude\logs\`
   - macOS: `~/Library/Logs/Claude/`
   - Linux: `~/.config/Claude/logs/`

### Problème: "ModuleNotFoundError: mcp_linux_infra"

**Cause**: PYTHONPATH incorrect

**Solution**:
```json
{
  "env": {
    "PYTHONPATH": "D:\\infra\\mcp-servers\\mcp-linux-infra\\src"
  }
}
```

Le chemin doit pointer vers le répertoire contenant `mcp_linux_infra/`

### Problème: "SSH connection failed"

**Cause**: Clés SSH non configurées

**Solution**:
1. Vérifier l'agent SSH: `ssh-add -l`
2. Charger les clés si nécessaire: `ssh-add ~/.ssh/mcp-reader`
3. Ou définir les chemins explicitement dans la config

### Problème: "Permission denied"

**Cause**: Clés publiques non installées sur le serveur cible

**Solution**:
```bash
ssh-copy-id -i ~/.ssh/mcp-reader.pub mcp-reader@server1
ssh-copy-id -i ~/.ssh/pra-runner.pub pra-runner@server1
```

### Problème: Claude Desktop se ferme immédiatement

**Cause**: Erreur dans le fichier JSON

**Solution**:
1. Valider le JSON: https://jsonlint.com/
2. Vérifier les virgules et guillemets
3. Pas de commentaires dans le JSON

## 📝 Configuration complète (template)

Voici un template complet pour Windows:

```json
{
  "mcpServers": {
    "mcp-linux-infra": {
      "command": "python",
      "args": [
        "-m",
        "mcp_linux_infra.server"
      ],
      "cwd": "D:\\infra\\mcp-servers\\mcp-linux-infra",
      "env": {
        "PYTHONPATH": "D:\\infra\\mcp-servers\\mcp-linux-infra\\src",

        "LINUX_MCP_USER": "admin",

        "LINUX_MCP_SSH_KEY_PATH": "${HOME}/.ssh/mcp-reader",
        "LINUX_MCP_PRA_KEY_PATH": "${HOME}/.ssh/pra-runner",
        "LINUX_MCP_PRA_USER": "pra-runner",

        "LINUX_MCP_SSH_CONNECTION_TIMEOUT": "30",
        "LINUX_MCP_SSH_KEEPALIVE_INTERVAL": "60",
        "LINUX_MCP_SSH_MAX_CONNECTIONS": "10",

        "LINUX_MCP_LOG_DIR": "D:\\infra\\logs\\mcp",
        "LINUX_MCP_LOG_LEVEL": "INFO",
        "LINUX_MCP_LOG_RETENTION_DAYS": "30",

        "LINUX_MCP_ALLOWED_HOSTS": "*",
        "LINUX_MCP_REQUIRE_APPROVAL_FOR_PRA": "true",

        "LINUX_MCP_DEFAULT_LOG_LINES": "100",
        "LINUX_MCP_DEFAULT_COMMAND_TIMEOUT": "120"
      }
    }
  }
}
```

Template pour macOS/Linux:

```json
{
  "mcpServers": {
    "mcp-linux-infra": {
      "command": "python3",
      "args": [
        "-m",
        "mcp_linux_infra.server"
      ],
      "cwd": "/path/to/mcp-linux-infra",
      "env": {
        "PYTHONPATH": "/path/to/mcp-linux-infra/src",
        "LINUX_MCP_ALLOWED_HOSTS": "*",
        "LINUX_MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## 🎨 Exemples de conversations

### Exemple 1: Diagnostic simple

**Toi:**
```
Utilise MCP pour me montrer les infos système de server1
```

**Claude:**
```
Je vais utiliser l'outil MCP pour obtenir les informations système.

[Appel de l'outil get_system_info avec host="server1"]

Voici les informations système de server1:
- OS: Ubuntu 22.04 LTS
- Kernel: 5.15.0-91-generic
- Uptime: 45 jours
- CPU: 8 cores @ 2.4GHz
- Memory: 16GB (12GB utilisés, 4GB libres)
- Disk: 256GB (180GB utilisés, 76GB libres)
```

### Exemple 2: Workflow multi-étapes

**Toi:**
```
Aide-moi à diagnostiquer pourquoi nginx ne répond plus sur server1
```

**Claude:**
```
Je vais faire un diagnostic complet en plusieurs étapes:

1. Vérification du service nginx...
[Appel get_service_status]
→ nginx est arrêté (dead)

2. Récupération des logs...
[Appel get_service_logs]
→ Erreur de configuration détectée

3. Analyse du problème...
Le port 80 est déjà utilisé par un autre processus.

4. Actions proposées:
   a) Identifier le processus sur le port 80
   b) Corriger la configuration nginx
   c) Redémarrer nginx

Souhaitez-vous que je procède à l'analyse du port 80?
```

### Exemple 3: Utilisation des plugins

**Toi:**
```
Montre-moi tous les plugins disponibles et leurs commandes
```

**Claude:**
```
[Appel list_command_plugins]

MCP Linux Infra dispose de 8 plugins avec 135 commandes:

🔍 Monitoring (10 commandes)
   - htop, iotop, vmstat, iostat, glances...

🌐 Network (14 commandes)
   - ping, curl, dig, netstat, ss, traceroute...

📁 Filesystem (17 commandes)
   - ls, find, grep, cat, du, df, tree...

⚙️ Systemd (15 commandes)
   - systemctl status/restart/start/stop
   - journalctl avec filtres

🐳 Containers (18 commandes)
   - podman/docker ps, logs, inspect, stats...

💻 POSIX System (24 commandes)
   - uname, date, uptime, who, id, pwd...

🔧 POSIX Process (16 commandes)
   - ps, kill, nice, lsof, strace...

📝 POSIX Text (21 commandes)
   - sed, awk, cut, sort, grep, tr...

Voulez-vous des détails sur un plugin spécifique?
```

## 🚀 Workflow avancés

### Workflow 1: Health Check automatisé

```
Crée un rapport de santé complet pour server1:
1. Info système
2. État de tous les services
3. Utilisation disque/mémoire/CPU
4. Dernières erreurs dans les logs
5. Recommandations d'actions
```

### Workflow 2: Déploiement sécurisé

```
Je veux redémarrer nginx sur server1 en utilisant MCP:
1. Analyse d'abord la commande "systemctl restart nginx"
2. Vérifie que c'est sûr
3. Si OK, propose le workflow PRA complet
4. Attend mon approbation avant exécution
```

### Workflow 3: Investigation de problème

```
Un serveur est lent, aide-moi à investiguer:
1. Vérifie les métriques système
2. Liste les processus consommant le plus de CPU
3. Vérifie l'espace disque
4. Récupère les logs système récents
5. Propose des hypothèses basées sur les données
```

## 📚 Ressources

- **README.md**: Architecture complète
- **PLUGINS.md**: Référence des 135 commandes
- **COMMAND-ANALYSIS.md**: Système d'analyse intelligente
- **SSH-AGENT-SETUP.md**: Configuration SSH Agent
- **QUICK-DEPLOY.md**: Guide de déploiement

## 🔐 Sécurité

### Bonnes pratiques

1. **Utiliser SSH Agent** (mode préféré)
2. **Limiter les hosts autorisés** avec `LINUX_MCP_ALLOWED_HOSTS`
3. **Activer l'approbation PRA** avec `LINUX_MCP_REQUIRE_APPROVAL_FOR_PRA=true`
4. **Logs d'audit** toujours activés
5. **Deux comptes SSH** séparés (mcp-reader, pra-runner)

### Ce que MCP ne fera JAMAIS automatiquement

- ❌ Commandes destructives (rm -rf, dd, mkfs, etc.)
- ❌ Modifications système sans approbation
- ❌ Accès à des hosts non autorisés
- ❌ Bypass de la whitelist de commandes

### Ce que tu dois toujours approuver

- ⚠️ Redémarrage de services
- ⚠️ Modifications de configuration
- ⚠️ Actions PRA (Plan de Reprise d'Activité)
- ⚠️ Commandes avec niveau MANUAL ou HIGH

## 🎯 Checklist de configuration

- [ ] MCP Linux Infra installé (`pip install -e .`)
- [ ] SSH Agent configuré (voir SSH-AGENT-SETUP.md)
- [ ] Clés SSH chargées (`ssh-add -l`)
- [ ] Clés distribuées sur serveurs cibles
- [ ] Fichier claude_desktop_config.json édité
- [ ] Chemins adaptés dans la config
- [ ] Claude Desktop redémarré
- [ ] Test avec "Liste les outils MCP disponibles"
- [ ] Test connexion SSH vers un serveur

---

**Version**: 0.3.0
**Date**: 2026-01-19
**Status**: ✅ Production Ready
