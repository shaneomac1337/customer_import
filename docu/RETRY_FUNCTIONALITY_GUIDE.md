# Automatic Retry File Creation - User Guide

## 🎯 **Overview**

The Bulk Customer Import tool now **automatically creates retry files** when batches fail during import. These retry files are formatted correctly for **immediate re-import** without any manual intervention.

## 🔄 **How It Works**

### **Automatic Detection**
- When any batch fails during import, the tool automatically detects the failure
- Failed customers are extracted and saved in the correct API format
- Retry files are created in a timestamped directory

### **What Gets Created**
When failures occur, the tool creates:

```
retry_batches_YYYYMMDD_HHMMSS/
├── retry_batch_01_failed.json    # Failed customers in correct API format
├── retry_batch_02_failed.json    # (if multiple batches failed)
├── retry_summary.json            # Detailed error information
└── RETRY_INSTRUCTIONS.md         # Step-by-step retry guide
```

## 📋 **File Contents**

### **Retry Batch Files** (`retry_batch_XX_failed.json`)
- **Perfect API Format**: Contains only failed customers in correct JSON structure
- **Ready for Import**: Can be loaded directly into the GUI
- **No Manual Editing**: No need to modify or reformat

**Example Structure:**
```json
{
  "data": [
    {
      "changeType": "CREATE",
      "type": "PERSON",
      "person": {
        "customerId": "50000001000",
        "status": "UNACTIVATED",
        "firstName": "EMMA",
        "lastName": "SJÖBERG",
        ...
      }
    }
  ]
}
```

### **Retry Summary** (`retry_summary.json`)
- **Error Details**: Specific error messages for each failed batch
- **Statistics**: Count of failed batches and customers
- **File Mapping**: Which retry file contains which failed batch

### **Instructions File** (`RETRY_INSTRUCTIONS.md`)
- **Step-by-step guide** for using retry files
- **GUI instructions** for loading retry files
- **Error explanations** for troubleshooting

## 🚀 **How to Use Retry Files**

### **Method 1: GUI Auto-Load (Recommended)**
1. **Popup Notification**: When failures occur, you'll see a popup asking if you want to load retry files
2. **Click "Yes"**: The tool will automatically:
   - Clear current file selection
   - Load all retry files
   - Switch to Files tab
   - Show loaded retry files

### **Method 2: Manual Load**
1. **Open GUI**: Launch the Bulk Import GUI
2. **Files Tab**: Go to the Files tab
3. **Add Directory**: Click "Add Directory"
4. **Select Retry Directory**: Choose the `retry_batches_YYYYMMDD_HHMMSS` folder
5. **Configure Credentials**: Set your API credentials
6. **Start Import**: Click "Start Import"

### **Method 3: Individual Files**
1. **Add Files**: Use "Add Files" to select specific retry files
2. **Load Only What You Need**: Cherry-pick specific failed batches

## 📊 **GUI Integration**

### **Real-time Notifications**
- **Progress Updates**: See retry file creation in real-time
- **Popup Alerts**: Get notified when retry files are ready
- **Log Messages**: Detailed logging of retry file creation

### **Automatic Loading**
- **One-Click Retry**: Option to immediately load retry files
- **Smart File Management**: Automatically clears current selection
- **Tab Switching**: Automatically shows Files tab with loaded retry files

## 🛠️ **Technical Details**

### **Format Validation**
- **API Compliance**: All retry files use exact API format
- **Structure Validation**: Proper `data` wrapper and `person` objects
- **Field Completeness**: All required fields preserved

### **Error Preservation**
- **Original Error Messages**: Full error details preserved
- **Status Codes**: HTTP status codes captured
- **Batch Context**: Which original batch failed

### **Thread Safety**
- **Concurrent Safe**: Works correctly with multithreaded imports
- **Data Integrity**: No data loss during retry file creation
- **Progress Tracking**: Real-time updates during retry file generation

## 🎯 **Benefits**

### **Zero Manual Work**
- ✅ **No Reformatting**: Files are ready for immediate import
- ✅ **No Data Loss**: All failed customers preserved
- ✅ **No Manual Editing**: Perfect API format guaranteed

### **Smart Recovery**
- ✅ **Selective Retry**: Only failed customers, not successful ones
- ✅ **Batch Preservation**: Original batch structure maintained
- ✅ **Error Context**: Full error details for troubleshooting

### **Workflow Integration**
- ✅ **GUI Integration**: Seamless workflow within the GUI
- ✅ **One-Click Loading**: Immediate retry capability
- ✅ **Progress Tracking**: Real-time feedback

## 📝 **Example Workflow**

1. **Start Import**: Import 1000 customers in 20 batches
2. **Partial Failure**: 18 batches succeed, 2 batches fail
3. **Automatic Creation**: Tool creates `retry_batches_20250703_143022/`
4. **Popup Notification**: "Retry files created! Load now?"
5. **Click Yes**: Failed batches automatically loaded
6. **Fix Issues**: Update credentials or fix network issues
7. **Retry Import**: Click "Start Import" to retry only failed customers
8. **Success**: All customers imported successfully

## 🔍 **Troubleshooting**

### **Common Scenarios**
- **Network Issues**: Retry files preserve customers for when network is restored
- **Authentication Errors**: Fix credentials and retry with same files
- **Rate Limiting**: Retry with lower concurrency settings
- **Partial API Failures**: Only failed customers need to be retried

### **File Locations**
- **Retry Directories**: Created in the same directory as the main tool
- **Timestamped Names**: `retry_batches_YYYYMMDD_HHMMSS` format
- **Persistent Storage**: Files remain until manually deleted

## 🎉 **Summary**

The automatic retry functionality transforms failed imports from a manual, error-prone process into a **one-click recovery operation**. No more:
- ❌ Manual file editing
- ❌ Format guessing
- ❌ Data loss
- ❌ Complex recovery procedures

Instead, you get:
- ✅ **Automatic retry file creation**
- ✅ **Perfect API format**
- ✅ **One-click recovery**
- ✅ **Complete error context**

**Your bulk import workflow is now failure-resistant and recovery-friendly!** 🚀
