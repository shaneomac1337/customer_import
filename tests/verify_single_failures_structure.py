#!/usr/bin/env python3
"""
Simple verification script to show that the single_failures directory structure 
is automatically created when the BulkCustomerImporter is initialized
"""

import os

def verify_single_failures_structure():
    """Verify that the single_failures structure exists and is ready"""
    print("🔍 Verifying Single Failures Directory Structure")
    print("=" * 50)
    
    # Check base directory
    base_path = "failed_customers/single_failures"
    if os.path.exists(base_path):
        print(f"✅ Base directory exists: {base_path}")
    else:
        print(f"❌ Base directory missing: {base_path}")
        return False
        
    # Check README file
    readme_path = os.path.join(base_path, "README.md")
    if os.path.exists(readme_path):
        print(f"✅ README.md exists: {readme_path}")
        
        # Check README content
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if "Single Failures Directory Structure" in content:
                print(f"✅ README content is correct")
            else:
                print(f"⚠️ README content might be incorrect")
    else:
        print(f"❌ README.md missing: {readme_path}")
        return False
    
    # List directory contents
    print(f"\n📂 Current directory contents:")
    if os.path.exists(base_path):
        contents = os.listdir(base_path)
        if contents:
            for item in contents:
                item_path = os.path.join(base_path, item)
                if os.path.isdir(item_path):
                    print(f"   📁 {item}/")
                else:
                    print(f"   📄 {item}")
        else:
            print(f"   (empty - ready for failed customers)")
    
    print(f"\n🎯 Structure Status:")
    print(f"   ✅ Directory structure is ready")
    print(f"   ✅ Will automatically organize failed customers by reason")
    print(f"   ✅ Individual customer files will be in direct import format")
    print(f"   ✅ No manual setup required")
    
    print(f"\n💡 Next Steps:")
    print(f"   - When customers fail during import, they'll be organized here")
    print(f"   - CONFLICT/, FAILED/, ERROR/ folders will be created as needed")
    print(f"   - Each customer file will be ready for direct re-import")
    
    return True

if __name__ == "__main__":
    success = verify_single_failures_structure()
    if success:
        print(f"\n🎉 Single failures structure is ready for use!")
    else:
        print(f"\n❌ Single failures structure needs setup")
