#!/usr/bin/env python3
"""
Check for spaces in firstName fields across batch files.
This script will scan all batch files and identify customers with spaces in their firstName.
"""

import json
import os
import sys
from datetime import datetime
import glob

def check_firstname_spaces(batch_dir="customer_batches", output_file="firstname_spaces_report.json"):
    """
    Check all batch files for firstName fields containing spaces.
    
    Args:
        batch_dir (str): Directory containing batch files
        output_file (str): Output file for the report
    """
    
    print("=" * 60)
    print("FIRSTNAME SPACE CHECKER")
    print("=" * 60)
    print(f"Batch directory: {batch_dir}")
    print(f"Output report: {output_file}")
    print("=" * 60)
    
    if not os.path.exists(batch_dir):
        print(f"ERROR: Directory '{batch_dir}' not found!")
        return False
    
    # Find all batch JSON files
    batch_files = glob.glob(os.path.join(batch_dir, "batch_*.json"))
    if not batch_files:
        batch_files = glob.glob(os.path.join(batch_dir, "*.json"))
    
    if not batch_files:
        print(f"ERROR: No batch files found in '{batch_dir}'!")
        return False
    
    batch_files.sort()  # Process in order
    print(f"Found {len(batch_files)} batch files to process")
    
    # Results tracking
    customers_with_spaces = []
    total_customers = 0
    total_batches = 0
    files_with_issues = []
    
    print("\nProcessing batch files...")
    
    for batch_file in batch_files:
        try:
            with open(batch_file, 'r', encoding='utf-8') as f:
                batch_data = json.load(f)
            
            # Extract customers array
            if isinstance(batch_data, dict) and 'data' in batch_data:
                customers = batch_data['data']
            elif isinstance(batch_data, list):
                customers = batch_data
            else:
                print(f"WARNING: Unexpected format in {os.path.basename(batch_file)}")
                continue
            
            batch_issues = []
            
            for i, customer in enumerate(customers):
                total_customers += 1
                
                # Navigate to firstName field
                first_name = None
                customer_id = "Unknown"
                
                try:
                    if 'person' in customer and 'firstName' in customer['person']:
                        first_name = customer['person']['firstName']
                        customer_id = customer['person'].get('customerId', 'Unknown')
                    elif 'firstName' in customer:
                        first_name = customer['firstName']
                        customer_id = customer.get('customerId', customer.get('id', 'Unknown'))
                    
                    # Check for spaces in firstName
                    if first_name and ' ' in first_name:
                        issue = {
                            "batch_file": os.path.basename(batch_file),
                            "customer_index": i,
                            "customer_id": customer_id,
                            "firstName": first_name,
                            "space_count": first_name.count(' '),
                            "words": first_name.split()
                        }
                        
                        customers_with_spaces.append(issue)
                        batch_issues.append(issue)
                
                except Exception as e:
                    print(f"WARNING: Error processing customer {i} in {os.path.basename(batch_file)}: {e}")
            
            total_batches += 1
            
            if batch_issues:
                files_with_issues.append({
                    "file": os.path.basename(batch_file),
                    "issues_count": len(batch_issues),
                    "issues": batch_issues
                })
                print(f"  {os.path.basename(batch_file)}: Found {len(batch_issues)} customers with spaces in firstName")
            
            # Progress update every 100 files
            if total_batches % 100 == 0:
                print(f"  📊 Progress: {total_batches}/{len(batch_files)} files processed ({total_customers:,} customers)")
        
        except Exception as e:
            print(f"ERROR: Failed to process {os.path.basename(batch_file)}: {e}")
            continue
    
    # Generate detailed report
    report = {
        "scan_date": datetime.now().isoformat(),
        "summary": {
            "total_batches_scanned": total_batches,
            "total_customers_scanned": total_customers,
            "customers_with_spaces": len(customers_with_spaces),
            "files_with_issues": len(files_with_issues),
            "percentage_with_spaces": (len(customers_with_spaces) / total_customers * 100) if total_customers > 0 else 0
        },
        "files_with_issues": files_with_issues,
        "all_customers_with_spaces": customers_with_spaces,
        "statistics": {
            "most_common_patterns": get_common_patterns(customers_with_spaces),
            "space_count_distribution": get_space_distribution(customers_with_spaces)
        }
    }
    
    # Save report
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "=" * 60)
    print("SCAN COMPLETE!")
    print("=" * 60)
    print(f"[STATS] Total batches scanned: {total_batches}")
    print(f"[STATS] Total customers scanned: {total_customers:,}")
    print(f"[STATS] Customers with spaces in firstName: {len(customers_with_spaces):,}")
    print(f"[STATS] Files with issues: {len(files_with_issues)}")
    print(f"[STATS] Percentage with spaces: {report['summary']['percentage_with_spaces']:.2f}%")
    print(f"[STATS] Report saved to: {output_file}")
    
    if customers_with_spaces:
        print(f"\n[ISSUES FOUND] Examples of firstName with spaces:")
        for i, issue in enumerate(customers_with_spaces[:10]):  # Show first 10
            print(f"  {i+1}. '{issue['firstName']}' (Customer ID: {issue['customer_id']}, File: {issue['batch_file']})")
        
        if len(customers_with_spaces) > 10:
            print(f"  ... and {len(customers_with_spaces) - 10} more (see report file for full list)")
    else:
        print(f"\n[SUCCESS] No customers found with spaces in firstName!")
    
    return True

def get_common_patterns(customers_with_spaces):
    """Analyze common patterns in firstName with spaces"""
    patterns = {}
    
    for customer in customers_with_spaces:
        words = customer['words']
        pattern = f"{len(words)} words"
        
        if pattern not in patterns:
            patterns[pattern] = {
                "count": 0,
                "examples": []
            }
        
        patterns[pattern]["count"] += 1
        if len(patterns[pattern]["examples"]) < 5:  # Keep up to 5 examples
            patterns[pattern]["examples"].append(customer['firstName'])
    
    return patterns

def get_space_distribution(customers_with_spaces):
    """Get distribution of space counts"""
    distribution = {}
    
    for customer in customers_with_spaces:
        space_count = customer['space_count']
        
        if space_count not in distribution:
            distribution[space_count] = 0
        
        distribution[space_count] += 1
    
    return distribution

def main():
    """Main function with command line argument support"""
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Usage: python check_firstname_spaces.py [batch_directory] [output_file]")
        print("Example: python check_firstname_spaces.py customer_batches firstname_report.json")
        print("Default: python check_firstname_spaces.py customer_batches firstname_spaces_report.json")
        return
    
    batch_dir = sys.argv[1] if len(sys.argv) > 1 else "customer_batches"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "firstname_spaces_report.json"
    
    success = check_firstname_spaces(batch_dir, output_file)
    
    if success:
        print(f"\n✅ Successfully scanned batch files!")
        print(f"📁 Check '{output_file}' for detailed report")
    else:
        print(f"\n❌ Failed to scan batch files")
        sys.exit(1)

if __name__ == "__main__":
    main()
