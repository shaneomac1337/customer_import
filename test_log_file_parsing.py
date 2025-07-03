#!/usr/bin/env python3
"""
Test parsing the response.log file directly to extract all 68 failed customers
"""

import json
import re
import os
from datetime import datetime
from bulk_import_multithreaded import BulkCustomerImporter

def test_log_file_parsing():
    """Test parsing the response.log file as a log file (not single JSON)"""
    
    print("🧪 TESTING LOG FILE PARSING FOR FAILED CUSTOMERS")
    print("=" * 60)
    
    if not os.path.exists("response.log"):
        print("❌ response.log file not found!")
        return
    
    # Read the log file
    print("📖 Reading response.log...")
    with open("response.log", 'r', encoding='utf-8') as f:
        log_content = f.read()
    
    print(f"✅ Loaded response.log ({len(log_content)} characters)")
    
    # Create importer instance
    importer = BulkCustomerImporter(
        api_url="https://test.com/api",
        auth_token="test_token",
        gk_passport="test_passport",
        batch_size=100,
        max_workers=1,
        failed_customers_file="test_log_parsing_failed.json"
    )
    
    # Create dummy batch data (we don't need real batch data for this test)
    dummy_batch = [{"customerId": f"6000000{i:04d}", "firstName": "Test", "lastName": f"Customer{i}"} for i in range(100)]
    
    print(f"\n🔍 METHOD 1: Testing with log content as raw response...")
    
    # Test 1: Pass the entire log content as raw response
    failed_customers_1 = importer._parse_api_response_for_failures(log_content, dummy_batch)
    
    print(f"📊 METHOD 1 RESULTS:")
    print(f"   - Failed customers detected: {len(failed_customers_1)}")
    print(f"   - Expected: 68")
    print(f"   - Match: {'✅ YES' if len(failed_customers_1) == 68 else '❌ NO'}")
    
    if failed_customers_1:
        print(f"\n📋 FIRST 5 DETECTED FAILURES (METHOD 1):")
        for i, fc in enumerate(failed_customers_1[:5], 1):
            print(f"   {i}. ID: {fc['customerId']} | Username: {fc['username']}")
    
    print(f"\n🔍 METHOD 2: Testing with wrapped log content...")
    
    # Test 2: Wrap the log content in a structure
    wrapped_response = {
        "raw_response": log_content,
        "log_file": True
    }
    
    failed_customers_2 = importer._parse_api_response_for_failures(wrapped_response, dummy_batch)
    
    print(f"📊 METHOD 2 RESULTS:")
    print(f"   - Failed customers detected: {len(failed_customers_2)}")
    print(f"   - Expected: 68")
    print(f"   - Match: {'✅ YES' if len(failed_customers_2) == 68 else '❌ NO'}")
    
    if failed_customers_2:
        print(f"\n📋 FIRST 5 DETECTED FAILURES (METHOD 2):")
        for i, fc in enumerate(failed_customers_2[:5], 1):
            print(f"   {i}. ID: {fc['customerId']} | Username: {fc['username']}")
    
    print(f"\n🔍 METHOD 3: Direct regex on log content...")
    
    # Test 3: Direct regex extraction (what should work)
    failed_pattern = r'"customerId":\s*"([^"]+)"[^}]*"username":\s*"([^"]+)"[^}]*"result":\s*"FAILED"'
    matches = re.findall(failed_pattern, log_content)
    
    print(f"📊 METHOD 3 RESULTS (Direct Regex):")
    print(f"   - Failed customers detected: {len(matches)}")
    print(f"   - Expected: 68")
    print(f"   - Match: {'✅ YES' if len(matches) == 68 else '❌ NO'}")
    
    if matches:
        print(f"\n📋 FIRST 5 DETECTED FAILURES (METHOD 3):")
        for i, (customer_id, username) in enumerate(matches[:5], 1):
            print(f"   {i}. ID: {customer_id} | Username: {username}")
    
    # Test which method works best
    best_method = None
    best_count = 0
    
    if len(failed_customers_1) == 68:
        best_method = "METHOD 1 (Raw log content)"
        best_count = len(failed_customers_1)
    elif len(failed_customers_2) == 68:
        best_method = "METHOD 2 (Wrapped log content)"
        best_count = len(failed_customers_2)
    elif len(matches) == 68:
        best_method = "METHOD 3 (Direct regex)"
        best_count = len(matches)
    
    print(f"\n" + "=" * 60)
    if best_method:
        print(f"🎯 SUCCESS: {best_method} detected all 68 failed customers!")
        print(f"   ✅ The parsing logic CAN extract all failures")
        
        # Test saving if we have failed customers
        if failed_customers_1 and len(failed_customers_1) == 68:
            test_customers = failed_customers_1
        elif failed_customers_2 and len(failed_customers_2) == 68:
            test_customers = failed_customers_2
        else:
            # Convert regex matches to failed customer format
            test_customers = []
            for customer_id, username in matches:
                test_customers.append({
                    'customerId': customer_id,
                    'username': username,
                    'result': 'FAILED',
                    'error': 'Extracted from log file',
                    'timestamp': datetime.now().isoformat(),
                    'originalData': None
                })
        
        if test_customers:
            print(f"\n💾 Testing save functionality...")
            importer._save_failed_customers(test_customers)
            
            if os.path.exists(importer.failed_customers_file):
                print(f"✅ Successfully saved {len(test_customers)} failed customers")
                
                # Cleanup
                os.remove(importer.failed_customers_file)
                print(f"🧹 Cleaned up test file")
            
    else:
        print(f"🚨 ISSUE: None of the methods detected all 68 failed customers")
        print(f"   - Method 1: {len(failed_customers_1)} customers")
        print(f"   - Method 2: {len(failed_customers_2)} customers") 
        print(f"   - Method 3: {len(matches)} customers")
        print(f"   ❌ Logic needs more improvement")
    
    # Clean up directory if empty
    if os.path.exists("failed_customers") and not os.listdir("failed_customers"):
        os.rmdir("failed_customers")
        print(f"🧹 Cleaned up empty directory")
    
    print("=" * 60)
    
    return best_method is not None

if __name__ == "__main__":
    test_log_file_parsing()
