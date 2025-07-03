#!/usr/bin/env python3
"""
Test the improved failed customer logic with the ACTUAL response.log data
to verify it would detect all 68 failed customers
"""

import json
import os
from bulk_import_multithreaded import BulkCustomerImporter

def test_with_real_response_data():
    """Test with the actual response.log data"""
    
    print("🧪 TESTING WITH REAL RESPONSE.LOG DATA")
    print("=" * 50)
    
    if not os.path.exists("response.log"):
        print("❌ response.log file not found!")
        return
    
    # Read the actual response data
    print("📖 Reading response.log...")
    with open("response.log", 'r', encoding='utf-8') as f:
        response_content = f.read()
    
    print(f"✅ Loaded response.log ({len(response_content)} characters)")
    
    # Create importer instance
    importer = BulkCustomerImporter(
        api_url="https://test.com/api",
        auth_token="test_token",
        gk_passport="test_passport",
        batch_size=100,
        max_workers=1,
        failed_customers_file="test_real_response_failed.json"
    )
    
    print(f"🔧 Created importer instance")
    
    # Test parsing the actual response content
    print(f"\n🔍 TESTING FAILED CUSTOMER PARSING WITH REAL DATA:")
    print(f"   Expected: 68 failed customers")
    
    # Try to parse as JSON first
    try:
        response_json = json.loads(response_content)
        print(f"✅ Response parsed as JSON successfully")
    except:
        # If not valid JSON, create a wrapper
        response_json = {"raw_response": response_content}
        print(f"⚠️ Response is not valid JSON, using raw text parsing")
    
    # Create dummy batch data (we don't need real batch data for this test)
    dummy_batch = [{"customerId": f"6000000{i:04d}", "firstName": "Test", "lastName": f"Customer{i}"} for i in range(100)]
    
    # Parse for failures
    print(f"\n🚨 PARSING FOR FAILED CUSTOMERS...")
    failed_customers = importer._parse_api_response_for_failures(response_json, dummy_batch)
    
    print(f"\n📊 RESULTS:")
    print(f"   - Failed customers detected: {len(failed_customers)}")
    print(f"   - Expected: 68")
    print(f"   - Match: {'✅ YES' if len(failed_customers) == 68 else '❌ NO'}")
    
    if failed_customers:
        print(f"\n📋 FIRST 10 DETECTED FAILURES:")
        for i, fc in enumerate(failed_customers[:10], 1):
            print(f"   {i:2d}. ID: {fc['customerId']} | Username: {fc['username']}")
            print(f"       Error: {fc['error']}")
            print(f"       Method: {fc.get('detectionMethod', 'Unknown')}")
        
        if len(failed_customers) > 10:
            print(f"   ... and {len(failed_customers) - 10} more")
        
        # Test saving
        print(f"\n💾 TESTING SAVE FUNCTIONALITY:")
        importer._save_failed_customers(failed_customers)
        
        if os.path.exists(importer.failed_customers_file):
            print(f"✅ Failed customers saved to: {importer.failed_customers_file}")
            
            # Verify file content
            with open(importer.failed_customers_file, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            print(f"✅ Verified: {len(saved_data)} customers in saved file")
            
            # Show summary
            summary = importer.get_failed_customers_summary()
            print(f"\n📊 SUMMARY:")
            print(f"   - Total Failed: {summary['total_failed']}")
            print(f"   - File Location: {summary['failed_customers_file']}")
            print(f"   - File Size: {os.path.getsize(summary['failed_customers_file'])} bytes")
            
        else:
            print(f"❌ Failed to save failed customers file")
    else:
        print(f"❌ NO FAILED CUSTOMERS DETECTED!")
        print(f"   This means the logic needs more work!")
    
    # Cleanup
    if os.path.exists(importer.failed_customers_file):
        os.remove(importer.failed_customers_file)
        print(f"🧹 Cleaned up test file")
    
    # Clean up directory if empty
    if os.path.exists("failed_customers") and not os.listdir("failed_customers"):
        os.rmdir("failed_customers")
        print(f"🧹 Cleaned up empty directory")
    
    print(f"\n" + "=" * 50)
    if len(failed_customers) == 68:
        print(f"🎯 SUCCESS: The improved logic WOULD detect all 68 failed customers!")
        print(f"   ✅ Ready for production use")
    else:
        print(f"🚨 ISSUE: Logic detected {len(failed_customers)} instead of 68")
        print(f"   ❌ Needs more improvement")
    print("=" * 50)
    
    return len(failed_customers) == 68

if __name__ == "__main__":
    test_with_real_response_data()
