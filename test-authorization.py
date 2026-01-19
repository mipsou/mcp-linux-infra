#!/usr/bin/env python3
"""
Test the authorization system

Quick test to verify imports and basic functionality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all modules import correctly"""
    print("Testing imports...")

    try:
        from mcp_linux_infra.authorization import (
            AuthLevel,
            CommandRule,
            CommandAuthorization,
            COMMAND_WHITELIST,
            AuthorizationEngine,
        )
        print("✅ Authorization models imported")

        from mcp_linux_infra.tools.execution import (
            ssh_executor,
            ansible_wrapper,
        )
        print("✅ Execution tools imported")

        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_whitelist():
    """Test whitelist loading"""
    print("\nTesting whitelist...")

    try:
        from mcp_linux_infra.authorization import COMMAND_WHITELIST, AuthLevel

        auto_count = sum(1 for r in COMMAND_WHITELIST if r.auth_level == AuthLevel.AUTO)
        manual_count = sum(1 for r in COMMAND_WHITELIST if r.auth_level == AuthLevel.MANUAL)
        blocked_count = sum(1 for r in COMMAND_WHITELIST if r.auth_level == AuthLevel.BLOCKED)

        print(f"✅ Whitelist loaded: {len(COMMAND_WHITELIST)} rules")
        print(f"   - AUTO: {auto_count}")
        print(f"   - MANUAL: {manual_count}")
        print(f"   - BLOCKED: {blocked_count}")

        return True
    except Exception as e:
        print(f"❌ Whitelist test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_authorization_engine():
    """Test authorization engine"""
    print("\nTesting authorization engine...")

    try:
        from mcp_linux_infra.authorization import (
            AuthorizationEngine,
            COMMAND_WHITELIST,
            AuthLevel,
        )

        engine = AuthorizationEngine(COMMAND_WHITELIST)

        # Test AUTO command
        auth = engine.check_command("coreos-11", "systemctl status unbound")
        assert auth.allowed == True
        assert auth.auth_level == AuthLevel.AUTO
        print("✅ AUTO command check passed")

        # Test MANUAL command
        auth = engine.check_command("coreos-11", "systemctl restart unbound")
        assert auth.allowed == False
        assert auth.auth_level == AuthLevel.MANUAL
        assert auth.needs_approval == True
        assert auth.approval_id is not None
        print("✅ MANUAL command check passed")

        # Test BLOCKED command
        auth = engine.check_command("coreos-11", "rm -rf /var")
        assert auth.allowed == False
        assert auth.auth_level == AuthLevel.BLOCKED
        print("✅ BLOCKED command check passed")

        # Test unknown command (should be blocked)
        auth = engine.check_command("coreos-11", "some-unknown-command")
        assert auth.allowed == False
        assert auth.auth_level == AuthLevel.BLOCKED
        print("✅ Unknown command blocked (default deny)")

        return True
    except Exception as e:
        print(f"❌ Authorization engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_approval_workflow():
    """Test approval workflow"""
    print("\nTesting approval workflow...")

    try:
        from mcp_linux_infra.authorization import (
            AuthorizationEngine,
            COMMAND_WHITELIST,
        )

        engine = AuthorizationEngine(COMMAND_WHITELIST)

        # Create approval request
        auth = engine.check_command("coreos-11", "systemctl restart unbound")
        approval_id = auth.approval_id

        # Check pending
        pending = engine.get_all_pending()
        assert len(pending) == 1
        print("✅ Approval request created")

        # Approve
        approved = engine.approve_command(approval_id)
        assert approved is not None
        assert approved.approved == True
        print("✅ Command approved")

        # Mark executed
        result = engine.mark_executed(approval_id)
        assert result == True
        print("✅ Command marked as executed")

        # Check pending again
        pending = engine.get_all_pending()
        assert len(pending) == 0
        print("✅ No pending approvals after execution")

        return True
    except Exception as e:
        print(f"❌ Approval workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("AUTHORIZATION SYSTEM TEST")
    print("=" * 70)

    tests = [
        ("Imports", test_imports),
        ("Whitelist", test_whitelist),
        ("Authorization Engine", test_authorization_engine),
        ("Approval Workflow", test_approval_workflow),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n{'=' * 70}")
        print(f"Test: {name}")
        print('=' * 70)
        result = test_func()
        results.append((name, result))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    all_passed = all(r for _, r in results)

    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
