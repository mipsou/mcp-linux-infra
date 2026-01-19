# 🧠 Smart Command Analysis & Auto-Learning

**Version**: 0.2.0
**Feature**: Intelligent whitelist management with auto-learning

---

## 🎯 Vue d'Ensemble

Le système d'analyse de commandes et d'auto-apprentissage permet de :

1. **Analyser** la sécurité de n'importe quelle commande
2. **Apprendre** des patterns de commandes bloquées
3. **Suggérer** automatiquement des ajouts à la whitelist
4. **Workflow interactif** avec recommandations intelligentes

---

## 🔍 Fonctionnalités

### 1. Analyse de Commande (`analyze_command`)

Analyse une commande et fournit des recommandations détaillées.

#### Usage

```python
analyze_command(command="htop", host="coreos-11")
```

#### Output

```
🔍 COMMAND ANALYSIS

Command: htop
Host: coreos-11
Status: NOT_IN_WHITELIST

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 RISK ASSESSMENT

Risk Level: LOW
Category: monitoring
Read-Only: Yes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 SUGGESTION

Recommended Action: ADD_AUTO

Authorization Level: AUTO
SSH User: mcp-reader
Rationale: Interactive process viewer (read-only)

Can Auto-Add: Yes ✅

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 SIMILAR COMMANDS IN WHITELIST

  • Check service status (AUTO)
  • List system units (AUTO)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚙️  NEXT STEPS

1. Add to whitelist as AUTO (recommended):
   Pattern: ^htop$
   Level: AUTO
   User: mcp-reader

2. Execute once via PRA:
   Use: propose_pra_action(action="htop", host="coreos-11")
```

---

### 2. Auto-Learning Stats (`get_learning_stats`)

Affiche les statistiques d'apprentissage du système.

#### Usage

```python
get_learning_stats()
```

#### Output

```
📊 AUTO-LEARNING STATISTICS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Overview:
  • Total Unique Commands: 15
  • Total Block Attempts: 47
  • Stats File: D:\infra\mcp-servers\mcp-linux-infra\logs\command_stats.json

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Risk Level Breakdown:
  • LOW: 10 commands
  • MEDIUM: 3 commands
  • CRITICAL: 2 commands

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Category Breakdown:
  • monitoring: 8 commands
  • network: 2 commands
  • system_modification: 3 commands
  • destructive: 2 commands

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔝 TOP 10 MOST BLOCKED COMMANDS:

  1. htop
     Blocked: 15 times | Risk: LOW
     Users: alice, bob

  2. iotop
     Blocked: 12 times | Risk: LOW
     Users: alice, charlie

  3. systemctl restart nginx
     Blocked: 8 times | Risk: MEDIUM
     Users: bob

💡 Use get_learning_suggestions() to see whitelist recommendations.
```

---

### 3. Learning Suggestions (`get_learning_suggestions`)

Obtient des suggestions basées sur l'historique des commandes bloquées.

#### Usage

```python
get_learning_suggestions(min_count=5, min_age_hours=24)
```

#### Paramètres

- `min_count` (int): Nombre minimum de tentatives bloquées (défaut: 5)
- `min_age_hours` (int): Âge minimum en heures (défaut: 24)

#### Output

```
📊 AUTO-LEARNING SUGGESTIONS

Found 3 command(s) that could be added to whitelist.

Criteria:
  • Minimum blocked attempts: 5
  • Minimum age: 24 hours
  • Maximum risk: LOW

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【1】 htop

  Statistics:
    • Blocked 15 times
    • First seen 72 hours ago
    • Users: alice, bob
    • Hosts: coreos-11, coreos-12

  Analysis:
    • Risk Level: LOW
    • Category: monitoring
    • Suggested Level: AUTO
    • SSH User: mcp-reader
    • Rationale: Interactive process viewer (read-only)

  Recommendation: ADD_AUTO
  ✅ Can auto-add

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【2】 iotop

  Statistics:
    • Blocked 12 times
    • First seen 48 hours ago
    • Users: alice, charlie
    • Hosts: coreos-11

  Analysis:
    • Risk Level: LOW
    • Category: monitoring
    • Suggested Level: AUTO
    • SSH User: mcp-reader
    • Rationale: I/O monitoring (read-only)

  Recommendation: ADD_AUTO
  ✅ Can auto-add

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 To add a command to whitelist:
   1. Edit src/mcp_linux_infra/authorization/whitelist.py
   2. Add CommandRule with suggested parameters
   3. Restart MCP server
```

---

## 🚀 Workflow Interactif

Quand une commande est bloquée, le système suggère automatiquement des actions.

### Scénario 1 : Commande Sûre Bloquée

```
User: Exécute 'htop' sur coreos-11
```

**Réponse** :
```
❌ COMMAND BLOCKED

Command: htop
Reason: Command not in whitelist (default deny policy)
Risk Level: LOW
Category: monitoring

This command is blocked for security reasons.

💡 SUGGESTIONS:

  ✅ This command appears SAFE (read-only)
  → You can analyze it with: analyze_command("htop")
  → Or execute once via PRA: propose_pra_action(action="htop", host="coreos-11")
```

### Scénario 2 : Commande Dangereuse Bloquée

```
User: Exécute 'rm -rf /var/log' sur coreos-11
```

**Réponse** :
```
❌ COMMAND BLOCKED

Command: rm -rf /var/log
Reason: Command not in whitelist (default deny policy)
Risk Level: CRITICAL
Category: destructive

This command is blocked for security reasons.

💡 SUGGESTIONS:

  ⚠️  This command is DANGEROUS
  → Use Ansible playbook instead for safe execution
  → Consider safer alternatives
```

---

## 📊 Niveaux de Risque

### CRITICAL (Bloqué permanent)
- Commandes destructives : `rm -rf /`, `dd`, `mkfs`, `fdisk`
- Fork bombs
- Modifications dangereuses de permissions

**Action** : BLOCK - Ne jamais whitelister

### HIGH
- Modifications système importantes
- Changements de sécurité

**Action** : Utiliser Ansible avec rollback

### MEDIUM (Nécessite approbation)
- Redémarrages de services
- Modifications de configuration
- `reboot`, `shutdown`

**Action** : ADD_MANUAL - Whitelist avec approbation humaine

### LOW (Sûr)
- Commandes read-only
- Outils de monitoring : `htop`, `iotop`, `netstat`
- Lecture de logs

**Action** : ADD_AUTO - Whitelist automatiquement

### UNKNOWN
- Commande non reconnue

**Action** : Analyse manuelle requise

---

## 🎓 Catalogue de Commandes Sûres

Le système reconnaît automatiquement ces commandes comme sûres :

### Monitoring
- `htop` - Process viewer interactif
- `top` - Process monitor
- `iotop` - I/O monitoring
- `iftop` - Network bandwidth
- `nethogs` - Network traffic per process

### Network
- `netstat` - Network connections
- `ip addr` - IP addresses
- `ip route` - Routing table
- `ping` - Connectivity test
- `traceroute` - Network path

### System Info
- `hostname` - Hostname
- `uname` - System info
- `lsblk` - Block devices
- `lscpu` - CPU info
- `lsmem` - Memory info

### File Operations (Read-Only)
- `ls` - List files
- `head` - File beginning
- `tail` - File end
- `less` - File viewer
- `grep` - Text search

---

## 🛠️ Comment Ajouter une Commande à la Whitelist

### 1. Analyser la Commande

```python
analyze_command("htop")
```

### 2. Vérifier les Suggestions

Regarder la section "NEXT STEPS" de l'analyse.

### 3. Éditer la Whitelist

Fichier : `src/mcp_linux_infra/authorization/whitelist.py`

```python
from .models import CommandRule, AuthorizationLevel

# Ajouter à COMMAND_WHITELIST
CommandRule(
    pattern=r"^htop$",
    level=AuthorizationLevel.AUTO,
    ssh_user="mcp-reader",
    description="Interactive process viewer",
    rationale="Read-only monitoring tool"
)
```

### 4. Redémarrer MCP

```bash
# Redémarrer Claude Desktop
# Ou si serveur standalone
uv run mcp-linux-infra
```

---

## 📈 Métriques et Monitoring

### Fichier de Stats

```
D:\infra\mcp-servers\mcp-linux-infra\logs\command_stats.json
```

Format :
```json
{
  "htop": {
    "command": "htop",
    "count": 15,
    "first_seen": "2026-01-19T10:00:00",
    "last_seen": "2026-01-19T14:30:00",
    "users": ["alice", "bob"],
    "hosts": ["coreos-11", "coreos-12"],
    "risk_level": "LOW",
    "category": "monitoring"
  }
}
```

### Consulter les Stats

```bash
# Via jq
cat logs/command_stats.json | jq '.[] | select(.count > 10)'

# Via MCP
get_learning_stats()
```

---

## 🔐 Sécurité

### Garanties

1. **Seules les commandes LOW risk** sont suggérées pour auto-add
2. **Commandes CRITICAL** ne sont jamais suggérées
3. **Learning data** n'affecte pas la whitelist (lecture seule)
4. **Suggestions** nécessitent action manuelle pour être appliquées

### Protection

- Auto-learning ne peut **pas** modifier la whitelist automatiquement
- Toutes les suggestions nécessitent **édition manuelle** du code
- Stats persistées dans fichier **logs/** (pas dans code)

---

## 🎯 Use Cases

### UC1 : Nouveau Tool de Monitoring

**Problème** : Équipe utilise `iftop` non whitelisté

**Solution** :
1. Bloquer 5+ fois → apparaît dans suggestions
2. `get_learning_suggestions()` → voir `iftop` recommandé
3. Analyser avec `analyze_command("iftop")`
4. Ajouter à whitelist si LOW risk

### UC2 : Audit des Commandes Bloquées

**Problème** : Comprendre ce qui est bloqué fréquemment

**Solution** :
1. `get_learning_stats()` → voir top 10
2. Identifier patterns (ex: beaucoup de commandes monitoring)
3. Whitelist batch des commandes LOW risk

### UC3 : Découverte de Nouvelles Commandes

**Problème** : Commande inconnue `htop` utilisée par dev

**Solution** :
1. Tentative → bloqué avec suggestion
2. `analyze_command("htop")` → voir analyse détaillée
3. Décision informée : ADD_AUTO, ADD_MANUAL, ou BLOCK

---

## 📚 API Reference

### analyze_command(command, host)

Analyse une commande et fournit recommandations.

**Args:**
- `command` (str): Commande à analyser
- `host` (str): Host cible (pour contexte)

**Returns:** Rapport d'analyse formaté

---

### get_learning_suggestions(min_count, min_age_hours)

Obtient suggestions basées sur historique.

**Args:**
- `min_count` (int): Minimum tentatives (défaut: 5)
- `min_age_hours` (int): Âge minimum (défaut: 24)

**Returns:** Liste de suggestions

---

### get_learning_stats()

Statistiques du système d'apprentissage.

**Returns:** Résumé des stats avec breakdown

---

## 🔄 Workflow Complet

```
Commande inconnue exécutée
         ↓
    BLOCKED par whitelist
         ↓
  Enregistré dans learning stats
         ↓
  Suggestion interactive affichée
         ↓
┌────────┴────────┐
│                 │
Analyse          PRA
manuelle      one-time
│                 │
↓                 ↓
ADD_AUTO      Exécution
ADD_MANUAL    temporaire
BLOCK
```

---

## ✨ Exemples Concrets

### Exemple 1 : Monitoring Tool

```
# Tentative
execute_ssh_command("htop", host="coreos-11")

# Résultat
❌ BLOCKED avec suggestion ADD_AUTO

# Analyse
analyze_command("htop")
→ Risk: LOW, Can auto-add: Yes

# Action
Ajouter à whitelist.py comme AUTO
```

### Exemple 2 : Service Restart

```
# Tentative
execute_ssh_command("systemctl restart nginx", host="coreos-11")

# Résultat
❌ BLOCKED avec suggestion ADD_MANUAL

# Analyse
analyze_command("systemctl restart nginx")
→ Risk: MEDIUM, Needs approval

# Action
Ajouter à whitelist.py comme MANUAL
```

### Exemple 3 : Dangerous Command

```
# Tentative
execute_ssh_command("rm -rf /var", host="coreos-11")

# Résultat
❌ BLOCKED - DANGEROUS

# Analyse
analyze_command("rm -rf /var")
→ Risk: CRITICAL, BLOCK permanently

# Action
Utiliser Ansible playbook à la place
```

---

## 🆕 Nouveaux Tools (v0.2.0)

Total : **34 tools** (31 + 3 nouveaux)

### Ajouts

1. `analyze_command` - Analyse de sécurité
2. `get_learning_suggestions` - Suggestions d'apprentissage
3. `get_learning_stats` - Statistiques d'apprentissage

---

**Version**: 0.2.0
**Date**: 2026-01-19
**Status**: ✅ Production Ready
