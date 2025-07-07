#!/usr/bin/env python3
"""
Test script to create sample failed customers data for testing the Failed Customers tab
"""

import json
import os
from datetime import datetime

def create_sample_failed_customers():
    """Create sample failed customers data for testing"""
    
    # Ensure failed_customers directory exists (relative to project root)
    failed_customers_dir = "../failed_customers"
    os.makedirs(failed_customers_dir, exist_ok=True)
    
    # Sample failed customers data
    sample_failed_customers = [
        {
            'customerId': '50000001001',
            'username': 'ERIK ANDERSSON',
            'result': 'FAILED',
            'error': 'Customer already exists with this ID',
            'timestamp': datetime.now().isoformat(),
            'batchInfo': 'Found in structured response data',
            'originalData': {
                'changeType': 'CREATE',
                'type': 'PERSON',
                'person': {
                    'customerId': '50000001001',
                    'status': 'UNACTIVATED',
                    'firstName': 'ERIK',
                    'lastName': 'ANDERSSON'
                }
            }
        },
        {
            'customerId': '50000001002',
            'username': 'ANNA BJÖRK',
            'result': 'FAILED',
            'error': 'Invalid postal code format',
            'timestamp': datetime.now().isoformat(),
            'batchInfo': 'Found in structured response data',
            'originalData': {
                'changeType': 'CREATE',
                'type': 'PERSON',
                'person': {
                    'customerId': '50000001002',
                    'status': 'UNACTIVATED',
                    'firstName': 'ANNA',
                    'lastName': 'BJÖRK'
                }
            }
        },
        {
            'customerId': '50000001003',
            'username': 'LARS SVENSSON',
            'result': 'FAILED',
            'error': 'Missing required field: birthday',
            'timestamp': datetime.now().isoformat(),
            'batchInfo': 'Found via regex extraction',
            'originalData': {
                'changeType': 'CREATE',
                'type': 'PERSON',
                'person': {
                    'customerId': '50000001003',
                    'status': 'UNACTIVATED',
                    'firstName': 'LARS',
                    'lastName': 'SVENSSON'
                }
            }
        },
        {
            'customerId': '50000001004',
            'username': 'MARIA LINDQVIST',
            'result': 'FAILED',
            'error': 'Database connection timeout',
            'timestamp': datetime.now().isoformat(),
            'batchInfo': 'Found in errors array',
            'originalData': {
                'changeType': 'CREATE',
                'type': 'PERSON',
                'person': {
                    'customerId': '50000001004',
                    'status': 'UNACTIVATED',
                    'firstName': 'MARIA',
                    'lastName': 'LINDQVIST'
                }
            }
        },
        {
            'customerId': '50000001005',
            'username': 'JOHAN PETERSSON',
            'result': 'FAILED',
            'error': 'Invalid email address format: johan.petersson@invalid',
            'timestamp': datetime.now().isoformat(),
            'batchInfo': 'Found in structured response data',
            'originalData': {
                'changeType': 'CREATE',
                'type': 'PERSON',
                'person': {
                    'customerId': '50000001005',
                    'status': 'UNACTIVATED',
                    'firstName': 'JOHAN',
                    'lastName': 'PETERSSON'
                }
            }
        }
    ]
    
    # Save to failed customers file
    failed_customers_file = os.path.join(failed_customers_dir, "failed_customers.json")
    with open(failed_customers_file, 'w', encoding='utf-8') as f:
        json.dump(sample_failed_customers, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created sample failed customers data:")
    print(f"   - File: {failed_customers_file}")
    print(f"   - Count: {len(sample_failed_customers)} failed customers")
    print(f"   - Size: {os.path.getsize(failed_customers_file)} bytes")
    
    print(f"\n📋 Sample Failed Customers:")
    for i, customer in enumerate(sample_failed_customers, 1):
        print(f"   {i}. ID: {customer['customerId']} | Username: {customer['username']}")
        print(f"      Error: {customer['error']}")
    
    print(f"\n🎯 You can now:")
    print(f"   1. Launch the GUI: python ../bulk_import_gui.py")
    print(f"   2. Go to the 'Failed Customers' tab")
    print(f"   3. Click 'Refresh' to load the sample data")
    print(f"   4. Double-click any row to see detailed information")
    print(f"   5. Test export functionality")

if __name__ == "__main__":
    create_sample_failed_customers()
