# Changelog - MCP Linux Infra

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.3.0] - 2026-01-19

### 🎉 Version majeure - Plugin System + Déploiement complet

### Added
- **Plugin Architecture**: Système de plugins modulaire et extensible
  - 8 plugins builtin avec 135+ commandes
  - Auto-discovery des plugins depuis `catalog/`
  - Plugin registry avec recherche et filtrage
  - Système de catégorisation (monitoring, network, filesystem, systemd, containers, posix)

- **POSIX Command Support**: 3 nouveaux plugins POSIX
  - PosixSystemPlugin: 24 commandes (uname, hostname, uptime, date, etc.)
  - PosixProcessPlugin: 16 commandes (ps, kill, nice, lsof, etc.)
  - PosixTextPlugin: 21 commandes (sed, awk, cut, sort, etc.)

- **Deployment Infrastructure**:
  - `deploy.sh`: Script de déploiement automatisé
  - `test-system.sh`: Script de validation du système
  - `DEPLOYMENT-READY.md`: Checklist complète de déploiement
  - `QUICK-DEPLOY.md`: Guide de déploiement rapide (5 minutes)

- **Docker/Podman Configurations**:
  - `ansible-compose.yml`: Déploiement conteneurs Ansible + AWX
  - `dns-stack-compose.yml`: Stack DNS (Unbound + Caddy + DoH)
  - `unbound.conf`: Configuration Unbound avec DNS-over-TLS
  - `Caddyfile`: Configuration Caddy avec HTTPS automatique

- **MCP Tools** (6 nouveaux):
  - `list_command_plugins`: Liste tous les plugins
  - `get_plugin_details`: Détails d'un plugin spécifique
  - `search_commands`: Recherche full-text dans tous les plugins

### Changed
- **pyproject.toml**: Version 0.3.0, description mise à jour
- **Command Analysis**: Utilise maintenant le plugin system en priorité
- **Plugin Base**: Correction import `AuthLevel` (était `AuthorizationLevel`)
- **Config**: Ajout fonction `get_settings()` pour singleton

### Fixed
- Import errors: `AuthorizationLevel` → `AuthLevel` dans tous les fichiers
- Tous les tests plugins passent (16/16)
- 31/37 tests globaux passent (83.8%)

### Documentation
- **PLUGINS.md**: Documentation complète des 8 plugins (500+ lignes)
- Mise à jour README.md avec statistiques v0.3.0
- Examples de configuration pour Ansible et DNS
- Guides de troubleshooting

### Statistics v0.3.0
- **Plugins**: 8
- **Commandes**: 135 (vs 75 en v0.2.0)
- **AUTO approval**: 111 commandes (82.2%)
- **MANUAL approval**: 24 commandes (17.8%)
- **Risk LOW**: 111 (82.2%)
- **Risk MEDIUM**: 19 (14.1%)
- **Risk HIGH**: 5 (3.7%)

---

## [0.2.0] - 2026-01-19

### 🧠 Smart Analysis & Auto-Learning

### Added
- **Smart Command Analysis System**:
  - `command_analysis.py`: Moteur d'analyse de risque (370 lignes)
  - Niveaux de risque: CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN
  - Détection patterns dangereux (rm -rf, dd, mkfs, etc.)
  - Détection patterns medium-risk (systemctl restart, reboot, etc.)
  - Détection patterns read-only (ls, cat, grep, etc.)
  - Catalogue de commandes connues sûres (20+ commandes)
  - Recherche de commandes similaires pour suggestions

- **Auto-Learning System**:
  - `auto_learning.py`: Moteur d'apprentissage automatique (250 lignes)
  - Tracking des commandes bloquées avec métadonnées
  - Stockage persistant JSON (`logs/command_stats.json`)
  - Suggestions basées sur fréquence (min_count) et ancienneté (min_age_hours)
  - Filtrage intelligent par niveau de risque
  - Statistiques détaillées (top blocked, by risk, by category)

- **MCP Tools** (3 nouveaux):
  - `analyze_command`: Analyse complète de sécurité d'une commande
  - `get_learning_suggestions`: Suggestions d'ajout à la whitelist
  - `get_learning_stats`: Tableau de bord statistiques

- **Interactive Workflow**:
  - Messages intelligents lors de blocage de commande
  - Suggestions automatiques basées sur l'analyse
  - Recommandations d'action (ADD_AUTO, ADD_MANUAL, BLOCK)

### Changed
- **Authorization Engine**: Intégré avec auto-learning
  - Enregistrement automatique des commandes bloquées
  - Tracking de l'utilisateur et de l'host
- **SSH Executor**: Messages enrichis avec suggestions intelligentes
  - Affichage du niveau de risque
  - Proposition de commandes similaires whitelistées
  - Guidance contextuelle basée sur l'analyse

### Documentation
- **COMMAND-ANALYSIS.md**: Guide complet (500+ lignes)
  - Architecture du système d'analyse
  - Niveaux de risque expliqués
  - Exemples d'utilisation
  - API reference complète
  - Guide d'intégration

### Tests
- `test_command_analysis.py`: 13 tests
  - Tests commandes safe, dangerous, medium-risk
  - Tests patterns read-only
  - Tests catalogue known-safe
  - Tests commandes whitelistées
- `test_auto_learning.py`: 11 tests
  - Tests recording et persistence
  - Tests suggestions avec filtres
  - Tests statistiques

---

## [0.1.0] - 2026-01-18

### Initial Release - Production-Ready MCP Server

### Added
- **Core MCP Server**:
  - FastMCP-based server with 31 tools
  - SSH key-based authentication (two-tier)
  - Connection pooling and management

- **Authorization System**:
  - Authorization engine with whitelist
  - Three levels: AUTO, MANUAL, BLOCKED
  - PRA (Plan de Reprise d'Activité) workflow
  - Whitelist management tools

- **Diagnostic Tools** (9 outils):
  - System info (CPU, memory, disk, hardware)
  - Service management (list, status, logs)
  - Network diagnostics (interfaces, connections, ports)
  - Log reading (journal, audit, custom logs)

- **PRA Tools** (5 outils):
  - Propose → Approve → Execute workflow
  - Action tracking and validation
  - Baseline capture and comparison
  - Auto-heal with safety checks

- **SSH Tools**:
  - Two-user system (mcp-reader, pra-runner)
  - Forced-command SSH support
  - Connection pooling (10 max)
  - Keepalive management

- **Advanced Features**:
  - Network connectivity matrix
  - Security audit
  - Health monitoring with trends
  - Performance baseline
  - Log hunting and correlation

### Documentation
- README.md with complete architecture
- Detailed security principles
- SSH configuration examples
- Tool reference (31 tools)

### Tests
- Basic integration tests
- SSH connection tests
- Authorization tests

---

## Version History Summary

| Version | Date | Features | Tools | Commands |
|---------|------|----------|-------|----------|
| 0.1.0 | 2026-01-18 | MCP Server + PRA | 31 | ~20 |
| 0.2.0 | 2026-01-19 | Smart Analysis + Learning | 34 | ~75 |
| 0.3.0 | 2026-01-19 | Plugin System + Deployment | 37 | 135+ |

---

## Roadmap

### Planned for v0.4.0
- [ ] WebUI pour gestion des plugins
- [ ] Métriques Prometheus
- [ ] Tests d'intégration E2E
- [ ] Support Kubernetes (kubectl)
- [ ] Plugin Terraform
- [ ] CI/CD avec GitHub Actions

### Future
- [ ] Multi-tenant support
- [ ] RBAC avancé
- [ ] Plugin marketplace
- [ ] ML-based anomaly detection
- [ ] Integration avec Grafana/Loki

---

## Contributors

- **Initial Development**: Claude Code Agent (Anthropic)
- **Architecture**: Basé sur MCP (Model Context Protocol)
- **Security Design**: Two-tier SSH authentication pattern

---

## License

[Your License Here]

---

*Last Updated: 2026-01-19*
