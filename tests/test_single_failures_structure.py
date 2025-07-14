#!/usr/bin/env python3
"""
Test script to verify that the single_failures directory structure 
is created automatically when the BulkCustomerImporter is initialized
"""

import sys
import os
import tempfile
import shutil

# Add parent directory to path to import the bulk importer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bulk_import_multithreaded import BulkCustomerImporter

def test_single_failures_structure_creation():
    """Test that single_failures structure is created automatically"""
    print("🧪 Testing Single Failures Structure Auto-Creation")
    print("=" * 55)
    
    # Create a temporary directory for testing
    test_dir = tempfile.mkdtemp(prefix="test_structure_")
    original_cwd = os.getcwd()
    
    try:
        # Change to test directory
        os.chdir(test_dir)
        print(f"📁 Working in test directory: {test_dir}")
        
        # Create importer - this should automatically create the structure
        print(f"\n🔧 Creating BulkCustomerImporter...")
        importer = BulkCustomerImporter(
            api_url="https://test.example.com/api",
            auth_token="test_token",
            batch_size=10,
            max_workers=1,
            use_auto_auth=False
        )
        
        # Verify the structure was created
        print(f"\n✅ Verifying structure creation...")
        
        # Check base directory
        base_path = "failed_customers/single_failures"
        if os.path.exists(base_path):
            print(f"   ✅ Base directory created: {base_path}")
        else:
            print(f"   ❌ Base directory missing: {base_path}")
            return False
            
        # Check README file
        readme_path = os.path.join(base_path, "README.md")
        if os.path.exists(readme_path):
            print(f"   ✅ README.md created: {readme_path}")
            
            # Check README content
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "Single Failures Directory Structure" in content:
                    print(f"   ✅ README content looks correct")
                else:
                    print(f"   ⚠️ README content might be incorrect")
        else:
            print(f"   ❌ README.md missing: {readme_path}")
            return False
        
        # List directory contents
        print(f"\n📂 Directory contents:")
        if os.path.exists(base_path):
            contents = os.listdir(base_path)
            for item in contents:
                print(f"   - {item}")
        
        print(f"\n🎉 Structure creation test completed successfully!")
        print(f"   ✅ single_failures directory ready for use")
        print(f"   ✅ README.md with instructions created")
        print(f"   ✅ Structure will be available for real imports")
        
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
    success = test_single_failures_structure_creation()
    sys.exit(0 if success else 1)
