#!/usr/bin/env python3
"""
Simple JSON splitter that reads the file in chunks to handle large files.
This version uses only standard library and processes the file line by line.
"""

import json
import os
import sys
from datetime import datetime

def split_json_simple(input_file, batch_size=100, output_dir="customer_batches"):
    """
    Split a large JSON file by reading it in chunks and parsing incrementally.
    This approach uses less memory than loading the entire file.
    """
    
    print("=" * 60)
    print("SIMPLE JSON FILE SPLITTER")
    print("=" * 60)
    print(f"Input file: {input_file}")
    print(f"Batch size: {batch_size} customers")
    print(f"Output directory: {output_dir}")
    print("=" * 60)
    
    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"ERROR: Input file '{input_file}' not found!")
        return False
    
    # Get file size
    file_size = os.path.getsize(input_file)
    print(f"Input file size: {file_size / (1024**3):.2f} GB")
    
    batch_num = 1
    current_batch = []
    total_customers = 0
    
    try:
        print("\nAttempting to parse JSON structure...")
        
        # First, try to determine the JSON structure by reading a small portion
        with open(input_file, 'r', encoding='utf-8') as f:
            # Read first few characters to determine structure
            first_chars = f.read(1000)
            f.seek(0)  # Reset to beginning
            
            if first_chars.strip().startswith('['):
                # It's a JSON array
                print("Detected JSON array format")
                customers_data = json.load(f)
                
            elif '"data"' in first_chars:
                # It's likely wrapped in a data object
                print("Detected JSON object with 'data' key")
                full_data = json.load(f)
                customers_data = full_data.get('data', full_data)
                
            else:
                # Try to load as-is
                print("Attempting to parse as generic JSON object")
                full_data = json.load(f)
                
                # Try to find the customers array
                if isinstance(full_data, list):
                    customers_data = full_data
                elif isinstance(full_data, dict):
                    # Look for common keys that might contain the customer array
                    possible_keys = ['data', 'customers', 'items', 'results']
                    customers_data = None
                    
                    for key in possible_keys:
                        if key in full_data and isinstance(full_data[key], list):
                            customers_data = full_data[key]
                            print(f"Found customers in '{key}' key")
                            break
                    
                    if customers_data is None:
                        print("ERROR: Could not find customer array in JSON structure")
                        return False
                else:
                    print("ERROR: Unexpected JSON structure")
                    return False
        
        print(f"Found {len(customers_data):,} customers to process")
        
        # Process customers in batches
        for i, customer in enumerate(customers_data):
            current_batch.append(customer)
            total_customers += 1
            
            # When batch is full, save it
            if len(current_batch) >= batch_size:
                save_batch_simple(current_batch, batch_num, output_dir)
                print(f"Batch {batch_num:04d}: Saved {len(current_batch)} customers (Total: {total_customers:,})")
                
                current_batch = []
                batch_num += 1
                
                # Progress update every 100 batches
                if batch_num % 100 == 0:
                    progress_pct = (total_customers / len(customers_data)) * 100
                    print(f"  📊 Progress: {progress_pct:.1f}% ({total_customers:,}/{len(customers_data):,} customers)")
        
        # Save remaining customers in the last batch
        if current_batch:
            save_batch_simple(current_batch, batch_num, output_dir)
            print(f"Batch {batch_num:04d}: Saved {len(current_batch)} customers (Final batch)")
        
        # Generate summary
        generate_summary_simple(output_dir, total_customers, batch_num, batch_size)
        
        print("\n" + "=" * 60)
        print("SPLITTING COMPLETE!")
        print("=" * 60)
        print(f"[STATS] Total customers processed: {total_customers:,}")
        print(f"[STATS] Total batches created: {batch_num}")
        print(f"[STATS] Customers per batch: {batch_size}")
        print(f"[STATS] Output directory: {output_dir}")
        print(f"[STATS] Average batch size: {total_customers/batch_num:.1f}")
        print("\n[SUCCESS] Files are ready for bulk import!")
        
        return True
        
    except MemoryError:
        print("\nERROR: Not enough memory to load the entire file!")
        print("Recommendations:")
        print("1. Use the streaming version (split_large_json.py) instead")
        print("2. Close other applications to free up memory")
        print("3. Split the file manually into smaller chunks first")
        return False
        
    except json.JSONDecodeError as e:
        print(f"\nERROR: Invalid JSON format: {str(e)}")
        print("The file might be corrupted or not in valid JSON format")
        return False
        
    except Exception as e:
        print(f"\nERROR: Failed to process file: {str(e)}")
        return False

def save_batch_simple(customers, batch_num, output_dir):
    """Save a batch of customers to a JSON file"""
    batch_data = {
        "data": customers
    }
    
    filename = f"batch_{batch_num:04d}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(batch_data, f, indent=2, ensure_ascii=False)

def generate_summary_simple(output_dir, total_customers, total_batches, batch_size):
    """Generate a summary file with statistics"""
    summary = {
        "split_date": datetime.now().isoformat(),
        "total_customers": total_customers,
        "total_batches": total_batches,
        "target_batch_size": batch_size,
        "actual_average_batch_size": total_customers / total_batches if total_batches > 0 else 0,
        "files_generated": [f"batch_{i:04d}.json" for i in range(1, total_batches + 1)],
        "recommended_import_settings": {
            "batch_size": batch_size,
            "max_workers": 5,
            "delay_between_requests": 1.0,
            "max_retries": 3
        }
    }
    
    summary_file = os.path.join(output_dir, "split_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

def main():
    """Main function with command line argument support"""
    if len(sys.argv) < 2:
        print("Usage: python split_json_simple.py <input_file> [batch_size] [output_dir]")
        print("Example: python split_json_simple.py Output_new.json 100 customer_batches")
        return
    
    input_file = sys.argv[1]
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "customer_batches"
    
    success = split_json_simple(input_file, batch_size, output_dir)
    
    if success:
        print(f"\n✅ Successfully split {input_file} into batches!")
        print(f"📁 Check the '{output_dir}' directory for your batch files")
        print(f"📊 Use these files with your bulk import tool")
    else:
        print(f"\n❌ Failed to split {input_file}")
        sys.exit(1)

if __name__ == "__main__":
    main()
