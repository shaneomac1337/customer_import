"""
Test script to verify failed customer tracking functionality
"""

import json
import os
from bulk_import_multithreaded import BulkCustomerImporter

def test_failed_customer_parsing():
    """Test the failed customer parsing functionality"""
    
    # Create a test importer instance
    importer = BulkCustomerImporter(
        api_url="https://test.example.com/api",
        auth_token="test_token",
        gk_passport="test_passport",
        failed_customers_file="test_failed_customers.json"
    )
    
    # Test data - simulate API response with mixed success/failure
    test_response = {
        "customers": [
            {
                "customerId": "60000002633",
                "username": "BJÖRN PATRIK-JÖNSSON-1193",
                "result": "FAILED",
                "error": "Invalid personal number format"
            },
            {
                "customerId": "60000002634", 
                "username": "ANNA SVENSSON-1194",
                "result": "SUCCESS"
            },
            {
                "customerId": "60000002635",
                "username": "ERIK ANDERSSON-1195", 
                "result": "FAILED",
                "error": "Duplicate customer record"
            }
        ]
    }
    
    # Test batch customers (original data)
    test_batch = [
        {
            "personalNumber": "19931201-1193",
            "firstName": "Björn Patrik",
            "lastName": "Jönsson",
            "customerCards": [{"cardNumber": "60000002633"}]
        },
        {
            "personalNumber": "19941201-1194", 
            "firstName": "Anna",
            "lastName": "Svensson",
            "customerCards": [{"cardNumber": "60000002634"}]
        },
        {
            "personalNumber": "19951201-1195",
            "firstName": "Erik", 
            "lastName": "Andersson",
            "customerCards": [{"cardNumber": "60000002635"}]
        }
    ]
    
    print("Testing failed customer parsing...")
    
    # Test the parsing function
    failed_customers = importer._parse_api_response_for_failures(test_response, test_batch)
    
    print(f"Found {len(failed_customers)} failed customers:")
    for customer in failed_customers:
        print(f"  - ID: {customer['customerId']}")
        print(f"    Username: {customer['username']}")
        print(f"    Error: {customer['error']}")
        print(f"    Timestamp: {customer['timestamp']}")
        print()
    
    # Test saving failed customers
    if failed_customers:
        print("Testing failed customer saving...")
        importer._save_failed_customers(failed_customers)
        
        # Verify file was created
        if os.path.exists(importer.failed_customers_file):
            print(f"✅ Failed customers file created: {importer.failed_customers_file}")
            
            # Read and display contents
            with open(importer.failed_customers_file, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                print(f"✅ Saved {len(saved_data)} failed customers to file")
        else:
            print("❌ Failed customers file was not created")
    
    # Test summary function
    print("\nTesting failed customers summary...")
    summary = importer.get_failed_customers_summary()
    print(f"Summary: {json.dumps(summary, indent=2)}")
    
    # Cleanup test file
    if os.path.exists(importer.failed_customers_file):
        os.remove(importer.failed_customers_file)
        print(f"🧹 Cleaned up test file: {importer.failed_customers_file}")

    # Also cleanup the failed_customers directory if it's empty
    failed_customers_dir = "failed_customers"
    if os.path.exists(failed_customers_dir) and not os.listdir(failed_customers_dir):
        os.rmdir(failed_customers_dir)
        print(f"🧹 Cleaned up empty directory: {failed_customers_dir}")

def test_error_response_parsing():
    """Test parsing of error responses"""
    
    importer = BulkCustomerImporter(
        api_url="https://test.example.com/api",
        auth_token="test_token", 
        gk_passport="test_passport",
        failed_customers_file="test_failed_customers_errors.json"
    )
    
    # Test error response format
    error_response = {
        "errors": [
            {
                "customerId": "60000002636",
                "username": "TEST USER-1196",
                "message": "Database connection timeout"
            },
            {
                "customerId": "60000002637", 
                "username": "TEST USER-1197",
                "message": "Validation failed: missing required field"
            }
        ]
    }
    
    print("\nTesting error response parsing...")
    
    failed_customers = importer._parse_api_response_for_failures(error_response, [])
    
    print(f"Found {len(failed_customers)} failed customers from error response:")
    for customer in failed_customers:
        print(f"  - ID: {customer['customerId']}")
        print(f"    Username: {customer['username']}")
        print(f"    Error: {customer['error']}")
        print()
    
    # Cleanup
    if os.path.exists(importer.failed_customers_file):
        os.remove(importer.failed_customers_file)

    # Also cleanup the failed_customers directory if it's empty
    failed_customers_dir = "failed_customers"
    if os.path.exists(failed_customers_dir) and not os.listdir(failed_customers_dir):
        os.rmdir(failed_customers_dir)

if __name__ == "__main__":
    print("🧪 Testing Failed Customer Tracking Functionality")
    print("=" * 60)
    
    test_failed_customer_parsing()
    test_error_response_parsing()
    
    print("\n✅ All tests completed!")
