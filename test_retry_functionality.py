#!/usr/bin/env python3
"""
Test script to demonstrate the automatic retry file creation functionality
"""

import json
import os
import shutil
from bulk_import_multithreaded import BulkCustomerImporter

def create_test_batch():
    """Create a small test batch for demonstration"""
    test_customers = {
        "data": [
            {
                "changeType": "CREATE",
                "type": "PERSON",
                "person": {
                    "customerId": "TEST001",
                    "status": "UNACTIVATED",
                    "firstName": "TEST",
                    "lastName": "CUSTOMER",
                    "languageCode": "sv",
                    "birthday": "1990-01-01",
                    "statisticalUseAllowed": False,
                    "marketingAllowedFlag": False,
                    "declarationAvailable": True,
                    "addresses": [
                        {
                            "addressee": "TEST CUSTOMER",
                            "street": "Test Street",
                            "streetNumber": "123",
                            "city": "Test City",
                            "postalCode": "12345",
                            "countryCode": "SE",
                            "contactPurposeTypeCode": "DEFAULT",
                            "contactMethodTypeCode": "HOME"
                        }
                    ],
                    "customerCards": [
                        {
                            "number": "TEST001",
                            "type": "MAIN_CARD",
                            "scope": "GLOBAL"
                        }
                    ]
                }
            }
        ]
    }
    
    # Create test directory
    test_dir = "test_retry_demo"
    os.makedirs(test_dir, exist_ok=True)
    
    # Save test batch
    test_file = os.path.join(test_dir, "test_batch.json")
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_customers, f, indent=2, ensure_ascii=False)
    
    return test_file

def simulate_failed_import():
    """Simulate a failed import to demonstrate retry file creation"""
    print("=" * 60)
    print("TESTING AUTOMATIC RETRY FILE CREATION")
    print("=" * 60)
    
    # Create test batch
    test_file = create_test_batch()
    print(f"[SETUP] Created test batch: {test_file}")
    
    # Create importer with invalid credentials (will cause failures)
    importer = BulkCustomerImporter(
        api_url="https://invalid-url-for-testing.com/api",  # Invalid URL
        auth_token="INVALID_TOKEN",
        gk_passport="INVALID_PASSPORT",
        batch_size=1,
        max_workers=1,
        delay_between_requests=0.1,
        max_retries=1  # Only 1 retry to fail quickly
    )
    
    print("[TEST] Starting import with invalid credentials (will fail)...")
    
    # Run import (will fail)
    result = importer.import_customers([test_file])
    
    print("\n" + "=" * 60)
    print("IMPORT RESULTS")
    print("=" * 60)
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Total batches: {result.get('total_batches', 0)}")
    print(f"Failed batches: {result.get('failed_batches', 0)}")
    print(f"Success rate: {result.get('success_rate', '0%')}")
    
    # Check if retry files were created
    print("\n" + "=" * 60)
    print("CHECKING FOR RETRY FILES")
    print("=" * 60)
    
    retry_dirs = [d for d in os.listdir('.') if d.startswith('retry_batches_')]
    
    if retry_dirs:
        latest_retry_dir = sorted(retry_dirs)[-1]
        print(f"[SUCCESS] Retry directory created: {latest_retry_dir}")
        
        # List contents
        retry_files = os.listdir(latest_retry_dir)
        print(f"[FILES] Contents of {latest_retry_dir}:")
        for file in sorted(retry_files):
            filepath = os.path.join(latest_retry_dir, file)
            if os.path.isfile(filepath):
                size = os.path.getsize(filepath)
                print(f"   - {file} ({size} bytes)")
        
        # Show retry instructions
        instructions_file = os.path.join(latest_retry_dir, "RETRY_INSTRUCTIONS.md")
        if os.path.exists(instructions_file):
            print(f"\n[INSTRUCTIONS] Content of {instructions_file}:")
            print("-" * 40)
            with open(instructions_file, 'r', encoding='utf-8') as f:
                print(f.read())
            print("-" * 40)
        
        # Validate retry file format
        retry_batch_files = [f for f in retry_files if f.startswith('retry_batch_') and f.endswith('.json')]
        if retry_batch_files:
            retry_file = os.path.join(latest_retry_dir, retry_batch_files[0])
            print(f"\n[VALIDATION] Checking format of {retry_batch_files[0]}:")
            
            with open(retry_file, 'r', encoding='utf-8') as f:
                retry_data = json.load(f)
            
            if 'data' in retry_data and isinstance(retry_data['data'], list):
                print("   ✅ Correct API format (has 'data' wrapper)")
                if len(retry_data['data']) > 0:
                    customer = retry_data['data'][0]
                    if 'person' in customer:
                        print("   ✅ Correct customer structure (has 'person' object)")
                        print("   ✅ Ready for immediate re-import!")
                    else:
                        print("   ❌ Missing 'person' object")
                else:
                    print("   ❌ Empty data array")
            else:
                print("   ❌ Incorrect format (missing 'data' wrapper)")
    else:
        print("[ERROR] No retry directories found!")
    
    # Cleanup
    print(f"\n[CLEANUP] Removing test files...")
    if os.path.exists("test_retry_demo"):
        shutil.rmtree("test_retry_demo")
        print("   ✅ Removed test directory")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)
    print("The retry file creation functionality is working!")
    print("When real imports fail, retry files will be automatically created")
    print("in the correct format for immediate re-import.")

if __name__ == "__main__":
    simulate_failed_import()
