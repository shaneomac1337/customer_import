# Bulk Customer Import GUI

A user-friendly graphical interface for importing customers with multithreaded processing.

## 🚀 Quick Start

### Option 1: Double-click the batch file
```
Double-click: Launch_Bulk_Import_GUI.bat
```

### Option 2: Run with Python
```bash
python launch_gui.py
```

### Option 3: Run GUI directly
```bash
python bulk_import_gui.py
```

## 📋 Features

### 🔧 Configuration Tab
- **API Settings**: Enter your API URL, Auth Token, and GK-Passport
- **Import Settings**: Configure batch size, worker threads, delays, and retries
- **Presets**: Quick settings for Conservative, Balanced, or Aggressive imports
- **Show/Hide**: Toggle visibility for sensitive credential fields

### 📁 Files Tab
- **File Selection**: Add individual files or entire directories
- **Quick Load**: One-click loading of the 700 customer files
- **File Validation**: View customer counts, file sizes, and validation status
- **File Management**: Clear selections and manage your import queue

### ▶️ Import Tab
- **Import Control**: Start/stop import with real-time progress
- **Progress Tracking**: Visual progress bar and detailed statistics
- **Connection Testing**: Validate your API credentials before importing
- **Live Statistics**: Monitor batches, success rates, and import speed

### 📊 Results Tab
- **Import Log**: Real-time logging of all import activities
- **Log Management**: Clear, save, and export log files
- **Results Export**: Export detailed import results

## 🔐 Security Features

- **Credential Protection**: Password fields with show/hide toggles
- **No Storage**: Credentials are not saved to disk
- **Session Only**: All sensitive data cleared when application closes

## ⚙️ Import Settings

### Presets Available:

**Conservative (Safe)**
- Batch Size: 50 customers
- Worker Threads: 2
- Request Delay: 1.0 seconds
- Max Retries: 5

**Balanced (Recommended)**
- Batch Size: 70 customers
- Worker Threads: 3
- Request Delay: 0.5 seconds
- Max Retries: 3

**Aggressive (Fast)**
- Batch Size: 100 customers
- Worker Threads: 5
- Request Delay: 0.2 seconds
- Max Retries: 2

## 📂 File Requirements

### Required Files in Same Directory:
- `bulk_import_gui.py` - Main GUI application
- `bulk_import_multithreaded.py` - Import engine
- `launch_gui.py` - Launcher script

### Customer Files:
- JSON files with customer data in the correct format
- Use "Load 700 Customer Files" button for pre-generated test data
- Files should be in `bulk_import_700_customers/` directory

## 🎯 Usage Instructions

### Step 1: Configure API Settings
1. Open the **Configuration** tab
2. Enter your **Auth Token** (Bearer token)
3. Enter your **GK-Passport** value
4. Optionally modify the API URL if different
5. Choose a preset or customize import settings

### Step 2: Select Files
1. Open the **Files** tab
2. Click **"Load 700 Customer Files"** for test data, or
3. Click **"Add Files"** to select individual JSON files, or
4. Click **"Add Directory"** to add all JSON files from a folder
5. Verify file validation shows green status

### Step 3: Run Import
1. Open the **Import** tab
2. Click **"Validate Files"** to check your data
3. Optionally click **"Test Connection"** to verify API access
4. Click **"Start Import"** to begin the process
5. Monitor progress in real-time

### Step 4: Review Results
1. Open the **Results** tab
2. Review the import log for detailed information
3. Save or export results as needed

## 🔍 Troubleshooting

### Common Issues:

**"Missing Files" Error**
- Ensure `bulk_import_multithreaded.py` is in the same directory
- Check that all required files are present

**"No files selected" Error**
- Use the Files tab to add customer JSON files
- Verify files contain valid customer data

**"Please enter Auth Token and GK-Passport" Error**
- Go to Configuration tab and enter your credentials
- Use the "Show" buttons to verify credentials are entered correctly

**Import Fails with Connection Errors**
- Verify your Auth Token is current and valid
- Check that GK-Passport value is correct
- Test with Conservative preset first

**Unicode/Encoding Errors**
- Ensure customer files are saved with UTF-8 encoding
- Check that customer names don't contain unsupported characters

### Performance Tips:

**For Large Imports:**
- Start with Conservative preset
- Monitor success rate and adjust settings
- Use smaller batch sizes if you see timeouts

**For Speed:**
- Use Balanced or Aggressive presets
- Increase worker threads (but watch for rate limiting)
- Reduce request delays (but monitor for errors)

## 📈 Expected Performance

### 700 Customers (10 files × 70 customers):
- **Conservative**: ~8-12 minutes
- **Balanced**: ~5-8 minutes  
- **Aggressive**: ~3-5 minutes

### Success Rates:
- **70-customer batches**: 95-99% success rate
- **100-customer batches**: 85-95% success rate
- **50-customer batches**: 99%+ success rate

## 🛠️ Technical Details

### Built With:
- **Python 3.7+** with tkinter for GUI
- **Threading** for non-blocking imports
- **Requests** for HTTP API calls
- **JSON** for data processing

### Architecture:
- **Main Thread**: GUI and user interaction
- **Worker Thread**: Import processing
- **Queue Communication**: Progress updates between threads
- **Modular Design**: Separate GUI and import logic

## 📞 Support

If you encounter issues:
1. Check the Results tab for detailed error logs
2. Try the Conservative preset for problematic imports
3. Validate your customer files using the Files tab
4. Test your connection using the Import tab

## 🔄 Updates

To update the application:
1. Replace the Python files with newer versions
2. Restart the application
3. Your settings and file selections will reset (this is by design for security)

---

**Version**: 1.0  
**Last Updated**: July 2025  
**Compatibility**: Windows 10/11, Python 3.7+