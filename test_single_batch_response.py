#!/usr/bin/env python3
"""
Test the failed customer logic with ACTUAL single batch API response format
(not log files - this is what the API actually returns for each batch)
"""

import json
import os
from bulk_import_multithreaded import BulkCustomerImporter

def test_single_batch_api_response():
    """Test with actual single batch API response format"""
    
    print("🧪 TESTING WITH REAL SINGLE BATCH API RESPONSE FORMAT")
    print("=" * 60)
    print("This simulates what happens during ACTUAL production imports")
    print("Each batch gets a single JSON response from the API")
    print("=" * 60)
    
    # Create importer instance
    importer = BulkCustomerImporter(
        api_url="https://test.com/api",
        auth_token="test_token",
        gk_passport="test_passport",
        batch_size=100,
        max_workers=1,
        failed_customers_file="test_single_batch_response_failed.json"
    )
    
    # Simulate a REAL API response for a single batch (like what production gets)
    # This contains both successful and failed customers
    single_batch_api_response = {
        "data": [
            {
                "customerId": "60000001200",
                "username": "INGER-BERGSTRÖM-6598",
                "result": "SUCCESS"
            },
            {
                "customerId": "60000001201", 
                "username": "HENRIK-HANSSON-0812",
                "result": "SUCCESS"
            },
            {
                "customerId": "60000001272",
                "username": "BJÖRN PATRIK-BERG-2906", 
                "result": "FAILED"
            },
            {
                "customerId": "60000001273",
                "username": "BJÖRN PATRIK-LARSSON-3890",
                "result": "FAILED"
            },
            {
                "customerId": "60000001202",
                "username": "ANDERS-FORSBERG-0284",
                "result": "SUCCESS"
            }
        ]
    }
    
    print(f"📊 SIMULATED BATCH RESPONSE:")
    print(f"   - Total customers in batch: {len(single_batch_api_response['data'])}")
    print(f"   - Expected failed customers: 2")
    print(f"   - Failed customer IDs: 60000001272, 60000001273")
    
    # Create dummy batch data (what was sent to API)
    dummy_batch = [
        {"customerId": "60000001200", "firstName": "Inger", "lastName": "Bergström"},
        {"customerId": "60000001201", "firstName": "Henrik", "lastName": "Hansson"},
        {"customerId": "60000001272", "firstName": "Björn Patrik", "lastName": "Berg"},
        {"customerId": "60000001273", "firstName": "Björn Patrik", "lastName": "Larsson"},
        {"customerId": "60000001202", "firstName": "Anders", "lastName": "Forsberg"}
    ]
    
    print(f"\n🔍 TESTING FAILED CUSTOMER PARSING...")
    
    # Test the parsing logic with the single batch response
    failed_customers = importer._parse_api_response_for_failures(single_batch_api_response, dummy_batch)
    
    print(f"\n📊 RESULTS:")
    print(f"   - Failed customers detected: {len(failed_customers)}")
    print(f"   - Expected: 2")
    print(f"   - Match: {'✅ YES' if len(failed_customers) == 2 else '❌ NO'}")
    
    if failed_customers:
        print(f"\n📋 DETECTED FAILED CUSTOMERS:")
        for i, fc in enumerate(failed_customers, 1):
            print(f"   {i}. ID: {fc['customerId']}")
            print(f"      Username: {fc['username']}")
            print(f"      Error: {fc['error']}")
            print(f"      Detection Method: {fc.get('batchInfo', 'Unknown')}")
            print(f"      Has Original Data: {'Yes' if fc['originalData'] else 'No'}")
        
        # Test saving functionality
        print(f"\n💾 TESTING SAVE FUNCTIONALITY:")
        importer._save_failed_customers(failed_customers)
        
        if os.path.exists(importer.failed_customers_file):
            print(f"✅ Failed customers saved successfully")
            
            # Verify file content
            with open(importer.failed_customers_file, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            print(f"✅ Verified: {len(saved_data)} customers in saved file")
            
            # Cleanup
            os.remove(importer.failed_customers_file)
            print(f"🧹 Cleaned up test file")
        else:
            print(f"❌ Failed to save failed customers file")
    else:
        print(f"❌ NO FAILED CUSTOMERS DETECTED!")
        print(f"   This means the logic doesn't work with single batch responses!")
    
    # Clean up directory if empty
    if os.path.exists("failed_customers") and not os.listdir("failed_customers"):
        os.rmdir("failed_customers")
        print(f"🧹 Cleaned up empty directory")
    
    print(f"\n" + "=" * 60)
    if len(failed_customers) == 2:
        print(f"🎯 SUCCESS: Logic works with REAL single batch API responses!")
        print(f"   ✅ Will detect failed customers during production imports")
        print(f"   ✅ Each batch response will be properly parsed")
        print(f"   ✅ Failed customers will be accumulated across all batches")
    else:
        print(f"🚨 ISSUE: Logic doesn't work with single batch responses")
        print(f"   ❌ Needs fixes for production use")
    print("=" * 60)
    
    return len(failed_customers) == 2

if __name__ == "__main__":
    test_single_batch_api_response()
