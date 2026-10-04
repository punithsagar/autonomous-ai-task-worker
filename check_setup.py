"""
Setup verification script - checks if everything is ready to run.
"""
import sys
import os
from pathlib import Path

def print_status(check_name, passed, message=""):
    """Print a colored status message."""
    symbol = "[OK]" if passed else "[X]"
    status = "PASS" if passed else "FAIL"
    print(f"{symbol} {check_name}: {status}")
    if message:
        print(f"   -> {message}")
    print()

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    required = (3, 9)
    passed = version >= required

    current = f"{version.major}.{version.minor}.{version.micro}"
    required_str = f"{required[0]}.{required[1]}+"

    print_status(
        "Python Version",
        passed,
        f"Found {current}, need {required_str}" if not passed else f"Python {current}"
    )
    return passed

def check_dependencies():
    """Check if required packages are installed."""
    required = [
        "anthropic",
        "playwright",
        "pydantic",
        "fastapi",
        "uvicorn",
        "httpx",
        "dotenv"
    ]

    missing = []
    for package in required:
        try:
            if package == "dotenv":
                __import__("dotenv")
            else:
                __import__(package)
        except ImportError:
            missing.append(package)

    passed = len(missing) == 0

    if missing:
        print_status(
            "Python Packages",
            False,
            f"Missing: {', '.join(missing)}\n   Run: pip install -r requirements.txt"
        )
    else:
        print_status("Python Packages", True, "All required packages installed")

    return passed

def check_playwright():
    """Check if Playwright browser is installed."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        print_status("Playwright Browser", True, "Chromium installed")
        return True
    except Exception as e:
        print_status(
            "Playwright Browser",
            False,
            f"Not installed or not working\n   Run: playwright install chromium"
        )
        return False

def check_api_key():
    """Check if API key is configured."""
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print_status(
            "Anthropic API Key",
            False,
            "Not found in .env file\n   Add: ANTHROPIC_API_KEY=your_key_here"
        )
        return False

    if api_key == "your_api_key_here":
        print_status(
            "Anthropic API Key",
            False,
            "Using placeholder value\n   Replace with real API key from console.anthropic.com"
        )
        return False

    if not api_key.startswith("sk-ant-"):
        print_status(
            "Anthropic API Key",
            False,
            "Key format looks wrong (should start with 'sk-ant-')"
        )
        return False

    print_status("Anthropic API Key", True, "Found and looks valid")
    return True

def check_project_structure():
    """Check if key files exist."""
    required_files = [
        "src/orchestrator.py",
        "src/planner.py",
        "src/executor.py",
        "src/state_manager.py",
        "src/models.py",
        "demo/mock_system.py",
        "demo/run_demo.py",
        "requirements.txt"
    ]

    missing = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing.append(file_path)

    passed = len(missing) == 0

    if missing:
        print_status(
            "Project Files",
            False,
            f"Missing files: {', '.join(missing)}"
        )
    else:
        print_status("Project Files", True, "All core files present")

    return passed

def check_sample_data():
    """Check if sample invoices exist."""
    sample_dir = Path("demo/sample_data")
    if not sample_dir.exists():
        print_status("Sample Data", False, "demo/sample_data folder not found")
        return False

    invoices = list(sample_dir.glob("invoice_*.txt"))

    if len(invoices) == 0:
        print_status("Sample Data", False, "No invoice files found")
        return False

    print_status("Sample Data", True, f"Found {len(invoices)} sample invoices")
    return True

def main():
    """Run all checks."""
    print("\n" + "="*60)
    print("  AUTONOMOUS AI TASK WORKER - SETUP CHECK")
    print("="*60 + "\n")

    checks = [
        ("Python Version", check_python_version),
        ("Project Files", check_project_structure),
        ("Sample Data", check_sample_data),
        ("Python Packages", check_dependencies),
        ("Playwright Browser", check_playwright),
        ("API Key", check_api_key),
    ]

    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print_status(name, False, f"Error: {e}")
            results[name] = False

    # Summary
    print("="*60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\nSummary: {passed}/{total} checks passed\n")

    if passed == total:
        print("[OK] ALL CHECKS PASSED! You're ready to run the demo.\n")
        print("Next steps:")
        print("  1. Terminal 1: python demo/mock_system.py")
        print("  2. Terminal 2: python demo/run_demo.py")
        print()
    else:
        print("[!] Some checks failed. Please fix the issues above.\n")
        print("Quick fixes:")
        if not results.get("Python Packages"):
            print("  -> python -m pip install -r requirements.txt")
        if not results.get("Playwright Browser"):
            print("  -> python -m playwright install chromium")
        if not results.get("API Key"):
            print("  -> Edit .env file with your Anthropic API key")
        print()
        print("See START_HERE.md for detailed instructions.")
        print()

if __name__ == "__main__":
    main()
