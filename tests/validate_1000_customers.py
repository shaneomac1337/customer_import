#!/usr/bin/env python3
"""
Validate the 1000 customers format against the working 700 customers format
"""

import json
import os

def validate_customer_format(filepath):
    """Validate a single customer file format"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check top-level structure
        if not isinstance(data, dict):
            return False, "Root should be a dict, not a list"
        
        if "data" not in data:
            return False, "Missing 'data' key at root level"
        
        if not isinstance(data["data"], list):
            return False, "'data' should be a list"
        
        # Check first customer structure
        if len(data["data"]) == 0:
            return False, "No customers in data array"
        
        customer = data["data"][0]
        
        # Required top-level fields
        required_fields = ["changeType", "type", "person"]
        for field in required_fields:
            if field not in customer:
                return False, f"Missing required field: {field}"
        
        # Check person structure
        person = customer["person"]
        required_person_fields = [
            "customerId", "status", "firstName", "lastName", 
            "languageCode", "birthday", "statisticalUseAllowed",
            "marketingAllowedFlag", "declarationAvailable", 
            "addresses", "customerCards"
        ]
        
        for field in required_person_fields:
            if field not in person:
                return False, f"Missing required person field: {field}"
        
        # Check addresses structure
        if not isinstance(person["addresses"], list) or len(person["addresses"]) == 0:
            return False, "addresses should be a non-empty list"
        
        address = person["addresses"][0]
        required_address_fields = [
            "addressee", "street", "streetNumber", "city", 
            "postalCode", "countryCode", "contactPurposeTypeCode", 
            "contactMethodTypeCode"
        ]
        
        for field in required_address_fields:
            if field not in address:
                return False, f"Missing required address field: {field}"
        
        # Check customerCards structure
        if not isinstance(person["customerCards"], list) or len(person["customerCards"]) == 0:
            return False, "customerCards should be a non-empty list"
        
        card = person["customerCards"][0]
        required_card_fields = ["number", "type", "scope"]
        
        for field in required_card_fields:
            if field not in card:
                return False, f"Missing required card field: {field}"
        
        return True, "Format is correct"
        
    except json.JSONDecodeError as e:
        return False, f"JSON decode error: {e}"
    except Exception as e:
        return False, f"Validation error: {e}"

def main():
    """Validate all 1000 customer files"""
    print("=" * 60)
    print("VALIDATING 1000 CUSTOMER FILES FORMAT")
    print("=" * 60)
    
    customer_dir = "bulk_import_1000_customers"
    
    if not os.path.exists(customer_dir):
        print(f"[ERROR] Directory '{customer_dir}' not found!")
        return
    
    total_files = 0
    valid_files = 0
    invalid_files = []
    
    # Check all batch files
    for i in range(1, 21):
        filename = f"customers_50_batch_{i:02d}.json"
        filepath = os.path.join(customer_dir, filename)
        
        if os.path.exists(filepath):
            total_files += 1
            is_valid, message = validate_customer_format(filepath)
            
            if is_valid:
                valid_files += 1
                print(f"[OK] {filename} - {message}")
            else:
                invalid_files.append((filename, message))
                print(f"[ERROR] {filename} - {message}")
        else:
            print(f"[MISSING] {filename}")
    
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Total files checked: {total_files}")
    print(f"Valid files: {valid_files}")
    print(f"Invalid files: {len(invalid_files)}")
    
    if invalid_files:
        print("\nInvalid files:")
        for filename, error in invalid_files:
            print(f"  - {filename}: {error}")
    else:
        print("\n[SUCCESS] All files have correct format!")
        print("Ready for bulk import!")

if __name__ == "__main__":
    main()
