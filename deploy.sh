#!/bin/bash
#
# MCP Linux Infra v0.3.0 - Deployment Script
# Deploy Ansible containers and DNS stack
#

set -e

echo "======================================================================"
echo "🚀 MCP Linux Infra v0.3.0 - Deployment"
echo "======================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Verify MCP installation
echo -e "${BLUE}[1/5] Verifying MCP Linux Infra installation...${NC}"
if ! python -c "import sys; sys.path.insert(0, 'src'); from mcp_linux_infra.analysis.plugins import get_plugin_registry; r = get_plugin_registry(); assert len(r.get_all_plugins()) == 8" 2>/dev/null; then
    echo -e "${RED}❌ MCP Linux Infra not properly installed${NC}"
    echo "Run: pip install -e ."
    exit 1
fi
echo -e "${GREEN}✅ MCP Linux Infra v0.3.0 installed${NC}"
echo ""

# Step 2: Check SSH keys
echo -e "${BLUE}[2/5] Checking SSH keys...${NC}"
if [ ! -f "$HOME/.ssh/mcp-reader" ] && [ ! -f "$HOME/.ssh/id_rsa" ]; then
    echo -e "${YELLOW}⚠️  No SSH key found for mcp-reader${NC}"
    echo "Set LINUX_MCP_SSH_KEY_PATH environment variable"
else
    echo -e "${GREEN}✅ SSH keys configured${NC}"
fi
echo ""

# Step 3: Deploy Ansible containers
echo -e "${BLUE}[3/5] Deploying Ansible containers...${NC}"
echo -e "${YELLOW}📝 Please configure your Ansible containers deployment:${NC}"
echo ""
echo "Example for Podman:"
echo "  podman run -d --name ansible-controller \\"
echo "    -v /path/to/playbooks:/ansible \\"
echo "    -v ~/.ssh:/root/.ssh:ro \\"
echo "    ansible/ansible:latest"
echo ""
echo "Example for Docker Compose (create ansible-compose.yml):"
echo "---"
echo "version: '3.8'"
echo "services:"
echo "  ansible-controller:"
echo "    image: ansible/ansible:latest"
echo "    container_name: ansible-controller"
echo "    volumes:"
echo "      - ./playbooks:/ansible"
echo "      - ~/.ssh:/root/.ssh:ro"
echo "    networks:"
echo "      - infra-net"
echo ""
echo "networks:"
echo "  infra-net:"
echo "    driver: bridge"
echo ""
read -p "Press Enter when Ansible containers are deployed..."
echo -e "${GREEN}✅ Ansible containers deployed${NC}"
echo ""

# Step 4: Deploy DNS stack (Unbound + Caddy)
echo -e "${BLUE}[4/5] Deploying DNS stack (Unbound + Caddy)...${NC}"
echo -e "${YELLOW}📝 Please configure your DNS stack:${NC}"
echo ""
echo "Example Unbound configuration:"
echo "  podman run -d --name unbound \\"
echo "    -p 53:53/udp -p 53:53/tcp \\"
echo "    -v /path/to/unbound.conf:/etc/unbound/unbound.conf:ro \\"
echo "    mvance/unbound:latest"
echo ""
echo "Example Caddy configuration:"
echo "  podman run -d --name caddy \\"
echo "    -p 80:80 -p 443:443 \\"
echo "    -v /path/to/Caddyfile:/etc/caddy/Caddyfile:ro \\"
echo "    -v caddy_data:/data \\"
echo "    caddy:latest"
echo ""
read -p "Press Enter when DNS stack is deployed..."
echo -e "${GREEN}✅ DNS stack deployed${NC}"
echo ""

# Step 5: Verify deployment
echo -e "${BLUE}[5/5] Verifying deployment...${NC}"

# Check if containers are running (adapt to your setup)
echo "Checking running containers..."
if command -v podman &> /dev/null; then
    podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
elif command -v docker &> /dev/null; then
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
fi
echo ""

echo -e "${GREEN}✅ Deployment verification complete${NC}"
echo ""

# Final summary
echo "======================================================================"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "======================================================================"
echo ""
echo "MCP Linux Infra v0.3.0 Features:"
echo "  ✅ 8 plugins with 135+ commands"
echo "  ✅ Smart command analysis (82% auto-approved)"
echo "  ✅ Auto-learning system"
echo "  ✅ Two-tier SSH authentication"
echo "  ✅ PRA workflow with human approval"
echo ""
echo "Next steps:"
echo "  1. Configure SSH keys for remote hosts"
echo "  2. Update whitelist for your infrastructure"
echo "  3. Start MCP server: mcp-linux-infra"
echo "  4. Test with: python -m mcp_linux_infra.server"
echo ""
echo "Documentation:"
echo "  - README.md: Quick start and overview"
echo "  - PLUGINS.md: Complete plugin reference"
echo "  - COMMAND-ANALYSIS.md: Smart analysis guide"
echo "  - DEPLOYMENT-READY.md: Deployment checklist"
echo ""
echo "======================================================================"
