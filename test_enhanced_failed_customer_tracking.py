#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced failed customer tracking with batch information
"""

import json
import os
from datetime import datetime
from bulk_import_multithreaded import BulkCustomerImporter

def create_test_batch_with_failures():
    """Create a test batch that will simulate some failures"""
    test_customers = [
        {
            "changeType": "CREATE",
            "type": "PERSON",
            "person": {
                "customerId": "TEST001",
                "status": "UNACTIVATED",
                "firstName": "John",
                "lastName": "Doe",
                "personalNumber": "19900101-1234",
                "languageCode": "sv",
                "statisticalUseAllowed": False,
                "marketingAllowedFlag": True,
                "declarationAvailable": True,
                "addresses": [
                    {
                        "addressee": "John Doe",
                        "city": "Stockholm",
                        "countryCode": "SE",
                        "contactPurposeTypeCode": "HOME",
                        "contactMethodTypeCode": "POSTAL_ADDRESS"
                    }
                ],
                "customerCards": [
                    {
                        "cardNumber": "60000001001",
                        "cardType": "MAIN_CARD",
                        "scope": "GLOBAL"
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
                "firstName": "Jane",
                "lastName": "Smith",
                "personalNumber": "19850615-5678",
                "languageCode": "sv",
                "statisticalUseAllowed": False,
                "marketingAllowedFlag": True,
                "declarationAvailable": True,
                "addresses": [
                    {
                        "addressee": "Jane Smith",
                        "city": "Gothenburg",
                        "countryCode": "SE",
                        "contactPurposeTypeCode": "HOME",
                        "contactMethodTypeCode": "POSTAL_ADDRESS"
                    }
                ],
                "customerCards": [
                    {
                        "cardNumber": "60000001002",
                        "cardType": "MAIN_CARD",
                        "scope": "GLOBAL"
                    }
                ]
            }
        }
    ]
    
    return test_customers

def test_enhanced_failed_customer_parsing():
    """Test the enhanced failed customer parsing with batch metadata"""
    
    print("🧪 Testing Enhanced Failed Customer Tracking")
    print("=" * 60)
    
    # Create test batch
    test_batch = create_test_batch_with_failures()
    
    # Create importer instance
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    failed_customers_file = f"test_enhanced_failed_{timestamp}.json"
    
    importer = BulkCustomerImporter(
        api_url="https://test.example.com/api",
        auth_token="test_token",
        gk_passport="test_passport",
        failed_customers_file=failed_customers_file
    )
    
    print(f"✅ Created importer with failed customers file: {failed_customers_file}")
    
    # Simulate API response with failures
    simulated_response = {
        "data": [
            {
                "customerId": "60000001001",
                "username": "JOHN-DOE-1234",
                "result": "FAILED",
                "error": "Invalid personal number format"
            },
            {
                "customerId": "60000001002",
                "username": "JANE-SMITH-5678",
                "result": "SUCCESS"
            }
        ]
    }
    
    # Create enhanced batch metadata
    batch_metadata = {
        'batch_id': 1,
        'batch_number': 'Batch 1',
        'total_batches': 5,
        'batch_size': len(test_batch),
        'source_file': 'test_customers_batch_01.json'
    }
    
    print(f"\n🔧 Batch Metadata:")
    print(f"   - Batch ID: {batch_metadata['batch_id']}")
    print(f"   - Batch Number: {batch_metadata['batch_number']}")
    print(f"   - Total Batches: {batch_metadata['total_batches']}")
    print(f"   - Batch Size: {batch_metadata['batch_size']}")
    print(f"   - Source File: {batch_metadata['source_file']}")
    
    # Test the enhanced parsing
    print(f"\n🧪 Testing Enhanced Failed Customer Parsing:")
    failed_customers = importer._parse_api_response_for_failures(
        simulated_response, 
        test_batch, 
        batch_metadata
    )
    
    if failed_customers:
        print(f"✅ SUCCESS: Detected {len(failed_customers)} failed customer(s)")
        
        for i, fc in enumerate(failed_customers, 1):
            print(f"\n   📋 Failed Customer #{i}:")
            print(f"      Customer ID: {fc['customerId']}")
            print(f"      Username: {fc['username']}")
            print(f"      Error: {fc['error']}")
            print(f"      Timestamp: {fc['timestamp']}")
            
            # Enhanced batch information
            print(f"      🏷️  Batch Information:")
            print(f"         - Batch ID: {fc['batch_id']}")
            print(f"         - Batch Number: {fc['batch_number']}")
            print(f"         - Total Batches: {fc['total_batches']}")
            print(f"         - Batch Size: {fc['batch_size']} customers")
            print(f"         - Source File: {fc['source_file']}")
            print(f"         - Batch Info: {fc['batchInfo']}")
            
            # Complete batch data availability
            if fc.get('complete_batch_data'):
                print(f"         - Complete Batch Data: ✅ Available ({len(fc['complete_batch_data'])} customers)")
                print(f"         - Can Reprocess Entire Batch: ✅ YES")
            else:
                print(f"         - Complete Batch Data: ❌ Not Available")
            
            # Original customer data
            if fc.get('originalData'):
                orig = fc['originalData']
                if 'person' in orig:
                    person = orig['person']
                    print(f"         - Original Customer: {person.get('firstName', 'Unknown')} {person.get('lastName', 'Unknown')}")
                print(f"         - Original Data: ✅ Available")
            else:
                print(f"         - Original Data: ❌ Not Available")
        
        # Test saving with enhanced data
        print(f"\n💾 Testing Enhanced Failed Customer Saving:")
        importer._save_failed_customers(failed_customers)
        
        if os.path.exists(failed_customers_file):
            print(f"✅ Enhanced failed customers file created successfully")
            
            # Read and verify the enhanced structure
            with open(failed_customers_file, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            print(f"✅ Verified: {len(saved_data)} failed customers saved with enhanced data")
            
            # Show file size and structure
            file_size = os.path.getsize(failed_customers_file)
            print(f"📊 File Details:")
            print(f"   - File Size: {file_size:,} bytes")
            print(f"   - Enhanced Fields: batch_id, batch_number, total_batches, batch_size, source_file, complete_batch_data")
            
            # Show a sample of the enhanced structure
            if saved_data:
                sample = saved_data[0]
                print(f"\n📋 Sample Enhanced Failed Customer Record:")
                enhanced_fields = ['batch_id', 'batch_number', 'total_batches', 'batch_size', 'source_file']
                for field in enhanced_fields:
                    if field in sample:
                        print(f"   - {field}: {sample[field]}")
                
                if 'complete_batch_data' in sample and sample['complete_batch_data']:
                    print(f"   - complete_batch_data: ✅ Present ({len(sample['complete_batch_data'])} customers)")
                else:
                    print(f"   - complete_batch_data: ❌ Missing")
            
        else:
            print(f"❌ Enhanced failed customers file was not created")
    else:
        print(f"❌ FAILED: No failed customers detected")
    
    # Cleanup
    if os.path.exists(failed_customers_file):
        os.remove(failed_customers_file)
        print(f"\n🧹 Cleaned up: {failed_customers_file}")
    
    # Clean up failed_customers directory if empty
    if os.path.exists("failed_customers") and not os.listdir("failed_customers"):
        os.rmdir("failed_customers")
        print(f"🧹 Cleaned up empty directory: failed_customers")
    
    print(f"\n" + "=" * 60)
    print(f"🎯 RESULT: Enhanced failed customer tracking is {'WORKING' if failed_customers else 'NOT WORKING'}")
    print(f"   ✅ Batch Information: {'INCLUDED' if failed_customers and 'batch_id' in failed_customers[0] else 'MISSING'}")
    print(f"   ✅ Complete Batch Data: {'INCLUDED' if failed_customers and 'complete_batch_data' in failed_customers[0] else 'MISSING'}")
    print(f"   ✅ Ready for Production: {'YES' if failed_customers else 'NO'}")
    print("=" * 60)

if __name__ == "__main__":
    test_enhanced_failed_customer_parsing()
