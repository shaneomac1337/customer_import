# 🧪 Tests Directory

This directory contains test scripts and utilities for the Customer Import System.

## 📋 **Test Scripts**

### **🚨 Failed Customers Testing**
- **`test_failed_customers_tab.py`** - Creates sample failed customers data for testing the Failed Customers tab functionality

### **📊 Data Generation**
- **`generate_1000_customers.py`** - Generate 1000 sample customers for testing
- **`generate_100_batches.py`** - Generate 100 customer batches
- **`generate_50_batches.py`** - Generate 50 customer batches

### **🔍 Analysis & Validation**
- **`validate_1000_customers.py`** - Validate customer data integrity
- **`analyze_failed_customers_by_batch.py`** - Analyze failure patterns by batch
- **`extract_all_failed_customers.py`** - Extract and consolidate failed customer data

## 🚀 **Usage**

### **Run from tests directory:**
```bash
cd tests
python test_failed_customers_tab.py
python generate_1000_customers.py
```

### **Run from project root:**
```bash
python tests/test_failed_customers_tab.py
python tests/generate_1000_customers.py
```

## 📝 **Notes**

- Test scripts are configured to work with relative paths to the project root
- Generated data is saved to appropriate directories in the project structure
- Use these scripts to create sample data for testing GUI functionality

## 🎯 **Quick Test Workflow**

1. **Generate Sample Data**: `python tests/generate_1000_customers.py`
2. **Create Failed Customers**: `python tests/test_failed_customers_tab.py`
3. **Launch GUI**: `python bulk_import_gui.py`
4. **Test Failed Customers Tab**: Go to "Failed Customers" tab and click "Refresh"
5. **Validate Results**: `python tests/validate_1000_customers.py`
