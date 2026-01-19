# Architecture MCP Linux Infra

## Vue d'ensemble

MCP Linux Infra implémente une architecture de **séparation stricte des privilèges** basée sur SSH avec authentification par clés.

## Principe Fondamental

**2 canaux SSH distincts, 2 clés différentes, 2 niveaux de confiance**

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

## Composants

### 1. MCP Server (Python/asyncssh)

**Localisation:** Windows (D:\infra\mcp-servers\mcp-linux-infra)

**Responsabilités:**
- Gestion de 2 connection pools SSH séparés
- Exposition des tools MCP à Claude
- Audit logging structuré
- Validation de sécurité (host whitelist, command sanitization)

**Technologies:**
- Python 3.11+
- asyncssh (connection pooling)
- FastMCP (Model Context Protocol)
- Pydantic (configuration)

### 2. Linux Targets

**Comptes système:**

#### mcp-reader (diagnostics)
- **Shell:** /bin/bash
- **Clé SSH:** mcp-reader.key
- **Forced-command:** /usr/local/bin/mcp-wrapper
- **Privilèges:** AUCUN sudo
- **Usage:** Diagnostics read-only uniquement

#### pra-runner (actions)
- **Shell:** /usr/sbin/nologin (pas de shell interactif)
- **Clé SSH:** pra-exec.key
- **Forced-command:** /usr/local/bin/pra-exec
- **Privilèges:** sudo NOPASSWD /usr/local/bin/pra-run
- **Usage:** Actions PRA validées uniquement

### 3. Wrappers de Sécurité

#### /usr/local/bin/mcp-wrapper
- Whitelist stricte de commandes read-only
- Log toutes les tentatives dans /var/log/mcp-wrapper.log
- Rejette toute commande non listée
- Force --no-pager sur systemctl/journalctl

Exemples autorisés:
```bash
systemctl status nginx
journalctl -u unbound -n 100
ss -lntup
df -h
cat /var/log/nginx/error.log
```

#### /usr/local/bin/pra-exec
- Whitelist stricte d'actions PRA
- Log toutes les tentatives dans /var/log/pra-exec.log
- Appelle /usr/local/bin/pra-run avec sudo
- Rejette toute action non listée

Exemples autorisés:
```bash
restart_unbound
reload_caddy
flush_dns_cache
```

#### /usr/local/bin/pra-run
- Implémentation réelle des actions PRA
- Exécuté avec sudo par pra-runner
- Log dans /var/log/pra-run.log
- Chaque action = commande système atomique

## Flux de Données

### Diagnostic (Read-Only)

```
1. Claude appelle tool MCP (ex: get_service_status)
2. MCP server → SSH mcp-reader@target
3. SSH authorized_keys → force /usr/local/bin/mcp-wrapper
4. Wrapper vérifie whitelist
5. Si OK: exécute commande (systemctl status)
6. Retour stdout → MCP server → Claude
```

**Sécurité:**
- Aucune écriture possible
- Aucun sudo
- Jail SSH via forced-command
- Whitelist stricte

### Action PRA (Exec)

```
1. Claude propose action (propose_pra_action)
2. MCP server crée PRAAction(status=PROPOSED)
3. HUMAIN approuve (approve_pra_action)
4. MCP server → status=APPROVED
5. Claude exécute (execute_pra_action)
6. MCP server → SSH pra-runner@target
7. SSH authorized_keys → force /usr/local/bin/pra-exec
8. pra-exec vérifie whitelist
9. Si OK: sudo /usr/local/bin/pra-run <action>
10. pra-run exécute action réelle
11. Retour → MCP server → Claude
```

**Sécurité:**
- Validation humaine obligatoire
- 2 whitelists (pra-exec + pra-run)
- sudo limité à 1 seul script
- Audit trail complet (3 logs)

## Connection Pooling

```python
class SSHConnectionManager:
    _read_connections: dict[str, SSHClientConnection]  # mcp-reader
    _exec_connections: dict[str, SSHClientConnection]  # pra-runner
```

**Avantages:**
- Réutilisation des connexions SSH
- Performance optimale
- Keepalive automatique
- Cleanup des connexions fermées

## Audit Trail

**4 niveaux de logging:**

1. **/var/log/mcp-wrapper.log** (target)
   - Toutes les commandes read-only tentées
   - Format: `timestamp USER=mcp-reader CMD=<command>`

2. **/var/log/pra-exec.log** (target)
   - Toutes les actions PRA tentées
   - Format: `timestamp USER=pra-runner CMD=<action>`

3. **/var/log/pra-run.log** (target)
   - Exécution réelle des actions avec sudo
   - Succès/échec

4. **MCP server logs** (Windows)
   - Audit structuré JSON
   - SSH connections, tool calls, PRA lifecycle
   - Sanitization des secrets

## Sécurité Multicouche

### Couche 1: Host Whitelist
```python
CONFIG.allowed_hosts = "web01.infra,web02.infra"
```

### Couche 2: SSH Forced-Command
```bash
command="/usr/local/bin/mcp-wrapper",no-pty,no-agent-forwarding ssh-ed25519 ...
```

### Couche 3: Wrapper Whitelist
```bash
case "$SSH_ORIGINAL_COMMAND" in
    "systemctl status "*) exec $SSH_ORIGINAL_COMMAND ;;
    *) echo "DENIED" >&2; exit 1 ;;
esac
```

### Couche 4: Sudo Restriction
```bash
pra-runner ALL=(root) NOPASSWD: /usr/local/bin/pra-run
```

### Couche 5: Action Validation
```python
if pra_action.status != PRAActionStatus.APPROVED:
    raise Error("Not approved")
```

## Scalabilité

**Horizontal:**
- Connection pooling par host
- Parallélisation des diagnostics
- Pas de state partagé entre tools

**Vertical:**
- Async/await natif (asyncssh)
- Pas de threading
- Memory-efficient

**Multi-target:**
- Chaque target = entrée dans connection pool
- Configuration centralisée (CONFIG.allowed_hosts)
- Ansible pour déploiement à grande échelle

## Idempotence

**Diagnostics:** Naturellement idempotents (read-only)

**Actions PRA:** Dépend de l'implémentation dans pra-run

Exemple idempotent:
```bash
restart_unbound)
    # Idempotent: systemctl restart est toujours safe
    systemctl restart unbound
    ;;
```

Non-idempotent (à éviter):
```bash
# MAUVAIS: pas idempotent
echo "entry" >> /etc/config
```

**Recommandation:** Utiliser Ansible pour actions complexes nécessitant idempotence garantie.

## Extensibilité

### Ajouter un Tool Diagnostic

1. Créer fonction dans `src/mcp_linux_infra/tools/diagnostics/<module>.py`
2. Utiliser `execute_command()` pour SSH
3. Décorer avec `@app.call_tool()` dans `server.py`
4. Ajouter commande dans `/usr/local/bin/mcp-wrapper` whitelist

### Ajouter une Action PRA

1. Ajouter dans `PRA_ACTION_CATALOG` (tools/pra/actions.py)
2. Définir impact (LOW/MEDIUM/HIGH)
3. Ajouter dans `/usr/local/bin/pra-exec` whitelist
4. Implémenter dans `/usr/local/bin/pra-run`
5. Tester idempotence

### Ajouter un Target

1. Générer clés SSH si besoin
2. Ajouter dans inventaire Ansible
3. Run `ansible-playbook deploy-mcp-infra.yml`
4. Ajouter dans `CONFIG.allowed_hosts`
5. Tester avec `get_system_info(host="new-target")`

## Performance

**Benchmarks typiques:**

| Opération | Latence | Notes |
|-----------|---------|-------|
| Diagnostic (cached connection) | ~50ms | SSH command exec |
| Diagnostic (new connection) | ~200ms | SSH handshake + command |
| PRA action | ~300ms | SSH + sudo + systemctl |
| Connection pool cleanup | ~10ms | Async background task |

**Optimisations:**
- Connection pooling (-80% latency sur requêtes répétées)
- Async I/O (pas de blocking)
- Keepalive SSH (évite reconnexions)

## Limites Actuelles

1. **Pas de bastion/jumphost** (à implémenter)
2. **known_hosts désactivé** (INSECURE, à activer en prod)
3. **Pas de retry automatique** sur échec SSH
4. **Pas de health check** des connexions poolées
5. **PRA actions sans paramètres** (ex: restart_container nécessite container_name)

## Roadmap

- [ ] Support bastion SSH (ProxyJump)
- [ ] Strict known_hosts validation
- [ ] Connection health checks
- [ ] Retry logic avec backoff
- [ ] Actions PRA paramétrées
- [ ] Integration Vault pour clés
- [ ] Métriques Prometheus
- [ ] Dashboard validation PRA
