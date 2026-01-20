#!/usr/bin/env python3
"""
Migrate PRA (Plan de Reprise d'Activité) to EXEC (Remote Execution)

This script renames all PRA-related variables, functions, and comments
to use the clearer "Remote Execution" (exec) terminology.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple


# Mapping of old names to new names
REPLACEMENTS: Dict[str, str] = {
    # Variables and config
    "pra_key_path": "exec_key_path",
    "pra_user": "exec_user",
    "pra_key_passphrase": "exec_key_passphrase",
    "PRA_KEY_PATH": "EXEC_KEY_PATH",
    "PRA_USER": "EXEC_USER",

    # Functions
    "propose_pra_action": "propose_remote_execution",
    "approve_pra_action": "approve_remote_execution",
    "execute_pra_action": "execute_remote_execution",
    "execute_pra_command": "execute_exec_command",
    "get_exec_connection": "get_exec_connection",  # Already correct

    # Classes and types
    "PRAAction": "RemoteExecution",
    "PRAActionStatus": "RemoteExecutionStatus",
    "PRAImpact": "ExecutionImpact",
    "PRA_ACTION_CATALOG": "REMOTE_EXECUTION_CATALOG",

    # File/module names
    "tools/pra/": "tools/remote_exec/",

    # Comments and strings (case-insensitive matches)
    "Plan de Reprise d'Activité": "Remote Execution",
    "PRA actions": "remote executions",
    "PRA action": "remote execution",
    "pra-runner": "exec-runner",
    "pra-exec": "exec-runner",
}

# Files to process
SRC_DIR = Path(__file__).parent.parent / "src"
PATTERNS = ["**/*.py", "**/*.md", "**/README*"]


def process_file(file_path: Path) -> Tuple[int, List[str]]:
    """Process a single file and return number of changes."""
    try:
        content = file_path.read_text(encoding="utf-8")
        original = content
        changes = []

        # Apply replacements
        for old, new in REPLACEMENTS.items():
            if old in content:
                count = content.count(old)
                content = content.replace(old, new)
                changes.append(f"  {old} → {new} ({count}x)")

        # Case-insensitive for comments
        content = re.sub(
            r'\bPRA\b(?!_)',
            'Remote Execution',
            content,
            flags=re.IGNORECASE
        )

        if content != original:
            file_path.write_text(content, encoding="utf-8")
            return len(changes), changes

        return 0, []

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0, []


def main():
    """Run the migration."""
    print("🔄 Migrating PRA → Remote Execution\n")

    total_files = 0
    total_changes = 0

    for pattern in PATTERNS:
        for file_path in SRC_DIR.glob(pattern):
            if file_path.is_file():
                num_changes, changes = process_file(file_path)
                if num_changes > 0:
                    total_files += 1
                    total_changes += num_changes
                    print(f"✅ {file_path.relative_to(SRC_DIR)}")
                    for change in changes:
                        print(change)
                    print()

    print(f"\n✨ Migration complete!")
    print(f"   Files modified: {total_files}")
    print(f"   Total replacements: {total_changes}")

    # Rename directories
    pra_dir = SRC_DIR / "mcp_linux_infra" / "tools" / "pra"
    if pra_dir.exists():
        exec_dir = SRC_DIR / "mcp_linux_infra" / "tools" / "remote_exec"
        pra_dir.rename(exec_dir)
        print(f"\n📁 Renamed: tools/pra/ → tools/remote_exec/")


if __name__ == "__main__":
    main()
