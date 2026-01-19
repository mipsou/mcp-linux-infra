#!/usr/bin/env python3
"""Fix Annotated and Tool imports in all tool files."""

import re
from pathlib import Path

base = Path("D:/infra/mcp-servers/mcp-linux-infra/src/mcp_linux_infra/tools")

for pyfile in base.rglob("*.py"):
    if pyfile.name == "__init__.py":
        continue

    content = pyfile.read_text(encoding="utf-8")
    original = content

    # Nettoyage ligne par ligne
    lines = content.split("\n")
    cleaned = []

    for line in lines:
        # Supprimer imports
        if "from typing import Annotated" in line:
            continue
        if "from mcp.types import Tool" in line:
            continue

        # Remplacer Annotated - patterns multiples
        line = re.sub(r'Annotated\[str \| None, Tool\([^)]+\)\]', r'str | None', line)
        line = re.sub(r'Annotated\[str, Tool\([^)]+\)\]', r'str', line)
        line = re.sub(r'Annotated\[int, Tool\([^)]+\)\]', r'int', line)
        line = re.sub(r'Annotated\[float, Tool\([^)]+\)\]', r'float', line)
        line = re.sub(r'Annotated\[bool, Tool\([^)]+\)\]', r'bool', line)

        cleaned.append(line)

    content = "\n".join(cleaned)

    if content != original:
        pyfile.write_text(content, encoding="utf-8")
        print(f"✅ {pyfile.name}")

print("✅ Terminé")
