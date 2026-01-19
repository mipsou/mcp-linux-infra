# Command Authorization System

## 🎯 Overview

The **Command Authorization System** provides a security layer for SSH command execution with three authorization levels:

- **AUTO**: Execute immediately (read-only commands)
- **MANUAL**: Require human approval before execution
- **BLOCKED**: Refuse execution (dangerous commands)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Claude Desktop (MCP Client)                                 │
│                                                              │
│ "Execute systemctl restart unbound on coreos-11"            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ linux-infra MCP Server                                      │
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Authorization Engine                                    │ │
│ │                                                         │ │
│ │ 1. Check command against whitelist                     │ │
│ │ 2. Determine authorization level:                      │ │
│ │    ├─ AUTO    → Execute immediately                    │ │
│ │    ├─ MANUAL  → Create approval request               │ │
│ │    └─ BLOCKED → Refuse                                 │ │
│ └─────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ SSH Connection (mcp-reader or pra-runner)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Authorization Levels

### ✅ AUTO (Auto-Approved)

**Purpose**: Read-only diagnostic commands

**Behavior**: Execute immediately without human approval

**SSH User**: `mcp-reader`

**Examples**:
- `systemctl status unbound`
- `journalctl -u caddy`
- `df -h`
- `podman ps`
- `ansible-playbook deploy.yml --check` (dry-run)

**Rationale**: No system impact, safe for automated execution

---

### ⚠️ MANUAL (Manual Approval Required)

**Purpose**: Commands that modify system state

**Behavior**: Create approval request, wait for human confirmation

**SSH User**: `pra-runner`

**Examples**:
- `systemctl restart unbound`
- `podman restart pihole`
- `ansible-playbook deploy.yml` (real execution)
- `reboot`

**Workflow**:
1. Command execution requested
2. Approval request created with unique ID
3. Human reviews and approves
4. Command executes with approved parameters

**Rationale**: Service interruption or system changes need human oversight

---

### ❌ BLOCKED (Blocked)

**Purpose**: Dangerous or destructive commands

**Behavior**: Refuse execution immediately

**SSH User**: None

**Examples**:
- `rm -rf /var`
- `dd of=/dev/sda`
- `mkfs.ext4 /dev/sda1`
- `:(){ :|:& };:` (fork bomb)

**Rationale**: Could destroy system or cause DoS

---

## 🛠️ MCP Tools

### execute_ssh_command

Execute SSH command with authorization check.

```python
execute_ssh_command(
    host: str,
    command: str,
    auto_approve: bool = False
) -> str
```

**Examples**:

```python
# AUTO command (executes immediately)
result = execute_ssh_command("coreos-11", "systemctl status unbound")
# Returns: ✅ Executed (auto-approved) ...

# MANUAL command (requires approval)
result = execute_ssh_command("coreos-11", "systemctl restart unbound")
# Returns: 📋 APPROVAL REQUIRED ... Approval ID: cmd_abc12345

# BLOCKED command
result = execute_ssh_command("coreos-11", "rm -rf /var")
# Returns: ❌ COMMAND BLOCKED ...
```

---

### approve_command

Approve and execute a pending command.

```python
approve_command(approval_id: str) -> str
```

**Example**:

```python
# Step 1: Request execution (returns approval ID)
result = execute_ssh_command("coreos-11", "systemctl restart unbound")
# Approval ID: cmd_abc12345

# Step 2: Approve and execute
result = approve_command("cmd_abc12345")
# Returns: ✅ Executed (approved) ...
```

---

### list_pending_approvals

List all pending command approvals.

```python
list_pending_approvals() -> str
```

**Example**:

```python
result = list_pending_approvals()
# Returns:
# 📋 PENDING APPROVALS
#
# ID: cmd_abc12345
# Command: systemctl restart unbound
# Host: coreos-11
# ...
```

---

### show_command_whitelist

Show all authorized commands and their levels.

```python
show_command_whitelist() -> str
```

**Example**:

```python
result = show_command_whitelist()
# Returns complete whitelist with AUTO/MANUAL/BLOCKED commands
```

---

## 🎯 Ansible Integration

### run_ansible_playbook

High-level wrapper for Ansible execution.

```python
run_ansible_playbook(
    host: str,
    playbook_path: str,
    inventory: str = "localhost,",
    check_mode: bool = True,
    extra_vars: dict | None = None,
    auto_approve: bool = False
) -> str
```

**Examples**:

```python
# Dry-run (AUTO - executes immediately)
result = run_ansible_playbook(
    host="coreos-11",
    playbook_path="/opt/infra/playbooks/deploy-pihole-v6.yml",
    check_mode=True
)

# Real execution (MANUAL - requires approval)
result = run_ansible_playbook(
    host="coreos-11",
    playbook_path="/opt/infra/playbooks/deploy-pihole-v6.yml",
    check_mode=False
)
# Returns approval ID, then use approve_command(approval_id)

# With extra variables
result = run_ansible_playbook(
    host="coreos-11",
    playbook_path="/opt/infra/playbooks/deploy.yml",
    check_mode=False,
    extra_vars={"pihole_version": "v6"}
)
```

---

### check_ansible_playbook

Run Ansible in check mode (always auto-approved).

```python
check_ansible_playbook(
    host: str,
    playbook_path: str,
    inventory: str = "localhost,",
    extra_vars: dict | None = None
) -> str
```

**Example**:

```python
result = check_ansible_playbook(
    host="coreos-11",
    playbook_path="/opt/infra/playbooks/deploy-pihole-v6.yml"
)
# Executes immediately (read-only)
```

---

## 📋 Whitelist Configuration

### Default Whitelist

Located in: `src/mcp_linux_infra/authorization/whitelist.py`

### Custom Whitelist (YAML)

Create: `config/command-whitelist.yml`

```yaml
auto_approved:
  - pattern: "^systemctl status\\s+"
    ssh_user: "mcp-reader"
    description: "Check service status"
    rationale: "Read-only"

manual_approval:
  - pattern: "^systemctl restart\\s+"
    ssh_user: "pra-runner"
    description: "Restart service"
    rationale: "Service interruption"

blocked:
  - pattern: ".*rm\\s+-rf\\s+/"
    ssh_user: "none"
    description: "Recursive delete"
    rationale: "Dangerous"
```

Load custom whitelist:

```python
from mcp_linux_infra.authorization import load_whitelist_from_yaml
whitelist = load_whitelist_from_yaml(Path("config/command-whitelist.yml"))
```

---

## 🔒 Security Model

### Defense in Depth

1. **Whitelist Matching**: Commands must match approved patterns
2. **Authorization Level**: AUTO/MANUAL/BLOCKED decision
3. **SSH User Separation**: `mcp-reader` (read-only) vs `pra-runner` (exec)
4. **Approval Workflow**: Human confirmation for MANUAL commands
5. **Audit Logging**: All commands logged with authorization decision

### Default Deny Policy

Commands **not in the whitelist** are **BLOCKED by default**.

This ensures:
- No unexpected command execution
- Explicit authorization required
- Easy to audit (all allowed commands documented)

---

## 📊 Workflow Examples

### Example 1: Read-Only Diagnostic (AUTO)

```
User: "Check unbound status on coreos-11"
  ↓
Claude: execute_ssh_command("coreos-11", "systemctl status unbound")
  ↓
Authorization Engine: ✅ AUTO (matches "^systemctl status")
  ↓
SSH: mcp-reader@coreos-11 "systemctl status unbound"
  ↓
Result: ✅ Executed (auto-approved)
  Service active (running)
```

### Example 2: Service Restart (MANUAL)

```
User: "Restart unbound on coreos-11"
  ↓
Claude: execute_ssh_command("coreos-11", "systemctl restart unbound")
  ↓
Authorization Engine: ⚠️ MANUAL (matches "^systemctl restart")
  ↓
Create approval: cmd_abc12345
  ↓
User: approve_command("cmd_abc12345")
  ↓
SSH: pra-runner@coreos-11 "systemctl restart unbound"
  ↓
Result: ✅ Executed (approved)
  Service restarted
```

### Example 3: Dangerous Command (BLOCKED)

```
User: "Delete /var on coreos-11"
  ↓
Claude: execute_ssh_command("coreos-11", "rm -rf /var")
  ↓
Authorization Engine: ❌ BLOCKED (matches dangerous pattern)
  ↓
Result: ❌ COMMAND BLOCKED
  Reason: DANGEROUS: Could destroy system
```

### Example 4: Ansible Deployment (MANUAL)

```
User: "Deploy Pi-hole v6"
  ↓
Claude: run_ansible_playbook(
    "coreos-11",
    "/opt/infra/playbooks/deploy-pihole-v6.yml",
    check_mode=False
)
  ↓
Authorization Engine: ⚠️ MANUAL (ansible-playbook without --check)
  ↓
Create approval: cmd_def45678
  ↓
User: approve_command("cmd_def45678")
  ↓
SSH: pra-runner@coreos-11 "cd /opt/infra && ansible-playbook ..."
  ↓
Result: ✅ Executed (approved)
  Playbook completed: changed=5, failed=0
```

---

## 🎯 Best Practices

### 1. Always Use Check Mode First

```python
# GOOD: Check first
check_ansible_playbook("coreos-11", "/opt/infra/playbooks/deploy.yml")
# Review output, then:
run_ansible_playbook("coreos-11", "/opt/infra/playbooks/deploy.yml", check_mode=False)

# BAD: Direct execution
run_ansible_playbook("coreos-11", "/opt/infra/playbooks/deploy.yml", check_mode=False)
```

### 2. Never Use auto_approve in Production

```python
# GOOD: Require approval
run_ansible_playbook(..., check_mode=False)
# Then: approve_command(approval_id)

# BAD: Skip approval (DANGEROUS)
run_ansible_playbook(..., check_mode=False, auto_approve=True)
```

### 3. Review Pending Approvals Regularly

```python
# Check what's pending
list_pending_approvals()

# Review before approving
approve_command(approval_id)
```

### 4. Audit the Whitelist

```python
# Review authorized commands
show_command_whitelist()

# Ensure only necessary commands are AUTO or MANUAL
```

---

## 📈 Statistics

From `test-authorization.py`:

```
✅ Whitelist loaded: 26 rules
   - AUTO: 11 (read-only diagnostics)
   - MANUAL: 10 (system modifications)
   - BLOCKED: 5 (dangerous operations)

✅ Authorization Engine: 4/4 tests passed
✅ Approval Workflow: 4/4 tests passed
```

---

## 🔗 Related Documentation

- [Architecture](ARCHITECTURE.md)
- [Security Model](SECURITY.md)
- [SSH Agent Security](SSH-AGENT-SECURITY.md)
- [PRA Procedures](PRA-PROCEDURES.md)

---

**Command Authorization System** - Full Remote SSH Execution with Security Controls

*Created for production-ready infrastructure management* ❤️
