# Modèle de Sécurité

## Principes Fondamentaux

### Principe du Moindre Privilège

**Chaque compte ne peut faire que ce pour quoi il est conçu, rien de plus.**

- `mcp-reader` : AUCUN sudo, lecture seule
- `pra-runner` : sudo UNIQUEMENT pour `/usr/local/bin/pra-run`

### Défense en Profondeur

**5 couches de sécurité indépendantes:**

```
1. Host Whitelist (CONFIG)
2. SSH Forced-Command (authorized_keys)
3. Wrapper Whitelist (mcp-wrapper / pra-exec)
4. Sudo Restriction (sudoers)
5. Action Validation (PRA workflow)
```

**Chaque couche peut arrêter une attaque indépendamment.**

### Séparation des Privilèges

**2 canaux SSH complètement séparés:**

| Aspect | mcp-reader | pra-runner |
|--------|------------|-----------|
| Clé SSH | mcp-reader.key | pra-exec.key |
| Shell | /bin/bash | /usr/sbin/nologin |
| Sudo | ❌ AUCUN | ✅ 1 script seulement |
| Usage | Diagnostics | Actions validées |
| Risque | LOW | MEDIUM |

**Compromission de mcp-reader ≠ compromission de pra-runner**

### Zero Trust

**Aucune confiance implicite:**
- Toute commande est validée (whitelist)
- Toute action PRA nécessite validation humaine
- Tout accès est loggé
- Aucun wildcard dans les permissions

## Menaces et Mitigations

### Menace 1: Compromission de mcp-reader.key

**Scénario:** Attaquant obtient la clé SSH read-only

**Impact:**
- ✅ Peut lire diagnostics système
- ❌ AUCUNE modification possible
- ❌ AUCUN sudo
- ❌ AUCUN shell libre (forced-command)

**Mitigation:**
1. Forced-command bloque shell interactif
2. Wrapper refuse toute commande non listée
3. Aucun privilège système
4. Révocation rapide: supprimer la ligne dans authorized_keys

**Détection:**
- Logs SSH anormaux dans /var/log/auth.log
- Tentatives de commandes refusées dans /var/log/mcp-wrapper.log
- Patterns anormaux (volume, horaires)

**Réponse:**
```bash
# Sur target Linux
sudo sed -i '/mcp-reader/d' /home/mcp-reader/.ssh/authorized_keys

# Générer nouvelle clé
ssh-keygen -t ed25519 -f keys/mcp-reader-new.key
ansible-playbook rotate-keys.yml
```

### Menace 2: Compromission de pra-exec.key

**Scénario:** Attaquant obtient la clé SSH PRA

**Impact:**
- ✅ Peut exécuter actions PRA whitelistées
- ❌ AUCUNE autre action possible
- ❌ AUCUN shell (forced-command)
- ❌ sudo limité à 1 script

**Mitigation:**
1. Forced-command bloque shell
2. Whitelist stricte dans pra-exec
3. Actions PRA requièrent validation humaine upstream (MCP server)
4. Sudo ne donne accès qu'à pra-run (pas bash/sh)

**Détection:**
- Actions PRA sans validation humaine
- Logs pra-exec avec commandes refusées
- Appels directs SSH (pas via MCP server)

**Réponse:**
```bash
# Révocation immédiate
sudo sed -i '/pra-runner/d' /home/pra-runner/.ssh/authorized_keys

# Audit des actions récentes
sudo grep pra-run /var/log/pra-run.log | tail -100

# Investigation
sudo journalctl -u sshd | grep pra-runner

# Rotation clé
ssh-keygen -t ed25519 -f keys/pra-exec-new.key
ansible-playbook rotate-keys.yml --tags pra
```

### Menace 3: Exploitation Wrapper (Command Injection)

**Scénario:** Attaquant tente d'injecter commandes via wrapper

**Exemple:**
```bash
# Tentative
ssh mcp-reader@target "systemctl status nginx; rm -rf /"
```

**Mitigation:**

**Pattern 1: Whitelist stricte (pas de wildcard)**
```bash
# BIEN
case "$SSH_ORIGINAL_COMMAND" in
    "systemctl status nginx") exec $SSH_ORIGINAL_COMMAND ;;
esac

# MAUVAIS
case "$SSH_ORIGINAL_COMMAND" in
    "systemctl status "*) exec $SSH_ORIGINAL_COMMAND ;;  # Dangereux
esac
```

**Pattern 2: Validation des arguments**
```bash
case "$SSH_ORIGINAL_COMMAND" in
    "tail -n "*/var/log/*)
        # Vérifier que chemin est dans /var/log
        if [[ "$SSH_ORIGINAL_COMMAND" =~ tail\ -n\ [0-9]+\ /var/log/.* ]]; then
            exec $SSH_ORIGINAL_COMMAND
        fi
        ;;
esac
```

**Pattern 3: Pas de shell metacharacters**
```bash
# Log et rejeter toute tentative d'injection
if [[ "$SSH_ORIGINAL_COMMAND" =~ [\;\|\&\$\`] ]]; then
    echo "SECURITY: Shell metacharacters detected" >&2
    exit 1
fi
```

### Menace 4: Escalade Privilege via Sudo

**Scénario:** Attaquant tente d'exploiter sudo pra-runner

**Tentatives typiques:**
```bash
sudo /usr/local/bin/pra-run "restart_unbound; bash"  # Injection
sudo bash  # Shell direct
sudo -i  # Interactive shell
sudo su  # Switch user
```

**Mitigation:**

**Sudoers strict:**
```bash
# BIEN
pra-runner ALL=(root) NOPASSWD: /usr/local/bin/pra-run

# MAUVAIS (ne jamais faire)
pra-runner ALL=(root) NOPASSWD: ALL
pra-runner ALL=(root) NOPASSWD: /usr/local/bin/*
pra-runner ALL=(root) NOPASSWD: /bin/bash
```

**Deny shell dans sudoers:**
```bash
pra-runner ALL=(root) !/bin/bash, !/bin/sh, !/usr/bin/bash
```

**pra-run n'accepte qu'un seul argument (action name):**
```bash
#!/bin/bash
if [ $# -ne 1 ]; then
    echo "ERROR: Exactly one action required" >&2
    exit 1
fi

ACTION="$1"
# Pas d'évaluation shell, juste case/esac
```

### Menace 5: Actions PRA Malveillantes

**Scénario:** IA propose action destructive sans validation humaine

**Exemple:**
```python
propose_pra_action(
    action="reboot_system",
    host="prod-db",
    rationale="Performance optimization",
    auto_approve=True  # DANGEREUX
)
```

**Mitigation:**

**1. Auto-approve limité à LOW impact:**
```python
if auto_approve and action_def["impact"] == PRAImpact.LOW:
    # OK pour restart service, flush cache
    pra_action.status = PRAActionStatus.APPROVED
else:
    # Requiert validation humaine
    pra_action.status = PRAActionStatus.PROPOSED
```

**2. Impact levels:**
```python
PRA_ACTION_CATALOG = {
    "restart_unbound": {"impact": PRAImpact.LOW},  # Auto-approve OK
    "reload_caddy": {"impact": PRAImpact.LOW},
    "reboot_system": {"impact": PRAImpact.HIGH},  # Jamais auto-approve
}
```

**3. Validation humaine obligatoire:**
```python
if pra_action.status != PRAActionStatus.APPROVED:
    raise Error("Action requires human approval")
```

**4. Timeout sur approbations:**
```python
if (datetime.now() - pra_action.proposed_at).seconds > 300:
    # Expirer après 5 minutes
    del _pending_actions[action_id]
```

### Menace 6: Man-in-the-Middle SSH

**Scénario:** Attaquant intercepte connexion SSH

**Mitigation:**

**1. Strict host key checking (TODO: activer en prod):**
```python
conn = await asyncssh.connect(
    host=host,
    known_hosts="/path/to/known_hosts",  # Actuellement None (INSECURE)
)
```

**2. SSH Certificates (avancé):**
```bash
# CA pour signer les clés
ssh-keygen -s ca-key -I mcp-reader -n mcp-reader mcp-reader.key.pub

# authorized_keys avec CA
cert-authority ssh-ed25519 AAAAC3... ca-key.pub
```

**3. Bastion/Jumphost:**
```
MCP Server → Bastion (VPN) → Targets
```

## Audit et Détection

### Logs à Monitorer

**1. SSH Auth (target):**
```bash
sudo tail -f /var/log/auth.log | grep "sshd\|mcp-reader\|pra-runner"
```

**Patterns anormaux:**
- Échecs d'authentification répétés
- Connexions depuis IPs inconnues
- Horaires inhabituels

**2. MCP Wrapper (target):**
```bash
sudo tail -f /var/log/mcp-wrapper.log
```

**Patterns anormaux:**
- DENIED entries
- Commandes non standards
- Volume élevé soudain

**3. PRA Execution (target):**
```bash
sudo tail -f /var/log/pra-exec.log /var/log/pra-run.log
```

**Patterns anormaux:**
- Actions échouées répétées
- Actions HIGH impact
- Actions hors heures d'ouverture

**4. MCP Server Audit (Windows):**
```powershell
Get-Content mcp-audit-*.json | ConvertFrom-Json | Where-Object { $_.event_type -eq "security_violation" }
```

### Alerting

**Critères d'alerte:**

**CRITICAL:**
- Tentative d'injection shell détectée
- Escalade sudo refusée
- Action PRA HIGH impact sans approbation
- >10 échecs SSH en 1 minute

**WARNING:**
- >5 commandes DENIED en 5 minutes
- Action PRA échouée
- Connexion depuis IP inhabituelle

**INFO:**
- Nouvelle clé SSH ajoutée
- Rotation de clés effectuée
- Action PRA MEDIUM impact

### Forensics

**En cas d'incident:**

**1. Snapshot logs:**
```bash
sudo tar czf /tmp/incident-$(date +%s).tar.gz \
    /var/log/auth.log \
    /var/log/mcp-wrapper.log \
    /var/log/pra-exec.log \
    /var/log/pra-run.log \
    /var/log/syslog
```

**2. Audit recent SSH connections:**
```bash
sudo lastlog | grep -E "mcp-reader|pra-runner"
sudo last | grep -E "mcp-reader|pra-runner"
```

**3. Check active sessions:**
```bash
sudo w
sudo who
```

**4. Review recent sudo commands:**
```bash
sudo grep pra-runner /var/log/auth.log | grep sudo
```

**5. Analyze command history:**
```bash
# Wrapper logs
sudo awk '{print $3}' /var/log/mcp-wrapper.log | sort | uniq -c | sort -rn
```

## Recommandations Production

### Avant Déploiement

- [ ] Activer strict `known_hosts` validation
- [ ] Générer clés SSH dédiées par environnement
- [ ] Configurer SIEM/alerting sur logs
- [ ] Définir runbook incident response
- [ ] Tester procédures de révocation
- [ ] Documenter contacts escalation

### Hardening Additionnel

**1. Fail2ban pour SSH:**
```bash
# /etc/fail2ban/jail.local
[sshd]
enabled = true
maxretry = 3
bantime = 3600
```

**2. Rate limiting wrapper:**
```bash
# /usr/local/bin/mcp-wrapper
# Limiter à 100 commandes/minute
if [ $(wc -l < /tmp/mcp-wrapper-rate) -gt 100 ]; then
    echo "RATE LIMIT EXCEEDED" >&2
    exit 1
fi
```

**3. 2FA pour actions HIGH impact:**
```python
if action_def["impact"] == PRAImpact.HIGH:
    require_otp = True
```

**4. Network segmentation:**
- MCP server → VPN → Bastion → Targets
- Firewall rules: deny tout sauf SSH from bastion

**5. Key rotation automatique:**
```bash
# Cron mensuel
0 0 1 * * /usr/local/bin/rotate-mcp-keys.sh
```

## Compliance

### Audit Trail Requirements

**RGPD/SOC2:**
- ✅ Toutes les actions loggées
- ✅ Authentification traçable (clés SSH)
- ✅ Séparation des privilèges
- ✅ Logs immutables (append-only)
- ✅ Révocation rapide (< 5 min)

### Data Protection

**Secrets handling:**
- ✅ Clés SSH chiffrées au repos
- ✅ Passphrases jamais loggées
- ✅ Sanitization dans audit logs
- ✅ Pas de secrets dans code source

### Access Control

- ✅ Principe moindre privilège
- ✅ Séparation duties (read vs exec)
- ✅ Validation humaine obligatoire
- ✅ Audit trail complet

## Contact Sécurité

**Signaler une vulnérabilité:** security@example.com

**PGP Key:** [À définir]

**Bug Bounty:** [À définir]
