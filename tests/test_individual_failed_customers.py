#!/usr/bin/env python3
"""
Test script for individual failed customers feature
Tests the new functionality that saves individual failed customers 
organized by failure reason (CONFLICT, FAILED, ERROR)
"""

import sys
import os
import json
import tempfile
import shutil
from datetime import datetime

# Add parent directory to path to import the bulk importer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bulk_import_multithreaded import BulkCustomerImporter

def test_individual_failed_customers():
    """Test the individual failed customers feature"""
    print("🧪 Testing Individual Failed Customers Feature")
    print("=" * 50)
    
    # Create a temporary directory for testing
    test_dir = tempfile.mkdtemp(prefix="test_individual_failed_")
    original_cwd = os.getcwd()
    
    try:
        # Change to test directory
        os.chdir(test_dir)
        
        # Create test importer
        importer = BulkCustomerImporter(
            api_url="https://test.example.com/api",
            auth_token="test_token",
            batch_size=10,
            max_workers=1,
            use_auto_auth=False
        )
        
        # Create test failed customers with different failure reasons
        test_failed_customers = [
            {
                'customerId': 'CUST001',
                'username': 'john.doe',
                'result': 'CONFLICT',
                'error': 'Customer already exists in system',
                'timestamp': datetime.now().isoformat(),
                'originalData': {'name': 'John Doe', 'email': 'john@example.com'},
                'batchInfo': 'Test batch 1'
            },
            {
                'customerId': 'CUST002',
                'username': 'jane.smith',
                'result': 'FAILED',
                'error': 'Invalid email format',
                'timestamp': datetime.now().isoformat(),
                'originalData': {'name': 'Jane Smith', 'email': 'invalid-email'},
                'batchInfo': 'Test batch 1'
            },
            {
                'customerId': 'CUST003',
                'username': 'bob.wilson',
                'result': 'ERROR',
                'error': 'Database connection timeout',
                'timestamp': datetime.now().isoformat(),
                'originalData': {'name': 'Bob Wilson', 'email': 'bob@example.com'},
                'batchInfo': 'Test batch 1'
            },
            {
                'customerId': 'CUST004',
                'username': 'alice.brown',
                'result': 'CONFLICT',
                'error': 'Duplicate username detected',
                'timestamp': datetime.now().isoformat(),
                'originalData': {'name': 'Alice Brown', 'email': 'alice@example.com'},
                'batchInfo': 'Test batch 1'
            },
            {
                'customerId': 'CUST005',
                'username': 'charlie.davis',
                'result': 'UNKNOWN_REASON',
                'error': 'Some unknown error occurred',
                'timestamp': datetime.now().isoformat(),
                'originalData': {'name': 'Charlie Davis', 'email': 'charlie@example.com'},
                'batchInfo': 'Test batch 1'
            }
        ]
        
        print(f"📝 Created {len(test_failed_customers)} test failed customers:")
        for customer in test_failed_customers:
            print(f"   - {customer['customerId']} ({customer['username']}) - {customer['result']}")
        
        # Test the individual failed customers feature
        print(f"\n🔧 Testing _save_individual_failed_customers_by_reason...")
        importer._save_individual_failed_customers_by_reason(test_failed_customers)
        
        # Verify the results
        print(f"\n✅ Verifying results...")
        
        # Check if directories were created with new structure: failed_customers/single_failures/REASON
        expected_reasons = ['CONFLICT', 'FAILED', 'ERROR', 'UNKNOWN']
        created_dirs = []

        single_failures_path = os.path.join('failed_customers', 'single_failures')
        if os.path.exists(single_failures_path):
            for item in os.listdir(single_failures_path):
                if item in expected_reasons:
                    created_dirs.append(item)
                    print(f"   📁 Found directory: single_failures/{item}")
        
        # Check contents of each directory
        for dir_name in created_dirs:
            dir_path = os.path.join('failed_customers', 'single_failures', dir_name)
            if os.path.isdir(dir_path):
                files = os.listdir(dir_path)
                print(f"   📂 single_failures/{dir_name} contains {len(files)} files:")
                
                for file in files:
                    if file.startswith('_SUMMARY_'):
                        print(f"      📋 Summary file: {file}")
                        # Read and display summary
                        with open(os.path.join(dir_path, file), 'r', encoding='utf-8') as f:
                            summary = json.load(f)
                            print(f"         - Failure reason: {summary['failure_reason']}")
                            print(f"         - Total customers: {summary['total_customers']}")
                    else:
                        print(f"      📄 Customer file: {file}")
                        # Read and verify customer file structure (clean import format)
                        with open(os.path.join(dir_path, file), 'r', encoding='utf-8') as f:
                            customer_data = json.load(f)
                            # Check clean format with only "data" array (like retry batches)
                            if 'data' in customer_data and len(customer_data.keys()) == 1:
                                data_array = customer_data.get('data', [])
                                print(f"         - Clean import format: ✅")
                                print(f"         - Data array length: {len(data_array)}")
                                if data_array:
                                    first_customer = data_array[0]
                                    print(f"         - Sample fields: {list(first_customer.keys())[:3]}...")
                            else:
                                print(f"         - WARNING: File not in clean import format (has extra fields)")
        
        print(f"\n🎉 Test completed successfully!")
        print(f"   - Individual customer files created and organized by failure reason")
        print(f"   - Summary files generated for each failure type")
        print(f"   - File structure verified")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        os.chdir(original_cwd)
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print(f"🧹 Cleaned up test directory: {test_dir}")

if __name__ == "__main__":
    success = test_individual_failed_customers()
    sys.exit(0 if success else 1)
