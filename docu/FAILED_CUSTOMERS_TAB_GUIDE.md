# 🚨 Failed Customers Tab - User Guide

## 📋 **Overview**

The **Failed Customers** tab is a new feature in the Bulk Customer Import GUI that provides comprehensive visibility into customers that failed during import operations. This tab displays detailed information about each failed customer, including their ID, username, error message, and timestamp.

## 🎯 **Key Features**

### **📊 Real-time Display**
- **Live Updates**: Automatically refreshes during import operations (when auto-refresh is enabled)
- **Total Count**: Shows the total number of failed customers at the top right
- **Sortable Columns**: Click column headers to sort data
- **Detailed View**: Double-click any row to see complete customer details

### **🔄 Data Management**
- **Refresh Button**: Manually refresh the display to load latest failed customers
- **Auto-refresh**: Toggle automatic updates during import operations
- **Clear Function**: Clear failed customers data (with confirmation dialog)
- **Export Options**: Export failed customers to JSON or CSV format

### **📋 Column Information**
1. **Customer ID**: The unique identifier of the failed customer
2. **Username**: The customer's username/name
3. **Error**: The specific error message (truncated for display)
4. **Timestamp**: When the failure was detected
5. **Batch Info**: Information about how the failure was detected

## 🚀 **How to Use**

### **Accessing the Tab**
1. Launch the Bulk Import GUI: `python bulk_import_gui.py`
2. Click on the **"Failed Customers"** tab
3. The tab will show "No failed customers" initially

### **During Import Operations**
1. **Start an Import**: Use the Import tab to begin importing customers
2. **Auto-refresh Enabled**: Failed customers appear automatically as they occur
3. **Real-time Count**: The total count updates in real-time
4. **Live Monitoring**: Watch failures as they happen during import

### **After Import Completion**
1. **Final Refresh**: The tab automatically refreshes when import completes
2. **Review Failures**: Examine all failed customers and their errors
3. **Export Data**: Export failed customers for further analysis
4. **Detailed Analysis**: Double-click rows for complete customer information

## 🛠️ **Button Functions**

### **🔄 Refresh**
- **Purpose**: Manually refresh the failed customers display
- **When to Use**: 
  - After import completion
  - When auto-refresh is disabled
  - To reload data from saved files

### **📤 Export Failed Customers**
- **Purpose**: Export failed customers data to file
- **Formats Supported**:
  - **JSON**: Complete data with all fields
  - **CSV**: Tabular format for spreadsheet analysis
  - **TXT**: Plain text format
- **Use Cases**:
  - Analysis in external tools
  - Reporting to stakeholders
  - Backup of failure data

### **🗑️ Clear Failed Customers**
- **Purpose**: Clear failed customers from memory and display
- **Safety**: Requires confirmation dialog
- **Note**: Does NOT delete saved files, only clears current session data

### **⚙️ Auto-refresh during import**
- **Purpose**: Toggle automatic refresh during import operations
- **Default**: Enabled (checked)
- **Performance**: Minimal impact on import speed

## 📊 **Data Sources**

The Failed Customers tab pulls data from multiple sources:

### **1. Active Importer**
- **Primary Source**: Current import session data
- **Real-time**: Updates as failures occur
- **Thread-safe**: Safely accesses data during multithreaded imports

### **2. Saved Files**
- **Fallback Source**: `failed_customers/failed_customers.json`
- **Persistence**: Data survives between GUI sessions
- **Backup**: Available even if importer is not active

### **3. Data Structure**
Each failed customer record contains:
```json
{
  "customerId": "50000001001",
  "username": "ERIK ANDERSSON", 
  "result": "FAILED",
  "error": "Customer already exists with this ID",
  "timestamp": "2025-01-07T10:30:45.123456",
  "batchInfo": "Found in structured response data",
  "originalData": { /* Complete original customer data */ }
}
```

## 🔍 **Detailed Customer View**

### **Double-click Functionality**
- **Trigger**: Double-click any row in the table
- **Window**: Opens a new popup window with complete details
- **Content**: 
  - All customer fields
  - Complete error information
  - Original customer data (JSON formatted)
  - Batch context information

### **Detail Window Features**
- **Scrollable**: Handle large customer data
- **Formatted**: JSON data is properly indented
- **Copyable**: Text can be selected and copied
- **Modal**: Stays on top until closed

## 📈 **Integration with Import Process**

### **Automatic Detection**
The tab integrates seamlessly with the import engine's **three-method failure detection**:

1. **Structured Data Parsing**: Failures in API response JSON
2. **Regex Fallback**: Pattern matching in raw response text  
3. **Error Array Processing**: Failures in error arrays

### **Real-time Updates**
- **API Response Processing**: Updates when each batch completes
- **Thread Safety**: Safe concurrent access during multithreaded imports
- **Performance Optimized**: Minimal impact on import speed

## 🎯 **Best Practices**

### **During Import**
1. **Keep Auto-refresh Enabled**: Monitor failures in real-time
2. **Watch the Count**: Keep an eye on the total failed count
3. **Don't Clear During Import**: Wait until import completes

### **After Import**
1. **Review All Failures**: Check each failed customer
2. **Export for Analysis**: Save data for detailed review
3. **Use Details View**: Double-click for complete information
4. **Plan Retry Strategy**: Use failure data to plan corrections

### **Troubleshooting**
1. **No Data Showing**: Click Refresh button
2. **Count Mismatch**: Refresh to reload from all sources
3. **Export Issues**: Check file permissions and disk space
4. **Performance**: Disable auto-refresh for very large imports

## 🔧 **Technical Notes**

### **Performance Considerations**
- **Efficient Updates**: Only refreshes when needed
- **Memory Management**: Handles large numbers of failed customers
- **Thread Safety**: Safe concurrent access patterns

### **File Locations**
- **Failed Customers**: `failed_customers/failed_customers.json`
- **Retry Batches**: `retry_batches_YYYYMMDD_HHMMSS/`
- **API Responses**: `api_responses/`

### **Error Handling**
- **Graceful Failures**: Continues working even if data sources are unavailable
- **User Feedback**: Clear error messages for any issues
- **Recovery**: Automatic retry of failed operations

## 🎉 **Benefits**

### **Visibility**
- **Complete Overview**: See all failed customers in one place
- **Real-time Monitoring**: Watch failures as they occur
- **Detailed Information**: Access complete failure context

### **Analysis**
- **Export Capabilities**: Analyze data in external tools
- **Error Categorization**: Group failures by error type
- **Batch Context**: Understand which batches had issues

### **Workflow Integration**
- **Seamless Operation**: Works automatically with existing import process
- **No Configuration**: Ready to use out of the box
- **Performance Optimized**: Minimal impact on import operations

---

**🚀 The Failed Customers tab transforms failure monitoring from a manual, error-prone process into an automated, comprehensive visibility solution!**
