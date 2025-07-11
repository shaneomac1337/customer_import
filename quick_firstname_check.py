#!/usr/bin/env python3
"""
Quick checker for spaces in firstName fields.
This script provides immediate console output for quick verification.
"""

import json
import os
import sys
import glob

def quick_check_firstname_spaces(batch_dir="customer_batches", max_examples=20):
    """
    Quick check for firstName fields containing spaces with console output.
    
    Args:
        batch_dir (str): Directory containing batch files
        max_examples (int): Maximum number of examples to show
    """
    
    print("🔍 Quick FirstName Space Checker")
    print("=" * 50)
    
    if not os.path.exists(batch_dir):
        print(f"❌ Directory '{batch_dir}' not found!")
        return False
    
    # Find batch files
    batch_files = glob.glob(os.path.join(batch_dir, "batch_*.json"))
    if not batch_files:
        batch_files = glob.glob(os.path.join(batch_dir, "*.json"))
    
    if not batch_files:
        print(f"❌ No batch files found in '{batch_dir}'!")
        return False
    
    batch_files.sort()
    print(f"📁 Found {len(batch_files)} batch files")
    
    customers_with_spaces = []
    total_customers = 0
    files_processed = 0
    
    print("\n🔄 Scanning files...")
    
    for batch_file in batch_files:
        try:
            with open(batch_file, 'r', encoding='utf-8') as f:
                batch_data = json.load(f)
            
            # Extract customers
            if isinstance(batch_data, dict) and 'data' in batch_data:
                customers = batch_data['data']
            elif isinstance(batch_data, list):
                customers = batch_data
            else:
                continue
            
            for i, customer in enumerate(customers):
                total_customers += 1
                
                # Get firstName
                first_name = None
                customer_id = "Unknown"
                
                try:
                    if 'person' in customer and 'firstName' in customer['person']:
                        first_name = customer['person']['firstName']
                        customer_id = customer['person'].get('customerId', 'Unknown')
                    elif 'firstName' in customer:
                        first_name = customer['firstName']
                        customer_id = customer.get('customerId', 'Unknown')
                    
                    # Check for spaces
                    if first_name and ' ' in first_name:
                        customers_with_spaces.append({
                            "file": os.path.basename(batch_file),
                            "customer_id": customer_id,
                            "firstName": first_name,
                            "word_count": len(first_name.split())
                        })
                
                except Exception:
                    continue
            
            files_processed += 1
            
            # Progress indicator
            if files_processed % 50 == 0:
                print(f"  📊 {files_processed}/{len(batch_files)} files processed...")
        
        except Exception as e:
            print(f"⚠️  Error in {os.path.basename(batch_file)}: {e}")
            continue
    
    # Results
    print("\n" + "=" * 50)
    print("📊 RESULTS")
    print("=" * 50)
    print(f"Total customers scanned: {total_customers:,}")
    print(f"Customers with spaces in firstName: {len(customers_with_spaces):,}")
    
    if total_customers > 0:
        percentage = (len(customers_with_spaces) / total_customers) * 100
        print(f"Percentage with spaces: {percentage:.2f}%")
    
    if customers_with_spaces:
        print(f"\n🔍 Examples (showing first {min(max_examples, len(customers_with_spaces))}):")
        print("-" * 50)
        
        for i, customer in enumerate(customers_with_spaces[:max_examples]):
            print(f"{i+1:2d}. '{customer['firstName']}' ({customer['word_count']} words)")
            print(f"    Customer ID: {customer['customer_id']}")
            print(f"    File: {customer['file']}")
            print()
        
        if len(customers_with_spaces) > max_examples:
            print(f"... and {len(customers_with_spaces) - max_examples} more")
        
        # Show word count distribution
        word_counts = {}
        for customer in customers_with_spaces:
            count = customer['word_count']
            word_counts[count] = word_counts.get(count, 0) + 1
        
        print(f"\n📈 Word Count Distribution:")
        for count in sorted(word_counts.keys()):
            print(f"  {count} words: {word_counts[count]:,} customers")
    
    else:
        print("\n✅ No customers found with spaces in firstName!")
    
    return True

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Usage: python quick_firstname_check.py [batch_directory] [max_examples]")
        print("Example: python quick_firstname_check.py customer_batches 30")
        print("Default: python quick_firstname_check.py customer_batches 20")
        return
    
    batch_dir = sys.argv[1] if len(sys.argv) > 1 else "customer_batches"
    max_examples = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    # Check if specific directory exists, try alternatives
    if not os.path.exists(batch_dir):
        # Try to find directories with batch files
        possible_dirs = [
            "customer_batches_20250709_160330",
            "customer_batches",
            "batches_to_retry",
            "."
        ]
        
        found_dir = None
        for dir_name in possible_dirs:
            if os.path.exists(dir_name):
                batch_files = glob.glob(os.path.join(dir_name, "*.json"))
                if batch_files:
                    found_dir = dir_name
                    break
        
        if found_dir:
            print(f"📁 Using directory: {found_dir}")
            batch_dir = found_dir
        else:
            print(f"❌ No batch directory found. Tried: {', '.join(possible_dirs)}")
            return
    
    success = quick_check_firstname_spaces(batch_dir, max_examples)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
