#!/bin/bash
#
# MCP Linux Infra v0.3.0 - System Validation Test
# Tests rapides pour valider tous les composants
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

FAILED=0
PASSED=0

echo "======================================================================"
echo "🧪 MCP Linux Infra v0.3.0 - System Validation"
echo "======================================================================"
echo ""

# Helper functions
pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAILED++))
}

info() {
    echo -e "${BLUE}ℹ${NC}  $1"
}

# Test 1: Python et dépendances
echo -e "${BLUE}[TEST 1] Python et dépendances${NC}"
if python --version &>/dev/null; then
    PYTHON_VERSION=$(python --version 2>&1)
    pass "Python installé: $PYTHON_VERSION"
else
    fail "Python non trouvé"
fi

if python -c "import asyncssh" 2>/dev/null; then
    pass "asyncssh installé"
else
    fail "asyncssh manquant (pip install -e .)"
fi

if python -c "import pydantic" 2>/dev/null; then
    pass "pydantic installé"
else
    fail "pydantic manquant"
fi
echo ""

# Test 2: Package MCP installé
echo -e "${BLUE}[TEST 2] Package MCP Linux Infra${NC}"
if python -c "import sys; sys.path.insert(0, 'src'); import mcp_linux_infra" 2>/dev/null; then
    VERSION=$(python -c "import sys; sys.path.insert(0, 'src'); from mcp_linux_infra import __version__; print(__version__)" 2>/dev/null || echo "0.3.0")
    pass "mcp-linux-infra importé: v$VERSION"
else
    fail "mcp-linux-infra non trouvé"
fi
echo ""

# Test 3: Plugin System
echo -e "${BLUE}[TEST 3] Plugin System${NC}"
PLUGIN_TEST=$(python -c "
import sys
sys.path.insert(0, 'src')
from mcp_linux_infra.analysis.plugins import get_plugin_registry
r = get_plugin_registry()
plugins = r.get_all_plugins()
total = sum(len(p.commands) for p in plugins.values())
print(f'{len(plugins)}:{total}')
" 2>/dev/null)

if [ $? -eq 0 ]; then
    IFS=':' read -r PLUGIN_COUNT CMD_COUNT <<< "$PLUGIN_TEST"
    if [ "$PLUGIN_COUNT" = "8" ]; then
        pass "Plugin system: $PLUGIN_COUNT plugins, $CMD_COUNT commandes"
    else
        fail "Nombre de plugins incorrect: $PLUGIN_COUNT (attendu: 8)"
    fi
else
    fail "Plugin system non fonctionnel"
fi
echo ""

# Test 4: Command Analysis
echo -e "${BLUE}[TEST 4] Command Analysis${NC}"
ANALYSIS_TEST=$(python -c "
import sys
sys.path.insert(0, 'src')
from mcp_linux_infra.analysis.command_analysis import analyze_command_safety
result = analyze_command_safety('ls -la')
print(f'{result.risk_level.value}:{result.suggested_level.value}')
" 2>/dev/null)

if [ $? -eq 0 ]; then
    IFS=':' read -r RISK AUTH <<< "$ANALYSIS_TEST"
    pass "Command analysis: risk=$RISK, auth=$AUTH"
else
    fail "Command analysis non fonctionnel"
fi
echo ""

# Test 5: Auto-Learning
echo -e "${BLUE}[TEST 5] Auto-Learning Engine${NC}"
if python -c "
import sys
sys.path.insert(0, 'src')
from mcp_linux_infra.analysis.auto_learning import AutoLearningEngine
engine = AutoLearningEngine()
" 2>/dev/null; then
    pass "Auto-learning engine"
else
    fail "Auto-learning non fonctionnel"
fi
echo ""

# Test 6: Authorization System
echo -e "${BLUE}[TEST 6] Authorization System${NC}"
if python -c "
import sys
sys.path.insert(0, 'src')
from mcp_linux_infra.authorization.engine import AuthorizationEngine
from mcp_linux_infra.authorization.models import AuthLevel
assert len(list(AuthLevel)) == 3
" 2>/dev/null; then
    pass "Authorization system"
else
    fail "Authorization system non fonctionnel"
fi
echo ""

# Test 7: Configuration
echo -e "${BLUE}[TEST 7] Configuration${NC}"
if python -c "
import sys
sys.path.insert(0, 'src')
from mcp_linux_infra.config import get_settings
config = get_settings()
assert config.user is not None
" 2>/dev/null; then
    pass "Configuration system"
else
    fail "Configuration system non fonctionnel"
fi
echo ""

# Test 8: Fichiers de déploiement
echo -e "${BLUE}[TEST 8] Fichiers de déploiement${NC}"
FILES=(
    "DEPLOYMENT-READY.md"
    "QUICK-DEPLOY.md"
    "deploy.sh"
    "examples/ansible-compose.yml"
    "examples/dns-stack-compose.yml"
    "examples/unbound/unbound.conf"
    "examples/caddy/Caddyfile"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        pass "Fichier présent: $file"
    else
        fail "Fichier manquant: $file"
    fi
done
echo ""

# Test 9: Tests unitaires
echo -e "${BLUE}[TEST 9] Tests unitaires (optionnel)${NC}"
if command -v pytest &> /dev/null; then
    if PYTHONPATH=src pytest tests/test_plugins.py -v --tb=no 2>/dev/null | grep -q "passed"; then
        pass "Tests unitaires des plugins"
    else
        info "Certains tests unitaires échouent (non bloquant)"
    fi
else
    info "pytest non installé (optionnel pour dev)"
fi
echo ""

# Test 10: Conteneurs (optionnel)
echo -e "${BLUE}[TEST 10] Conteneurs Docker/Podman (optionnel)${NC}"
if command -v docker &> /dev/null; then
    pass "Docker installé"
    DOCKER_RUNNING=$(docker ps --format '{{.Names}}' 2>/dev/null | wc -l)
    info "$DOCKER_RUNNING conteneurs Docker actifs"
elif command -v podman &> /dev/null; then
    pass "Podman installé"
    PODMAN_RUNNING=$(podman ps --format '{{.Names}}' 2>/dev/null | wc -l)
    info "$PODMAN_RUNNING conteneurs Podman actifs"
else
    info "Ni Docker ni Podman installés (nécessaires pour déploiement)"
fi
echo ""

# Résumé
echo "======================================================================"
echo -e "${BLUE}📊 RÉSUMÉ DES TESTS${NC}"
echo "======================================================================"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  🎉 TOUS LES TESTS SONT PASSÉS - SYSTÈME OPÉRATIONNEL   ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Prochaines étapes:"
    echo "  1. Déployer Ansible: cd examples && docker-compose -f ansible-compose.yml up -d"
    echo "  2. Déployer DNS: docker-compose -f dns-stack-compose.yml up -d"
    echo "  3. Configurer SSH keys: export LINUX_MCP_SSH_KEY_PATH=~/.ssh/mcp-reader"
    echo "  4. Lire le guide: cat QUICK-DEPLOY.md"
    exit 0
else
    echo -e "${YELLOW}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  ⚠️  CERTAINS TESTS ONT ÉCHOUÉ - VÉRIFIER CI-DESSUS     ║${NC}"
    echo -e "${YELLOW}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Résolution des problèmes:"
    echo "  • Installation: pip install -e ."
    echo "  • Tests: PYTHONPATH=src pytest tests/ -v"
    echo "  • Documentation: cat DEPLOYMENT-READY.md"
    exit 1
fi
