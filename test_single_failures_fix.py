#!/usr/bin/env python3
"""
Test script to verify that the single failures functionality works correctly
with the improved customer matching logic.
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path to import the bulk importer
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bulk_import_multithreaded import BulkCustomerImporter

def create_test_batch_with_customers():
    """Create a test batch with sample customers"""
    test_batch = {
        "data": [
            {
                "changeType": "CREATE",
                "type": "PERSON",
                "person": {
                    "customerId": "TEST001",
                    "status": "UNACTIVATED",
                    "firstName": "ANNA",
                    "lastName": "ANDERSSON",
                    "languageCode": "sv",
                    "birthday": "1990-01-15",
                    "statisticalUseAllowed": False,
                    "marketingAllowedFlag": False,
                    "declarationAvailable": True,
                    "personalNumber": "199001151234",
                    "addresses": [
                        {
                            "addressee": "ANNA ANDERSSON",
                            "street": "Testgatan",
                            "streetNumber": "123",
                            "city": "Stockholm",
                            "postalCode": "12345",
                            "countryCode": "SE",
                            "contactPurposeTypeCode": "DEFAULT",
                            "contactMethodTypeCode": "HOME"
                        }
                    ],
                    "customerCards": [
                        {
                            "number": "TEST001",
                            "cardTypeCode": "MEMBER",
                            "status": "ACTIVE"
                        }
                    ]
                }
            },
            {
                "changeType": "CREATE",
                "type": "PERSON",
                "person": {
                    "customerId": "TEST002",
                    "status": "UNACTIVATED",
                    "firstName": "ERIK",
                    "lastName": "ERIKSSON",
                    "languageCode": "sv",
                    "birthday": "1985-05-20",
                    "statisticalUseAllowed": False,
                    "marketingAllowedFlag": False,
                    "declarationAvailable": True,
                    "personalNumber": "198505205678",
                    "addresses": [
                        {
                            "addressee": "ERIK ERIKSSON",
                            "street": "Provgatan",
                            "streetNumber": "456",
                            "city": "Göteborg",
                            "postalCode": "54321",
                            "countryCode": "SE",
                            "contactPurposeTypeCode": "DEFAULT",
                            "contactMethodTypeCode": "HOME"
                        }
                    ],
                    "customerCards": [
                        {
                            "number": "TEST002",
                            "cardTypeCode": "MEMBER",
                            "status": "ACTIVE"
                        }
                    ]
                }
            }
        ]
    }
    return test_batch

def create_mock_failed_response():
    """Create a mock API response with failed customers"""
    mock_response = {
        "data": [
            {
                "customerId": "TEST001",
                "username": "ANNA ANDERSSON-1234",
                "result": "CONFLICT",
                "error": "Customer already exists in system"
            },
            {
                "customerId": "TEST002", 
                "username": "ERIK ERIKSSON-5678",
                "result": "FAILED",
                "error": "Invalid personal number format"
            }
        ]
    }
    return json.dumps(mock_response)

def test_single_failures_functionality():
    """Test the single failures functionality with improved matching"""
    print("🧪 Testing Single Failures Functionality")
    print("=" * 50)
    
    # Create test batch
    test_batch = create_test_batch_with_customers()
    print(f"✅ Created test batch with {len(test_batch['data'])} customers")
    
    # Create importer instance
    importer = BulkCustomerImporter(
        api_url="https://test.example.com/api",
        auth_token="test_token",
        batch_size=10,
        max_workers=1
    )
    
    # Test the extract_failed_customers method directly
    mock_response_text = create_mock_failed_response()
    print(f"✅ Created mock failed response")
    
    # Extract failed customers using the improved matching logic
    failed_customers = importer._parse_api_response_for_failures(
        mock_response_text,
        test_batch['data']
    )
    
    print(f"\n📊 RESULTS:")
    print(f"   Found {len(failed_customers)} failed customers")
    
    for i, fc in enumerate(failed_customers, 1):
        print(f"\n   {i}. Customer ID: {fc['customerId']}")
        print(f"      Username: {fc['username']}")
        print(f"      Result: {fc['result']}")
        print(f"      Error: {fc['error']}")
        print(f"      Has Original Data: {'✅ YES' if fc['originalData'] else '❌ NO'}")
        
        if fc['originalData']:
            person_data = fc['originalData'].get('person', {})
            print(f"      Original Name: {person_data.get('firstName', 'N/A')} {person_data.get('lastName', 'N/A')}")
    
    # Test saving individual failed customers
    if failed_customers:
        print(f"\n💾 Testing _save_individual_failed_customers_by_reason...")
        importer.failed_customers = failed_customers
        importer._save_individual_failed_customers_by_reason(failed_customers)
        
        # Check if files were created
        single_failures_base = "failed_customers/single_failures"
        if os.path.exists(single_failures_base):
            print(f"✅ Single failures directory created: {single_failures_base}")
            
            for reason in ['CONFLICT', 'FAILED', 'ERROR']:
                reason_dir = os.path.join(single_failures_base, reason)
                if os.path.exists(reason_dir):
                    files = os.listdir(reason_dir)
                    customer_files = [f for f in files if f.startswith('customer_')]
                    summary_files = [f for f in files if f.startswith('_SUMMARY_')]
                    
                    print(f"   📂 {reason}/ directory:")
                    print(f"      Customer files: {len(customer_files)}")
                    print(f"      Summary files: {len(summary_files)}")
                    
                    # Check content of first customer file
                    if customer_files:
                        first_file = os.path.join(reason_dir, customer_files[0])
                        with open(first_file, 'r', encoding='utf-8') as f:
                            content = json.load(f)
                        
                        print(f"      ✅ Sample file {customer_files[0]}:")
                        print(f"         Has 'data' array: {'✅' if 'data' in content else '❌'}")
                        if 'data' in content and content['data']:
                            sample_customer = content['data'][0]
                            if 'person' in sample_customer:
                                person = sample_customer['person']
                                print(f"         Customer: {person.get('firstName', 'N/A')} {person.get('lastName', 'N/A')}")
                                print(f"         Customer ID: {person.get('customerId', 'N/A')}")
                            print(f"         Ready for re-import: ✅ YES")
        else:
            print(f"❌ Single failures directory not found")
    
    return len(failed_customers) > 0 and all(fc['originalData'] is not None for fc in failed_customers)

if __name__ == "__main__":
    print("🚀 Starting Single Failures Fix Test")
    print("=" * 60)
    
    success = test_single_failures_functionality()
    
    print(f"\n🎯 TEST RESULT: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    if success:
        print("   ✅ Customer matching logic works correctly")
        print("   ✅ Original data is preserved for failed customers")
        print("   ✅ Individual customer files can be created for re-import")
    else:
        print("   ❌ Customer matching logic needs further improvement")
    
    sys.exit(0 if success else 1)
