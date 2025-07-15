#!/usr/bin/env python3
"""
Split a large JSON file with customers into smaller batches of 100 customers each
"""

import json
import os
import math
import sys
from datetime import datetime

def split_json_file(input_file, batch_size=100, output_dir="split_batches"):
    """
    Split a large JSON file into smaller batch files
    
    Args:
        input_file (str): Path to the input JSON file
        batch_size (int): Number of customers per batch (default: 100)
        output_dir (str): Directory to save batch files
    """
    
    print(f"SPLITTING LARGE JSON FILE")
    print("=" * 50)
    print(f"Input file: {input_file}")
    print(f"Batch size: {batch_size} customers")
    print(f"Output directory: {output_dir}")
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"ERROR: Input file '{input_file}' not found!")
        return False
    
    # Get file size for progress info
    file_size = os.path.getsize(input_file)
    print(f"File size: {file_size:,} bytes ({file_size / (1024*1024):.1f} MB)")
    
    try:
        # Load the JSON file
        print(f"Loading JSON file... (this may take a moment for large files)")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"JSON loaded successfully")
        
        # Validate structure
        if not isinstance(data, dict) or 'data' not in data:
            print(f"ERROR: JSON structure invalid. Expected format: {{'data': [...]}}")
            return False
        
        customers = data['data']
        if not isinstance(customers, list):
            print(f"ERROR: 'data' field should be a list of customers")
            return False
        
        total_customers = len(customers)
        print(f"Total customers found: {total_customers:,}")
        
        if total_customers == 0:
            print(f"WARNING: No customers found in the file")
            return False
        
        # Calculate number of batches needed
        num_batches = math.ceil(total_customers / batch_size)
        print(f"Will create {num_batches} batch files")
        
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_output_dir = f"{output_dir}_{timestamp}"
        os.makedirs(full_output_dir, exist_ok=True)
        print(f"Created output directory: {full_output_dir}")
        
        # Split into batches
        batch_files = []
        for batch_num in range(num_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, total_customers)
            
            batch_customers = customers[start_idx:end_idx]
            actual_batch_size = len(batch_customers)
            
            # Create batch data structure
            batch_data = {
                "data": batch_customers
            }
            
            # Generate filename (5 digits for 50K+ files)
            batch_filename = f"batch_{batch_num + 1:05d}_customers_{actual_batch_size}.json"
            batch_filepath = os.path.join(full_output_dir, batch_filename)
            
            # Save batch file
            with open(batch_filepath, 'w', encoding='utf-8') as f:
                json.dump(batch_data, f, indent=2, ensure_ascii=False)
            
            batch_files.append({
                'filename': batch_filename,
                'batch_number': batch_num + 1,
                'customer_count': actual_batch_size,
                'start_customer': start_idx + 1,
                'end_customer': end_idx
            })
            
            # Progress update
            progress = ((batch_num + 1) / num_batches) * 100
            print(f"Created {batch_filename} ({actual_batch_size} customers) - {progress:.1f}% complete")
        
        # Create summary file
        summary_file = os.path.join(full_output_dir, "split_summary.json")
        summary_data = {
            'timestamp': timestamp,
            'input_file': input_file,
            'input_file_size_mb': round(file_size / (1024*1024), 2),
            'total_customers': total_customers,
            'batch_size': batch_size,
            'total_batches': num_batches,
            'output_directory': full_output_dir,
            'batch_files': batch_files
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nSPLITTING COMPLETED SUCCESSFULLY!")
        print(f"Summary:")
        print(f"   - Total customers: {total_customers:,}")
        print(f"   - Batch files created: {num_batches}")
        print(f"   - Customers per batch: {batch_size}")
        print(f"   - Output directory: {full_output_dir}")
        print(f"   - Summary file: split_summary.json")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return False
    except MemoryError:
        print(f"Memory error: File too large to load into memory")
        print(f"Try using a streaming JSON parser for files larger than available RAM")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    # Configuration
    BATCH_SIZE = 100
    OUTPUT_DIR = "customer_batches"
    
    print("JSON BATCH SPLITTER")
    print("=" * 50)
    
    # Check for command line arguments (drag and drop support)
    if len(sys.argv) > 1:
        INPUT_FILE = sys.argv[1]
        print(f"File dropped: {INPUT_FILE}")
    else:
        # Fallback to interactive mode
        INPUT_FILE = "large_customers.json"  # Default file name
        
        # Ask user for input file if default doesn't exist
        if not os.path.exists(INPUT_FILE):
            print(f"Default file '{INPUT_FILE}' not found.")
            user_input = input(f"Enter the path to your JSON file (or drag and drop a file on the exe): ").strip()
            if user_input:
                INPUT_FILE = user_input
            else:
                print("ERROR: No input file provided. Exiting.")
                try:
                    input("Press Enter to exit...")
                except EOFError:
                    pass
                sys.exit(1)
    
    # Run the splitting
    success = split_json_file(INPUT_FILE, BATCH_SIZE, OUTPUT_DIR)
    
    if success:
        print(f"\nAll done! Your batch files are ready for import.")
    else:
        print(f"\nSplitting failed. Please check the error messages above.")
    
    # Keep console open so user can see results
    try:
        input("\nPress Enter to exit...")
    except EOFError:
        pass
