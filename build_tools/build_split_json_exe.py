"""
Automated build script for creating split_large_json.py executable
This script uses PyInstaller to create a standalone .exe file that supports drag and drop
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
        "split_large_json.py"
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
    ['split_large_json.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'json',
        'os',
        'math',
        'sys',
        'datetime'
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
    name='JsonSplitter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console window for user interaction
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon file path here if you have one
    version_file=None,
)
'''
    
    with open('split_json.spec', 'w') as f:
        f.write(spec_content)
    
    print("[OK] Created PyInstaller spec file")

def build_executable():
    """Build the executable using PyInstaller"""
    
    print("\n" + "="*60)
    print("BUILDING JSON SPLITTER EXECUTABLE")
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
        'split_json.spec'
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
    
    if not os.path.exists('dist/JsonSplitter.exe'):
        print("[ERROR] Executable not found in dist directory")
        return False
    
    print("\n" + "="*60)
    print("CREATING DISTRIBUTION PACKAGE")
    print("="*60)
    
    # Create distribution directory
    dist_dir = "JsonSplitter_Portable"
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    
    os.makedirs(dist_dir)
    
    # Copy executable
    shutil.copy2('dist/JsonSplitter.exe', dist_dir)
    print(f"[COPY] Copied executable to {dist_dir}")
    
    # Create usage instructions
    usage_instructions = """# JSON Splitter - Portable Version

## Quick Start - Drag and Drop
1. Drag your large JSON file onto JsonSplitter.exe
2. The program will automatically split it into batches of 100 customers each
3. Output will be saved in a timestamped folder (e.g., customer_batches_20250715_201500)

## Manual Usage
1. Double-click JsonSplitter.exe
2. Enter the path to your JSON file when prompted
3. The program will split the file automatically

## Expected JSON Format
Your JSON file should have this structure:
```json
{
  "data": [
    {
      "customer_id": "123",
      "name": "John Doe",
      ...
    },
    {
      "customer_id": "456", 
      "name": "Jane Smith",
      ...
    }
  ]
}
```

## Output
- Creates a timestamped folder with batch files
- Each batch contains up to 100 customers
- Includes a split_summary.json with processing details
- Batch files are named: batch_00001_customers_100.json, batch_00002_customers_100.json, etc.

## System Requirements
- Windows 10/11 (64-bit)
- No Python installation required
- Sufficient disk space for output files

## Troubleshooting
- If the exe doesn't start, try running as administrator
- Check Windows Defender/antivirus settings if blocked
- Ensure your JSON file is valid and follows the expected format
- For very large files, ensure you have enough memory available

## Features
- Drag and drop support for easy file processing
- Automatic batch size optimization (100 customers per batch)
- Progress tracking during processing
- Error handling for invalid JSON files
- Memory-efficient processing
- Timestamped output directories to avoid conflicts

Version: Portable Executable
Built: """ + str(Path().absolute()) + """
"""
    
    with open(os.path.join(dist_dir, "README_PORTABLE.txt"), 'w') as f:
        f.write(usage_instructions)
    
    print(f"[COPY] Created usage instructions")
    
    # Get file sizes
    exe_size = os.path.getsize(os.path.join(dist_dir, 'JsonSplitter.exe'))
    
    print(f"\n[READY] DISTRIBUTION READY!")
    print(f"   Directory: {dist_dir}")
    print(f"   Executable size: {exe_size:,} bytes ({exe_size/1024/1024:.1f} MB)")
    print(f"   Ready for deployment!")
    
    return True

def main():
    """Main build process"""
    
    print("="*60)
    print("JSON SPLITTER - EXECUTABLE BUILDER")
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
    print("Your portable JSON splitter is ready in: JsonSplitter_Portable/")
    print("You can copy this entire folder to any Windows machine.")
    print("No Python installation required on target machines!")
    print("\nTo use:")
    print("1. Drag and drop a JSON file onto JsonSplitter.exe")
    print("2. Or double-click JsonSplitter.exe and enter file path")
    
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