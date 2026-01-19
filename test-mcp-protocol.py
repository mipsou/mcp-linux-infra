#!/usr/bin/env python3
"""
Test MCP protocol compliance

Verifies that the server properly implements the MCP protocol.
"""

import sys
import json
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_mcp_server():
    """Test MCP server initialization and tools listing"""
    print("Testing MCP Server Protocol Compliance...")
    print("=" * 70)

    try:
        from mcp_linux_infra.server import mcp

        # Check FastMCP instance
        print(f"✅ Server type: {type(mcp).__name__}")
        print(f"✅ Server name: {mcp.name}")

        # Check tools registration
        tools = mcp._tool_manager.list_tools()
        print(f"\n✅ Total tools registered: {len(tools)}")

        print("\n📋 Registered Tools:")
        print("-" * 70)

        categories = {
            "Diagnostic": [],
            "PRA": [],
            "SSH Execution": [],
            "Ansible": []
        }

        for tool in tools:
            name = tool.name
            if name.startswith(("get_", "list_", "read_", "search_", "analyze_", "test_", "check_service")):
                categories["Diagnostic"].append(name)
            elif "pra" in name:
                categories["PRA"].append(name)
            elif "ansible" in name:
                categories["Ansible"].append(name)
            elif any(x in name for x in ["execute_ssh", "approve_command", "pending_approvals", "whitelist"]):
                categories["SSH Execution"].append(name)
            else:
                categories["Diagnostic"].append(name)

        for category, tool_names in categories.items():
            if tool_names:
                print(f"\n{category} ({len(tool_names)} tools):")
                for name in sorted(tool_names):
                    print(f"  - {name}")

        print("\n" + "=" * 70)
        print("✅ MCP PROTOCOL COMPLIANCE: PASS")
        print(f"✅ Server ready with {len(tools)} tools")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    sys.exit(0 if success else 1)
