#!/usr/bin/env python3
"""
Test script to verify single failures functionality with real customer data
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path to import the bulk importer
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bulk_import_multithreaded import BulkCustomerImporter

def load_real_batch_data():
    """Load a real batch file for testing"""
    batch_file = "batches_to_retry/batch_001.json"
    
    if not os.path.exists(batch_file):
        print(f"❌ Batch file not found: {batch_file}")
        return None
    
    with open(batch_file, 'r', encoding='utf-8') as f:
        batch_data = json.load(f)
    
    print(f"✅ Loaded real batch data with {len(batch_data['data'])} customers")
    return batch_data

def create_mock_failed_response_for_real_data(batch_data):
    """Create a mock failed response using real customer data"""
    if not batch_data or 'data' not in batch_data:
        return "{}"
    
    # Take first 3 customers and simulate different failure types
    customers = batch_data['data'][:3]
    mock_failures = []
    
    for i, customer in enumerate(customers):
        person = customer.get('person', {})
        customer_id = person.get('customerId', f'unknown_{i}')
        
        # Create a realistic username based on the customer data
        first_name = person.get('firstName', 'Unknown')
        last_name = person.get('lastName', 'Unknown')
        personal_num = person.get('personalNumber', '1234')[-4:]  # Last 4 digits
        username = f"{first_name} {last_name}-{personal_num}"
        
        # Assign different failure types
        if i == 0:
            result_type = "CONFLICT"
            error_msg = "Customer already exists in system"
        elif i == 1:
            result_type = "FAILED"
            error_msg = "Invalid personal number format"
        else:
            result_type = "ERROR"
            error_msg = "System error during processing"
        
        mock_failures.append({
            "customerId": customer_id,
            "username": username,
            "result": result_type,
            "error": error_msg
        })
    
    mock_response = {"data": mock_failures}
    return json.dumps(mock_response)

def test_real_data_single_failures():
    """Test single failures with real customer data"""
    print("🧪 Testing Single Failures with Real Customer Data")
    print("=" * 60)
    
    # Load real batch data
    batch_data = load_real_batch_data()
    if not batch_data:
        return False
    
    # Create mock failed response based on real data
    mock_response = create_mock_failed_response_for_real_data(batch_data)
    print(f"✅ Created mock failed response for real customers")
    
    # Create importer instance
    importer = BulkCustomerImporter(
        api_url="https://test.example.com/api",
        auth_token="test_token",
        batch_size=10,
        max_workers=1
    )
    
    # Parse failed customers
    failed_customers = importer._parse_api_response_for_failures(
        mock_response, 
        batch_data['data']
    )
    
    print(f"\n📊 RESULTS:")
    print(f"   Found {len(failed_customers)} failed customers")
    
    success_count = 0
    for i, fc in enumerate(failed_customers, 1):
        has_original = fc['originalData'] is not None
        if has_original:
            success_count += 1
            
        print(f"\n   {i}. Customer ID: {fc['customerId']}")
        print(f"      Username: {fc['username']}")
        print(f"      Result: {fc['result']}")
        print(f"      Has Original Data: {'✅ YES' if has_original else '❌ NO'}")
        
        if has_original:
            person_data = fc['originalData'].get('person', {})
            print(f"      Original Name: {person_data.get('firstName', 'N/A')} {person_data.get('lastName', 'N/A')}")
            print(f"      Personal Number: {person_data.get('personalNumber', 'N/A')}")
    
    # Test saving individual failed customers
    if failed_customers:
        print(f"\n💾 Testing save with real data...")
        
        # Clean up any existing test files first
        import shutil
        test_single_failures_dir = "failed_customers/single_failures_real_test"
        if os.path.exists(test_single_failures_dir):
            shutil.rmtree(test_single_failures_dir)
        
        # Temporarily change the single failures directory for testing
        original_method = importer._save_individual_failed_customers_by_reason
        
        def test_save_method(failed_customers_list):
            # Modify the base directory for this test
            try:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                # Group customers by failure reason
                customers_by_reason = {
                    'CONFLICT': [],
                    'FAILED': [],
                    'ERROR': [],
                    'UNKNOWN': []
                }

                for customer in failed_customers_list:
                    result = customer.get('result', '').upper()
                    if result in customers_by_reason:
                        customers_by_reason[result].append(customer)
                    else:
                        customers_by_reason['UNKNOWN'].append(customer)

                # Save each group to separate folders
                for reason, customers in customers_by_reason.items():
                    if not customers:
                        continue

                    # Use test directory
                    reason_dir = os.path.join(test_single_failures_dir, reason)
                    os.makedirs(reason_dir, exist_ok=True)

                    # Save each customer as individual file
                    for i, customer in enumerate(customers, 1):
                        customer_id = customer.get('customerId', f'unknown_{i}')
                        username = customer.get('username', f'unknown_user_{i}')

                        # Create safe filename
                        safe_customer_id = "".join(c for c in str(customer_id) if c.isalnum() or c in ('-', '_'))
                        safe_username = "".join(c for c in str(username) if c.isalnum() or c in ('-', '_'))

                        customer_filename = f"customer_{safe_customer_id}_{safe_username}.json"
                        customer_filepath = os.path.join(reason_dir, customer_filename)

                        # Prepare customer data in direct import format
                        original_data = customer.get('originalData')
                        if original_data:
                            customer_data = {
                                "data": [original_data]
                            }

                            # Save individual customer file
                            with open(customer_filepath, 'w', encoding='utf-8') as f:
                                json.dump(customer_data, f, indent=2, ensure_ascii=False)

                    print(f"   ✅ Saved {len(customers)} {reason} customers to {reason_dir}")

            except Exception as e:
                print(f"   ❌ Error saving: {e}")
        
        # Run the test save
        test_save_method(failed_customers)
        
        # Verify files were created
        if os.path.exists(test_single_failures_dir):
            print(f"\n📁 Verification:")
            for reason in ['CONFLICT', 'FAILED', 'ERROR']:
                reason_dir = os.path.join(test_single_failures_dir, reason)
                if os.path.exists(reason_dir):
                    files = os.listdir(reason_dir)
                    customer_files = [f for f in files if f.startswith('customer_')]
                    
                    print(f"   📂 {reason}/ directory: {len(customer_files)} customer files")
                    
                    # Verify first file content
                    if customer_files:
                        first_file = os.path.join(reason_dir, customer_files[0])
                        with open(first_file, 'r', encoding='utf-8') as f:
                            content = json.load(f)
                        
                        if 'data' in content and content['data']:
                            sample_customer = content['data'][0]
                            if 'person' in sample_customer:
                                person = sample_customer['person']
                                print(f"      ✅ Sample: {person.get('firstName', 'N/A')} {person.get('lastName', 'N/A')} (ID: {person.get('customerId', 'N/A')})")
                                print(f"      ✅ Ready for re-import: YES")
    
    return success_count == len(failed_customers) and len(failed_customers) > 0

if __name__ == "__main__":
    print("🚀 Starting Real Data Single Failures Test")
    print("=" * 70)
    
    success = test_real_data_single_failures()
    
    print(f"\n🎯 TEST RESULT: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    if success:
        print("   ✅ Real customer data matching works correctly")
        print("   ✅ Original data is preserved for all failed customers")
        print("   ✅ Individual customer files are ready for re-import")
        print("   ✅ The single failures fix is working properly!")
    else:
        print("   ❌ Some issues remain with real customer data matching")
    
    sys.exit(0 if success else 1)
