"""
Ansible wrapper for simplified playbook execution

Provides high-level tools for running Ansible playbooks via SSH.
"""

from typing import Optional

from .ssh_executor import execute_ssh_command, approve_command


async def run_ansible_playbook(
    host: str,
    playbook_path: str,
    inventory: str = "localhost,",
    check_mode: bool = True,
    extra_vars: Optional[dict] = None,
    auto_approve: bool = False
) -> str:
    """
    Execute Ansible playbook on remote host

    This is a convenience wrapper around execute_ssh_command that builds
    the ansible-playbook command with proper arguments.

    Args:
        host: Target host where Ansible is installed
        playbook_path: Path to playbook on remote host (e.g., "/opt/infra/playbooks/deploy-pihole-v6.yml")
        inventory: Ansible inventory (default: "localhost," for local execution)
        check_mode: Run in dry-run mode (default: True for safety)
        extra_vars: Extra variables for Ansible (dict)
        auto_approve: Skip approval for non-check mode execution (DANGEROUS!)

    Returns:
        Ansible execution output or approval request

    Examples:
        # Dry-run (auto-approved)
        result = await run_ansible_playbook(
            host="coreos-11",
            playbook_path="/opt/infra/playbooks/deploy-pihole-v6.yml",
            check_mode=True
        )

        # Real execution (requires approval unless auto_approve=True)
        result = await run_ansible_playbook(
            host="coreos-11",
            playbook_path="/opt/infra/playbooks/deploy-pihole-v6.yml",
            check_mode=False
        )
        # Returns approval ID, then use approve_command(approval_id)

        # With extra variables
        result = await run_ansible_playbook(
            host="coreos-11",
            playbook_path="/opt/infra/playbooks/deploy.yml",
            check_mode=False,
            extra_vars={"pihole_version": "v6", "enable_ipv6": True}
        )
    """

    # Build ansible-playbook command
    cmd_parts = [
        "cd /opt/infra &&",
        "ansible-playbook",
        playbook_path,
        f"--inventory={inventory}",
    ]

    # Add check mode flag
    if check_mode:
        cmd_parts.append("--check")

    # Add extra variables
    if extra_vars:
        # Convert dict to ansible format: key1=value1 key2=value2
        vars_str = " ".join(f"{k}={v}" for k, v in extra_vars.items())
        cmd_parts.append(f'--extra-vars "{vars_str}"')

    # Join command
    command = " ".join(cmd_parts)

    # Execute via authorization system
    return await execute_ssh_command(
        host=host,
        command=command,
        auto_approve=auto_approve
    )


async def check_ansible_playbook(
    host: str,
    playbook_path: str,
    inventory: str = "localhost,",
    extra_vars: Optional[dict] = None
) -> str:
    """
    Run Ansible playbook in check mode (dry-run)

    This is always auto-approved as it's read-only.

    Args:
        host: Target host
        playbook_path: Path to playbook on remote host
        inventory: Ansible inventory
        extra_vars: Extra variables

    Returns:
        Ansible check mode output

    Example:
        result = await check_ansible_playbook(
            host="coreos-11",
            playbook_path="/opt/infra/playbooks/deploy-pihole-v6.yml"
        )
    """
    return await run_ansible_playbook(
        host=host,
        playbook_path=playbook_path,
        inventory=inventory,
        check_mode=True,
        extra_vars=extra_vars,
        auto_approve=False  # Not needed for check mode, but explicit
    )


async def list_ansible_playbooks(host: str, playbooks_dir: str = "/opt/infra/playbooks") -> str:
    """
    List available Ansible playbooks on remote host

    Args:
        host: Target host
        playbooks_dir: Directory containing playbooks

    Returns:
        List of playbook files

    Example:
        result = await list_ansible_playbooks("coreos-11")
    """
    command = f"ls -lh {playbooks_dir}/*.yml"
    return await execute_ssh_command(host=host, command=command)


async def show_ansible_inventory(host: str, inventory_path: str = "/opt/infra/inventory") -> str:
    """
    Show Ansible inventory on remote host

    Args:
        host: Target host
        inventory_path: Path to inventory directory or file

    Returns:
        Inventory contents

    Example:
        result = await show_ansible_inventory("coreos-11")
    """
    command = f"cat {inventory_path}/hosts || cat {inventory_path}"
    return await execute_ssh_command(host=host, command=command)
