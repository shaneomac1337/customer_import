# Single Failures Directory Structure

This directory will contain individual failed customers organized by failure reason when imports have failures.

## Directory Structure (Created Automatically):
```
single_failures/
├── CONFLICT/          # Customers that failed due to conflicts (duplicates, etc.)
├── FAILED/            # Customers that failed due to validation or business logic
├── ERROR/             # Customers that failed due to system errors
└── UNKNOWN/           # Customers with unrecognized failure reasons
```

**Note**: Directories are created automatically when customers fail during import.

## File Types:
- **customer_*.json** - Individual customer files with complete data and retry instructions
- **_SUMMARY_*.json** - Summary files with overview of each failure type

## How to Use:
1. **Individual Retry**: Use any customer_*.json file to retry a single customer
2. **Batch Retry**: Collect multiple customers and create a batch for retry
3. **Analysis**: Use summary files to understand failure patterns

## File Format:
Each customer file is in **clean import format** (identical to retry batches):
```json
{
  "data": [
    {
      // Complete customer data ready for import
    }
  ]
}
```

**Ready for Direct Import**: Just drag and drop any customer_*.json file into the import tool!

## Auto-Generated:
These folders and files are automatically created when customers fail during import.
The structure helps organize failures by type for easier handling and retry.
