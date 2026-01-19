#!/usr/bin/env python3
"""Test import du serveur MCP."""

import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

try:
    from mcp_linux_infra.server import app
    print("✅ Import réussi")
    print(f"✅ Server name: {app.name}")
except Exception as e:
    print(f"❌ Erreur import: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
