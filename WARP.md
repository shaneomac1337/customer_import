# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

A bulk customer import system for the CSE Customer Profile Service. The system includes a multithreaded GUI application that handles customer data import with automatic authentication, retry mechanisms, and comprehensive failure tracking. The project supports both development mode (Python) and portable standalone executables.

## Architecture

### Core Components

**Three-Tier Import Architecture:**
1. **GUI Layer** (`bulk_import_gui.py`) - Tkinter-based interface with tabbed navigation
2. **Import Engine** (`bulk_import_multithreaded.py`) - ThreadPoolExecutor-based batch processor
3. **Auth Layer** (`auth_manager.py`) - Automatic OAuth2 token management with refresh

**Key Design Patterns:**
- **Lazy Batch Loading**: Files loaded on-demand to minimize memory footprint with large datasets
- **Automatic Token Refresh**: Tokens refresh 50 minutes before expiry (default 3600s lifetime)
- **Single Failures Structure**: Failed customers automatically organized by failure reason (CONFLICT/FAILED/ERROR/UNKNOWN)

### Data Flow

```
JSON Files → Load/Parse → Create Batches → Thread Pool → API Calls → Response Parser → Success/Failure Tracking
                                              ↓
                                      Auth Manager (auto-refresh)
```

### Authentication Modes

The system supports two authentication modes:
- **Manual Token Mode**: User provides Bearer token directly (legacy)
- **Automatic Mode** (default): Username/password OAuth2 with automatic token refresh

**Critical Auth Details:**
- GK-Passport header is hardcoded: `1.1:CiMg46zV+88yKOOMxZPwMjIDMDAxOg5idXNpbmVzc1VuaXRJZBIKCAISBnVzZXJJZBoSCAIaCGNsaWVudElkIgR3c0lkIhoaGGI6Y3VzdC5jdXN0b21lci5pbXBvcnRlcg==`
- Default credentials: username=`coop_sweden`, password=`coopsverige123`
- Token refresh buffer: 3000 seconds (tokens refresh every ~10 minutes for 1-hour tokens)

## Development Commands

### Run the GUI Application
```powershell
python bulk_import_gui.py
```

### Quick Launch (Windows)
```powershell
# Launch GUI directly
.\Launch_Bulk_Import_GUI.bat

# Launch with pre-loaded test data (1000 customers)
.\Load_1000_Customers_GUI.bat
```

### Build Standalone Executable
```powershell
# Automated build process (installs dependencies and builds)
.\Build_EXE.bat

# Or manual build
python build_exe.py
```

**Build Output:**
- Creates `BulkCustomerImport_Portable/` directory with standalone `.exe`
- No Python installation required on target machines
- PyInstaller creates single-file executable with all dependencies bundled

### Data Utilities

**Convert CSV to Import Format:**
```powershell
python scripts\shx_csv_to_import.py
```
Input: `SHX_TestData_MemberHousehold_Krokek_4 more.csv` (semicolon-delimited)  
Output: `batches_to_retry/batch_from_shx.json`

**Split Large JSON Files:**
```powershell
python split_large_json.py
```
Creates individual customer files (1 per JSON) from large batch files.  
Output: `individual_customers_YYYYMMDD_HHMMSS/customer_NNNNN.json`

### Testing

**No formal test framework** - Manual testing scripts in `/tests`:
```powershell
# Validate customer data structure
python tests\validate_1000_customers.py

# Analyze failure patterns by batch
python tests\analyze_failed_customers_by_batch.py

# Extract all failed customers
python tests\extract_all_failed_customers.py

# Test single failures structure
python test_single_failures_fix.py
```

## API Integration

**Endpoint:** `https://prod.cse.cloud4retail.co/customer-profile-service/tenants/001/services/rest/customers-import/v1/customers`

**Authentication Endpoint:** `https://prod.cse.cloud4retail.co/auth-service/tenants/001/oauth/token`

**Customer Data Format:**
```json
{
  "data": [
    {
      "changeType": "CREATE",
      "type": "PERSON",
      "person": {
        "customerId": "string",
        "firstName": "string",
        "lastName": "string",
        "statisticalUseAllowed": true,
        "declarationAvailable": true,
        "status": "ACTIVE",
        "customerCards": [
          {"number": "string", "type": "MAIN_CARD", "scope": "GLOBAL"}
        ]
      }
    }
  ]
}
```

## Configuration & Settings

### Default Import Settings
- **Batch Size**: 70 customers per batch
- **Worker Threads**: 3-5 concurrent threads (configurable 1-10)
- **Request Delay**: 0.5 seconds between requests
- **Max Retries**: 3 attempts for failed batches

### Performance Presets (in GUI)
- **Conservative (Safe)**: 50 batch, 3 workers, 1.0s delay, 3 retries
- **Balanced (Recommended)**: 70 batch, 5 workers, 0.5s delay, 3 retries
- **Aggressive (Fast)**: 100 batch, 10 workers, 0.1s delay, 5 retries

### Environment Setup

**Python Version**: 3.7+

**Install Dependencies:**
```powershell
pip install -r requirements.txt
```

**Core Dependencies:**
- `requests>=2.25.0` - HTTP client
- `urllib3>=1.26.0` - HTTP utilities
- `pyinstaller>=5.0.0` - Executable builder
- `tkinter` (built-in) - GUI framework

**Virtual Environment (Recommended):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## File Structure and Output

### Key Directories
- `/docu` - Comprehensive documentation (guides for GUI, auth, retry, etc.)
- `/tests` - Manual test scripts and utilities
- `/scripts` - Data conversion utilities (CSV to JSON)
- `/failed_customers` - All failed import data
- `/failed_customers/single_failures` - Individual failed customers organized by reason
- `/BulkCustomerImport_Portable` - Standalone executable distribution (gitignored)

### Failed Customer Structure

**Auto-generated on first failure:**
```
failed_customers/
├── single_failures/
│   ├── CONFLICT/          # Duplicate/conflict failures
│   │   ├── customer_*.json
│   │   └── _SUMMARY_*.json
│   ├── FAILED/            # Validation/business logic failures
│   ├── ERROR/             # System errors
│   ├── UNKNOWN/           # Unrecognized failures
│   └── README.md
└── failed_customers.json  # Consolidated failure log
```

**Each customer file is in direct import format** - can be retried immediately.

## Common Patterns

### Adding New Batch Processing Logic

When modifying the import engine:
1. Changes go in `bulk_import_multithreaded.py`
2. Use `self.logger` for all logging (UTF-8 configured)
3. Failed customers tracked in `self.failed_customers` list (thread-safe with lock)
4. Progress updates via `self.progress_callback(message)` (queued to GUI)

### Modifying GUI Behavior

GUI uses multi-tab structure:
- **Configuration Tab**: API settings, auth mode selection
- **Files Tab**: File selection and customer count display
- **Import Tab**: Start/stop controls, live progress
- **Results Tab**: Real-time log display
- **API Responses Tab**: Raw API response viewer
- **Failed Customers Tab**: Failure analysis and retry generation

**Threading Pattern**: GUI updates via `queue.Queue` to avoid cross-thread tkinter issues

### Authentication Modifications

`auth_manager.py` handles OAuth2 flow:
- Token stored in `self.current_token`
- Expiry tracked in `self.token_expires_at`
- Automatic refresh triggered by `_needs_refresh()` check
- Thread-safe with `self.token_lock`

**To change auth endpoint or credentials**: Modify constructor defaults in `AuthenticationManager.__init__()`

## Important Notes

### Memory Management
- Files loaded on-demand (lazy loading) for large datasets
- Each batch processed independently
- Garbage collection triggered between batches (`gc.collect()`)

### Sensitive Data
**Never commit these files** (see `.gitignore`):
- `config.json` - Any configuration with credentials
- `customers_*.json` - Customer PII data
- `*.log` - May contain sensitive information
- Build artifacts (`build/`, `dist/`, `*_Portable/`)

### API Response Logging
All API responses saved to `/api_responses/` directory:
- Format: `api_response_YYYYMMDD_HHMMSS.json`
- Contains both successful and failed batch responses
- Used for debugging and failure analysis

### Failure Recovery

**Retry Workflow:**
1. Failed customers auto-saved to `/failed_customers/single_failures/{REASON}/`
2. Each customer file can be directly imported (no modification needed)
3. Summary files (`_SUMMARY_*.json`) provide failure overview
4. Load individual files or create new batch for retry

**Batch Retry Creation:**
Use GUI "Export Failed Customers" → Creates retry batch in proper format

## Documentation

Comprehensive guides available in `/docu`:
- `BULK_IMPORT_SUMMARY.md` - Complete system overview
- `README_GUI.md` - GUI usage instructions
- `FAILED_CUSTOMERS_TAB_GUIDE.md` - Failure management
- `RETRY_FUNCTIONALITY_GUIDE.md` - Retry system
- `AUTOMATIC_AUTHENTICATION_GUIDE.md` - Auth setup and troubleshooting
- `BUILD_INSTRUCTIONS.md` - Creating executables

Main README: `/README.md` - Quick start and project overview
