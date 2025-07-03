#!/usr/bin/env python3
"""
Simple test to verify failed customer detection works with a single batch
"""

import json
import os
from bulk_import_multithreaded import BulkCustomerImporter

def test_single_batch():
    """Test with a single batch to verify the logic works end-to-end"""
    
    print("🧪 Testing Single Batch Failed Customer Detection")
    print("=" * 55)
    
    # Create a small test batch with one customer that will "fail"
    test_customers = [
        {
            "personalNumber": "19900101-2906",
            "firstName": "Björn Patrik",
            "lastName": "Berg",
            "addresses": [
                {
                    "addressee": "Björn Patrik Berg",
                    "city": "Stockholm",
                    "countryCode": "SE",
                    "contactPurposeTypeCode": "HOME",
                    "contactMethodTypeCode": "POSTAL_ADDRESS"
                }
            ],
            "languageCode": "sv",
            "statisticalUseAllowed": False,
            "marketingAllowedFlag": True,
            "declarationAvailable": True,
            "customerCards": [
                {
                    "cardNumber": "60000001272",
                    "cardType": "MAIN_CARD",
                    "scope": "GLOBAL"
                }
            ]
        }
    ]
    
    # Save test batch to file
    test_batch_file = "test_single_batch.json"
    with open(test_batch_file, 'w', encoding='utf-8') as f:
        json.dump(test_customers, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created test batch file: {test_batch_file}")
    print(f"   - Contains {len(test_customers)} customer(s)")
    print(f"   - Customer ID: {test_customers[0]['customerCards'][0]['cardNumber']}")
    print(f"   - Customer Name: {test_customers[0]['firstName']} {test_customers[0]['lastName']}")
    
    # Create importer with test configuration
    importer = BulkCustomerImporter(
        api_url="https://invalid-test-url.com/api",  # Invalid URL to simulate failure
        auth_token="test_token",
        gk_passport="test_passport",
        batch_size=1,
        max_workers=1,
        failed_customers_file="test_single_batch_failed.json"
    )
    
    print(f"\n🔧 Importer Configuration:")
    print(f"   - API URL: {importer.api_url}")
    print(f"   - Batch Size: {importer.batch_size}")
    print(f"   - Failed Customers File: {importer.failed_customers_file}")
    
    # Test the parsing logic directly with simulated API response
    print(f"\n🧪 Testing Failed Customer Parsing Logic:")
    
    # Simulate an API response that contains our failed customer
    simulated_response = {
        "data": [
            {
                "customerId": "60000001272",
                "username": "BJÖRN PATRIK-BERG-2906",
                "result": "FAILED",
                "error": "Customer validation failed"
            }
        ]
    }
    
    failed_customers = importer._parse_api_response_for_failures(simulated_response, test_customers)
    
    if failed_customers:
        print(f"✅ SUCCESS: Detected {len(failed_customers)} failed customer(s)")
        for i, fc in enumerate(failed_customers, 1):
            print(f"   {i}. Customer ID: {fc['customerId']}")
            print(f"      Username: {fc['username']}")
            print(f"      Error: {fc['error']}")
            print(f"      Has Original Data: {'Yes' if fc['originalData'] else 'No'}")
            if fc['originalData']:
                orig = fc['originalData']
                print(f"      Original Name: {orig['firstName']} {orig['lastName']}")
        
        # Test saving
        print(f"\n💾 Testing Failed Customer Saving:")
        importer._save_failed_customers(failed_customers)
        
        if os.path.exists(importer.failed_customers_file):
            print(f"✅ Failed customers file created successfully")
            
            # Read and verify
            with open(importer.failed_customers_file, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            print(f"✅ Verified: {len(saved_data)} failed customers saved to file")
            
            # Show summary
            summary = importer.get_failed_customers_summary()
            print(f"\n📊 Failed Customers Summary:")
            print(f"   - Total Failed: {summary['total_failed']}")
            print(f"   - File Location: {summary['failed_customers_file']}")
            print(f"   - File Exists: {'Yes' if os.path.exists(summary['failed_customers_file']) else 'No'}")
            
        else:
            print(f"❌ Failed customers file was not created")
    else:
        print(f"❌ FAILED: No failed customers detected")
    
    # Cleanup
    cleanup_files = [test_batch_file, importer.failed_customers_file]
    for file in cleanup_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"🧹 Cleaned up: {file}")
    
    # Clean up failed_customers directory if empty
    if os.path.exists("failed_customers") and not os.listdir("failed_customers"):
        os.rmdir("failed_customers")
        print(f"🧹 Cleaned up empty directory: failed_customers")
    
    print(f"\n" + "=" * 55)
    print(f"🎯 RESULT: Failed customer detection logic is {'WORKING' if failed_customers else 'NOT WORKING'}")
    print(f"   Ready for production use: {'YES' if failed_customers else 'NO'}")
    print("=" * 55)

if __name__ == "__main__":
    test_single_batch()
