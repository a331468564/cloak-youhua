import importlib.util
import os
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CHECKS = [
    {
        "name": "Python",
        "type": "runtime",
        "check": lambda: sys.version.split()[0],
        "required": True,
        "purpose": "Run local CSV, queue, extraction, and reporting scripts.",
    },
    {
        "name": "Scrapling",
        "type": "python_package",
        "module": "scrapling",
        "required": False,
        "purpose": "Extract candidate contact/KP evidence from websites.",
    },
    {
        "name": "curl_cffi",
        "type": "python_package",
        "module": "curl_cffi",
        "required": False,
        "purpose": "Runtime dependency for Scrapling static fetching.",
    },
    {
        "name": "Playwright",
        "type": "python_package",
        "module": "playwright",
        "required": False,
        "purpose": "Browser runtime dependency for dynamic extraction.",
    },
    {
        "name": "Patchright",
        "type": "python_package",
        "module": "patchright",
        "required": False,
        "purpose": "Stealth browser runtime dependency for Scrapling.",
    },
    {
        "name": "browserforge",
        "type": "python_package",
        "module": "browserforge",
        "required": False,
        "purpose": "Browser header/fingerprint generation used by Scrapling.",
    },
    {
        "name": "msgspec",
        "type": "python_package",
        "module": "msgspec",
        "required": False,
        "purpose": "Runtime dependency for Scrapling browser fetchers.",
    },
    {
        "name": "certifi",
        "type": "python_package",
        "module": "certifi",
        "required": False,
        "purpose": "Provide a CA bundle for Tavily API HTTPS requests.",
    },
    {
        "name": "PowerShell",
        "type": "command",
        "command": "powershell",
        "required": True,
        "purpose": "Run local operating commands and dashboard launcher.",
    },
    {
        "name": "Node.js",
        "type": "command",
        "command": "node",
        "required": False,
        "purpose": "Run project-local MCP desktop notification tooling.",
    },
    {
        "name": "npm",
        "type": "command",
        "command": "npm.cmd" if os.name == "nt" else "npm",
        "required": False,
        "purpose": "Install or restore project-local MCP desktop notification tooling.",
    },
]


def package_status(module_name):
    return importlib.util.find_spec(module_name) is not None


def command_status(command_name):
    return shutil.which(command_name) is not None


def main():
    print("# Capability Inventory Check")
    print()
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Python executable: {sys.executable}")
    print()

    missing = []
    for item in CHECKS:
        if item["type"] == "python_package":
            ok = package_status(item["module"])
            detail = item["module"]
        elif item["type"] == "command":
            ok = command_status(item["command"])
            detail = shutil.which(item["command"]) or item["command"]
        else:
            ok = True
            detail = item["check"]()

        status = "OK" if ok else "MISSING"
        print(f"- {status}: {item['name']} ({detail})")
        print(f"  Purpose: {item['purpose']}")
        if not ok:
            missing.append(item["name"])

    browser_path = PROJECT_ROOT / ".ms-playwright"
    print()
    if browser_path.exists():
        print(f"- OK: Project-local Playwright browsers ({browser_path})")
    else:
        print(f"- MISSING: Project-local Playwright browsers ({browser_path})")
        missing.append("Project-local Playwright browsers")

    print()
    if os.environ.get("TAVILY_API_KEY"):
        print("- OK: Tavily API key environment variable (TAVILY_API_KEY)")
    else:
        print("- OPTIONAL: Tavily API key environment variable is not set (TAVILY_API_KEY)")
    print("  Purpose: Run small approved Tavily search-task batches without storing the key in project files.")

    notification_pkg = PROJECT_ROOT / ".codex" / "tools" / "mcp-notifications" / "node_modules" / "@topvisor" / "mcp-notifications" / "package.json"
    print()
    if notification_pkg.exists():
        print(f"- OK: Project-local MCP notifications package ({notification_pkg})")
    else:
        print(f"- OPTIONAL: Project-local MCP notifications package is not installed ({notification_pkg})")
        print(r"  Restore with: npm.cmd install --prefix .codex\tools\mcp-notifications @topvisor/mcp-notifications")

    print()
    if missing:
        print("Missing capabilities:")
        for name in missing:
            print(f"- {name}")
        print()
        print("Suggested setup:")
        print(r"python -m venv .venv")
        print(r".\.venv\Scripts\python -m pip install -r requirements.txt")
        print(r"$env:PLAYWRIGHT_BROWSERS_PATH='E:\AI\TestProject-v2\.ms-playwright'; .\.venv\Scripts\python -m playwright install chromium")
        return 1

    print("All checked capabilities are available.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
