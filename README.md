# 🚀 Customer Import System

A comprehensive bulk customer import system with GUI interface for efficient customer data processing.

## 📋 Quick Start

### **🖥️ GUI Application**
```bash
python bulk_import_gui.py
```

### **⚡ Quick Launch (Windows)**
- Double-click `Launch_Bulk_Import_GUI.bat`
- Or use `Load_1000_Customers_GUI.bat` for pre-loaded test data

### **📦 Portable Version**
- Use `BulkCustomerImport_Portable/BulkCustomerImport.exe` for standalone execution

## 🎯 **Key Features**

- **🔄 Multithreaded Processing**: Efficient bulk import with configurable batch sizes
- **🖥️ User-Friendly GUI**: Intuitive interface with real-time progress tracking
- **🚨 Failed Customers Tab**: Comprehensive visibility into import failures
- **🔄 Retry Functionality**: Automatic retry file generation for failed imports
- **🔐 Automatic Authentication**: Seamless token management
- **📊 Real-time Monitoring**: Live progress updates and statistics
- **📤 Export Capabilities**: Export failed customers and retry data

## 📁 **Project Structure**

```
customer_import/
├── 📄 README.md                    # This file
├── 📋 requirements.txt             # Python dependencies
├── 🔧 WARP.md                      # Project configuration
├── 🎮 Launch_Bulk_Import_GUI.bat   # Quick launch script
├── 🎮 Load_1000_Customers_GUI.bat  # Launch with test data
│
├── 🖥️ Core Application Files
│   ├── bulk_import_gui.py          # Main GUI application
│   ├── bulk_import_multithreaded.py # Core import engine
│   └── auth_manager.py              # Authentication management (C4R/Engage)
│
├── 📁 build_tools/                 # Build scripts & configurations
│   ├── build_exe.py                # Build GUI executable
│   ├── build_split_json_exe.py     # Build JSON splitter
│   ├── Build_EXE.bat               # Build launcher
│   ├── bulk_import.spec            # PyInstaller spec (GUI)
│   └── split_json.spec             # PyInstaller spec (Splitter)
│
├── 📁 generators/                  # Customer data generators
│   ├── generate_one_customer.py    # Single customer generator
│   ├── generate_1000_customers.py  # 1K customers (20 batches)
│   ├── generate_50_batches.py      # 5K customers (50 batches)
│   └── generate_100_batches.py     # 10K customers (100 batches)
│
├── 📁 utils/                       # Utility scripts
│   ├── split_json_simple.py        # Simple JSON splitter
│   ├── split_large_json.py         # Large file splitter
│   ├── verify_split_integrity.py   # Verify split files
│   ├── check_firstname_spaces.py   # Name validation
│   ├── quick_firstname_check.py    # Quick name check
│   └── shx_csv_to_import.py        # CSV converter
│
├── 📁 tests/                       # Test scripts
│   ├── test_dual_mode.py           # Test C4R/Engage modes
│   ├── test_failed_customers_tab.py # Test failed customers UI
│   └── analyze_failed_customers_by_batch.py # Failure analysis
│
├── 📁 test_data/                   # Sample data files
│   ├── customer_*.json             # Sample customers
│   └── *.csv                       # CSV test data
│
├── 📁 output/                      # Generated data & results
│   ├── bulk_import_*_batches/      # Generated customer batches
│   ├── failed_customers/           # Failed customer tracking
│   └── retry_batches_*/            # Retry files
│
├── 📁 temp/                        # Temporary files
│   ├── build/                      # Build artifacts
│   ├── dist/                       # Distribution files
│   └── *.log                       # Old log files
│
├── 📁 docu/                        # Documentation
│   └── *.md                        # Guides & documentation
│
└── 📁 BulkCustomerImport_Portable/ # Standalone executable
    └── BulkCustomerImport.exe      # Ready-to-run application
```

## 🛠️ **Installation**

### **Prerequisites**
- Python 3.7+
- Required packages: `pip install -r requirements.txt`

### **Dependencies**
- `tkinter` - GUI framework
- `requests` - HTTP client
- `threading` - Multithreaded processing
- `json` - Data handling

## 📖 **Documentation**

Comprehensive documentation is available in the `/docu` folder:

- **📋 [Bulk Import Summary](docu/BULK_IMPORT_SUMMARY.md)** - Complete system overview
- **🖥️ [GUI Guide](docu/README_GUI.md)** - GUI usage instructions
- **🚨 [Failed Customers Tab](docu/FAILED_CUSTOMERS_TAB_GUIDE.md)** - Failed customer management
- **🔄 [Retry Functionality](docu/RETRY_FUNCTIONALITY_GUIDE.md)** - Retry system guide
- **🔐 [Authentication Guide](docu/AUTOMATIC_AUTHENTICATION_GUIDE.md)** - Auth setup
- **🏗️ [Build Instructions](docu/BUILD_INSTRUCTIONS.md)** - Creating executables

## 🧪 **Testing**

Test utilities are available in the `/tests` folder:

- **`test_failed_customers_tab.py`** - Test failed customers functionality
- **`generate_*_customers.py`** - Generate sample customer data
- **`validate_1000_customers.py`** - Validate customer data
- **`analyze_failed_customers_by_batch.py`** - Analyze failure patterns
- **`extract_all_failed_customers.py`** - Extract failure data

## 🚀 **Usage Examples**

### **Basic Import**
1. Launch GUI: `python bulk_import_gui.py`
2. Select customer files in the "Files" tab
3. Configure settings in the "Import" tab
4. Click "Start Import"
5. Monitor progress and failures in real-time

### **Failed Customer Management**
1. Go to "Failed Customers" tab
2. View failed customers with details
3. Export failure data for analysis
4. Use retry functionality to reprocess

### **Batch Processing**
1. Use pre-generated batches in `bulk_import_*_batches/` folders
2. Load via GUI or batch files
3. Process with configurable batch sizes and thread counts

## 🔧 **Configuration**

Key configuration options:
- **Batch Size**: Number of customers per batch (default: 50)
- **Max Threads**: Concurrent processing threads (default: 5)
- **API Endpoints**: Configurable via authentication settings
- **Retry Settings**: Automatic retry file generation

## 📊 **Monitoring & Analytics**

- **Real-time Progress**: Live updates during import
- **Success Rate Tracking**: Detailed statistics
- **Failure Analysis**: Comprehensive error reporting
- **Export Capabilities**: Data export for external analysis

## 🤝 **Support**

For issues, questions, or contributions:
1. Check documentation in `/docu` folder
2. Review test examples in `/tests` folder
3. Use the GUI's built-in logging and error reporting

## 📄 **License**

Internal use - Customer Import System

---

**🎯 Ready to import customers efficiently with comprehensive failure management and real-time monitoring!**
