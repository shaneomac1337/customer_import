#!/usr/bin/env python3
"""
Extract ALL 68 failed customers from the actual response.log file
"""

import json
import re
import os
from datetime import datetime

def extract_all_failed_customers_from_response_log():
    """Extract all failed customers from the actual response.log file"""
    
    print("🔍 EXTRACTING ALL FAILED CUSTOMERS FROM RESPONSE.LOG")
    print("=" * 60)
    
    if not os.path.exists("response.log"):
        print("❌ response.log file not found!")
        return
    
    print("📖 Reading response.log file...")
    with open("response.log", 'r', encoding='utf-8') as f:
        response_content = f.read()
    
    print(f"✅ Loaded response.log ({len(response_content)} characters)")
    
    # Method 1: Extract using regex pattern for failed customers
    failed_pattern = r'"customerId":\s*"([^"]+)"[^}]*"username":\s*"([^"]+)"[^}]*"result":\s*"(?:FAILED|ERROR|CONFLICT)"'
    matches = re.findall(failed_pattern, response_content)
    
    print(f"🔍 Regex search found {len(matches)} failed customers")
    
    # Method 2: Also try to parse JSON blocks and extract failed customers
    json_blocks = []
    try:
        # Try to find JSON response blocks
        json_pattern = r'\{[^{}]*"data":\s*\[[^\]]*\][^{}]*\}'
        json_matches = re.findall(json_pattern, response_content, re.DOTALL)
        
        for json_str in json_matches:
            try:
                json_data = json.loads(json_str)
                if 'data' in json_data:
                    json_blocks.append(json_data)
            except:
                continue
                
        print(f"🔍 Found {len(json_blocks)} JSON response blocks")
    except Exception as e:
        print(f"⚠️ JSON parsing error: {e}")
    
    # Collect all failed customers
    all_failed_customers = []
    
    # From regex matches
    for customer_id, username in matches:
        failed_customer = {
            'customerId': customer_id,
            'username': username,
            'result': 'FAILED',  # Will be updated below if we can determine the actual result
            'error': 'Extracted from response.log via regex',
            'timestamp': datetime.now().isoformat(),
            'source': 'regex_extraction',
            'originalData': None
        }
        all_failed_customers.append(failed_customer)
    
    # From JSON blocks
    for json_block in json_blocks:
        if 'data' in json_block:
            for customer_result in json_block['data']:
                if isinstance(customer_result, dict) and customer_result.get('result') in ['FAILED', 'ERROR', 'CONFLICT']:
                    failed_customer = {
                        'customerId': customer_result.get('customerId'),
                        'username': customer_result.get('username'),
                        'result': customer_result.get('result', 'FAILED'),
                        'error': customer_result.get('error', 'Extracted from response.log via JSON parsing'),
                        'timestamp': datetime.now().isoformat(),
                        'source': 'json_extraction',
                        'originalData': None
                    }
                    all_failed_customers.append(failed_customer)
    
    # Remove duplicates based on customerId
    unique_failed_customers = {}
    for fc in all_failed_customers:
        customer_id = fc['customerId']
        if customer_id not in unique_failed_customers:
            unique_failed_customers[customer_id] = fc
    
    final_failed_customers = list(unique_failed_customers.values())
    
    print(f"\n📊 EXTRACTION RESULTS:")
    print(f"   - Total matches found: {len(all_failed_customers)}")
    print(f"   - Unique failed customers: {len(final_failed_customers)}")
    print(f"   - Expected: 68 failed customers")
    
    if len(final_failed_customers) != 68:
        print(f"⚠️ WARNING: Expected 68 but found {len(final_failed_customers)}")
    else:
        print(f"✅ SUCCESS: Found all 68 expected failed customers!")
    
    # Show first 10 failed customers
    print(f"\n📋 FIRST 10 FAILED CUSTOMERS:")
    for i, fc in enumerate(final_failed_customers[:10], 1):
        print(f"   {i:2d}. ID: {fc['customerId']} | Username: {fc['username']}")
    
    if len(final_failed_customers) > 10:
        print(f"   ... and {len(final_failed_customers) - 10} more")
    
    # Save all failed customers to file
    failed_customers_dir = "failed_customers"
    if not os.path.exists(failed_customers_dir):
        os.makedirs(failed_customers_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{failed_customers_dir}/extracted_failed_customers_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_failed_customers, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 SAVED ALL FAILED CUSTOMERS:")
    print(f"   - File: {output_file}")
    print(f"   - Count: {len(final_failed_customers)} customers")
    print(f"   - Size: {os.path.getsize(output_file)} bytes")
    
    # Analyze the pattern
    print(f"\n🔍 PATTERN ANALYSIS:")
    bjorn_patrik_count = sum(1 for fc in final_failed_customers if 'BJÖRN PATRIK' in fc['username'])
    print(f"   - Customers with 'BJÖRN PATRIK': {bjorn_patrik_count}")
    print(f"   - Other failed customers: {len(final_failed_customers) - bjorn_patrik_count}")
    
    # Show customer ID range
    customer_ids = [int(fc['customerId']) for fc in final_failed_customers if fc['customerId'].isdigit()]
    if customer_ids:
        print(f"   - Customer ID range: {min(customer_ids)} to {max(customer_ids)}")
    
    print(f"\n" + "=" * 60)
    print(f"🎯 CONCLUSION:")
    print(f"   Successfully extracted {len(final_failed_customers)} failed customers from response.log")
    print(f"   These are the ACTUAL customers that failed during your import!")
    print(f"   File saved: {output_file}")
    print("=" * 60)
    
    return final_failed_customers

if __name__ == "__main__":
    extract_all_failed_customers_from_response_log()
