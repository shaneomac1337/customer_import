#!/usr/bin/env python3
"""
Verify that all customers from the original JSON file are present in the split batch files
"""

import json
import os
import glob
from collections import defaultdict

def verify_split_integrity(original_file, batch_directory):
    """
    Compare original file with split batch files to ensure data integrity
    
    Args:
        original_file (str): Path to the original JSON file
        batch_directory (str): Directory containing the split batch files
    """
    
    print(f"🔍 VERIFYING SPLIT INTEGRITY")
    print("=" * 60)
    print(f"📄 Original file: {original_file}")
    print(f"📁 Batch directory: {batch_directory}")
    
    # Check if files exist
    if not os.path.exists(original_file):
        print(f"❌ Error: Original file '{original_file}' not found!")
        return False
    
    if not os.path.exists(batch_directory):
        print(f"❌ Error: Batch directory '{batch_directory}' not found!")
        return False
    
    try:
        # Load original file
        print(f"📖 Loading original file...")
        with open(original_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        
        if not isinstance(original_data, dict) or 'data' not in original_data:
            print(f"❌ Error: Original file has invalid structure")
            return False
        
        original_customers = original_data['data']
        original_count = len(original_customers)
        print(f"✅ Original file: {original_count:,} customers")
        
        # Find all batch files
        batch_pattern = os.path.join(batch_directory, "batch_*.json")
        batch_files = sorted(glob.glob(batch_pattern))
        
        if not batch_files:
            print(f"❌ Error: No batch files found in '{batch_directory}'")
            return False
        
        print(f"📦 Found {len(batch_files)} batch files")
        
        # Load all batch files and count customers
        total_batch_customers = 0
        batch_details = []
        all_batch_customers = []
        
        for i, batch_file in enumerate(batch_files, 1):
            try:
                with open(batch_file, 'r', encoding='utf-8') as f:
                    batch_data = json.load(f)
                
                if not isinstance(batch_data, dict) or 'data' not in batch_data:
                    print(f"⚠️ Warning: Batch file '{batch_file}' has invalid structure")
                    continue
                
                batch_customers = batch_data['data']
                batch_count = len(batch_customers)
                total_batch_customers += batch_count
                
                batch_details.append({
                    'file': os.path.basename(batch_file),
                    'count': batch_count
                })
                
                # Store customers for detailed comparison
                all_batch_customers.extend(batch_customers)
                
                print(f"📦 {os.path.basename(batch_file)}: {batch_count} customers")
                
            except Exception as e:
                print(f"❌ Error loading batch file '{batch_file}': {e}")
                return False
        
        print(f"\n📊 SUMMARY COMPARISON:")
        print(f"   Original file customers: {original_count:,}")
        print(f"   Batch files customers:   {total_batch_customers:,}")
        print(f"   Difference:              {original_count - total_batch_customers:,}")
        
        # Basic count verification
        if original_count == total_batch_customers:
            print(f"✅ COUNT MATCH: All customers accounted for!")
        else:
            print(f"❌ COUNT MISMATCH: {abs(original_count - total_batch_customers)} customers missing/extra!")
            return False
        
        # Detailed verification - compare customer IDs
        print(f"\n🔍 DETAILED VERIFICATION:")
        print(f"   Comparing customer IDs for exact match...")
        
        # Extract customer IDs from original
        original_ids = set()
        for customer in original_customers:
            if isinstance(customer, dict) and 'person' in customer:
                customer_id = customer['person'].get('customerId')
                if customer_id:
                    original_ids.add(customer_id)
        
        # Extract customer IDs from batches
        batch_ids = set()
        for customer in all_batch_customers:
            if isinstance(customer, dict) and 'person' in customer:
                customer_id = customer['person'].get('customerId')
                if customer_id:
                    batch_ids.add(customer_id)
        
        print(f"   Original unique customer IDs: {len(original_ids):,}")
        print(f"   Batch unique customer IDs:    {len(batch_ids):,}")
        
        # Find missing and extra IDs
        missing_ids = original_ids - batch_ids
        extra_ids = batch_ids - original_ids
        
        if not missing_ids and not extra_ids:
            print(f"✅ PERFECT MATCH: All customer IDs match exactly!")
        else:
            if missing_ids:
                print(f"❌ MISSING IDs: {len(missing_ids)} customer IDs from original not found in batches")
                if len(missing_ids) <= 10:
                    print(f"   Missing IDs: {sorted(list(missing_ids))}")
                else:
                    print(f"   First 10 missing IDs: {sorted(list(missing_ids))[:10]}")
            
            if extra_ids:
                print(f"❌ EXTRA IDs: {len(extra_ids)} customer IDs in batches not found in original")
                if len(extra_ids) <= 10:
                    print(f"   Extra IDs: {sorted(list(extra_ids))}")
                else:
                    print(f"   First 10 extra IDs: {sorted(list(extra_ids))[:10]}")
            
            return False
        
        # Check for duplicates in batches
        batch_id_counts = defaultdict(int)
        for customer in all_batch_customers:
            if isinstance(customer, dict) and 'person' in customer:
                customer_id = customer['person'].get('customerId')
                if customer_id:
                    batch_id_counts[customer_id] += 1
        
        duplicates = {cid: count for cid, count in batch_id_counts.items() if count > 1}
        
        if duplicates:
            print(f"❌ DUPLICATES FOUND: {len(duplicates)} customer IDs appear multiple times in batches")
            if len(duplicates) <= 10:
                for cid, count in list(duplicates.items())[:10]:
                    print(f"   Customer ID '{cid}' appears {count} times")
            else:
                print(f"   First 10 duplicates: {list(duplicates.items())[:10]}")
            return False
        else:
            print(f"✅ NO DUPLICATES: Each customer appears exactly once in batches")
        
        # Create verification report
        report_file = os.path.join(batch_directory, "verification_report.json")
        report_data = {
            'verification_timestamp': __import__('datetime').datetime.now().isoformat(),
            'original_file': original_file,
            'batch_directory': batch_directory,
            'original_customer_count': original_count,
            'batch_customer_count': total_batch_customers,
            'count_match': original_count == total_batch_customers,
            'id_match': len(missing_ids) == 0 and len(extra_ids) == 0,
            'no_duplicates': len(duplicates) == 0,
            'batch_files': batch_details,
            'verification_passed': True
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ VERIFICATION COMPLETED SUCCESSFULLY!")
        print(f"📄 Verification report saved: {report_file}")
        print(f"🎉 All customers from original file are present in batch files!")
        
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error during verification: {e}")
        return False

if __name__ == "__main__":
    # Configuration - update these paths
    ORIGINAL_FILE = "large_customers.json"  # Your original large file
    BATCH_DIRECTORY = "customer_batches_20250708_143022"  # Directory with batch files
    
    print("🔍 SPLIT INTEGRITY VERIFIER")
    print("=" * 60)
    
    # Ask user for paths if defaults don't exist
    if not os.path.exists(ORIGINAL_FILE):
        print(f"Default original file '{ORIGINAL_FILE}' not found.")
        user_input = input(f"Enter path to original JSON file: ").strip()
        if user_input:
            ORIGINAL_FILE = user_input
    
    if not os.path.exists(BATCH_DIRECTORY):
        print(f"Default batch directory '{BATCH_DIRECTORY}' not found.")
        # Try to find batch directories automatically
        batch_dirs = [d for d in os.listdir('.') if d.startswith('customer_batches_') and os.path.isdir(d)]
        if batch_dirs:
            print(f"Found batch directories: {batch_dirs}")
            BATCH_DIRECTORY = batch_dirs[-1]  # Use the most recent one
            print(f"Using: {BATCH_DIRECTORY}")
        else:
            user_input = input(f"Enter path to batch directory: ").strip()
            if user_input:
                BATCH_DIRECTORY = user_input
    
    # Run verification
    success = verify_split_integrity(ORIGINAL_FILE, BATCH_DIRECTORY)
    
    if success:
        print(f"\n🎉 VERIFICATION PASSED: Your split is perfect!")
    else:
        print(f"\n💥 VERIFICATION FAILED: Please check the issues above.")
