#!/bin/bash
# Test d'intégrité du serveur linux-infra MCP
# Usage: ./test-integrity.sh

set -e

echo "🔍 Test d'Intégrité - linux-infra MCP"
echo "======================================"
echo

cd "$(dirname "$0")"

# Test 1: Syntaxe Python
echo "📝 Test 1: Vérification syntaxe Python..."
find src -name "*.py" -type f | while read file; do
    python -m py_compile "$file" && echo "  ✅ $file" || echo "  ❌ $file"
done
echo

# Test 2: Import du serveur
echo "📦 Test 2: Import du serveur MCP..."
.venv/Scripts/python.exe -c "
import sys
sys.path.insert(0, 'src')
from mcp_linux_infra.server import mcp
print('  ✅ Import serveur: OK')
" || echo "  ❌ Import serveur: ERREUR"
echo

# Test 3: Dépendances
echo "🔧 Test 3: Dépendances..."
~/.local/bin/uv.exe pip list | grep -E "(mcp|asyncssh|pydantic)" | while read line; do
    echo "  ✅ $line"
done
echo

# Test 4: Fichiers de configuration
echo "⚙️  Test 4: Fichiers de configuration..."
[ -f ".env" ] && echo "  ✅ .env: présent" || echo "  ⚠️  .env: absent"
[ -f "pyproject.toml" ] && echo "  ✅ pyproject.toml: présent" || echo "  ❌ pyproject.toml: absent"
[ -f "README.md" ] && echo "  ✅ README.md: présent" || echo "  ⚠️  README.md: absent"
echo

# Test 5: Exécutable
echo "🚀 Test 5: Binaire MCP..."
[ -f ".venv/Scripts/mcp-linux-infra.exe" ] && echo "  ✅ mcp-linux-infra.exe: présent" || echo "  ❌ mcp-linux-infra.exe: absent"
echo

# Test 6: Compte des tools
echo "🛠️  Test 6: Inventaire des tools..."
TOOL_COUNT=$(grep -E "^@mcp\.tool\(\)" src/mcp_linux_infra/server.py | wc -l)
echo "  ✅ Nombre de tools déclarés: $TOOL_COUNT"
echo

# Résumé
echo "======================================"
echo "✅ Test d'intégrité terminé!"
echo
echo "Prochaines étapes:"
echo "1. Redémarrer Claude Desktop"
echo "2. Tester avec: show_command_whitelist"
echo "3. Consulter: TEST-LINUX-INFRA.md"
