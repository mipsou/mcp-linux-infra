#!/bin/bash
#
# MCP Linux Infra v0.3.0 - SSH Agent Validation
# Test la configuration SSH Agent pour MCP
#

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0

echo "======================================================================"
echo "🔐 MCP Linux Infra - SSH Agent Validation"
echo "======================================================================"
echo ""

pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
}

info() {
    echo -e "${BLUE}ℹ${NC}  $1"
}

# Test 1: Détecter l'OS
echo -e "${BLUE}[TEST 1] Détection environnement${NC}"
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    OS_TYPE="windows"
    pass "OS détecté: Windows"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="linux"
    pass "OS détecté: Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
    pass "OS détecté: macOS"
else
    OS_TYPE="unknown"
    warn "OS non reconnu: $OSTYPE"
fi
echo ""

# Test 2: SSH Agent actif
echo -e "${BLUE}[TEST 2] SSH Agent${NC}"
if [ -n "$SSH_AUTH_SOCK" ] && [ -S "$SSH_AUTH_SOCK" ]; then
    pass "SSH Agent actif: $SSH_AUTH_SOCK"
else
    fail "SSH Agent non détecté"
    info "Solution Linux/macOS: eval \$(ssh-agent -s)"
    info "Solution Windows: Start-Service ssh-agent"
fi
echo ""

# Test 3: Clés chargées dans l'agent
echo -e "${BLUE}[TEST 3] Clés SSH chargées${NC}"
if command -v ssh-add &> /dev/null; then
    KEY_COUNT=$(ssh-add -l 2>/dev/null | grep -c "SHA256" || echo "0")
    if [ "$KEY_COUNT" -gt 0 ]; then
        pass "$KEY_COUNT clé(s) chargée(s) dans l'agent"
        info "Clés disponibles:"
        ssh-add -l 2>/dev/null | while read line; do
            echo "    • $line"
        done
    else
        fail "Aucune clé dans l'agent"
        info "Ajouter clés: ssh-add ~/.ssh/mcp-reader"
    fi
else
    fail "ssh-add non disponible"
fi
echo ""

# Test 4: Fichiers de clés (optionnel)
echo -e "${BLUE}[TEST 4] Fichiers de clés SSH${NC}"
KEY_FILES=(
    "$HOME/.ssh/mcp-reader"
    "$HOME/.ssh/pra-runner"
)

for key_file in "${KEY_FILES[@]}"; do
    if [ -f "$key_file" ]; then
        # Vérifier permissions
        if [[ "$OS_TYPE" != "windows" ]]; then
            PERMS=$(stat -c %a "$key_file" 2>/dev/null || stat -f %Lp "$key_file" 2>/dev/null)
            if [ "$PERMS" = "600" ] || [ "$PERMS" = "400" ]; then
                pass "Clé trouvée avec bonnes permissions: $key_file ($PERMS)"
            else
                warn "Clé trouvée mais permissions incorrectes: $key_file ($PERMS)"
                info "Corriger: chmod 600 $key_file"
            fi
        else
            pass "Clé trouvée: $key_file"
        fi
    else
        warn "Clé non trouvée: $key_file"
        info "Générer: ssh-keygen -t ed25519 -f $key_file"
    fi
done
echo ""

# Test 5: Clés publiques
echo -e "${BLUE}[TEST 5] Clés publiques${NC}"
PUB_FILES=(
    "$HOME/.ssh/mcp-reader.pub"
    "$HOME/.ssh/pra-runner.pub"
)

for pub_file in "${PUB_FILES[@]}"; do
    if [ -f "$pub_file" ]; then
        pass "Clé publique trouvée: $pub_file"
        KEY_TYPE=$(awk '{print $1}' "$pub_file")
        KEY_COMMENT=$(awk '{print $3}' "$pub_file")
        info "  Type: $KEY_TYPE, Comment: $KEY_COMMENT"
    else
        warn "Clé publique manquante: $pub_file"
    fi
done
echo ""

# Test 6: Configuration MCP
echo -e "${BLUE}[TEST 6] Configuration MCP${NC}"
if [ -n "$LINUX_MCP_SSH_KEY_PATH" ]; then
    warn "LINUX_MCP_SSH_KEY_PATH défini: $LINUX_MCP_SSH_KEY_PATH"
    info "En mode agent, cette variable n'est pas nécessaire"
    info "MCP utilisera le fallback si l'agent n'est pas disponible"
else
    pass "LINUX_MCP_SSH_KEY_PATH non défini (bon pour mode agent)"
fi

if [ -n "$LINUX_MCP_DISABLE_SSH_AGENT" ]; then
    warn "LINUX_MCP_DISABLE_SSH_AGENT=$LINUX_MCP_DISABLE_SSH_AGENT"
    info "L'agent SSH est désactivé, MCP utilisera les clés directes"
else
    pass "Agent SSH non désactivé"
fi

if [ -n "$LINUX_MCP_FORCE_AUTH_MODE" ]; then
    info "Mode forcé: $LINUX_MCP_FORCE_AUTH_MODE"
fi
echo ""

# Test 7: Test MCP Python
echo -e "${BLUE}[TEST 7] Détection MCP${NC}"
if [ -d "src/mcp_linux_infra" ]; then
    AUTH_MODE=$(python -c "
import sys
sys.path.insert(0, 'src')
try:
    from mcp_linux_infra.connection.smart_ssh import SmartSSHManager
    manager = SmartSSHManager()
    print(manager._auth_mode.value)
except Exception as e:
    print(f'error:{e}')
" 2>/dev/null)

    if [[ "$AUTH_MODE" == "agent" ]]; then
        pass "MCP détecte le mode agent ✅"
        info "Configuration optimale"
    elif [[ "$AUTH_MODE" == "direct" ]]; then
        warn "MCP utilise le mode fallback (clés directes)"
        info "L'agent SSH n'a pas été détecté ou est désactivé"
    elif [[ "$AUTH_MODE" == "none" ]]; then
        fail "MCP ne trouve aucune méthode d'authentification"
        info "Configurer l'agent SSH ou définir les clés"
    else
        fail "Erreur lors de la détection: $AUTH_MODE"
    fi
else
    info "Répertoire MCP non trouvé (exécuter depuis la racine du projet)"
fi
echo ""

# Test 8: Test connexion (optionnel)
echo -e "${BLUE}[TEST 8] Test connexion SSH (optionnel)${NC}"
if [ -n "$MCP_TEST_HOST" ]; then
    info "Test de connexion vers: $MCP_TEST_HOST"

    # Test mcp-reader
    if ssh -o BatchMode=yes -o ConnectTimeout=5 mcp-reader@$MCP_TEST_HOST 'echo "OK"' 2>/dev/null | grep -q "OK"; then
        pass "Connexion mcp-reader@$MCP_TEST_HOST réussie"
    else
        fail "Connexion mcp-reader@$MCP_TEST_HOST échouée"
        info "Vérifier que la clé publique est installée sur $MCP_TEST_HOST"
    fi

    # Test pra-runner
    if ssh -o BatchMode=yes -o ConnectTimeout=5 pra-runner@$MCP_TEST_HOST 'echo "OK"' 2>/dev/null | grep -q "OK"; then
        pass "Connexion pra-runner@$MCP_TEST_HOST réussie"
    else
        fail "Connexion pra-runner@$MCP_TEST_HOST échouée"
    fi
else
    info "Définir MCP_TEST_HOST pour tester les connexions SSH"
    info "Exemple: export MCP_TEST_HOST=server1.example.com"
fi
echo ""

# Résumé
echo "======================================================================"
echo -e "${BLUE}📊 RÉSUMÉ${NC}"
echo "======================================================================"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ] && [ $PASSED -ge 5 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                           ║${NC}"
    echo -e "${GREEN}║  ✅ CONFIGURATION SSH AGENT OPTIMALE                     ║${NC}"
    echo -e "${GREEN}║                                                           ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "MCP utilisera l'agent SSH pour une sécurité maximale."
    echo ""
    echo "Prochaines étapes:"
    echo "  1. Distribuer les clés publiques sur les serveurs:"
    echo "     ssh-copy-id -i ~/.ssh/mcp-reader.pub mcp-reader@server1"
    echo "     ssh-copy-id -i ~/.ssh/pra-runner.pub pra-runner@server1"
    echo ""
    echo "  2. Tester avec MCP_TEST_HOST:"
    echo "     export MCP_TEST_HOST=server1"
    echo "     bash test-ssh-agent.sh"
    echo ""
    echo "  3. Lancer MCP:"
    echo "     mcp-linux-infra"
    exit 0
elif [ $FAILED -eq 0 ]; then
    echo -e "${YELLOW}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║                                                           ║${NC}"
    echo -e "${YELLOW}║  ⚠️  CONFIGURATION PARTIELLE - MODE FALLBACK             ║${NC}"
    echo -e "${YELLOW}║                                                           ║${NC}"
    echo -e "${YELLOW}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "MCP utilisera les clés directes (moins sécurisé)."
    echo ""
    echo "Pour utiliser l'agent SSH (recommandé):"
    echo "  1. Démarrer l'agent:"
    echo "     eval \$(ssh-agent -s)      # Linux/macOS"
    echo "     Start-Service ssh-agent   # Windows PowerShell"
    echo ""
    echo "  2. Charger les clés:"
    echo "     ssh-add ~/.ssh/mcp-reader"
    echo "     ssh-add ~/.ssh/pra-runner"
    echo ""
    echo "  3. Relancer ce script pour vérifier"
    exit 0
else
    echo -e "${RED}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                           ║${NC}"
    echo -e "${RED}║  ❌ CONFIGURATION INCOMPLÈTE                              ║${NC}"
    echo -e "${RED}║                                                           ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Consulter la documentation complète:"
    echo "  cat SSH-AGENT-SETUP.md"
    echo ""
    echo "Configuration rapide:"
    echo "  1. Générer les clés:"
    echo "     ssh-keygen -t ed25519 -f ~/.ssh/mcp-reader -C 'mcp-reader'"
    echo "     ssh-keygen -t ed25519 -f ~/.ssh/pra-runner -C 'pra-runner'"
    echo ""
    echo "  2. Démarrer l'agent:"
    echo "     eval \$(ssh-agent -s)"
    echo ""
    echo "  3. Charger les clés:"
    echo "     ssh-add ~/.ssh/mcp-reader"
    echo "     ssh-add ~/.ssh/pra-runner"
    echo ""
    echo "  4. Relancer ce script"
    exit 1
fi
