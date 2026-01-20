"""MCP Linux Infra Server - Production-Ready Infrastructure Management."""

from mcp.server.fastmcp import FastMCP

from .tools.diagnostics import logs, network, services, system
from .tools.Remote Execution import actions
from .tools.execution import ssh_executor

# Initialize MCP server with FastMCP
mcp = FastMCP("mcp-linux-infra")


# ============================================================================
# DIAGNOSTIC TOOLS (Read-Only via SSH mcp-reader)
# ============================================================================

@mcp.tool()
async def get_system_info(host: str | None = None) -> str:
    """Get comprehensive system information (read-only)."""
    return await system.get_system_info(host)


@mcp.tool()
async def get_cpu_info(host: str | None = None) -> str:
    """Get CPU information (read-only)."""
    return await system.get_cpu_info(host)


@mcp.tool()
async def get_memory_info(host: str | None = None) -> str:
    """Get memory information (read-only)."""
    return await system.get_memory_info(host)


@mcp.tool()
async def get_disk_usage(host: str | None = None) -> str:
    """Get disk usage information (read-only)."""
    return await system.get_disk_usage(host)


@mcp.tool()
async def get_block_devices(host: str | None = None) -> str:
    """List block devices (read-only)."""
    return await system.get_block_devices(host)


@mcp.tool()
async def list_services(host: str | None = None) -> str:
    """List all systemd services (read-only)."""
    return await services.list_services(host)


@mcp.tool()
async def get_service_status(service_name: str, host: str | None = None) -> str:
    """Get detailed status of a systemd service (read-only)."""
    return await services.get_service_status(service_name, host)


@mcp.tool()
async def get_service_logs(service_name: str, lines: int = 50, host: str | None = None) -> str:
    """Get recent logs for a systemd service (read-only)."""
    return await services.get_service_logs(service_name, lines, host)


@mcp.tool()
async def check_service_health(service_name: str, host: str | None = None) -> str:
    """Comprehensive health check for a service (read-only)."""
    return await services.check_service_health(service_name, host)


@mcp.tool()
async def get_network_interfaces(host: str | None = None) -> str:
    """Get network interfaces configuration (read-only)."""
    return await network.get_network_interfaces(host)


@mcp.tool()
async def get_routing_table(host: str | None = None) -> str:
    """Get routing table (read-only)."""
    return await network.get_routing_table(host)


@mcp.tool()
async def get_listening_ports(host: str | None = None) -> str:
    """Get listening TCP/UDP ports (read-only)."""
    return await network.get_listening_ports(host)


@mcp.tool()
async def get_active_connections(host: str | None = None) -> str:
    """Get active network connections (read-only)."""
    return await network.get_active_connections(host)


@mcp.tool()
async def get_dns_config(host: str | None = None) -> str:
    """Get DNS configuration (read-only)."""
    return await network.get_dns_config(host)


@mcp.tool()
async def test_connectivity(target: str, count: int = 4, host: str | None = None) -> str:
    """Test network connectivity to a target (read-only)."""
    return await network.test_connectivity(target, count, host)


@mcp.tool()
async def get_journal_logs(
    lines: int = 100,
    priority: str | None = None,
    since: str | None = None,
    unit: str | None = None,
    host: str | None = None,
) -> str:
    """Get systemd journal logs with filters (read-only)."""
    return await logs.get_journal_logs(lines, priority, since, unit, host)


@mcp.tool()
async def read_log_file(path: str, lines: int = 100, host: str | None = None) -> str:
    """Read a specific log file (read-only)."""
    return await logs.read_log_file(path, lines, host)


@mcp.tool()
async def search_logs(
    pattern: str,
    log_path: str | None = None,
    lines: int = 50,
    context: int = 2,
    host: str | None = None,
) -> str:
    """Search for pattern in logs (read-only)."""
    return await logs.search_logs(pattern, log_path, lines, context, host)


@mcp.tool()
async def analyze_errors(
    service: str | None = None, since: str = "1h", host: str | None = None
) -> str:
    """Analyze error logs (read-only)."""
    return await logs.analyze_errors(service, since, host)


# ============================================================================
# Remote Execution ACTIONS (Exec via SSH exec-runner, requires human validation)
# ============================================================================

@mcp.tool()
async def propose_remote_execution(
    action: str, host: str, rationale: str, auto_approve: bool = False
) -> str:
    """
    Propose a remote execution for human validation.

    Step 1 of Remote Execution workflow.
    """
    return await actions.propose_remote_execution(action, host, rationale, auto_approve)


@mcp.tool()
async def approve_remote_execution(action_id: str, approved: bool, approver: str = "human") -> str:
    """
    Approve or reject a proposed remote execution.

    Step 2 of Remote Execution workflow (human validation).
    """
    return await actions.approve_remote_execution(action_id, approved, approver)


@mcp.tool()
async def execute_remote_execution(action_id: str) -> str:
    """
    Execute an approved remote execution.

    Step 3 of Remote Execution workflow (execution).
    """
    return await actions.execute_remote_execution(action_id)


@mcp.tool()
async def list_pending_actions() -> str:
    """List all pending remote executions awaiting approval."""
    return await actions.list_pending_actions()


# ============================================================================
# SSH COMMAND EXECUTION (with Authorization)
# ============================================================================

@mcp.tool()
async def execute_ssh_command(host: str, command: str, auto_approve: bool = False) -> str:
    """
    Execute SSH command with authorization check.

    Commands are checked against a whitelist:
    - AUTO: Execute immediately (read-only commands)
    - MANUAL: Require human approval
    - BLOCKED: Refuse execution (dangerous commands)

    Args:
        host: Target host (e.g., "coreos-11")
        command: Command to execute
        auto_approve: Skip approval for MANUAL commands (DANGEROUS!)

    Returns:
        Command output or approval request
    """
    return await ssh_executor.execute_ssh_command(host, command, auto_approve)


@mcp.tool()
async def approve_command(approval_id: str) -> str:
    """
    Approve and execute a pending command.

    Args:
        approval_id: Approval request ID from execute_ssh_command

    Returns:
        Execution result
    """
    return await ssh_executor.approve_command(approval_id)


@mcp.tool()
async def list_pending_approvals() -> str:
    """List all pending command approvals."""
    return await ssh_executor.list_pending_approvals()


@mcp.tool()
async def show_command_whitelist() -> str:
    """Show all authorized commands and their authorization levels."""
    return await ssh_executor.show_command_whitelist()


# ============================================================================
# ANSIBLE EXECUTION (High-Level Wrappers)
# ============================================================================

@mcp.tool()
async def run_ansible_playbook(
    host: str,
    playbook_path: str,
    inventory: str = "localhost,",
    check_mode: bool = True,
    extra_vars: dict | None = None,
    auto_approve: bool = False
) -> str:
    """
    Execute Ansible playbook on remote host.

    Args:
        host: Target host where Ansible is installed
        playbook_path: Path to playbook on remote host (e.g., "/opt/infra/playbooks/deploy.yml")
        inventory: Ansible inventory (default: "localhost," for local execution)
        check_mode: Run in dry-run mode (default: True for safety)
        extra_vars: Extra variables for Ansible (dict)
        auto_approve: Skip approval for non-check mode execution (DANGEROUS!)

    Returns:
        Ansible output or approval request
    """
    from .tools.execution import ansible_wrapper
    return await ansible_wrapper.run_ansible_playbook(
        host, playbook_path, inventory, check_mode, extra_vars, auto_approve
    )


@mcp.tool()
async def check_ansible_playbook(
    host: str,
    playbook_path: str,
    inventory: str = "localhost,",
    extra_vars: dict | None = None
) -> str:
    """
    Run Ansible playbook in check mode (dry-run, always auto-approved).

    Args:
        host: Target host
        playbook_path: Path to playbook on remote host
        inventory: Ansible inventory
        extra_vars: Extra variables

    Returns:
        Ansible check mode output
    """
    from .tools.execution import ansible_wrapper
    return await ansible_wrapper.check_ansible_playbook(host, playbook_path, inventory, extra_vars)


@mcp.tool()
async def list_ansible_playbooks(host: str, playbooks_dir: str = "/opt/infra/playbooks") -> str:
    """
    List available Ansible playbooks on remote host.

    Args:
        host: Target host
        playbooks_dir: Directory containing playbooks

    Returns:
        List of playbook files
    """
    from .tools.execution import ansible_wrapper
    return await ansible_wrapper.list_ansible_playbooks(host, playbooks_dir)


@mcp.tool()
async def show_ansible_inventory(host: str, inventory_path: str = "/opt/infra/inventory") -> str:
    """
    Show Ansible inventory on remote host.

    Args:
        host: Target host
        inventory_path: Path to inventory directory or file

    Returns:
        Inventory contents
    """
    from .tools.execution import ansible_wrapper
    return await ansible_wrapper.show_ansible_inventory(host, inventory_path)


# ============================================================================
# COMMAND ANALYSIS & LEARNING (Smart Whitelist Management)
# ============================================================================

@mcp.tool()
async def analyze_command(command: str, host: str = "localhost") -> str:
    """
    Analyze a command and provide safety recommendations.

    Performs comprehensive analysis including:
    - Risk assessment (CRITICAL/HIGH/MEDIUM/LOW/UNKNOWN)
    - Category identification (monitoring, network, destructive, etc.)
    - Similarity to existing whitelisted commands
    - Actionable suggestions (ADD_AUTO, ADD_MANUAL, BLOCK, etc.)

    Args:
        command: Command to analyze
        host: Target host (for context)

    Returns:
        Detailed analysis with risk level and suggestions
    """
    from .analysis.command_analysis import analyze_command_safety
    import json

    analysis = analyze_command_safety(command)

    result = {
        'command': command,
        'host': host,
        'status': 'NOT_IN_WHITELIST' if analysis.recommended_action != 'ALREADY_WHITELISTED' else 'WHITELISTED',
        'risk_assessment': {
            'risk_level': analysis.risk_level.value,
            'category': analysis.category,
            'is_readonly': analysis.is_readonly,
        },
        'suggestion': {
            'authorization_level': analysis.suggested_level.value if analysis.suggested_level else None,
            'ssh_user': analysis.suggested_ssh_user,
            'rationale': analysis.rationale,
            'can_auto_add': analysis.can_auto_add,
        },
        'similar_commands': analysis.similar_commands,
        'recommended_action': analysis.recommended_action,
    }

    # Format output
    output = f"""
🔍 COMMAND ANALYSIS

Command: {command}
Host: {host}
Status: {result['status']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 RISK ASSESSMENT

Risk Level: {result['risk_assessment']['risk_level']}
Category: {result['risk_assessment']['category']}
Read-Only: {'Yes' if result['risk_assessment']['is_readonly'] else 'No'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 SUGGESTION

Recommended Action: {result['recommended_action']}
"""

    if result['suggestion']['authorization_level']:
        output += f"""
Authorization Level: {result['suggestion']['authorization_level']}
SSH User: {result['suggestion']['ssh_user']}
Rationale: {result['suggestion']['rationale']}

Can Auto-Add: {'Yes ✅' if result['suggestion']['can_auto_add'] else 'No ⚠️'}
"""

    if result['similar_commands']:
        output += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 SIMILAR COMMANDS IN WHITELIST

"""
        for cmd in result['similar_commands']:
            output += f"  • {cmd}\n"

    # Add actionable next steps
    output += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚙️  NEXT STEPS

"""

    if result['recommended_action'] == 'ADD_AUTO':
        output += f"""1. Add to whitelist as AUTO (recommended):
   Pattern: ^{command.replace(' ', r'\s+')}$
   Level: AUTO
   User: {result['suggestion']['ssh_user']}

2. Execute once via Remote Execution:
   Use: propose_remote_execution(action="{command}", host="{host}")
"""
    elif result['recommended_action'] == 'ADD_MANUAL':
        output += f"""1. Add to whitelist as MANUAL:
   Pattern: ^{command.replace(' ', r'\s+')}
   Level: MANUAL
   User: {result['suggestion']['ssh_user']}

2. Execute once via Remote Execution:
   Use: propose_remote_execution(action="{command}", host="{host}")
"""
    elif result['recommended_action'] == 'BLOCK_PERMANENTLY':
        output += """1. DO NOT add to whitelist - DANGEROUS
2. Use Ansible playbook instead for safe execution
3. Consider alternative safer commands
"""
    elif result['recommended_action'] == 'ALREADY_WHITELISTED':
        output += f"""This command is already authorized.
You can execute it directly using:
  execute_ssh_command(command="{command}", host="{host}")
"""
    else:
        output += """1. Manual review required
2. Execute once via Remote Execution if needed:
   Use: propose_remote_execution(action="{}", host="{}")
"""

    return output


@mcp.tool()
async def get_learning_suggestions(
    min_count: int = 5,
    min_age_hours: int = 24
) -> str:
    """
    Get auto-learning suggestions for frequently blocked commands.

    Analyzes command execution history to identify:
    - Frequently blocked commands (>= min_count attempts)
    - Commands that have been blocked for sufficient time (>= min_age_hours)
    - Only LOW-risk commands are suggested for auto-addition

    Args:
        min_count: Minimum number of blocked attempts (default: 5)
        min_age_hours: Minimum age since first block in hours (default: 24)

    Returns:
        List of suggested commands to add to whitelist
    """
    from .analysis.auto_learning import get_learning_suggestions

    suggestions = get_learning_suggestions(
        min_count=min_count,
        min_age_hours=min_age_hours
    )

    if not suggestions:
        return """
📊 AUTO-LEARNING SUGGESTIONS

No suggestions at this time.

Criteria:
  • Minimum blocked attempts: {min_count}
  • Minimum age: {min_age_hours} hours
  • Maximum risk: LOW

The system is learning from blocked command patterns.
""".format(min_count=min_count, min_age_hours=min_age_hours)

    output = f"""
📊 AUTO-LEARNING SUGGESTIONS

Found {len(suggestions)} command(s) that could be added to whitelist.

Criteria:
  • Minimum blocked attempts: {min_count}
  • Minimum age: {min_age_hours} hours
  • Maximum risk: LOW

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

    for i, sug in enumerate(suggestions, 1):
        output += f"""
【{i}】 {sug['command']}

  Statistics:
    • Blocked {sug['count']} times
    • First seen {sug['age_hours']} hours ago
    • Users: {', '.join(sug['users'])}
    • Hosts: {', '.join(sug['hosts'])}

  Analysis:
    • Risk Level: {sug['risk_level']}
    • Category: {sug['category']}
    • Suggested Level: {sug['suggested_level']}
    • SSH User: {sug['suggested_ssh_user']}
    • Rationale: {sug['rationale']}

  Recommendation: {sug['recommended_action']}
  {'✅ Can auto-add' if sug['can_auto_add'] else '⚠️  Requires review'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    output += f"""

💡 To add a command to whitelist:
   1. Edit src/mcp_linux_infra/authorization/whitelist.py
   2. Add CommandRule with suggested parameters
   3. Restart MCP server
"""

    return output


@mcp.tool()
async def get_learning_stats() -> str:
    """
    Get statistics about auto-learning system.

    Returns:
        Summary of learning stats including:
        - Total unique blocked commands
        - Total block attempts
        - Breakdown by risk level
        - Breakdown by category
    """
    from .analysis.auto_learning import get_learning_engine

    engine = get_learning_engine()
    summary = engine.get_stats_summary()
    top_blocked = engine.get_top_blocked_commands(limit=10)

    output = f"""
📊 AUTO-LEARNING STATISTICS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Overview:
  • Total Unique Commands: {summary['total_unique_commands']}
  • Total Block Attempts: {summary['total_block_attempts']}
  • Stats File: {summary['stats_file']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Risk Level Breakdown:
"""

    for risk, count in summary['risk_breakdown'].items():
        output += f"  • {risk}: {count} commands\n"

    output += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Category Breakdown:
"""

    for category, count in summary['category_breakdown'].items():
        output += f"  • {category}: {count} commands\n"

    if top_blocked:
        output += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔝 TOP 10 MOST BLOCKED COMMANDS:

"""
        for i, stat in enumerate(top_blocked, 1):
            output += f"  {i}. {stat.command}\n"
            output += f"     Blocked: {stat.count} times | Risk: {stat.risk_level}\n"
            output += f"     Users: {', '.join(stat.users)}\n\n"

    output += """
💡 Use get_learning_suggestions() to see whitelist recommendations.
"""

    return output


# ============================================================================
# PLUGIN SYSTEM (Command Family Catalog)
# ============================================================================

@mcp.tool()
async def list_command_plugins() -> str:
    """
    List all available command plugins and their commands.

    Returns comprehensive catalog of command families:
    - Monitoring: htop, iotop, nethogs, etc.
    - Network: ping, curl, netstat, etc.
    - Filesystem: ls, cat, grep, etc.
    - Systemd: systemctl, journalctl, etc.
    - Containers: podman, docker, etc.

    Returns:
        Summary of all plugins with command counts
    """
    from .analysis.plugins import get_plugin_registry

    registry = get_plugin_registry()
    summary = registry.get_summary()

    output = f"""
🔌 COMMAND PLUGIN CATALOG

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Overview:
  • Total Plugins: {summary['total_plugins']}
  • Total Commands: {summary['total_commands']}
  • Categories: {', '.join(summary['categories'])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Plugins by Category:

"""

    for plugin_name, plugin_info in sorted(summary['plugins'].items()):
        output += f"""
【{plugin_name.upper()}】 - {plugin_info['description']}
  Category: {plugin_info['category']}
  Commands: {plugin_info['command_count']}

  Available commands:
"""
        for cmd_name, cmd_spec in list(plugin_info['commands'].items())[:5]:  # Show first 5
            output += f"    • {cmd_name} - {cmd_spec['description']}\n"

        if plugin_info['command_count'] > 5:
            output += f"    ... and {plugin_info['command_count'] - 5} more\n"

        output += "\n"

    output += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Use get_plugin_details(plugin_name) for full command list
"""

    return output


@mcp.tool()
async def get_plugin_details(plugin_name: str) -> str:
    """
    Get detailed information about a specific command plugin.

    Args:
        plugin_name: Plugin name (e.g., "monitoring", "network", "filesystem")

    Returns:
        Detailed guide with all commands, examples, and flags
    """
    from .analysis.plugins import get_plugin_registry

    registry = get_plugin_registry()
    plugin = registry.get_plugin(plugin_name)

    if not plugin:
        available = ', '.join(registry.list_plugins())
        return f"""
❌ Plugin '{plugin_name}' not found.

Available plugins: {available}

Use list_command_plugins() to see all plugins.
"""

    return plugin.get_usage_guide()


@mcp.tool()
async def search_commands(query: str) -> str:
    """
    Search for commands across all plugins.

    Args:
        query: Search term (searches command names and descriptions)

    Returns:
        List of matching commands with details
    """
    from .analysis.plugins import get_plugin_registry

    registry = get_plugin_registry()
    results = registry.search_commands(query)

    if not results:
        return f"""
🔍 SEARCH: "{query}"

No commands found matching your query.

Try:
  • list_command_plugins() to browse all commands
  • Broader search term
"""

    output = f"""
🔍 SEARCH RESULTS: "{query}"

Found {len(results)} matching command(s):

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

    for cmd_name, plugin, spec in results:
        output += f"""
【{cmd_name}】 ({plugin.category})
  Plugin: {plugin.name}
  Risk: {spec.risk.value} | Level: {spec.level.value}
  Description: {spec.description}
  Rationale: {spec.rationale}

"""
        if spec.examples:
            output += "  Examples:\n"
            for example in spec.examples[:2]:  # Show first 2
                output += f"    • {example}\n"
            output += "\n"

    output += f"""
💡 Use get_plugin_details("{results[0][1].name}") for full details
"""

    return output


# ============================================================================
# Server Entry Point
# ============================================================================

# FastMCP handles its own entry point
# No need for custom main() and run() functions
