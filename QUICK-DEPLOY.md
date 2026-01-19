# Guide de Déploiement Rapide
**MCP Linux Infra v0.3.0**

## 🚀 Installation en 5 minutes

### 1. Installer MCP Linux Infra

```bash
cd /d/infra/mcp-servers/mcp-linux-infra
pip install -e .
```

### 2. Configurer les clés SSH

```bash
# Générer les clés si nécessaire
ssh-keygen -t ed25519 -f ~/.ssh/mcp-reader -C "mcp-reader"
ssh-keygen -t ed25519 -f ~/.ssh/pra-runner -C "pra-runner"

# Variables d'environnement
export LINUX_MCP_SSH_KEY_PATH=~/.ssh/mcp-reader
export LINUX_MCP_PRA_KEY_PATH=~/.ssh/pra-runner
export LINUX_MCP_PRA_USER=pra-runner
```

### 3. Déployer les conteneurs Ansible

```bash
# Option A: Docker Compose
cd examples
docker-compose -f ansible-compose.yml up -d

# Option B: Podman
podman run -d --name ansible-controller \
  -v ./playbooks:/ansible/playbooks \
  -v ~/.ssh:/root/.ssh:ro \
  ansible/ansible:latest
```

### 4. Déployer la stack DNS

```bash
# Option A: Docker Compose (recommandé)
cd examples
docker-compose -f dns-stack-compose.yml up -d

# Option B: Podman
podman run -d --name unbound \
  -p 53:53/udp -p 53:53/tcp \
  -v ./unbound/unbound.conf:/opt/unbound/etc/unbound/unbound.conf:ro \
  mvance/unbound:latest

podman run -d --name caddy \
  -p 80:80 -p 443:443 \
  -v ./caddy/Caddyfile:/etc/caddy/Caddyfile:ro \
  caddy:latest
```

### 5. Vérifier le déploiement

```bash
# Tester MCP
python -c "
from mcp_linux_infra.analysis.plugins import get_plugin_registry
r = get_plugin_registry()
print(f'✅ {len(r.get_all_plugins())} plugins chargés')
"

# Vérifier les conteneurs
docker ps
# ou
podman ps

# Tester DNS
dig @localhost google.com
```

## 📊 Ce qui est déployé

### MCP Linux Infra
- ✅ 8 plugins (135 commandes)
- ✅ Analyse intelligente des commandes
- ✅ Auto-learning
- ✅ Authentification SSH deux niveaux
- ✅ Workflow PRA

### Conteneurs Ansible
- ✅ Ansible Controller
- ⚙️ AWX (optionnel - UI web)
- ⚙️ PostgreSQL (si AWX)
- ⚙️ Redis (si AWX)

### Stack DNS
- ✅ Unbound (DNS récursif avec DoT)
- ✅ Caddy (reverse proxy avec HTTPS auto)
- ⚙️ DoH Proxy (optionnel - DNS-over-HTTPS)

## 🔧 Configuration post-déploiement

### 1. Configurer les hosts autorisés

```python
# Dans votre config ou via env
export LINUX_MCP_ALLOWED_HOSTS="server1,server2,server3"
# Ou "*" pour tous
export LINUX_MCP_ALLOWED_HOSTS="*"
```

### 2. Distribuer les clés SSH

```bash
# Copier la clé publique sur les serveurs cibles
ssh-copy-id -i ~/.ssh/mcp-reader.pub mcp-reader@server1
ssh-copy-id -i ~/.ssh/pra-runner.pub pra-runner@server1
```

### 3. Tester les connexions

```bash
# Avec MCP reader (read-only)
ssh -i ~/.ssh/mcp-reader mcp-reader@server1 'ls -la'

# Avec PRA runner (actions)
ssh -i ~/.ssh/pra-runner pra-runner@server1 'sudo systemctl status nginx'
```

### 4. Configurer Unbound pour votre réseau

Éditez `examples/unbound/unbound.conf`:

```conf
# Zones locales
local-zone: "mycompany.local." static
local-data: "server1.mycompany.local. IN A 192.168.1.10"
local-data: "server2.mycompany.local. IN A 192.168.1.11"
```

Redémarrez Unbound:
```bash
docker-compose -f dns-stack-compose.yml restart unbound
```

### 5. Configurer Caddy pour vos services

Éditez `examples/caddy/Caddyfile`:

```
# Ajouter vos domaines
myservice.example.com {
    reverse_proxy backend:8080

    tls {
        protocols tls1.2 tls1.3
    }
}
```

Redémarrez Caddy:
```bash
docker-compose -f dns-stack-compose.yml restart caddy
```

## 🧪 Tests de validation

### Test 1: Plugin System
```bash
python -c "
from mcp_linux_infra.analysis.plugins import get_plugin_registry
r = get_plugin_registry()
plugins = r.get_all_plugins()
print(f'Plugins: {len(plugins)}')
print(f'Commands: {sum(len(p.commands) for p in plugins.values())}')
"
```

### Test 2: Command Analysis
```bash
python -c "
from mcp_linux_infra.analysis.command_analysis import analyze_command_safety
result = analyze_command_safety('systemctl restart nginx')
print(f'Command: {result.command}')
print(f'Risk: {result.risk_level.value}')
print(f'Auth: {result.suggested_level.value}')
"
```

### Test 3: Auto-Learning
```bash
python -c "
from mcp_linux_infra.analysis.auto_learning import AutoLearningEngine
engine = AutoLearningEngine()
engine.record_blocked_command('my-custom-command', user='test', host='localhost')
stats = engine.get_all_stats()
print(f'Blocked commands tracked: {len(stats)}')
"
```

### Test 4: DNS
```bash
# Test Unbound
dig @localhost google.com

# Test DoH (si activé)
curl -H 'accept: application/dns-json' \
  'https://doh.example.com/dns-query?name=google.com&type=A'
```

### Test 5: Caddy
```bash
# Test reverse proxy
curl -I http://localhost/
curl -I https://your-domain.com/
```

## 📚 Documentation complète

- **README.md**: Vue d'ensemble
- **PLUGINS.md**: Référence des plugins (135 commandes)
- **COMMAND-ANALYSIS.md**: Système d'analyse intelligente
- **DEPLOYMENT-READY.md**: Checklist de déploiement
- **examples/**: Configurations d'exemple

## 🐛 Troubleshooting

### Problème: Import error
```bash
# Solution: Réinstaller
pip uninstall mcp-linux-infra
pip install -e .
```

### Problème: SSH connection failed
```bash
# Vérifier les clés
ls -la ~/.ssh/mcp-reader*
ssh-add ~/.ssh/mcp-reader

# Tester manuellement
ssh -i ~/.ssh/mcp-reader mcp-reader@target-host
```

### Problème: DNS ne répond pas
```bash
# Vérifier Unbound
docker logs unbound
# ou
podman logs unbound

# Tester directement
dig @127.0.0.1 google.com
```

### Problème: Caddy certificate error
```bash
# Vérifier les logs
docker logs caddy

# Pour testing local, utiliser HTTP
# ou générer un certificat self-signed
```

## 🎯 Prochaines étapes

1. ✅ MCP installé et testé
2. ✅ Conteneurs Ansible déployés
3. ✅ Stack DNS opérationnelle
4. 🔄 Configurer les hosts cibles
5. 🔄 Créer des playbooks Ansible
6. 🔄 Démarrer le serveur MCP
7. 🔄 Intégrer avec Claude Desktop

## 📞 Support

- GitHub Issues: https://github.com/your-org/mcp-linux-infra/issues
- Documentation: Voir les fichiers .md à la racine
- Logs MCP: `logs/command_stats.json`
- Logs Ansible: `examples/logs/ansible/`
- Logs DNS: `examples/logs/unbound/` et `examples/logs/caddy/`

---

**Version**: 0.3.0
**Date**: 2026-01-19
**Status**: ✅ PRODUCTION READY
