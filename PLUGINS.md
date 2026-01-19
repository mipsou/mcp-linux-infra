# 🔌 Command Plugin System

**Version**: 0.3.0
**Feature**: Extensible command families with plugin architecture

---

## 🎯 Vue d'Ensemble

Le système de plugins organise les commandes par **familles** pour une meilleure maintenabilité et extensibilité.

### Architecture

```
analysis/plugins/
├── base.py                # CommandPlugin ABC
├── registry.py            # PluginRegistry + auto-discovery
└── catalog/               # Builtin plugins
    ├── monitoring.py      # Process, CPU, I/O monitoring
    ├── network.py         # Connectivity, DNS, routing
    ├── filesystem.py      # File operations
    ├── systemd.py         # Service management
    └── containers.py      # Podman/Docker
```

### Avantages

✅ **Modularité** : Chaque famille = 1 plugin isolé
✅ **Auto-Discovery** : Plugins chargés automatiquement
✅ **Extensibilité** : Ajouter plugin = nouveau fichier
✅ **Type Safety** : CommandSpec avec validation
✅ **Documentation** : Usage guides auto-générés
✅ **Testabilité** : Tests unitaires par plugin

---

## 📦 Plugins Builtin

Total : **8 plugins** avec **130+ commandes**

### 1. Monitoring Plugin (10 commandes)

**Catégorie** : `monitoring`
**Risk Level** : LOW (read-only)

| Commande | Description | Exemples |
|----------|-------------|----------|
| `htop` | Interactive process viewer | `htop`, `htop -u www-data` |
| `top` | Process monitor | `top`, `top -b -n 1` |
| `iotop` | I/O monitoring | `iotop`, `iotop -o` |
| `iftop` | Network bandwidth monitor | `iftop`, `iftop -i eth0` |
| `nethogs` | Network traffic per process | `nethogs`, `nethogs eth0` |
| `atop` | Advanced system monitor | `atop`, `atop -m` |
| `vmstat` | Virtual memory statistics | `vmstat`, `vmstat 1 10` |
| `iostat` | I/O statistics | `iostat`, `iostat -x 1` |
| `mpstat` | Per-CPU statistics | `mpstat`, `mpstat -P ALL` |
| `glances` | All-in-one monitor | `glances`, `glances -1` |

**Usage MCP** :
```python
get_plugin_details("monitoring")
```

---

### 2. Network Plugin (14 commandes)

**Catégorie** : `network`
**Risk Levels** : LOW (read-only), MEDIUM (writes), HIGH (packet capture)

| Commande | Risk | Level | Description |
|----------|------|-------|-------------|
| `ping` | LOW | AUTO | Connectivity test |
| `traceroute` | LOW | AUTO | Network path tracing |
| `netstat` | LOW | AUTO | Network connections |
| `ss` | LOW | AUTO | Socket statistics |
| `ip addr` | LOW | AUTO | Show IP addresses |
| `ip route` | LOW | AUTO | Routing table |
| `ip link` | LOW | AUTO | Network interfaces |
| `dig` | LOW | AUTO | DNS lookup |
| `nslookup` | LOW | AUTO | DNS query |
| `host` | LOW | AUTO | DNS lookup utility |
| `curl` | LOW | AUTO | HTTP client |
| `wget` | MEDIUM | MANUAL | Download files ⚠️ |
| `mtr` | LOW | AUTO | Combined traceroute/ping |
| `tcpdump` | HIGH | MANUAL | Packet capture ⚠️ |

**Usage MCP** :
```python
search_commands("dns")  # Find DNS-related commands
get_plugin_details("network")
```

---

### 3. Filesystem Plugin (17 commandes)

**Catégorie** : `filesystem`
**Risk Level** : LOW (all read-only)

| Commande | Description | Key Flags |
|----------|-------------|-----------|
| `ls` | List directories | `-la`, `-lh`, `-lt` |
| `cat` | Display files | `-n` (line numbers) |
| `head` | Show file beginning | `-n NUM` |
| `tail` | Show file end | `-f` (follow), `-n NUM` |
| `less` | File viewer | `+F` (follow), `-N` (line #) |
| `more` | File pager | - |
| `grep` | Text search | `-i`, `-r`, `-n` |
| `find` | Search files | `-name`, `-type`, `-size` |
| `du` | Disk usage | `-sh`, `--max-depth` |
| `df` | Disk space | `-h`, `-i` (inodes) |
| `file` | File type | `-i` (MIME) |
| `stat` | File status | `-c FORMAT` |
| `tree` | Directory tree | `-L LEVEL`, `-d` |
| `wc` | Word count | `-l` (lines) |
| `diff` | Compare files | `-u` (unified) |
| `md5sum` | MD5 checksum | `-c` (check) |
| `sha256sum` | SHA256 checksum | `-c` (check) |

**Usage MCP** :
```python
search_commands("search")  # Find search tools
analyze_command("grep -r pattern /var/log")
```

---

### 4. Systemd Plugin (15 commandes)

**Catégorie** : `systemd`
**Risk Levels** : LOW (status/logs), MEDIUM (state changes)

#### Read-Only (AUTO)

| Commande | Description |
|----------|-------------|
| `systemctl status` | Service status |
| `systemctl list-units` | List active units |
| `systemctl list-unit-files` | List unit files |
| `systemctl show` | Show unit properties |
| `systemctl is-active` | Check if active |
| `systemctl is-enabled` | Check if enabled |
| `systemctl cat` | Show unit file |
| `systemctl list-dependencies` | Show dependencies |
| `journalctl` | Query journal logs |

#### State Changes (MANUAL) ⚠️

| Commande | Description |
|----------|-------------|
| `systemctl restart` | Restart service |
| `systemctl reload` | Reload config |
| `systemctl start` | Start service |
| `systemctl stop` | Stop service |
| `systemctl enable` | Enable at boot |
| `systemctl disable` | Disable at boot |

**Usage MCP** :
```python
# Safe (no approval)
execute_ssh_command("systemctl status nginx", host="coreos-11")

# Requires approval
execute_ssh_command("systemctl restart nginx", host="coreos-11")
```

---

### 5. Containers Plugin (19 commandes)

**Catégorie** : `containers`
**Risk Levels** : LOW (inspection), MEDIUM (control), HIGH (delete)

#### Podman Read-Only (AUTO)

| Commande | Description |
|----------|-------------|
| `podman ps` | List containers |
| `podman inspect` | Inspect container |
| `podman logs` | Container logs |
| `podman images` | List images |
| `podman stats` | Resource usage |
| `podman top` | Container processes |

#### Podman Control (MANUAL) ⚠️

| Commande | Risk | Description |
|----------|------|-------------|
| `podman restart` | MEDIUM | Restart container |
| `podman start` | MEDIUM | Start container |
| `podman stop` | MEDIUM | Stop container |
| `podman rm` | HIGH | Remove container |

**Docker** : Commands équivalents disponibles

**Usage MCP** :
```python
# Read-only
execute_ssh_command("podman ps -a", host="coreos-11")
execute_ssh_command("podman logs mycontainer", host="coreos-11")

# Requires approval
execute_ssh_command("podman restart mycontainer", host="coreos-11")
```

---

## 🚀 Utilisation

### Via MCP Tools

#### 1. Lister tous les plugins

```python
list_command_plugins()
```

**Output** :
```
🔌 COMMAND PLUGIN CATALOG

Total Plugins: 5
Total Commands: 75+

【MONITORING】
  Commands: 10
  • htop - Interactive process viewer
  • iotop - I/O monitoring
  ...

【NETWORK】
  Commands: 14
  • ping - Network connectivity test
  • curl - HTTP client
  ...
```

#### 2. Détails d'un plugin

```python
get_plugin_details("monitoring")
```

**Output** : Usage guide complet avec exemples et flags

#### 3. Chercher des commandes

```python
search_commands("docker")
search_commands("log")
search_commands("process")
```

#### 4. Analyser une commande

```python
analyze_command("htop")
```

**Output** : Analyse avec référence au plugin source

---

## 🛠️ Créer un Plugin Custom

### Structure de Base

```python
# my_custom_plugin.py

from mcp_linux_infra.analysis.plugins.base import CommandPlugin, CommandSpec
from mcp_linux_infra.analysis.command_analysis import RiskLevel
from mcp_linux_infra.authorization.models import AuthorizationLevel


class MyCustomPlugin(CommandPlugin):
    """My custom command family."""

    @property
    def name(self) -> str:
        return "my-custom"

    @property
    def category(self) -> str:
        return "custom"

    @property
    def description(self) -> str:
        return "My custom commands"

    @property
    def commands(self) -> dict[str, CommandSpec]:
        return {
            'my-cmd': CommandSpec(
                pattern=r'^my-cmd(\s+.*)?$',
                risk=RiskLevel.LOW,
                level=AuthorizationLevel.AUTO,
                ssh_user='mcp-reader',
                description='My custom command',
                rationale='Does something useful',
                examples=[
                    'my-cmd',
                    'my-cmd --flag',
                ],
                flags=[
                    '--flag: Some flag',
                ]
            ),
        }
```

### Enregistrement

#### Option 1 : Builtin (auto-discovery)

Placez votre plugin dans `catalog/` :

```
plugins/catalog/
├── __init__.py  # Ajoutez votre import
├── monitoring.py
├── my_custom_plugin.py  # ← Nouveau plugin
```

Mettez à jour `catalog/__init__.py` :

```python
from .my_custom_plugin import MyCustomPlugin

__all__ = [
    ...,
    "MyCustomPlugin",
]
```

#### Option 2 : Enregistrement manuel

```python
from mcp_linux_infra.analysis.plugins import get_plugin_registry
from .my_custom_plugin import MyCustomPlugin

registry = get_plugin_registry()
registry.register(MyCustomPlugin())
```

---

### 6. POSIX System Plugin (24 commandes)

**Catégorie** : `posix`

Standard POSIX utilities : `uname`, `hostname`, `uptime`, `who`, `id`, `date`, `echo`, `pwd`, `which`, `test`, etc.

### 7. POSIX Process Plugin (16 commandes)

**Catégorie** : `posix`

Process management : `ps`, `pgrep`, `kill`, `nice`, `lsof`, `strace`, etc.

### 8. POSIX Text Plugin (21 commandes)

**Catégorie** : `posix`

Text processing : `sed`, `awk`, `cut`, `sort`, `uniq`, `tr`, `grep`, etc.

---

## 📊 Statistiques

### Commandes par Plugin

| Plugin | Commandes | Risk LOW | Risk MEDIUM | Risk HIGH |
|--------|-----------|----------|-------------|-----------|
| Monitoring | 10 | 10 | 0 | 0 |
| Network | 14 | 12 | 1 | 1 |
| Filesystem | 17 | 17 | 0 | 0 |
| Systemd | 15 | 9 | 6 | 0 |
| Containers | 19 | 12 | 6 | 1 |
| **POSIX System** | **24** | **23** | **1** | **0** |
| **POSIX Process** | **16** | **9** | **3** | **4** |
| **POSIX Text** | **21** | **20** | **1** | **0** |
| **TOTAL** | **136** | **112** | **18** | **6** |

### Auto-Approved vs. Approval Required

- **AUTO (112 commandes)** : 82.4% - Read-only, sûres
- **MANUAL (18 commandes)** : 13.2% - State changes
- **HIGH Risk (6 commandes)** : 4.4% - Destructive operations

---

## 🔍 Intégration avec Auto-Learning

Le système de plugins est **intégré** avec l'auto-learning :

```python
# analyze_command utilise les plugins
analyze_command("htop")
# → Trouve automatiquement MonitoringPlugin
# → Retourne risk, category, examples du plugin

# Auto-learning suggère basé sur plugins
get_learning_suggestions()
# → Compare avec plugin catalog
# → Suggère commandes reconnues par plugins
```

---

## 🧪 Tests

### Test d'un Plugin

```python
def test_my_plugin():
    plugin = MyCustomPlugin()

    assert plugin.name == "my-custom"
    assert len(plugin.commands) > 0

    # Test command spec
    spec = plugin.get_command_spec("my-cmd")
    assert spec is not None
    assert spec.risk == RiskLevel.LOW

    # Test matching
    assert spec.matches("my-cmd")
    assert spec.matches("my-cmd --flag")
```

### Test du Registry

```python
def test_registry_finds_custom_plugin():
    registry = get_plugin_registry()

    result = registry.find_command_spec("my-cmd")
    assert result is not None

    plugin, spec = result
    assert plugin.name == "my-custom"
```

---

## 📚 API Reference

### CommandPlugin

```python
class CommandPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def category(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def commands(self) -> Dict[str, CommandSpec]: ...

    def get_command_spec(self, command: str) -> Optional[CommandSpec]: ...
    def get_usage_guide(self) -> str: ...
    def get_summary(self) -> dict: ...
```

### CommandSpec

```python
@dataclass
class CommandSpec:
    pattern: str                    # Regex pattern
    risk: RiskLevel                 # CRITICAL/HIGH/MEDIUM/LOW/UNKNOWN
    level: AuthorizationLevel       # AUTO/MANUAL/BLOCKED
    ssh_user: str                   # mcp-reader or pra-runner
    description: str                # Short description
    rationale: str                  # Why this level?
    examples: Optional[List[str]]   # Usage examples
    flags: Optional[List[str]]      # Common flags

    def matches(self, command: str) -> bool: ...
    def to_dict(self) -> dict: ...
```

### PluginRegistry

```python
class PluginRegistry:
    def register(self, plugin: CommandPlugin): ...
    def get_plugin(self, name: str) -> Optional[CommandPlugin]: ...
    def list_plugins(self) -> List[str]: ...

    def find_command_spec(self, command: str) -> Optional[tuple]: ...
    def search_commands(self, query: str) -> List[tuple]: ...

    def get_commands_by_category(self, category: str) -> Dict: ...
    def get_all_categories(self) -> List[str]: ...

    def load_builtin_plugins(self): ...
    def get_summary(self) -> dict: ...
```

---

## 💡 Best Practices

### 1. Nommage des Plugins

- Utilisez des noms courts et clairs : `monitoring`, `network`
- Catégorie = nom du plugin (généralement)
- Un plugin = une famille cohérente de commandes

### 2. Patterns Regex

```python
# ✅ Bon
pattern=r'^htop(\s+.*)?$'  # htop avec ou sans flags

# ❌ Mauvais
pattern=r'htop'  # Trop lâche, match "myhtop"
```

### 3. Risk Assessment

```python
# Lecture seule → LOW + AUTO
risk=RiskLevel.LOW,
level=AuthorizationLevel.AUTO,
ssh_user='mcp-reader'

# Modification d'état → MEDIUM + MANUAL
risk=RiskLevel.MEDIUM,
level=AuthorizationLevel.MANUAL,
ssh_user='pra-runner'

# Destructif → HIGH + MANUAL ou CRITICAL + BLOCKED
risk=RiskLevel.HIGH,
level=AuthorizationLevel.MANUAL,
ssh_user='pra-runner'
```

### 4. Documentation

- **description** : Court (1 ligne)
- **rationale** : Pourquoi ce risk level?
- **examples** : 2-3 cas d'usage réels
- **flags** : Top 5 flags les plus utiles

---

## 🔄 Workflow Complet

```
1. User exécute commande inconnue
         ↓
2. PluginRegistry.find_command_spec()
         ↓
3. Plugin trouvé? → Utilise CommandSpec
   │
   └─ Pas trouvé → Fallback sur pattern matching
         ↓
4. Risk assessment basé sur spec
         ↓
5. Auto-learning enregistre si bloqué
         ↓
6. Suggestions basées sur plugins
```

---

## 📈 Roadmap

- [x] Architecture de base (v0.3.0)
- [x] 5 plugins builtin (75+ commandes)
- [x] Auto-discovery
- [x] Intégration avec command_analysis
- [x] 3 nouveaux MCP tools (list, details, search)
- [ ] Plugin pour commandes Git
- [ ] Plugin pour commandes security/audit
- [ ] Plugin pour commandes Kubernetes
- [ ] Hot-reload de plugins (sans restart)
- [ ] Plugin marketplace/registry

---

**Version**: 0.3.0
**Total Commandes**: 75+
**Total Plugins**: 5 builtin
**Date**: 2026-01-19
**Status**: ✅ Production Ready
