# Project Structure Documentation

This document explains the organized folder structure of the Customer Import System.

## 📁 Directory Overview

### Root Directory
Core application files that should remain in the root:
- **bulk_import_gui.py** - Main GUI application
- **bulk_import_multithreaded.py** - Core import engine with multithreading
- **auth_manager.py** - Authentication manager (supports C4R and Engage modes)
- **README.md** - Main project documentation
- **requirements.txt** - Python dependencies
- **WARP.md** - Project configuration file
- **Launch_Bulk_Import_GUI.bat** - Quick launcher for GUI
- **Load_1000_Customers_GUI.bat** - Launch GUI with test data

---

## 🛠️ build_tools/
**Purpose:** Build scripts and PyInstaller configurations

**Contents:**
- `build_exe.py` - Build the main GUI executable
- `build_split_json_exe.py` - Build the JSON splitter tool
- `Build_EXE.bat` - Batch file launcher for builds
- `bulk_import.spec` - PyInstaller spec for GUI
- `split_json.spec` - PyInstaller spec for JSON splitter
- `README.md` - Build tool documentation

**Usage:**
```powershell
python build_tools/build_exe.py
```

---

## 🔨 generators/
**Purpose:** Customer data generation scripts

**Contents:**
- `generate_one_customer.py` - Generate single customer
- `generate_1000_customers.py` - Generate 1,000 customers (20 files × 50)
- `generate_50_batches.py` - Generate 5,000 customers (50 files × 100)
- `generate_100_batches.py` - Generate 10,000 customers (100 files × 100)
- `README.md` - Generator documentation

**Usage:**
```powershell
python generators/generate_one_customer.py
python generators/generate_1000_customers.py
```

**Output:** Generated files are placed in `output/` directory

---

## 🔧 utils/
**Purpose:** Utility scripts for data processing and validation

**Contents:**

### Data Processing
- `split_json_simple.py` - Simple JSON file splitter
- `split_large_json.py` - Split large JSON files
- `verify_split_integrity.py` - Verify split file integrity

### Data Validation
- `check_firstname_spaces.py` - Check for spaces in first names
- `quick_firstname_check.py` - Quick first name validation

### Data Conversion
- `shx_csv_to_import.py` - Convert SHX CSV to import format

**Usage:**
```powershell
python utils/split_large_json.py input.json
```

---

## 🧪 tests/
**Purpose:** Test scripts and validation tools

**Contents:**
- `test_dual_mode.py` - Test C4R and Engage authentication modes
- `test_failed_customers_tab.py` - Test failed customers UI
- `test_individual_failed_customers.py` - Test individual failure handling
- `test_single_failures_fix.py` - Test single failure fixes
- `analyze_failed_customers_by_batch.py` - Analyze failure patterns
- `extract_all_failed_customers.py` - Extract failure data
- `validate_1000_customers.py` - Validate customer data
- `README.md` - Test documentation

**Usage:**
```powershell
python tests/test_dual_mode.py
```

---

## 📋 test_data/
**Purpose:** Sample customer data files for testing

**Contents:**
- `customer_elina_bylund.json` - Sample customer
- `customer_salomon_johansson.json` - Sample customer
- `single_customer_batch.json` - Single customer batch
- `SHX_TestData_*.csv` - CSV test data
- `README.md` - Test data documentation

**Usage:** Import these files through the GUI for testing

---

## 📤 output/
**Purpose:** Generated data and import results

**Auto-created subdirectories:**
- `bulk_import_*_batches/` - Generated customer batches
- `failed_customers/` - Failed customer tracking
- `failed_customers/single_failures/` - Individual failed customers
- `retry_batches_*/` - Retry files
- `api_responses/` - API response logs

**Note:** This directory is auto-created by generators and import tool

---

## 🗑️ temp/
**Purpose:** Temporary files and build artifacts

**Contents:**
- `build/` - PyInstaller build cache
- `dist/` - Distribution files
- `__pycache__/` - Python bytecode cache
- `*.log` - Old log files

**Note:** Safe to delete - files are auto-regenerated

---

## 📚 docu/
**Purpose:** Project documentation

**Contents:**
- `BULK_IMPORT_SUMMARY.md` - System overview
- `README_GUI.md` - GUI usage guide
- `FAILED_CUSTOMERS_TAB_GUIDE.md` - Failed customer management
- `RETRY_FUNCTIONALITY_GUIDE.md` - Retry system guide
- `AUTOMATIC_AUTHENTICATION_GUIDE.md` - Authentication setup
- `BUILD_INSTRUCTIONS.md` - Build guide

---

## 📦 BulkCustomerImport_Portable/
**Purpose:** Standalone executable distribution

**Contents:**
- `BulkCustomerImport.exe` - Standalone application
- `README_PORTABLE.txt` - Portable version instructions
- `requirements.txt` - Dependency reference

**Note:** No Python installation required to run the .exe

---

## 📦 JsonSplitter_Portable/
**Purpose:** Standalone JSON splitter executable

**Contents:**
- JSON splitter tool as standalone .exe

---

## 🎯 Quick Reference

### Run the Application
```powershell
python bulk_import_gui.py
# or
.\Launch_Bulk_Import_GUI.bat
```

### Generate Test Data
```powershell
python generators/generate_1000_customers.py
```

### Build Executable
```powershell
python build_tools/build_exe.py
```

### Run Tests
```powershell
python tests/test_dual_mode.py
```

### Process Utilities
```powershell
python utils/split_large_json.py data.json
```

---

## 🧹 Cleanup Strategy

### Safe to Delete
- `temp/` - Entire directory
- `output/` - Old generated data (keep README.md)
- `.gitignore` excludes these automatically

### Keep These
- All root `.py` files (core application)
- `generators/`, `utils/`, `build_tools/`, `tests/`
- `docu/` documentation
- `test_data/` sample files
- `BulkCustomerImport_Portable/` if distributed

---

## 🔄 Workflow Examples

### Complete Build & Test Workflow
```powershell
# 1. Generate test data
python generators/generate_1000_customers.py

# 2. Test authentication
python tests/test_dual_mode.py

# 3. Run GUI
python bulk_import_gui.py

# 4. Build executable
python build_tools/build_exe.py
```

### Data Processing Workflow
```powershell
# 1. Split large JSON
python utils/split_large_json.py large_file.json

# 2. Verify integrity
python utils/verify_split_integrity.py

# 3. Import via GUI
python bulk_import_gui.py
```

---

## 📝 Notes

- All Python scripts can be run from project root
- Use relative paths: `python generators/script.py`
- Generated files go to `output/`
- Build artifacts go to `temp/`
- Sample data stays in `test_data/`

This structure keeps the project organized and maintainable!
