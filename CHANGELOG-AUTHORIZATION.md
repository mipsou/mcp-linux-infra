# Changelog - Command Authorization System

## 🎯 New Feature: SSH Command Execution with Authorization

**Date**: 2026-01-17

### 📦 What's New

Added a complete **command authorization system** for SSH execution with three security levels:

- ✅ **AUTO**: Execute immediately (read-only commands)
- ⚠️ **MANUAL**: Require human approval (system modifications)
- ❌ **BLOCKED**: Refuse execution (dangerous commands)

---

## 🏗️ New Modules

### 1. Authorization System

**Location**: `src/mcp_linux_infra/authorization/`

#### Files Created:
- `__init__.py` - Module exports
- `models.py` - Data models (AuthLevel, CommandRule, CommandAuthorization, PendingCommand)
- `whitelist.py` - Command whitelist (26 rules: 11 AUTO, 10 MANUAL, 5 BLOCKED)
- `engine.py` - Authorization engine with approval workflow

**Features**:
- Regex-based command matching
- Three-tier authorization (AUTO/MANUAL/BLOCKED)
- Approval workflow with unique IDs
- Default deny policy (commands not in whitelist are blocked)

---

### 2. Execution Tools

**Location**: `src/mcp_linux_infra/tools/execution/`

#### Files Created:
- `__init__.py` - Module exports
- `ssh_executor.py` - Core SSH execution with authorization
- `ansible_wrapper.py` - High-level Ansible tools

**Features**:
- Authorized SSH command execution
- Approval management (approve, list pending)
- Whitelist visualization
- Ansible playbook execution (check mode + real execution)

---

## 🛠️ New MCP Tools

### Core Execution Tools

1. **execute_ssh_command** - Execute SSH command with authorization
   - Parameters: `host`, `command`, `auto_approve`
   - Returns: Output or approval request

2. **approve_command** - Approve pending command
   - Parameters: `approval_id`
   - Returns: Execution result

3. **list_pending_approvals** - List pending approvals
   - Returns: Pending commands awaiting approval

4. **show_command_whitelist** - Display authorization whitelist
   - Returns: Complete whitelist with levels

### Ansible Tools

5. **run_ansible_playbook** - Execute Ansible playbook
   - Parameters: `host`, `playbook_path`, `inventory`, `check_mode`, `extra_vars`, `auto_approve`
   - Returns: Ansible output or approval request

6. **check_ansible_playbook** - Run Ansible in check mode
   - Parameters: `host`, `playbook_path`, `inventory`, `extra_vars`
   - Returns: Ansible check mode output (always auto-approved)

7. **list_ansible_playbooks** - List available playbooks
   - Parameters: `host`, `playbooks_dir`
   - Returns: Playbook list

8. **show_ansible_inventory** - Show Ansible inventory
   - Parameters: `host`, `inventory_path`
   - Returns: Inventory contents

**Total New Tools**: 8

---

## 📋 Configuration

### Whitelist Configuration

**Default**: `src/mcp_linux_infra/authorization/whitelist.py`

**Custom (optional)**: `config/command-whitelist.yml`

Example YAML created at: `config/command-whitelist.example.yml`

---

## 🔐 Security Features

### Authorization Levels

#### AUTO (11 rules)
- `systemctl status`, `systemctl list-units`
- `journalctl`, `df -h`, `free -h`, `uptime`
- `ss -lntup`, `ip addr`, `ip route`
- `podman ps`, `podman inspect`, `podman logs`
- `ansible-playbook --check`
- `cat /var/log/`, `tail /var/log/`

#### MANUAL (10 rules)
- `systemctl restart/reload/start/stop`
- `podman restart/start/stop/rm`
- `ansible-playbook` (without --check)
- `reboot`, `shutdown`

#### BLOCKED (5 rules)
- `rm -rf /` (except /tmp)
- `dd of=/dev/`
- `mkfs.*`
- `fdisk`
- Fork bombs

### Security Properties

- ✅ **Default Deny**: Commands not in whitelist are blocked
- ✅ **User Separation**: AUTO uses `mcp-reader`, MANUAL uses `pra-runner`
- ✅ **Approval Workflow**: MANUAL commands require explicit human approval
- ✅ **Audit Trail**: All commands logged with authorization decision
- ✅ **No Bypass**: BLOCKED commands cannot be executed under any circumstances

---

## 🧪 Testing

### Test File Created

**Location**: `test-authorization.py`

### Test Results

```
✅ Whitelist: 26 rules loaded (11 AUTO, 10 MANUAL, 5 BLOCKED)
✅ Authorization Engine: All checks passed
  - AUTO command check: PASS
  - MANUAL command check: PASS
  - BLOCKED command check: PASS
  - Unknown command blocked: PASS
✅ Approval Workflow: All tests passed
  - Approval creation: PASS
  - Command approval: PASS
  - Mark executed: PASS
  - Pending cleanup: PASS
```

---

## 📚 Documentation

### New Documentation Created

1. **COMMAND-AUTHORIZATION.md**
   - Complete guide to authorization system
   - MCP tools reference
   - Workflow examples
   - Best practices
   - Security model

2. **command-whitelist.example.yml**
   - Template for custom whitelist
   - Documented examples for all three levels
   - Usage instructions

3. **CHANGELOG-AUTHORIZATION.md** (this file)
   - Feature summary
   - Technical details
   - Migration guide

---

## 🚀 Usage Examples

### Example 1: Execute Read-Only Command (AUTO)

```python
# In Claude Chat (with linux-infra MCP)
execute_ssh_command("coreos-11", "systemctl status unbound")

# Result: ✅ Executed (auto-approved)
# Service active (running)
```

### Example 2: Restart Service (MANUAL)

```python
# Step 1: Request
execute_ssh_command("coreos-11", "systemctl restart unbound")

# Result: 📋 APPROVAL REQUIRED
# Approval ID: cmd_abc12345

# Step 2: Approve
approve_command("cmd_abc12345")

# Result: ✅ Executed (approved)
# Service restarted
```

### Example 3: Ansible Deployment (MANUAL)

```python
# Dry-run first (AUTO)
check_ansible_playbook("coreos-11", "/opt/infra/playbooks/deploy-pihole-v6.yml")

# Result: ✅ Executed (auto-approved)
# Shows changes that would be made

# Real execution (MANUAL)
run_ansible_playbook("coreos-11", "/opt/infra/playbooks/deploy-pihole-v6.yml", check_mode=False)

# Result: 📋 APPROVAL REQUIRED
# Approval ID: cmd_def45678

# Approve
approve_command("cmd_def45678")

# Result: ✅ Executed (approved)
# Playbook completed
```

---

## 🔄 Integration with Existing System

### Compatible With

- ✅ **SSH Agent**: Uses existing smart_ssh connection manager
- ✅ **User Separation**: Leverages mcp-reader / pra-runner accounts
- ✅ **Audit Logging**: Integrates with existing audit system
- ✅ **PRA System**: Can coexist with existing PRA workflow

### Changes to Existing Code

**Modified Files**:
1. `src/mcp_linux_infra/server.py`
   - Added import: `from .tools.execution import ssh_executor`
   - Added 8 new MCP tools (see above)

**No Breaking Changes**:
- All existing tools continue to work
- Authorization system is additive only
- No modifications to diagnostic or PRA tools

---

## 🎯 Benefits

### For Users

1. **Safer Execution**: Three-tier authorization prevents accidents
2. **Full Remote**: Execute Ansible on coreos-11 without local SSH config
3. **Transparent Approval**: Clear workflow for manual approval
4. **Easy to Use**: High-level Ansible tools simplify common tasks

### For Security

1. **Defense in Depth**: Multiple security layers
2. **Default Deny**: Whitelist-based authorization
3. **Audit Trail**: All commands logged
4. **No Bypass**: BLOCKED commands cannot be overridden

### For Operations

1. **Ansible Integration**: Native playbook execution
2. **Dry-Run First**: Check mode encouraged and easy
3. **Approval Workflow**: Human oversight for changes
4. **Visibility**: See pending approvals and whitelist

---

## 📊 Statistics

### Code Added

- **Python Files**: 4 new modules
- **Lines of Code**: ~1,200 lines
- **MCP Tools**: 8 new tools
- **Whitelist Rules**: 26 rules
- **Documentation**: 2 new docs (~500 lines)

### Test Coverage

- **Unit Tests**: 4 test suites
- **Test Coverage**: Authorization engine, whitelist, approval workflow
- **Pass Rate**: 100% (excluding asyncssh import which requires venv)

---

## 🔮 Future Enhancements

### Planned Features

- [ ] YAML whitelist hot-reload
- [ ] Approval expiration (auto-cleanup old approvals)
- [ ] Command templates (parameterized commands)
- [ ] Approval delegation (user-based permissions)
- [ ] Metrics (commands executed, approval rate, etc.)
- [ ] Web UI for approval workflow
- [ ] Slack/email notifications for pending approvals

### Integration Ideas

- [ ] GitHub Actions integration
- [ ] Terraform execution support
- [ ] kubectl integration
- [ ] Database migration support

---

## 📝 Migration Guide

### For Existing Users

1. **No Action Required**
   - Existing tools (diagnostics, PRA) unchanged
   - Authorization system is additive

2. **To Use New Features**
   - Restart MCP server to load new tools
   - Use `show_command_whitelist()` to see authorized commands
   - Use `execute_ssh_command()` for ad-hoc commands
   - Use `run_ansible_playbook()` for Ansible execution

3. **Custom Whitelist (Optional)**
   - Copy `config/command-whitelist.example.yml` to `config/command-whitelist.yml`
   - Customize rules as needed
   - Modify code to load custom whitelist (see whitelist.py)

---

## 🤝 Contributing

To extend the whitelist:

1. Edit `src/mcp_linux_infra/authorization/whitelist.py`
2. Add new CommandRule to appropriate section (AUTO/MANUAL/BLOCKED)
3. Test with `test-authorization.py`
4. Document in COMMAND-AUTHORIZATION.md

---

## 📄 License

Same as main project (MIT)

---

**Command Authorization System v1.0** - Full Remote SSH Execution with Security

*Developed: 2026-01-17*
*Status: Production Ready ✅*
