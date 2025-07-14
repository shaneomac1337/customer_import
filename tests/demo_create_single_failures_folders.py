#!/usr/bin/env python3
"""
Demo script to create the single_failures folder structure in the real working directory
This demonstrates how the folders will look when customers actually fail during import
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path to import the bulk importer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bulk_import_multithreaded import BulkCustomerImporter

def demo_create_single_failures_folders():
    """Create demo single failures folders in the real working directory"""
    print("🎯 Creating Demo Single Failures Folders")
    print("=" * 50)
    
    # Create test importer (won't actually connect to API)
    importer = BulkCustomerImporter(
        api_url="https://demo.example.com/api",
        auth_token="demo_token",
        batch_size=10,
        max_workers=1,
        use_auto_auth=False
    )
    
    # Create demo failed customers with different failure reasons
    demo_failed_customers = [
        {
            'customerId': 'DEMO_CONFLICT_001',
            'username': 'john.doe.demo',
            'result': 'CONFLICT',
            'error': 'Customer already exists in system',
            'timestamp': datetime.now().isoformat(),
            'originalData': {
                'firstName': 'John',
                'lastName': 'Doe', 
                'email': 'john.doe@demo.com',
                'phone': '+1234567890'
            },
            'batchInfo': 'Demo batch for folder structure'
        },
        {
            'customerId': 'DEMO_CONFLICT_002',
            'username': 'jane.smith.demo',
            'result': 'CONFLICT',
            'error': 'Duplicate username detected',
            'timestamp': datetime.now().isoformat(),
            'originalData': {
                'firstName': 'Jane',
                'lastName': 'Smith',
                'email': 'jane.smith@demo.com',
                'phone': '+1234567891'
            },
            'batchInfo': 'Demo batch for folder structure'
        },
        {
            'customerId': 'DEMO_FAILED_001',
            'username': 'bob.wilson.demo',
            'result': 'FAILED',
            'error': 'Invalid email format provided',
            'timestamp': datetime.now().isoformat(),
            'originalData': {
                'firstName': 'Bob',
                'lastName': 'Wilson',
                'email': 'invalid-email-format',
                'phone': '+1234567892'
            },
            'batchInfo': 'Demo batch for folder structure'
        },
        {
            'customerId': 'DEMO_ERROR_001',
            'username': 'alice.brown.demo',
            'result': 'ERROR',
            'error': 'Database connection timeout during save',
            'timestamp': datetime.now().isoformat(),
            'originalData': {
                'firstName': 'Alice',
                'lastName': 'Brown',
                'email': 'alice.brown@demo.com',
                'phone': '+1234567893'
            },
            'batchInfo': 'Demo batch for folder structure'
        }
    ]
    
    print(f"📝 Creating demo folders with {len(demo_failed_customers)} sample failed customers:")
    for customer in demo_failed_customers:
        print(f"   - {customer['customerId']} ({customer['username']}) - {customer['result']}")
    
    # Use the individual failed customers feature to create the folders
    print(f"\n🔧 Creating single_failures folder structure...")
    importer._save_individual_failed_customers_by_reason(demo_failed_customers)
    
    # Verify the results
    print(f"\n✅ Verifying created folders...")
    
    base_path = "failed_customers/single_failures"
    if os.path.exists(base_path):
        print(f"   📁 Base directory created: {base_path}")
        
        for reason_folder in os.listdir(base_path):
            reason_path = os.path.join(base_path, reason_folder)
            if os.path.isdir(reason_path):
                files = os.listdir(reason_path)
                print(f"   📂 {reason_folder}/ contains {len(files)} files:")
                
                for file in files:
                    if file.startswith('_SUMMARY_'):
                        print(f"      📋 {file}")
                    else:
                        print(f"      📄 {file}")
    else:
        print(f"   ❌ Base directory not found: {base_path}")
        return False
    
    # Create a README file explaining the structure
    readme_path = os.path.join(base_path, "README.md")
    readme_content = """# Single Failures Directory Structure

This directory contains individual failed customers organized by failure reason.

## Directory Structure:
```
single_failures/
├── CONFLICT/          # Customers that failed due to conflicts (duplicates, etc.)
├── FAILED/            # Customers that failed due to validation or business logic
├── ERROR/             # Customers that failed due to system errors
└── UNKNOWN/           # Customers with unrecognized failure reasons
```

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
"""
    
    try:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"   📖 Created README.md with usage instructions")
    except Exception as e:
        print(f"   ⚠️ Could not create README: {e}")
    
    print(f"\n🎉 Demo completed successfully!")
    print(f"   📁 Check the 'failed_customers/single_failures' directory")
    print(f"   📂 You should now see CONFLICT/, FAILED/, ERROR/ folders")
    print(f"   📄 Each folder contains sample customer files and summaries")
    print(f"   📖 README.md explains how to use the structure")
    print(f"\n💡 Note: In real imports, these folders are created automatically")
    print(f"   when customers actually fail with CONFLICT, FAILED, or ERROR status.")
    
    return True

if __name__ == "__main__":
    success = demo_create_single_failures_folders()
    sys.exit(0 if success else 1)
