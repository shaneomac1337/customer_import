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
    Split a large JSON file into individual customer files

    Args:
        input_file (str): Path to the input JSON file
        batch_size (int): Number of customers per file (default: 1)
        output_dir (str): Directory to save customer files
    """
    
    print(f"SPLITTING LARGE JSON FILE INTO INDIVIDUAL CUSTOMERS")
    print("=" * 50)
    print(f"Input file: {input_file}")
    print(f"Customers per file: {batch_size}")
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
        
        # Calculate number of files needed
        num_files = math.ceil(total_customers / batch_size)
        print(f"Will create {num_files} individual customer files")
        
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_output_dir = f"{output_dir}_{timestamp}"
        os.makedirs(full_output_dir, exist_ok=True)
        print(f"Created output directory: {full_output_dir}")
        
        # Split into individual customer files
        customer_files = []
        for customer_num in range(num_files):
            start_idx = customer_num * batch_size
            end_idx = min(start_idx + batch_size, total_customers)

            customer_data_list = customers[start_idx:end_idx]
            actual_file_size = len(customer_data_list)

            # Create customer data structure (single customer wrapped in data array)
            customer_data = {
                "data": customer_data_list
            }

            # Generate filename (5 digits for 50K+ files)
            customer_filename = f"customer_{customer_num + 1:05d}.json"
            customer_filepath = os.path.join(full_output_dir, customer_filename)

            # Save customer file
            with open(customer_filepath, 'w', encoding='utf-8') as f:
                json.dump(customer_data, f, indent=2, ensure_ascii=False)

            customer_files.append({
                'filename': customer_filename,
                'file_number': customer_num + 1,
                'customer_count': actual_file_size,
                'customer_index': start_idx + 1
            })

            # Progress update
            progress = ((customer_num + 1) / num_files) * 100
            print(f"Created {customer_filename} (1 customer) - {progress:.1f}% complete")
        
        # Create summary file
        summary_file = os.path.join(full_output_dir, "split_summary.json")
        summary_data = {
            'timestamp': timestamp,
            'input_file': input_file,
            'input_file_size_mb': round(file_size / (1024*1024), 2),
            'total_customers': total_customers,
            'customers_per_file': batch_size,
            'total_files': num_files,
            'output_directory': full_output_dir,
            'customer_files': customer_files
        }

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)

        print(f"\nSPLITTING COMPLETED SUCCESSFULLY!")
        print(f"Summary:")
        print(f"   - Total customers: {total_customers:,}")
        print(f"   - Customer files created: {num_files}")
        print(f"   - Customers per file: {batch_size}")
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
    BATCH_SIZE = 1
    OUTPUT_DIR = "individual_customers"

    print("JSON INDIVIDUAL CUSTOMER SPLITTER")
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
        print(f"\nAll done! Your individual customer files are ready for import.")
    else:
        print(f"\nSplitting failed. Please check the error messages above.")
    
    # Keep console open so user can see results
    try:
        input("\nPress Enter to exit...")
    except EOFError:
        pass
