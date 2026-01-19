# 📚 Index de Documentation - linux-infra MCP

**Version**: 0.1.0
**Dernière mise à jour**: 2026-01-19

---

## 🎯 Pour Commencer

### Quick Start (⚡ 2 minutes)
**Fichier**: `QUICK-START-LINUX-INFRA.md` (racine D:\infra)
**Contenu**:
- Premier test après redémarrage
- 5 tests recommandés
- Commandes essentielles
- Liens vers docs complètes

**Quand l'utiliser**: Juste après redémarrage Claude Desktop

---

### Post-Reboot Checklist (✅ 10 minutes)
**Fichier**: `POST-REBOOT-CHECKLIST.md` (racine D:\infra)
**Contenu**:
- Checklist complète de vérification
- 5 tests à exécuter
- Points de contrôle
- Actions si erreurs

**Quand l'utiliser**: Pour valider l'installation après redémarrage

---

## 📖 Documentation Complète

### Architecture et Développement

#### README.md (principal)
**Fichier**: `D:\infra\mcp-servers\mcp-linux-infra\README.md`
**Contenu**:
- Architecture complète du serveur
- Structure du code
- Explication FastMCP
- Security model
- Développement et contribution

**Quand l'utiliser**: Pour comprendre comment fonctionne le serveur

---

### Tests et Validation

#### Tests Complets (📋 30 minutes)
**Fichier**: `TEST-LINUX-INFRA.md` (racine D:\infra)
**Contenu**:
- 40+ scénarios de test
- Tests read-only (19 tools)
- Tests SSH execution (4 tools)
- Tests PRA (4 tools)
- Tests Ansible (4 tools)
- Tests sécurité et edge cases

**Quand l'utiliser**: Pour tester toutes les fonctionnalités en détail

---

#### Rapport d'Intégrité (🔍 Référence)
**Fichier**: `INTEGRITY-CHECK-LINUX-INFRA.md` (racine D:\infra)
**Contenu**:
- Structure complète du projet
- Validation de tous les fichiers Python
- Dépendances installées
- Configuration Claude Desktop
- Inventaire des 31 tools
- Problèmes connus

**Quand l'utiliser**: Pour diagnostiquer ou vérifier l'état du serveur

---

### Résolution de Problèmes

#### Troubleshooting Guide (🔧 Support)
**Fichier**: `TROUBLESHOOTING.md` (dans mcp-linux-infra/)
**Contenu**:
- 7 erreurs communes et solutions
- Diagnostic SSH Agent
- Problèmes d'autorisation
- Timeouts et deadlocks
- Logs et debugging
- Reset complet

**Quand l'utiliser**: Quand quelque chose ne fonctionne pas

---

## 🛠️ Scripts et Outils

### Test d'Intégrité Automatisé
**Fichier**: `test-integrity.sh` (dans mcp-linux-infra/)
**Usage**:
```bash
cd D:\infra\mcp-servers\mcp-linux-infra
./test-integrity.sh
```
**Contenu**:
- Vérification syntaxe Python (24 fichiers)
- Test import serveur
- Vérification dépendances
- Vérification config
- Compte des tools (31)

**Quand l'utiliser**: Pour valider rapidement l'intégrité du code

---

## 📁 Fichiers de Configuration

### Configuration Claude Desktop
**Fichier**: `C:\Users\chpuj\AppData\Roaming\Claude\claude_desktop_config.json`
**Section**: `mcpServers.linux-infra`
**Contenu**:
```json
{
  "command": "uv.exe",
  "args": ["--directory", "...", "run", "mcp-linux-infra"],
  "env": {
    "SSH_AUTH_SOCK": "\\\\.\\\\pipe\\\\openssh-ssh-agent",
    "LINUX_MCP_LOG_LEVEL": "INFO"
  }
}
```

---

### Variables d'Environnement
**Fichier**: `.env` (dans mcp-linux-infra/)
**Contenu**:
- `LINUX_MCP_LOG_LEVEL` - Niveau de log
- `LINUX_MCP_ALLOWED_HOSTS` - Whitelist hosts
- `LINUX_MCP_REQUIRE_APPROVAL_FOR_PRA` - Validation PRA
- `SSH_AUTH_SOCK` - Named pipe SSH Agent

---

### Dépendances Python
**Fichier**: `pyproject.toml` (dans mcp-linux-infra/)
**Contenu**:
- mcp[cli] >= 1.2.0
- asyncssh >= 2.14.0
- pydantic >= 2.0.0
- pydantic-settings >= 2.0.0
- pyyaml >= 6.0.0

---

## 🗺️ Navigation dans le Code

### Structure des Fichiers

```
mcp-linux-infra/
├── 📄 README.md                    # Architecture principale
├── 📄 TROUBLESHOOTING.md           # Guide de dépannage
├── 📄 DOCS-INDEX.md                # Ce fichier
├── 🔧 test-integrity.sh            # Script de test
├── ⚙️  pyproject.toml               # Configuration projet
├── 🔐 .env                          # Variables d'environnement
│
├── src/mcp_linux_infra/
│   ├── 🚀 server.py                # Point d'entrée MCP (31 tools)
│   ├── ⚙️  config.py                # Configuration
│   ├── 📊 audit.py                 # Audit trail
│   │
│   ├── authorization/              # Moteur d'autorisation
│   │   ├── engine.py               # Authorization engine
│   │   ├── models.py               # Models Pydantic
│   │   └── whitelist.py            # Whitelist commandes
│   │
│   ├── connection/                 # Gestion SSH
│   │   ├── smart_ssh.py            # Smart SSH wrapper
│   │   ├── ssh.py                  # SSH client
│   │   └── ssh_agent.py            # SSH Agent integration
│   │
│   └── tools/                      # Outils MCP
│       ├── diagnostics/            # Read-only tools (19)
│       │   ├── system.py           # Système (5 tools)
│       │   ├── services.py         # Services (4 tools)
│       │   ├── network.py          # Réseau (6 tools)
│       │   └── logs.py             # Logs (4 tools)
│       │
│       ├── execution/              # Execution tools (8)
│       │   ├── ssh_executor.py     # SSH commands (4 tools)
│       │   └── ansible_wrapper.py  # Ansible (4 tools)
│       │
│       └── pra/                    # PRA actions (4)
│           └── actions.py          # PRA workflow
```

---

## 📍 Fichiers par Cas d'Usage

### Je veux...

#### Démarrer rapidement
→ `QUICK-START-LINUX-INFRA.md`

#### Vérifier après installation
→ `POST-REBOOT-CHECKLIST.md`

#### Tester toutes les fonctionnalités
→ `TEST-LINUX-INFRA.md`

#### Comprendre l'architecture
→ `README.md` (dans mcp-linux-infra/)

#### Résoudre un problème
→ `TROUBLESHOOTING.md`

#### Vérifier l'intégrité
→ `INTEGRITY-CHECK-LINUX-INFRA.md`
→ `test-integrity.sh`

#### Développer/Modifier le code
→ `README.md` (section Development)
→ Structure dans `src/mcp_linux_infra/`

#### Configurer SSH
→ `TROUBLESHOOTING.md` (section SSH)
→ `.env` (SSH_AUTH_SOCK)

#### Voir les tools disponibles
→ `server.py:17-324` (31 déclarations @mcp.tool)
→ `INTEGRITY-CHECK-LINUX-INFRA.md` (section Inventaire)

#### Modifier la whitelist
→ `src/mcp_linux_infra/authorization/whitelist.py`

---

## 🎓 Parcours d'Apprentissage

### Niveau 1: Utilisateur (30 min)
1. Lire `QUICK-START-LINUX-INFRA.md`
2. Suivre `POST-REBOOT-CHECKLIST.md`
3. Tester 5 commandes de base

### Niveau 2: Avancé (2h)
1. Lire `README.md` complet
2. Exécuter tous les tests de `TEST-LINUX-INFRA.md`
3. Consulter `TROUBLESHOOTING.md`

### Niveau 3: Développeur (4h+)
1. Étudier la structure dans `src/`
2. Lire `authorization/engine.py`
3. Comprendre le flow SSH dans `connection/`
4. Modifier la whitelist
5. Ajouter un nouveau tool

---

## 📞 Support et Ressources

### Logs
```
D:\infra\mcp-servers\mcp-linux-infra\logs\mcp-linux-infra.log
```

### Configuration
```
C:\Users\chpuj\AppData\Roaming\Claude\claude_desktop_config.json
```

### Tests Rapides
```bash
# Intégrité
./test-integrity.sh

# SSH direct
ssh ansible@coreos-11.local

# SSH Agent
ssh-add -l
```

### Commandes MCP
```
# Via Claude Desktop
show_command_whitelist
list_pending_approvals
get_system_info(host="coreos-11")
```

---

## 🔄 Mises à Jour

### Changelog
Voir: `CHANGELOG.md` (à créer)

### Versions
- **0.1.0** (2026-01-19): Version initiale FastMCP

---

## 📊 Métriques du Projet

- **Fichiers Python**: 24
- **Lines of Code**: ~2000
- **Tools MCP**: 31
- **Documentation**: 5 fichiers principaux
- **Tests**: 40+ scénarios
- **Dependencies**: 6 packages

---

**Maintenu par**: Claude (Sonnet 4.5)
**Projet**: Podman MCP Infrastructure
**Licence**: Voir projet parent
