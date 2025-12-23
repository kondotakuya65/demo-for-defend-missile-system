#!/usr/bin/env python3
"""
Verify that the development environment is set up correctly
"""

import sys

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"[FAIL] Python 3.8+ required. Found: {version.major}.{version.minor}")
        return False
    print(f"[OK] Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = {
        'OpenGL': 'PyOpenGL',
        'numpy': 'numpy',
        'PyQt6': 'PyQt6'
    }
    
    missing = []
    for module, package in required_packages.items():
        try:
            if module == 'OpenGL':
                import OpenGL
                print(f"[OK] {package} installed")
            elif module == 'PyQt6':
                import PyQt6
                print(f"[OK] {package} installed")
            else:
                __import__(module)
                print(f"[OK] {package} installed")
        except ImportError:
            print(f"[FAIL] {package} not installed")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    return True

def check_opengl():
    """Check OpenGL availability"""
    try:
        from OpenGL.GL import glGetString, GL_VERSION
        from OpenGL import error
        
        # Try to get OpenGL version (requires a context, so this might fail)
        print("[OK] PyOpenGL imported successfully")
        print("   Note: Full OpenGL test requires a rendering context")
        return True
    except ImportError as e:
        print(f"[FAIL] PyOpenGL import failed: {e}")
        return False
    except Exception as e:
        print(f"⚠️  OpenGL check incomplete: {e}")
        return True  # Not critical for basic check

def main():
    """Run all checks"""
    print("=" * 50)
    print("Environment Setup Verification")
    print("=" * 50)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("OpenGL", check_opengl),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        print("-" * 30)
        result = check_func()
        results.append(result)
    
    print("\n" + "=" * 50)
    if all(results):
        print("[OK] All checks passed! Environment is ready.")
        return 0
    else:
        print("⚠️  Some checks failed. Please install missing dependencies.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

