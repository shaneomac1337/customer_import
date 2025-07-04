#!/usr/bin/env python3
"""
Simple utility to browse and manage batch retry files
"""

import json
import os
from datetime import datetime

def list_batch_retry_files():
    """List all available batch retry files"""
    retry_dir = os.path.join("failed_customers", "batches_to_retry")
    
    if not os.path.exists(retry_dir):
        print("❌ No batch retry directory found!")
        print(f"   Expected: {retry_dir}")
        print("   Run some imports with failures first to generate batch retry files.")
        return []
    
    # Find all batch files
    batch_files = []
    for file in os.listdir(retry_dir):
        if file.startswith('batch_') and file.endswith('.json'):
            file_path = os.path.join(retry_dir, file)
            file_size = os.path.getsize(file_path)
            file_mtime = os.path.getmtime(file_path)
            
            # Try to read the file to get customer count
            customer_count = 0
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'data' in data:
                        customer_count = len(data['data'])
            except:
                pass
            
            batch_files.append({
                'filename': file,
                'filepath': file_path,
                'size': file_size,
                'modified': datetime.fromtimestamp(file_mtime),
                'customers': customer_count
            })
    
    # Sort by filename (which includes batch number)
    batch_files.sort(key=lambda x: x['filename'])
    
    return batch_files

def show_batch_details(batch_file_path):
    """Show details of a specific batch file"""
    try:
        with open(batch_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'data' not in data:
            print(f"❌ Invalid batch file format - missing 'data' key")
            return
        
        customers = data['data']
        print(f"\n📋 Batch Details: {os.path.basename(batch_file_path)}")
        print(f"   - Total Customers: {len(customers)}")
        print(f"   - File Size: {os.path.getsize(batch_file_path):,} bytes")
        print(f"   - Ready for Import: ✅ YES")
        
        print(f"\n👥 Customer List:")
        for i, customer in enumerate(customers[:10], 1):  # Show first 10
            if 'person' in customer:
                person = customer['person']
                customer_id = person.get('customerId', 'Unknown')
                first_name = person.get('firstName', 'Unknown')
                last_name = person.get('lastName', 'Unknown')
                print(f"   {i:2d}. {first_name} {last_name} (ID: {customer_id})")
            else:
                print(f"   {i:2d}. Unknown customer format")
        
        if len(customers) > 10:
            print(f"   ... and {len(customers) - 10} more customers")
        
        print(f"\n💡 To retry this batch:")
        print(f"   1. Open the Bulk Import GUI")
        print(f"   2. Click 'Browse' and select: {batch_file_path}")
        print(f"   3. Click 'Start Import' - the file is ready to use!")
        
    except Exception as e:
        print(f"❌ Error reading batch file: {e}")

def main():
    """Main function"""
    print("📁 Batch Retry Files Browser")
    print("=" * 50)
    
    batch_files = list_batch_retry_files()
    
    if not batch_files:
        return
    
    print(f"📊 Found {len(batch_files)} batch retry file(s):")
    print()
    
    total_customers = 0
    for i, batch_file in enumerate(batch_files, 1):
        total_customers += batch_file['customers']
        print(f"{i:2d}. {batch_file['filename']}")
        print(f"    - Customers: {batch_file['customers']}")
        print(f"    - Size: {batch_file['size']:,} bytes")
        print(f"    - Modified: {batch_file['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    print(f"📈 Summary:")
    print(f"   - Total Batch Files: {len(batch_files)}")
    print(f"   - Total Customers to Retry: {total_customers:,}")
    print(f"   - Directory: failed_customers/batches_to_retry/")
    
    # Interactive mode
    while True:
        print(f"\n🔍 Options:")
        print(f"   1-{len(batch_files)}: View details of batch file")
        print(f"   'all': Show details of all batch files")
        print(f"   'quit' or 'q': Exit")
        
        choice = input(f"\nEnter your choice: ").strip().lower()
        
        if choice in ['quit', 'q', 'exit']:
            break
        elif choice == 'all':
            for batch_file in batch_files:
                show_batch_details(batch_file['filepath'])
                print("-" * 50)
        else:
            try:
                index = int(choice) - 1
                if 0 <= index < len(batch_files):
                    show_batch_details(batch_files[index]['filepath'])
                else:
                    print(f"❌ Invalid choice. Please enter 1-{len(batch_files)}")
            except ValueError:
                print(f"❌ Invalid choice. Please enter a number, 'all', or 'quit'")
    
    print(f"\n👋 Goodbye!")

if __name__ == "__main__":
    main()
