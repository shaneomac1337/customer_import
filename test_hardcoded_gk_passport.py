#!/usr/bin/env python3
"""
Test script to verify that GK-Passport is properly hardcoded
"""

from auth_manager import AuthenticationManager
from bulk_import_multithreaded import BulkCustomerImporter

def test_auth_manager():
    """Test that AuthenticationManager has hardcoded GK-Passport"""
    print("=" * 50)
    print("TESTING AUTHENTICATION MANAGER")
    print("=" * 50)
    
    # Create auth manager without specifying GK-Passport
    auth_manager = AuthenticationManager()
    
    print(f"✅ GK-Passport hardcoded: {auth_manager.gk_passport[:50]}...")
    print(f"✅ Username: {auth_manager.username}")
    print(f"✅ Password: {'*' * len(auth_manager.password)}")
    
    expected_gk = "1.1:CiMg46zV+88yKOOMxZPwMjIDMDAxOg5idXNpbmVzc1VuaXRJZBIKCAISBnVzZXJJZBoSCAIaCGNsaWVudElkIgR3c0lkIhoaGGI6Y3VzdC5jdXN0b21lci5pbXBvcnRlcg=="
    
    if auth_manager.gk_passport == expected_gk:
        print("✅ GK-Passport matches expected value!")
    else:
        print("❌ GK-Passport does not match expected value!")
        return False
    
    return True

def test_bulk_importer():
    """Test that BulkCustomerImporter has hardcoded GK-Passport"""
    print("\n" + "=" * 50)
    print("TESTING BULK CUSTOMER IMPORTER")
    print("=" * 50)
    
    # Create importer without specifying GK-Passport
    importer = BulkCustomerImporter(
        api_url="https://test.com",
        auth_token="test_token"
    )
    
    print(f"✅ GK-Passport hardcoded: {importer.gk_passport[:50]}...")
    
    expected_gk = "1.1:CiMg46zV+88yKOOMxZPwMjIDMDAxOg5idXNpbmVzc1VuaXRJZBIKCAISBnVzZXJJZBoSCAIaCGNsaWVudElkIgR3c0lkIhoaGGI6Y3VzdC5jdXN0b21lci5pbXBvcnRlcg=="
    
    if importer.gk_passport == expected_gk:
        print("✅ GK-Passport matches expected value!")
    else:
        print("❌ GK-Passport does not match expected value!")
        return False
    
    return True

def test_auto_auth_importer():
    """Test that auto-auth importer has hardcoded GK-Passport"""
    print("\n" + "=" * 50)
    print("TESTING AUTO-AUTH IMPORTER")
    print("=" * 50)
    
    # Create importer with auto-auth without specifying GK-Passport
    importer = BulkCustomerImporter(
        api_url="https://test.com",
        use_auto_auth=True
    )
    
    print(f"✅ GK-Passport hardcoded: {importer.gk_passport[:50]}...")
    print(f"✅ Auth Manager GK-Passport: {importer.auth_manager.gk_passport[:50]}...")
    
    expected_gk = "1.1:CiMg46zV+88yKOOMxZPwMjIDMDAxOg5idXNpbmVzc1VuaXRJZBIKCAISBnVzZXJJZBoSCAIaCGNsaWVudElkIgR3c0lkIhoaGGI6Y3VzdC5jdXN0b21lci5pbXBvcnRlcg=="
    
    if importer.gk_passport == expected_gk and importer.auth_manager.gk_passport == expected_gk:
        print("✅ Both GK-Passport values match expected value!")
    else:
        print("❌ GK-Passport values do not match expected value!")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🧪 TESTING HARDCODED GK-PASSPORT IMPLEMENTATION")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: AuthenticationManager
    if test_auth_manager():
        tests_passed += 1
    
    # Test 2: BulkCustomerImporter
    if test_bulk_importer():
        tests_passed += 1
    
    # Test 3: Auto-auth BulkCustomerImporter
    if test_auto_auth_importer():
        tests_passed += 1
    
    # Results
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"✅ Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED! GK-Passport is properly hardcoded!")
    else:
        print("❌ Some tests failed. Check the implementation.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)