#!/usr/bin/env python3
"""
Split a large JSON file with customers into individual customer files (1 customer per JSON)
"""

import json
import os
import math
import sys
from datetime import datetime

def split_json_file(input_file, batch_size=1, output_dir="split_customers"):
    """
    Split a large JSON file into individual customer/household files

    Args:
        input_file (str): Path to the input JSON file
        batch_size (int): Number of customers/households per file (default: 1)
        output_dir (str): Directory to save files
    """
    
    print(f"SPLITTING LARGE JSON FILE")
    print("=" * 50)
    print(f"Input file: {input_file}")
    print(f"Items per file: {batch_size}")
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
        
        # Validate structure and auto-detect data key
        if not isinstance(data, dict):
            print(f"ERROR: JSON structure invalid. Expected format: {{'data': [...]}} or {{'households': [...]}}")
            return False
        
        # Auto-detect the data key and normalize
        # Input can be: 'data', 'customers', or 'households'
        # Output will be: 'data' (for customers) or 'households' (for households)
        input_key = None
        output_key = None
        
        if 'data' in data:
            input_key = 'data'
            output_key = 'data'
            item_type = 'customers'
        elif 'customers' in data:
            input_key = 'customers'
            output_key = 'data'  # Convert to 'data' for import compatibility
            item_type = 'customers'
            print(f"Note: Converting 'customers' key to 'data' key for import compatibility")
        elif 'households' in data:
            input_key = 'households'
            output_key = 'households'
            item_type = 'households'
        else:
            print(f"ERROR: JSON structure invalid. Expected 'data', 'customers', or 'households' key")
            return False
        
        print(f"Detected format: {item_type} (input key: '{input_key}', output key: '{output_key}')")
        
        customers = data[input_key]
        if not isinstance(customers, list):
            print(f"ERROR: '{input_key}' field should be a list")
            return False
        
        total_customers = len(customers)
        print(f"Total {item_type} found: {total_customers:,}")
        
        if total_customers == 0:
            print(f"WARNING: No customers found in the file")
            return False
        
        # Calculate number of files needed
        num_files = math.ceil(total_customers / batch_size)
        print(f"Will create {num_files} batch files ({batch_size} items per batch)")
        
        # Create output directory with type-specific name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if item_type == 'households':
            dir_name = f"household_batches_{timestamp}"
        else:
            dir_name = f"customer_batches_{timestamp}"
        full_output_dir = dir_name
        os.makedirs(full_output_dir, exist_ok=True)
        print(f"Created output directory: {full_output_dir}")
        
        # Split into individual customer files
        customer_files = []
        for customer_num in range(num_files):
            start_idx = customer_num * batch_size
            end_idx = min(start_idx + batch_size, total_customers)

            customer_data_list = customers[start_idx:end_idx]
            actual_file_size = len(customer_data_list)

            # Create data structure with output key (data or households)
            customer_data = {
                output_key: customer_data_list
            }

            # Generate filename (5 digits for 50K+ files)
            if output_key == "households":
                customer_filename = f"household_batch_{customer_num + 1:05d}.json"
            else:
                customer_filename = f"customer_batch_{customer_num + 1:05d}.json"
            customer_filepath = os.path.join(full_output_dir, customer_filename)

            # Save customer file
            with open(customer_filepath, 'w', encoding='utf-8') as f:
                json.dump(customer_data, f, indent=2, ensure_ascii=False)

            customer_files.append({
                'filename': customer_filename,
                'file_number': customer_num + 1,
                'item_count': actual_file_size,
                'item_index': start_idx + 1
            })

            # Progress update
            progress = ((customer_num + 1) / num_files) * 100
            print(f"Created {customer_filename} ({actual_file_size} {item_type}) - {progress:.1f}% complete")
        
        # Create summary file
        summary_file = os.path.join(full_output_dir, "split_summary.json")
        summary_data = {
            'timestamp': timestamp,
            'input_file': input_file,
            'input_file_size_mb': round(file_size / (1024*1024), 2),
            'import_type': item_type,
            'input_key': input_key,
            'output_key': output_key,
            'total_items': total_customers,
            'items_per_file': batch_size,
            'total_files': num_files,
            'output_directory': full_output_dir,
            'files': customer_files
        }

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)

        print(f"\nSPLITTING COMPLETED SUCCESSFULLY!")
        print(f"Summary:")
        print(f"   - Import type: {item_type}")
        print(f"   - Input key: '{input_key}' → Output key: '{output_key}'")
        print(f"   - Total items: {total_customers:,}")
        print(f"   - Files created: {num_files}")
        print(f"   - Items per file: {batch_size}")
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

    print("JSON BATCH SPLITTER (100 items per batch)")
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
