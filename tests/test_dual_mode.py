#!/usr/bin/env python3
"""
Test script for dual-mode authentication (C4R and Engage)
"""

from auth_manager import AuthenticationManager

def test_c4r_mode():
    """Test Cloud4Retail authentication"""
    print("=" * 60)
    print("Testing C4R (Cloud4Retail) Mode")
    print("=" * 60)
    
    try:
        auth_manager = AuthenticationManager(mode="C4R")
        
        print(f"Mode: {auth_manager.mode}")
        print(f"Auth URL: {auth_manager.auth_url}")
        print(f"Username: {auth_manager.username}")
        print(f"Has GK-Passport: {bool(auth_manager.gk_passport)}")
        print(f"Uses Basic Auth: {bool(auth_manager.basic_auth)}")
        print(f"Uses Client ID: {bool(auth_manager.client_id)}")
        print()
        
        result = auth_manager.test_authentication()
        
        if result['success']:
            print("✅ C4R Authentication: SUCCESS")
            print(f"   Token Preview: {result.get('token_preview', 'N/A')}")
            print(f"   Expires At: {result.get('expires_at', 'N/A')}")
            print(f"   Response Time: {result.get('response_time_ms', 0):.2f}ms")
        else:
            print("❌ C4R Authentication: FAILED")
            print(f"   Error: {result.get('error', 'Unknown')}")
            
    except Exception as e:
        print(f"❌ C4R Test Exception: {e}")
    
    print()

def test_engage_mode():
    """Test Engage authentication"""
    print("=" * 60)
    print("Testing Engage Mode")
    print("=" * 60)
    
    try:
        auth_manager = AuthenticationManager(mode="Engage")
        
        print(f"Mode: {auth_manager.mode}")
        print(f"Auth URL: {auth_manager.auth_url}")
        print(f"Username: {auth_manager.username}")
        print(f"Has GK-Passport: {bool(auth_manager.gk_passport)}")
        print(f"Uses Basic Auth: {bool(auth_manager.basic_auth)}")
        print(f"Uses Client ID: {bool(auth_manager.client_id)}")
        print(f"Client ID: {auth_manager.client_id}")
        print()
        
        result = auth_manager.test_authentication()
        
        if result['success']:
            print("✅ Engage Authentication: SUCCESS")
            print(f"   Token Preview: {result.get('token_preview', 'N/A')}")
            print(f"   Expires At: {result.get('expires_at', 'N/A')}")
            print(f"   Response Time: {result.get('response_time_ms', 0):.2f}ms")
            
            # Check token expiry time
            token_info = auth_manager.get_token_info()
            if token_info.get('time_until_expiry_seconds'):
                expiry_seconds = token_info['time_until_expiry_seconds']
                print(f"   Token Valid For: {expiry_seconds:.0f}s ({expiry_seconds/60:.1f} minutes)")
        else:
            print("❌ Engage Authentication: FAILED")
            print(f"   Error: {result.get('error', 'Unknown')}")
            
    except Exception as e:
        print(f"❌ Engage Test Exception: {e}")
    
    print()

def main():
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "Dual-Mode Authentication Test" + " " * 19 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    # Test C4R mode
    test_c4r_mode()
    
    # Test Engage mode
    test_engage_mode()
    
    print("=" * 60)
    print("Testing Complete")
    print("=" * 60)

if __name__ == "__main__":
    main()
