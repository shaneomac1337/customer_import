#!/usr/bin/env python3
"""
Utility script to analyze failed customers by batch and create batch-specific retry files
"""

import json
import os
from datetime import datetime
from collections import defaultdict, Counter

def load_failed_customers(file_path):
    """Load failed customers from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading failed customers file: {e}")
        return []

def analyze_failed_customers_by_batch(failed_customers):
    """Analyze failed customers grouped by batch"""
    
    # Group by batch
    batches = defaultdict(list)
    batch_info = {}
    
    for customer in failed_customers:
        batch_id = customer.get('batch_id', 'unknown')
        batches[batch_id].append(customer)
        
        # Store batch metadata
        if batch_id not in batch_info:
            batch_info[batch_id] = {
                'batch_number': customer.get('batch_number', 'unknown'),
                'total_batches': customer.get('total_batches', 'unknown'),
                'batch_size': customer.get('batch_size', 'unknown'),
                'source_file': customer.get('source_file', 'unknown'),
                'complete_batch_data': customer.get('complete_batch_data', [])
            }
    
    return batches, batch_info

def create_batch_retry_files(batches, batch_info, output_dir="batch_retry_files"):
    """Create individual retry files for each failed batch"""
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_output_dir = f"{output_dir}_{timestamp}"
    os.makedirs(full_output_dir, exist_ok=True)
    
    retry_files = []
    
    for batch_id, failed_customers in batches.items():
        if batch_id == 'unknown':
            continue
            
        batch_meta = batch_info[batch_id]
        
        # Use complete batch data if available, otherwise just failed customers
        if batch_meta['complete_batch_data']:
            retry_data = {
                "data": batch_meta['complete_batch_data']
            }
            file_suffix = "complete_batch"
        else:
            # Extract original data from failed customers
            retry_customers = []
            for fc in failed_customers:
                if fc.get('originalData'):
                    retry_customers.append(fc['originalData'])
            
            retry_data = {
                "data": retry_customers
            }
            file_suffix = "failed_only"
        
        # Create filename (5 digits for 50K+ files)
        batch_num = f"{batch_id:05d}"
        retry_filename = f"retry_batch_{batch_num}_{file_suffix}.json"
        retry_filepath = os.path.join(full_output_dir, retry_filename)
        
        # Save retry file
        with open(retry_filepath, 'w', encoding='utf-8') as f:
            json.dump(retry_data, f, indent=2, ensure_ascii=False)
        
        retry_files.append({
            'filename': retry_filename,
            'batch_id': batch_id,
            'batch_number': batch_meta['batch_number'],
            'failed_count': len(failed_customers),
            'total_customers': len(retry_data['data']),
            'source_file': batch_meta['source_file'],
            'type': file_suffix
        })
    
    return full_output_dir, retry_files

def print_batch_analysis(batches, batch_info):
    """Print detailed batch analysis"""
    
    print("📊 FAILED CUSTOMERS BATCH ANALYSIS")
    print("=" * 60)
    
    # Overall statistics
    total_failed = sum(len(customers) for customers in batches.values())
    total_batches = len(batches)
    
    print(f"📈 Overall Statistics:")
    print(f"   - Total Failed Customers: {total_failed:,}")
    print(f"   - Total Affected Batches: {total_batches}")
    print(f"   - Average Failures per Batch: {total_failed/total_batches:.1f}")
    
    # Error analysis
    all_errors = []
    for customers in batches.values():
        for customer in customers:
            all_errors.append(customer.get('error', 'Unknown'))
    
    error_counts = Counter(all_errors)
    print(f"\n🔍 Error Types:")
    for error, count in error_counts.most_common(5):
        print(f"   - {error}: {count} occurrences")
    
    print(f"\n📋 Batch Details:")
    print("-" * 60)
    
    # Sort batches by batch_id
    sorted_batches = sorted(batches.items(), key=lambda x: x[0] if isinstance(x[0], int) else 999)
    
    for batch_id, failed_customers in sorted_batches:
        batch_meta = batch_info[batch_id]
        
        print(f"🏷️  Batch {batch_id} ({batch_meta['batch_number']}):")
        print(f"   - Failed Customers: {len(failed_customers)}")
        print(f"   - Batch Size: {batch_meta['batch_size']}")
        print(f"   - Source File: {batch_meta['source_file']}")
        print(f"   - Complete Batch Available: {'✅ YES' if batch_meta['complete_batch_data'] else '❌ NO'}")
        
        # Show first few failed customers
        print(f"   - Failed Customer IDs: ", end="")
        customer_ids = [fc.get('customerId', 'Unknown') for fc in failed_customers[:3]]
        print(", ".join(customer_ids), end="")
        if len(failed_customers) > 3:
            print(f" ... and {len(failed_customers) - 3} more")
        else:
            print()
        
        # Show unique errors in this batch
        batch_errors = set(fc.get('error', 'Unknown') for fc in failed_customers)
        if len(batch_errors) == 1:
            print(f"   - Error: {list(batch_errors)[0]}")
        else:
            print(f"   - Errors: {len(batch_errors)} different types")
        
        print()

def main():
    """Main function to analyze failed customers"""
    
    print("🔍 Failed Customers Batch Analyzer")
    print("=" * 60)
    
    # Find failed customers files
    failed_files = []
    
    # Check current directory
    for file in os.listdir('.'):
        if file.startswith('failed_customers') and file.endswith('.json'):
            failed_files.append(file)
    
    # Check failed_customers directory
    if os.path.exists('failed_customers'):
        for file in os.listdir('failed_customers'):
            if file.endswith('.json'):
                failed_files.append(os.path.join('failed_customers', file))
    
    if not failed_files:
        print("❌ No failed customers files found!")
        print("   Looking for files matching: failed_customers*.json")
        print("   Or files in failed_customers/ directory")
        return
    
    print(f"📁 Found {len(failed_files)} failed customers file(s):")
    for i, file in enumerate(failed_files, 1):
        file_size = os.path.getsize(file)
        print(f"   {i}. {file} ({file_size:,} bytes)")
    
    # Use the most recent file (largest number in filename)
    latest_file = max(failed_files, key=lambda f: os.path.getmtime(f))
    print(f"\n📋 Analyzing: {latest_file}")
    
    # Load and analyze
    failed_customers = load_failed_customers(latest_file)
    
    if not failed_customers:
        print("❌ No failed customers data found!")
        return
    
    print(f"✅ Loaded {len(failed_customers)} failed customers")
    
    # Check if enhanced format is available
    sample_customer = failed_customers[0]
    has_batch_info = 'batch_id' in sample_customer
    has_complete_batch = 'complete_batch_data' in sample_customer
    
    print(f"🔧 Data Format:")
    print(f"   - Enhanced Batch Info: {'✅ Available' if has_batch_info else '❌ Not Available'}")
    print(f"   - Complete Batch Data: {'✅ Available' if has_complete_batch else '❌ Not Available'}")
    
    if not has_batch_info:
        print("\n⚠️  This file was created before the batch enhancement.")
        print("   Limited analysis available. Run a new import to get enhanced data.")
        return
    
    # Perform batch analysis
    batches, batch_info = analyze_failed_customers_by_batch(failed_customers)
    
    print_batch_analysis(batches, batch_info)
    
    # Create retry files
    print("🔄 Creating Batch-Specific Retry Files...")
    output_dir, retry_files = create_batch_retry_files(batches, batch_info)
    
    print(f"✅ Created {len(retry_files)} retry files in: {output_dir}")
    print("\n📄 Retry Files Created:")
    
    for retry_file in retry_files:
        print(f"   - {retry_file['filename']}")
        print(f"     Batch: {retry_file['batch_number']}")
        print(f"     Failed: {retry_file['failed_count']} customers")
        print(f"     Total: {retry_file['total_customers']} customers")
        print(f"     Type: {retry_file['type']}")
        print(f"     Source: {retry_file['source_file']}")
        print()
    
    print("🎯 ANALYSIS COMPLETE!")
    print(f"   - Use the retry files in {output_dir} for reprocessing")
    print(f"   - Each file contains the complete batch data for easy re-import")
    print("   - Load these files in the Bulk Import GUI for retry")

if __name__ == "__main__":
    main()
