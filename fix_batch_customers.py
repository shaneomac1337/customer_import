import json

def fix_batch_customers():
    """Fix the customers_100_batch.json file by adding missing customerIds"""
    
    filename = 'customers_100_batch.json'
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    if 'data' not in data or not isinstance(data['data'], list):
        print("Invalid file structure")
        return
    
    # Add customerIds to each customer
    for i, customer in enumerate(data['data']):
        if 'person' in customer:
            # Generate a unique customer ID
            customer_id = f"30000{i+1:06d}"
            customer['person']['customerId'] = customer_id
            print(f"Added customerId {customer_id} to customer {i+1}: {customer['person'].get('firstName', 'N/A')} {customer['person'].get('lastName', 'N/A')}")
    
    # Save the fixed file
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        print(f"\nSuccessfully fixed {filename}")
    except Exception as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    fix_batch_customers()