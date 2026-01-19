# MCP Linux Infra - Production-Ready Infrastructure Management

**Architecture de référence pour PRA (Plan de Reprise d'Activité) avec MCP et SSH key-based authentication**

**Version**: 0.3.0 - Smart Analysis + Auto-Learning + Plugin System 🧠🔌

## Architecture Sécurisée

```
┌─────────────────────────────────────────────────────────────┐
│                      CLAUDE (IA)                            │
└────────────┬────────────────────────────────┬───────────────┘
             │                                │
             │ MCP tool-call                  │ propose action
             │ (observation)                  │
             ▼                                ▼
     ┌───────────────┐              ┌─────────────────┐
     │  MCP Server   │              │ VALIDATION      │
     │  (SSH client) │              │ HUMAINE         │
     └───────┬───────┘              └────────┬────────┘
             │                                │
             │ ssh -i mcp-reader.key          │ ssh -i pra-exec.key
             │ mcp-reader@target              │ pra-runner@target
             ▼                                ▼
     ┌─────────────────────────────────────────────────────┐
     │           LINUX TARGET (infra réelle)               │
     │                                                     │
     │  mcp-reader → read-only (diagnostics)              │
     │  pra-runner → exec contrôlé (actions PRA)          │
     └─────────────────────────────────────────────────────┘
```

## Principes de Sécurité

### ✅ Séparation stricte des privilèges

**2 comptes SSH distincts :**
- `mcp-reader` : **read-only** (diagnostics, monitoring)
- `pra-runner` : **exec** (actions PRA validées par humain)

**2 clés SSH différentes :**
- `mcp-reader.key` : authentification diagnostics
- `pra-exec.key` : authentification actions

**2 niveaux de confiance :**
- MCP observe → aucune action possible
- PRA exécute → après validation humaine

### ✅ Forced-command SSH

```bash
# authorized_keys avec command= force
command="/usr/local/bin/mcp-wrapper",no-pty,no-agent-forwarding ssh-ed25519 ...
```

**Résultat :**
- Impossible d'ouvrir un shell
- Une seule commande possible : le wrapper
- Whitelist stricte dans le wrapper

### ✅ Audit trail complet

- Tous les appels SSH loggés (`/var/log/auth.log`)
- Actions PRA tracées (`/var/log/pra-exec.log`)
- Structured logging dans le MCP server
- Sanitization des paramètres sensibles

## Structure du Projet

```
mcp-linux-infra/
├── src/mcp_linux_infra/          # MCP Server (Python)
│   ├── server.py                  # Point d'entrée FastMCP (34 tools)
│   ├── config.py                  # Configuration centralisée
│   ├── audit.py                   # Logging structuré
│   ├── authorization/             # 🆕 Système d'autorisation
│   │   ├── engine.py              # Moteur d'autorisation
│   │   ├── models.py              # Modèles d'autorisation
│   │   └── whitelist.py           # Whitelist de commandes
│   ├── analysis/                  # 🆕 Smart Analysis & Learning
│   │   ├── command_analysis.py    # Analyse de sécurité
│   │   └── auto_learning.py       # Auto-apprentissage
│   ├── connection/
│   │   ├── ssh.py                 # SSH connection pooling
│   │   └── ansible.py             # Wrapper Ansible CLI
│   ├── tools/
│   │   ├── diagnostics/           # Read-only tools (SSH mcp-reader)
│   │   │   ├── system.py
│   │   │   ├── network.py
│   │   │   ├── services.py
│   │   │   └── logs.py
│   │   ├── pra/                   # Exec tools (SSH pra-runner)
│   │   │   ├── validation.py      # Validation humaine
│   │   │   ├── actions.py         # Actions PRA
│   │   │   └── idempotence.py     # Vérification idempotence
│   │   └── execution/             # 🆕 SSH Command Execution
│   │       ├── ssh_executor.py    # Exécuteur SSH autorisé
│   │       └── ansible_wrapper.py # Wrapper Ansible remote
│   └── utils/
│       ├── decorators.py          # Sécurité, logging
│       └── validation.py
│
├── system/                        # Scripts déployés sur targets
│   ├── wrappers/
│   │   ├── mcp-wrapper            # Whitelist read-only
│   │   └── pra-exec               # Whitelist actions PRA
│   ├── pra-run                    # Script exécuteur PRA
│   └── sudoers.d/
│       └── pra-runner             # Configuration sudo
│
├── ansible/                       # Déploiement automatisé
│   ├── playbooks/
│   │   ├── deploy-mcp-infra.yml   # Setup complet
│   │   └── rotate-keys.yml        # Rotation clés
│   └── roles/mcp_infra/
│       ├── tasks/
│       │   ├── main.yml
│       │   ├── users.yml          # Création comptes
│       │   ├── ssh.yml            # Config SSH
│       │   └── wrappers.yml       # Installation wrappers
│       ├── templates/
│       │   ├── authorized_keys.j2
│       │   ├── mcp-wrapper.j2
│       │   └── pra-exec.j2
│       └── files/
│           └── pra-run
│
├── docs/
│   ├── ARCHITECTURE.md            # Architecture détaillée
│   ├── SECURITY.md                # Modèle de sécurité
│   ├── PRA-PROCEDURES.md          # Procédures PRA
│   └── KEY-ROTATION.md            # Rotation des clés
│
├── keys/                          # Clés SSH (gitignored)
│   ├── mcp-reader.key             # Clé diagnostics
│   ├── mcp-reader.key.pub
│   ├── pra-exec.key               # Clé actions
│   └── pra-exec.key.pub
│
├── tests/
│   ├── test_security.py           # Tests sécurité
│   ├── test_wrappers.py           # Tests whitelist
│   └── test_idempotence.py        # Tests idempotence
│
├── pyproject.toml                 # Configuration projet
├── uv.lock                        # Lockfile dependencies
└── .env.example                   # Configuration exemple
```

## Installation Rapide

### 1. Génération des clés SSH

```bash
# Clé read-only (diagnostics)
ssh-keygen -t ed25519 -f keys/mcp-reader.key -C "mcp-reader@infra"

# Clé exec (PRA)
ssh-keygen -t ed25519 -f keys/pra-exec.key -C "pra-runner@infra"
```

### 2. Déploiement sur targets

```bash
# Avec Ansible (recommandé)
cd ansible
ansible-playbook -i inventory/production.ini playbooks/deploy-mcp-infra.yml

# Ou script manuel
./scripts/deploy-manual.sh target.example.com
```

### 3. Configuration MCP Server

```bash
# Installation dependencies
uv sync

# Configuration
cp .env.example .env
# Éditer .env avec vos paramètres

# Lancement
uv run mcp-linux-infra
```

### 4. Enregistrement dans Claude Desktop

```json
{
  "mcpServers": {
    "linux-infra": {
      "command": "uv",
      "args": [
        "--directory",
        "D:\\infra\\mcp-servers\\mcp-linux-infra",
        "run",
        "mcp-linux-infra"
      ],
      "env": {
        "LINUX_MCP_SSH_KEY_PATH": "D:\\infra\\mcp-servers\\mcp-linux-infra\\keys\\mcp-reader.key",
        "LINUX_MCP_PRA_KEY_PATH": "D:\\infra\\mcp-servers\\mcp-linux-infra\\keys\\pra-exec.key",
        "LINUX_MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Usage

### Diagnostics (automatique, aucune validation requise)

```python
# Via MCP tools (read-only, SSH mcp-reader)
mcp.call_tool("diagnose_system", {
    "host": "web01.infra",
    "checks": ["services", "network", "disk"]
})

mcp.call_tool("get_service_status", {
    "host": "web01.infra",
    "service": "unbound"
})

mcp.call_tool("fetch_logs", {
    "host": "web01.infra",
    "service": "caddy",
    "lines": 100
})
```

### Actions PRA (requiert validation humaine)

```python
# 1. IA détecte un problème
status = mcp.call_tool("diagnose_system", {"host": "web01.infra"})
# Résultat: unbound service inactive

# 2. IA propose une action
proposed_action = {
    "action": "restart_unbound",
    "host": "web01.infra",
    "rationale": "Service unbound inactive, impact sur résolution DNS"
}

# 3. Validation humaine (via interface)
# User: APPROVE

# 4. Exécution via PRA (SSH pra-runner)
result = mcp.call_tool("execute_pra_action", {
    "host": "web01.infra",
    "action": "restart_unbound",
    "approval_token": "user_approved_xyz"
})

# 5. Vérification post-action
verification = mcp.call_tool("verify_service", {
    "host": "web01.infra",
    "service": "unbound"
})
```

## Sécurité

### Ce que vous gagnez

✅ **Séparation stricte** : diagnostics ≠ actions
✅ **Traçabilité** : audit trail complet
✅ **Révocation rapide** : rotation des clés simple
✅ **Zéro confiance** : validation humaine obligatoire
✅ **Pas de credential replay** : clés SSH asymétriques
✅ **Jail SSH** : forced-command + whitelist
✅ **Compatible bastion** : architecture jumphost-ready

### Actions PRA disponibles

Par défaut, whitelist minimale (extensible) :
- `restart_unbound` : Redémarrage DNS
- `reload_caddy` : Rechargement reverse proxy
- `flush_dns_cache` : Purge cache DNS
- `restart_container` : Redémarrage conteneur Podman
- `rotate_logs` : Rotation logs applicatifs

**Ajouter une action :**
1. Ajouter dans `system/pra-run` (script)
2. Ajouter dans `system/wrappers/pra-exec` (whitelist)
3. Tester idempotence
4. Déployer avec Ansible

## 🆕 Nouvelles Fonctionnalités (v0.2.0)

### 🧠 Smart Command Analysis & Auto-Learning

Système intelligent pour gérer la whitelist de commandes :

#### 1. Analyse de Sécurité (`analyze_command`)

```python
analyze_command(command="htop", host="coreos-11")
```

Fournit :
- Évaluation du risque (CRITICAL/HIGH/MEDIUM/LOW)
- Catégorisation automatique
- Recommandations d'action (ADD_AUTO, ADD_MANUAL, BLOCK)
- Comparaison avec commandes similaires whitelistées

#### 2. Auto-Learning (`get_learning_suggestions`)

```python
get_learning_suggestions(min_count=5, min_age_hours=24)
```

Le système apprend automatiquement :
- Enregistre toutes les commandes bloquées
- Identifie les patterns récurrents
- Suggère des ajouts à la whitelist (commandes LOW risk uniquement)
- Trie par fréquence d'utilisation

#### 3. Statistiques (`get_learning_stats`)

```python
get_learning_stats()
```

Dashboard complet :
- Total de commandes bloquées
- Breakdown par niveau de risque
- Top 10 des commandes les plus bloquées
- Métriques d'utilisation

#### 4. Workflow Interactif

Quand une commande est bloquée, suggestions automatiques :

```
❌ COMMAND BLOCKED

Command: htop
Risk Level: LOW
Category: monitoring

💡 SUGGESTIONS:
  ✅ This command appears SAFE (read-only)
  → analyze_command("htop")
  → propose_pra_action(action="htop", host="...")
```

**Documentation complète** : [COMMAND-ANALYSIS.md](./COMMAND-ANALYSIS.md)

---

## 🔌 Plugin System (v0.3.0)

### Commandes organisées par famille

**136+ commandes** réparties dans **8 plugins** :

| Plugin | Commandes | Description |
|--------|-----------|-------------|
| 📊 **Monitoring** | 10 | htop, iotop, nethogs, glances... |
| 🌐 **Network** | 14 | ping, curl, netstat, dig... |
| 📁 **Filesystem** | 17 | ls, grep, cat, find... |
| ⚙️ **Systemd** | 15 | systemctl, journalctl... |
| 🐳 **Containers** | 19 | podman, docker (ps/logs/restart)... |
| 🔧 **POSIX System** | 24 | uname, hostname, date, pwd... |
| ⚡ **POSIX Process** | 16 | ps, kill, nice, lsof... |
| 📝 **POSIX Text** | 21 | sed, awk, cut, sort, tr... |

### Nouveaux MCP Tools

```python
# Lister tous les plugins
list_command_plugins()

# Détails d'un plugin avec exemples
get_plugin_details("monitoring")

# Chercher des commandes
search_commands("docker")
search_commands("process")
```

**Documentation complète** : [PLUGINS.md](./PLUGINS.md)

---

## Roadmap

- [x] Architecture core
- [x] SSH connection pooling
- [x] Tools diagnostics read-only
- [x] Système PRA avec validation
- [x] Wrappers SSH sécurisés
- [x] Déploiement Ansible
- [x] 🆕 Smart Command Analysis (v0.2.0)
- [x] 🆕 Auto-Learning System (v0.2.0)
- [x] �� Command Authorization Engine (v0.2.0)
- [x] 🔌 Plugin System (v0.3.0)
- [x] 🔌 8 Builtin Plugins - 136+ commands (v0.3.0)
- [x] 🔌 Plugin Auto-Discovery (v0.3.0)
- [x] 🔧 POSIX Plugins (System, Process, Text) (v0.3.0)
- [ ] Plugin Git commands
- [ ] Plugin Security/Audit
- [ ] Plugin Kubernetes
- [ ] Bastion/jumphost support
- [ ] Tests automatisés complets
- [ ] Monitoring métriques MCP
- [ ] Integration avec Vault (secrets)
- [ ] Dashboard validation PRA
- [ ] Multi-tenancy support

## License

MIT

## Support

- Documentation : `docs/`
- Issues : GitHub issues
- Security : voir `SECURITY.md`
