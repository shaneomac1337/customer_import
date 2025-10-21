# Build Tools

This folder contains scripts and configuration files for building executables.

## Files

### Build Scripts
- **build_exe.py** - Build the Bulk Customer Import GUI executable
- **build_split_json_exe.py** - Build the JSON splitter executable
- **Build_EXE.bat** - Batch file to launch the build script

### PyInstaller Specs
- **bulk_import.spec** - PyInstaller specification for bulk import tool
- **split_json.spec** - PyInstaller specification for JSON splitter

## Usage

### Build Bulk Import Tool
```powershell
python build_tools/build_exe.py
```

### Build JSON Splitter
```powershell
python build_tools/build_split_json_exe.py
```

Or use the batch file:
```powershell
.\build_tools\Build_EXE.bat
```

## Requirements
- PyInstaller must be installed: `pip install pyinstaller`
- All source files must be in the root directory
