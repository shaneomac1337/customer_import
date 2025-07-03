# 🔐 Automatic Authentication Guide

## Overview

The Bulk Customer Import tool now supports **automatic token refresh** functionality, eliminating the need for manual token management during long-running imports. This feature automatically handles OAuth2 authentication and refreshes tokens before they expire.

## 🆕 New Features

### 1. **Automatic Token Refresh**
- Tokens are automatically refreshed every **3600 seconds (1 hour)**
- Refresh happens **5 minutes before expiration** for safety
- No manual intervention required during long imports
- Thread-safe token management for multithreaded operations

### 2. **Dual Authentication Modes**
- **Manual Token Mode**: Traditional method using pre-obtained tokens
- **Automatic Mode**: Username/password authentication with auto-refresh

### 3. **Enhanced GUI Interface**
- Radio button selection for authentication mode
- Separate input fields for each mode
- Real-time authentication testing
- Token status information display

## 🚀 How to Use

### Automatic Authentication Mode (Recommended)

1. **Launch the Application**
   ```
   BulkCustomerImport.exe
   ```

2. **Select Authentication Mode**
   - Choose "Automatic (Username/Password)" radio button
   - The interface will switch to show username/password fields

3. **Enter Credentials**
   - **Username**: `coop_sweden` (pre-filled)
   - **Password**: `coopsverige123` (pre-filled)
   - **GK-Passport**: Your GK-Passport token

4. **Test Authentication**
   - Click "Test Authentication" button
   - Verify successful connection and token retrieval

5. **Run Import**
   - Select your customer files
   - Configure batch settings
   - Start the import process
   - Tokens will refresh automatically as needed

### Manual Token Mode (Legacy)

1. **Select Authentication Mode**
   - Choose "Manual Token" radio button
   - Interface shows traditional token input fields

2. **Enter Credentials**
   - **Auth Token**: Your Bearer token
   - **GK-Passport**: Your GK-Passport token

3. **Proceed with Import**
   - Note: Manual tokens may expire during long imports

## 🔧 Technical Details

### Authentication Manager
- **Class**: `AuthenticationManager`
- **Token Endpoint**: `https://prod.cse.cloud4retail.co/auth-service/tenants/001/oauth/token`
- **Grant Type**: OAuth2 Password Grant
- **Token Validity**: 3600 seconds (1 hour)
- **Refresh Buffer**: 300 seconds (5 minutes before expiry)

### API Request Format
```bash
curl --request POST \
  --url https://prod.cse.cloud4retail.co/auth-service/tenants/001/oauth/token \
  --header 'Authorization: Basic bGF1bmNocGFkOk5iV285MWxES3Y4N1JBQXdOUHJF' \
  --header 'content-type: application/x-www-form-urlencoded' \
  --data username=coop_sweden \
  --data password=coopsverige123 \
  --data grant_type=password
```

### Token Refresh Logic
1. **Initial Token**: Obtained when authentication manager is created
2. **Expiry Check**: Before each API request, check if token expires within 5 minutes
3. **Automatic Refresh**: If needed, request new token using stored credentials
4. **Thread Safety**: All token operations are protected with threading locks
5. **Error Handling**: Failed refresh attempts are logged and reported

## 📊 Benefits

### For Long-Running Imports
- **No Manual Intervention**: Tokens refresh automatically
- **Uninterrupted Processing**: Imports continue seamlessly
- **Error Reduction**: Eliminates authentication-related failures
- **Time Savings**: No need to monitor token expiration

### For Batch Processing
- **Parallel Safety**: Thread-safe token management
- **Consistent Authentication**: All threads use fresh tokens
- **Automatic Retry**: Failed authentication triggers immediate refresh
- **Comprehensive Logging**: All authentication events are logged

## 🛠️ Configuration Options

### Default Settings
```python
# Authentication Manager Settings
username = "coop_sweden"
password = "coopsverige123"
token_validity = 3600  # seconds
refresh_buffer = 300   # seconds (5 minutes)
```

### Customization
- All settings can be modified in the GUI
- Credentials are stored securely during session
- No persistent storage of sensitive information

## 🔍 Testing & Validation

### Authentication Test
- Click "Test Authentication" in the GUI
- Verifies credential validity
- Shows token preview and expiration time
- Displays authentication mode and status

### Import Validation
- Authentication is tested before import starts
- Real-time token status monitoring
- Automatic retry on authentication failures
- Comprehensive error reporting

## 📝 Logging & Monitoring

### Authentication Events
```
🔄 Refreshing authentication token...
✅ Token refreshed successfully. Expires at: 2025-07-03 14:46:28
❌ Authentication failed for batch 5: Token refresh failed
```

### Token Information
- Token preview (first 20 characters)
- Expiration timestamp
- Time until next refresh
- Authentication mode status

## 🚨 Error Handling

### Common Issues
1. **Network Connectivity**: Timeout errors when reaching auth endpoint
2. **Invalid Credentials**: Wrong username/password combination
3. **Token Expiry**: Automatic refresh handles this transparently
4. **API Limits**: Rate limiting protection built-in

### Error Recovery
- Automatic retry on network failures
- Graceful fallback to manual mode if needed
- Comprehensive error logging
- User-friendly error messages

## 📦 File Structure

```
BulkCustomerImport/
├── BulkCustomerImport.exe          # Main executable
├── auth_manager.py                 # Authentication manager
├── bulk_import_multithreaded.py    # Enhanced importer
├── bulk_import_gui.py              # Updated GUI
└── AUTOMATIC_AUTHENTICATION_GUIDE.md
```

## 🔄 Migration from Manual Mode

### Existing Users
1. **No Breaking Changes**: Manual mode still fully supported
2. **Gradual Migration**: Switch to automatic mode when ready
3. **Same Interface**: Familiar GUI with enhanced options
4. **Backward Compatibility**: All existing features preserved

### Recommended Approach
1. Test automatic authentication with small batches
2. Verify token refresh during longer operations
3. Monitor logs for authentication events
4. Switch to automatic mode for production use

## 🎯 Best Practices

### Security
- Never hardcode credentials in scripts
- Use GUI input fields for sensitive data
- Monitor authentication logs regularly
- Test connectivity before large imports

### Performance
- Use automatic mode for imports > 1 hour
- Monitor token refresh frequency
- Adjust batch sizes based on processing time
- Leverage parallel processing capabilities

### Reliability
- Always test authentication before imports
- Monitor network connectivity
- Use retry functionality for failed batches
- Keep comprehensive logs for troubleshooting

---

**Note**: This feature requires network connectivity to the authentication endpoint. Ensure your environment can reach `prod.cse.cloud4retail.co` on port 443.
