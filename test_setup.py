"""
PRISM Setup Test Script
Verifies that all components are properly installed and configured
"""

import sys
import os
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓{RESET} {text}")

def print_error(text):
    print(f"{RED}✗{RESET} {text}")

def print_warning(text):
    print(f"{YELLOW}⚠{RESET} {text}")

def print_info(text):
    print(f"{BLUE}ℹ{RESET} {text}")

def test_python_version():
    """Test Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor}.{version.micro} (3.10+ required)")
        return False

def test_module(module_name, package_name=None):
    """Test if a Python module is installed"""
    try:
        __import__(module_name)
        print_success(f"{package_name or module_name}")
        return True
    except ImportError:
        print_error(f"{package_name or module_name} (not installed)")
        return False

def test_env_file():
    """Test if .env file exists and has required keys"""
    env_path = Path(__file__).parent / ".env"
    
    if not env_path.exists():
        print_error(".env file not found")
        print_info("Run: copy .env.example .env")
        return False
    
    print_success(".env file exists")
    
    # Check for required keys
    with open(env_path, 'r') as f:
        content = f.read()
    
    has_nebius = 'NEBIUS_API_KEY' in content and 'neb-' in content
    has_porcupine = 'PORCUPINE_ACCESS_KEY' in content
    
    if has_nebius:
        print_success("  NEBIUS_API_KEY configured")
    else:
        print_warning("  NEBIUS_API_KEY not configured (required)")
    
    if has_porcupine and 'your-porcupine-key-here' not in content:
        print_success("  PORCUPINE_ACCESS_KEY configured")
    else:
        print_warning("  PORCUPINE_ACCESS_KEY not configured (optional)")
    
    return has_nebius

def test_directories():
    """Test if required directories exist"""
    base_path = Path(__file__).parent
    
    dirs = {
        'backend': base_path / 'backend',
        'ui': base_path / 'ui',
        'logs': base_path / 'logs',
        'ui/assets': base_path / 'ui' / 'assets'
    }
    
    all_exist = True
    for name, path in dirs.items():
        if path.exists():
            print_success(f"{name}/ directory")
        else:
            print_error(f"{name}/ directory (missing)")
            all_exist = False
    
    return all_exist

def test_node_modules():
    """Test if Node.js dependencies are installed"""
    node_modules = Path(__file__).parent / 'ui' / 'node_modules'
    
    if node_modules.exists():
        print_success("Node.js dependencies installed")
        return True
    else:
        print_error("Node.js dependencies not installed")
        print_info("Run: cd ui && npm install")
        return False

def test_backend_files():
    """Test if backend files exist"""
    base_path = Path(__file__).parent / 'backend'
    
    files = [
        'main.py',
        'prism_llm.py',
        'voice_pipeline.py',
        'tts.py',
        'system_control.py',
        'memory.py'
    ]
    
    all_exist = True
    for file in files:
        path = base_path / file
        if path.exists():
            print_success(f"backend/{file}")
        else:
            print_error(f"backend/{file} (missing)")
            all_exist = False
    
    return all_exist

def test_ui_files():
    """Test if UI files exist"""
    base_path = Path(__file__).parent / 'ui'
    
    files = [
        'main.js',
        'renderer.js',
        'index.html',
        'styles.css',
        'package.json'
    ]
    
    all_exist = True
    for file in files:
        path = base_path / file
        if path.exists():
            print_success(f"ui/{file}")
        else:
            print_error(f"ui/{file} (missing)")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print_header("PRISM Setup Verification")
    
    results = {}
    
    # Test Python version
    print_info("Checking Python version...")
    results['python'] = test_python_version()
    
    # Test Python modules
    print_info("\nChecking Python dependencies...")
    modules = [
        ('openai', 'openai'),
        ('dotenv', 'python-dotenv'),
        ('pvporcupine', 'pvporcupine'),
        ('whisper', 'openai-whisper'),
        ('TTS', 'TTS'),
        ('pyaudio', 'pyaudio'),
        ('win32com', 'pywin32'),
        ('pytest', 'pytest')
    ]
    
    module_results = []
    for module, package in modules:
        module_results.append(test_module(module, package))
    
    results['modules'] = all(module_results)
    
    # Test environment configuration
    print_info("\nChecking environment configuration...")
    results['env'] = test_env_file()
    
    # Test directories
    print_info("\nChecking project structure...")
    results['dirs'] = test_directories()
    
    # Test Node.js dependencies
    print_info("\nChecking Node.js dependencies...")
    results['node'] = test_node_modules()
    
    # Test backend files
    print_info("\nChecking backend files...")
    results['backend'] = test_backend_files()
    
    # Test UI files
    print_info("\nChecking UI files...")
    results['ui'] = test_ui_files()
    
    # Summary
    print_header("Test Summary")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\nTests Passed: {passed}/{total}\n")
    
    if passed == total:
        print_success("All tests passed! PRISM is ready to run.")
        print_info("\nNext steps:")
        print("  1. Make sure your .env file has valid API keys")
        print("  2. Run: start.bat")
        print("  3. Say 'PRISM' or click the orb to activate")
        return 0
    else:
        print_warning("Some tests failed. Please fix the issues above.")
        print_info("\nCommon fixes:")
        print("  • Missing dependencies: run setup.bat")
        print("  • Missing .env: copy .env.example to .env")
        print("  • Missing Node modules: cd ui && npm install")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        print()
        input("Press Enter to exit...")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)
