#!/usr/bin/env pwsh
#
# Test d'installation MCP Linux Infra
#
# Usage: .\test-installation.ps1 [-Target "web01.infra"]
#

param(
    [string]$Target = $null,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

Write-Host "🔧 MCP Linux Infra - Installation Test" -ForegroundColor Cyan
Write-Host "======================================`n" -ForegroundColor Cyan

$TestsPassed = 0
$TestsFailed = 0

function Test-Step {
    param(
        [string]$Name,
        [scriptblock]$Test
    )

    Write-Host "▶ Testing: $Name" -NoNewline

    try {
        & $Test
        Write-Host " ✅" -ForegroundColor Green
        $script:TestsPassed++
        return $true
    }
    catch {
        Write-Host " ❌" -ForegroundColor Red
        Write-Host "  Error: $_" -ForegroundColor Red
        $script:TestsFailed++
        return $false
    }
}

# ============================================================================
# Test 1: Environnement Python
# ============================================================================

Write-Host "`n📦 Environment Tests" -ForegroundColor Yellow

Test-Step "uv is installed" {
    $uv = Get-Command uv -ErrorAction Stop
    if (-not $uv) { throw "uv not found in PATH" }
}

Test-Step "Project directory exists" {
    if (-not (Test-Path ".\pyproject.toml")) {
        throw "Not in project root (pyproject.toml not found)"
    }
}

Test-Step "Dependencies installed" {
    if (-not (Test-Path ".\.venv") -and -not (Test-Path ".\venv")) {
        Write-Host "`n  ⚠️  No venv found, running uv sync..." -ForegroundColor Yellow
        & uv sync
    }
}

# ============================================================================
# Test 2: SSH Keys
# ============================================================================

Write-Host "`n🔑 SSH Keys Tests" -ForegroundColor Yellow

Test-Step "Keys directory exists" {
    if (-not (Test-Path ".\keys")) {
        throw "keys/ directory not found"
    }
}

$HasReaderKey = Test-Step "mcp-reader.key exists" {
    if (-not (Test-Path ".\keys\mcp-reader.key")) {
        throw "mcp-reader.key not found in keys/"
    }
}

$HasExecKey = Test-Step "pra-exec.key exists" {
    if (-not (Test-Path ".\keys\pra-exec.key")) {
        throw "pra-exec.key not found in keys/"
    }
}

Test-Step "Public keys exist" {
    if (-not (Test-Path ".\keys\mcp-reader.key.pub")) {
        throw "mcp-reader.key.pub not found"
    }
    if (-not (Test-Path ".\keys\pra-exec.key.pub")) {
        throw "pra-exec.key.pub not found"
    }
}

# ============================================================================
# Test 3: SSH Agent
# ============================================================================

Write-Host "`n🔐 SSH Agent Tests" -ForegroundColor Yellow

$AgentRunning = Test-Step "SSH Agent service running" {
    $service = Get-Service ssh-agent -ErrorAction SilentlyContinue
    if (-not $service) {
        throw "ssh-agent service not found (OpenSSH not installed?)"
    }
    if ($service.Status -ne "Running") {
        throw "ssh-agent service not running. Start with: Start-Service ssh-agent"
    }
}

if ($AgentRunning) {
    $AgentKeysLoaded = Test-Step "SSH Agent has keys loaded" {
        $keys = & ssh-add -l 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "No keys in agent. Load with: ssh-add .\keys\mcp-reader.key"
        }

        # Vérifier clés spécifiques
        $hasReader = $keys | Select-String "mcp-reader"
        $hasExec = $keys | Select-String "pra-runner"

        if (-not $hasReader) {
            Write-Host "`n  ⚠️  mcp-reader key not in agent" -ForegroundColor Yellow
        }
        if (-not $hasExec) {
            Write-Host "`n  ⚠️  pra-exec key not in agent" -ForegroundColor Yellow
        }
    }
}

# ============================================================================
# Test 4: Configuration
# ============================================================================

Write-Host "`n⚙️  Configuration Tests" -ForegroundColor Yellow

Test-Step ".env file exists" {
    if (-not (Test-Path ".\.env")) {
        throw ".env not found. Copy from .env.example"
    }
}

Test-Step "Configuration valid" {
    $env = Get-Content .\.env -Raw
    if ($env -match "LINUX_MCP_SSH_KEY_PATH=.*mcp-reader\.key") {
        # OK: using direct keys
    }
    elseif ($env -match "LINUX_MCP_USE_SSH_AGENT=true") {
        # OK: using agent
    }
    else {
        throw "No valid auth method in .env"
    }
}

# ============================================================================
# Test 5: System Wrappers (si target spécifié)
# ============================================================================

if ($Target) {
    Write-Host "`n🎯 Target System Tests ($Target)" -ForegroundColor Yellow

    Test-Step "Wrapper scripts exist" {
        if (-not (Test-Path ".\system\wrappers\mcp-wrapper")) {
            throw "mcp-wrapper not found"
        }
        if (-not (Test-Path ".\system\wrappers\pra-exec")) {
            throw "pra-exec not found"
        }
        if (-not (Test-Path ".\system\pra-run")) {
            throw "pra-run not found"
        }
    }

    Test-Step "Can ping target" {
        $ping = Test-Connection -ComputerName $Target -Count 1 -Quiet
        if (-not $ping) {
            throw "Cannot ping $Target"
        }
    }

    Test-Step "SSH to target works (read-only)" {
        if ($HasReaderKey) {
            $result = & ssh -i .\keys\mcp-reader.key -o StrictHostKeyChecking=no -o ConnectTimeout=5 mcp-reader@$Target "echo test" 2>&1
            if ($LASTEXITCODE -ne 0) {
                throw "SSH failed: $result"
            }
        }
        else {
            Write-Host " ⏭️  Skipped (no key)" -ForegroundColor Yellow
        }
    }

    Test-Step "Wrapper works on target" {
        if ($HasReaderKey) {
            $result = & ssh -i .\keys\mcp-reader.key -o StrictHostKeyChecking=no mcp-reader@$Target "systemctl status sshd" 2>&1
            if ($LASTEXITCODE -ne 0) {
                throw "Wrapper test failed: $result"
            }
        }
        else {
            Write-Host " ⏭️  Skipped (no key)" -ForegroundColor Yellow
        }
    }
}

# ============================================================================
# Test 6: MCP Server
# ============================================================================

Write-Host "`n🚀 MCP Server Tests" -ForegroundColor Yellow

Test-Step "Server can import" {
    $result = & uv run python -c "from mcp_linux_infra import server; print('OK')" 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Import failed: $result"
    }
}

Test-Step "Auth mode detection works" {
    $code = @"
from mcp_linux_infra.connection.smart_ssh import get_smart_ssh_manager, SSHAuthMode
manager = get_smart_ssh_manager()
mode = manager.get_auth_mode()
print(f'Mode: {mode.value}')

if mode == SSHAuthMode.AGENT:
    print('✅ Using SSH Agent (maximum security)')
elif mode == SSHAuthMode.DIRECT:
    print('⚠️  Using direct keys (reduced security)')
else:
    print('❌ No auth method')
"@

    $result = & uv run python -c $code 2>&1
    Write-Host ""
    $result | ForEach-Object { Write-Host "  $_" }

    if ($LASTEXITCODE -ne 0) {
        throw "Auth mode detection failed"
    }
}

# ============================================================================
# Résumé
# ============================================================================

Write-Host "`n" + ("="*50) -ForegroundColor Cyan
Write-Host "📊 Test Summary" -ForegroundColor Cyan
Write-Host ("="*50) -ForegroundColor Cyan

Write-Host "`n  ✅ Passed: $TestsPassed" -ForegroundColor Green
if ($TestsFailed -gt 0) {
    Write-Host "  ❌ Failed: $TestsFailed" -ForegroundColor Red
}

if ($TestsFailed -eq 0) {
    Write-Host "`n🎉 All tests passed! MCP Linux Infra is ready." -ForegroundColor Green

    Write-Host "`n📝 Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Add to Claude Desktop config (claude_desktop_config.json)"
    Write-Host "  2. Restart Claude Desktop"
    Write-Host "  3. Test with: get_system_info(host=`"$Target`")" -ForegroundColor Gray

    if (-not $AgentKeysLoaded) {
        Write-Host "`n⚠️  Recommendation: Load keys in SSH Agent for maximum security" -ForegroundColor Yellow
        Write-Host "  ssh-add .\keys\mcp-reader.key" -ForegroundColor Gray
        Write-Host "  ssh-add .\keys\pra-exec.key" -ForegroundColor Gray
    }
}
else {
    Write-Host "`n❌ Some tests failed. Please fix errors above." -ForegroundColor Red
    exit 1
}

# ============================================================================
# Afficher la config Claude Desktop
# ============================================================================

if ($TestsFailed -eq 0) {
    Write-Host "`n📋 Claude Desktop Configuration:" -ForegroundColor Cyan
    Write-Host @"
{
  "mcpServers": {
    "linux-infra": {
      "command": "uv",
      "args": [
        "--directory",
        "$($PWD.Path)",
        "run",
        "mcp-linux-infra"
      ],
      "env": {
        "LINUX_MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
"@ -ForegroundColor Gray
}
