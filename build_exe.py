"""
Automated build script for creating Bulk Customer Import GUI executable
This script uses PyInstaller to create a standalone .exe file
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        print(f"[OK] PyInstaller found: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("[ERROR] PyInstaller not found!")
        print("Install with: pip install pyinstaller")
        return False

def check_dependencies():
    """Check if all required files exist"""
    required_files = [
        "bulk_import_gui.py",
        "bulk_import_multithreaded.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"[ERROR] Missing required files: {missing_files}")
        return False
    
    print("[OK] All required files found")
    return True

def create_spec_file():
    """Create PyInstaller spec file"""
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['bulk_import_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('bulk_import_multithreaded.py', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'requests',
        'json',
        'threading',
        'queue',
        'datetime',
        'os',
        'sys'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BulkCustomerImport',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True if you want console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon file path here if you have one
    version_file=None,
)
'''
    
    with open('bulk_import.spec', 'w') as f:
        f.write(spec_content)
    
    print("[OK] Created PyInstaller spec file")

def build_executable():
    """Build the executable using PyInstaller"""
    
    print("\n" + "="*60)
    print("BUILDING EXECUTABLE")
    print("="*60)
    
    # Clean previous builds
    if os.path.exists('build'):
        shutil.rmtree('build')
        print("[CLEAN] Cleaned previous build directory")
    
    if os.path.exists('dist'):
        shutil.rmtree('dist')
        print("[CLEAN] Cleaned previous dist directory")
    
    # Build command
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        'bulk_import.spec'
    ]
    
    print(f"[BUILD] Running: {' '.join(cmd)}")
    print("This may take a few minutes...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("[SUCCESS] Build completed successfully!")
            return True
        else:
            print("[ERROR] Build failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("[ERROR] Build timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"[ERROR] Build error: {e}")
        return False

def create_distribution():
    """Create distribution package"""
    
    if not os.path.exists('dist/BulkCustomerImport.exe'):
        print("[ERROR] Executable not found in dist directory")
        return False
    
    print("\n" + "="*60)
    print("CREATING DISTRIBUTION PACKAGE")
    print("="*60)
    
    # Create distribution directory
    dist_dir = "BulkCustomerImport_Portable"
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    
    os.makedirs(dist_dir)
    
    # Copy executable
    shutil.copy2('dist/BulkCustomerImport.exe', dist_dir)
    print(f"[COPY] Copied executable to {dist_dir}")
    
    # Copy customer data if it exists
    customer_dir = "bulk_import_700_customers"
    if os.path.exists(customer_dir):
        shutil.copytree(customer_dir, os.path.join(dist_dir, customer_dir))
        print(f"[COPY] Copied customer data to {dist_dir}")
    
    # Copy documentation
    docs_to_copy = [
        "README_GUI.md",
        "BULK_IMPORT_SUMMARY.md",
        "requirements.txt"
    ]
    
    for doc in docs_to_copy:
        if os.path.exists(doc):
            shutil.copy2(doc, dist_dir)
            print(f"[COPY] Copied {doc}")
    
    # Create usage instructions
    usage_instructions = """# Bulk Customer Import - Portable Version

## Quick Start
1. Double-click `BulkCustomerImport.exe` to launch the GUI
2. Go to Configuration tab and enter your Auth Token and GK-Passport
3. Go to Files tab and click "Load 700 Customer Files" (or add your own files)
4. Go to Import tab and click "Start Import"
5. Monitor progress and check Results tab for logs

## Files Included
- `BulkCustomerImport.exe` - Main application
- `bulk_import_700_customers/` - Test customer data (700 customers in 10 files)
- `README_GUI.md` - Complete documentation
- `BULK_IMPORT_SUMMARY.md` - Feature overview

## System Requirements
- Windows 10/11 (64-bit)
- No Python installation required
- Internet connection for API calls

## Troubleshooting
- If the exe doesn't start, try running as administrator
- Check Windows Defender/antivirus settings if blocked
- Ensure customer data files are in the same directory as the exe

## Support
- Check the README_GUI.md for detailed instructions
- All features are the same as the Python version
- Customer data files can be modified or replaced as needed

Version: Portable Executable
Built: """ + str(Path().absolute()) + """
"""
    
    with open(os.path.join(dist_dir, "README_PORTABLE.txt"), 'w') as f:
        f.write(usage_instructions)
    
    print(f"[COPY] Created usage instructions")
    
    # Get file sizes
    exe_size = os.path.getsize(os.path.join(dist_dir, 'BulkCustomerImport.exe'))
    
    print(f"\n[READY] DISTRIBUTION READY!")
    print(f"   Directory: {dist_dir}")
    print(f"   Executable size: {exe_size:,} bytes ({exe_size/1024/1024:.1f} MB)")
    print(f"   Ready for deployment!")
    
    return True

def main():
    """Main build process"""
    
    print("="*60)
    print("BULK CUSTOMER IMPORT - EXECUTABLE BUILDER")
    print("="*60)
    
    # Check environment
    print("Checking build environment...")
    
    if not check_pyinstaller():
        print("\nInstall PyInstaller first:")
        print("pip install pyinstaller")
        return False
    
    if not check_dependencies():
        return False
    
    # Create spec file
    create_spec_file()
    
    # Build executable
    if not build_executable():
        return False
    
    # Create distribution
    if not create_distribution():
        return False
    
    print("\n" + "="*60)
    print("BUILD COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("Your portable executable is ready in: BulkCustomerImport_Portable/")
    print("You can copy this entire folder to any Windows machine.")
    print("No Python installation required on target machines!")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n[ERROR] Build failed!")
            input("Press Enter to exit...")
            sys.exit(1)
        else:
            print("\n[SUCCESS] Build successful!")
            input("Press Enter to exit...")
    except KeyboardInterrupt:
        print("\n\n[CANCEL] Build cancelled by user")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)