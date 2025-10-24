"""
Test Data Generator for Customers and Households
Generates matching customer and household JSON files for testing import functionality
"""

import json
import random
from datetime import datetime, timedelta
import argparse

# Sample Swedish names for realistic test data
FIRST_NAMES = [
    "Erik", "Lars", "Karl", "Anders", "Per", "Johan", "Nils", "Sven", "Olof", "Gustaf",
    "Anna", "Maria", "Karin", "Kristina", "Eva", "Birgitta", "Margareta", "Elisabeth", "Ingrid", "Monica",
    "Emma", "Oscar", "Alice", "Hugo", "Maja", "Elias", "Ella", "William", "Linnea", "Lucas",
    "Astrid", "Axel", "Ebba", "Liam", "Wilma", "Noah", "Alva", "Oliver", "Saga", "Matteo"
]

LAST_NAMES = [
    "Andersson", "Johansson", "Karlsson", "Nilsson", "Eriksson", "Larsson", "Olsson", "Persson", "Svensson", "Gustafsson",
    "Pettersson", "Jonsson", "Jansson", "Hansson", "Bengtsson", "Jönsson", "Lindberg", "Jakobsson", "Magnusson", "Olofsson",
    "Lindström", "Lindqvist", "Lindgren", "Berg", "Axelsson", "Bergström", "Lundberg", "Lind", "Lundgren", "Lundqvist",
    "Mattsson", "Berglund", "Fredriksson", "Sandberg", "Henriksson", "Forsberg", "Sjöberg", "Wallin", "Engström", "Eklund"
]

def generate_customer_id(start_id):
    """Generate a customer ID"""
    return str(start_id)

def generate_birthday():
    """Generate a random birthday between 1940 and 2010"""
    start_date = datetime(1940, 1, 1)
    end_date = datetime(2010, 12, 31)
    random_days = random.randint(0, (end_date - start_date).days)
    birthday = start_date + timedelta(days=random_days)
    return birthday.strftime("%Y-%m-%d")

def generate_customer(customer_id, first_name=None, last_name=None):
    """Generate a single customer object"""
    if not first_name:
        first_name = random.choice(FIRST_NAMES)
    if not last_name:
        last_name = random.choice(LAST_NAMES)
    
    return {
        "changeType": "CREATE",
        "type": "PERSON",
        "person": {
            "customerId": customer_id,
            "status": random.choice(["ACTIVE", "ACTIVE", "ACTIVE", "UNACTIVATED"]),  # 75% active
            "firstName": first_name,
            "lastName": last_name,
            "languageCode": "sv",
            "birthday": generate_birthday(),
            "statisticalUseAllowed": random.choice([True, False]),
            "marketingAllowedFlag": random.choice([True, False]),
            "declarationAvailable": True
        }
    }

def generate_household(household_id, primary_member_id, member_ids, primary_member_name):
    """Generate a single household object"""
    return {
        "changeType": "CREATE",
        "householdId": household_id,
        "name": primary_member_name,
        "status": "ACTIVE",
        "primaryMemberId": primary_member_id,
        "memberIds": member_ids
    }

def generate_test_data(num_customers=1000, start_id=60000000, output_prefix="generated"):
    """
    Generate test customer and household data
    
    Args:
        num_customers: Total number of customers to generate
        start_id: Starting customer ID
        output_prefix: Prefix for output files
    """
    
    print(f"🎲 Generating {num_customers} customers and matching households...")
    
    customers = []
    households = []
    
    current_id = start_id
    customers_created = 0
    
    while customers_created < num_customers:
        # Random household size (1-5 members)
        household_size = random.randint(1, 5)
        
        # Don't exceed total requested customers
        if customers_created + household_size > num_customers:
            household_size = num_customers - customers_created
        
        # Generate household members
        household_member_ids = []
        household_customers = []
        
        # Generate a shared last name for this household (80% chance)
        shared_last_name = random.choice(LAST_NAMES) if random.random() < 0.8 else None
        
        for i in range(household_size):
            customer_id = generate_customer_id(current_id)
            
            # Use shared last name if applicable
            last_name = shared_last_name if shared_last_name else random.choice(LAST_NAMES)
            customer = generate_customer(customer_id, last_name=last_name)
            
            customers.append(customer)
            household_member_ids.append(customer_id)
            household_customers.append(customer)
            
            current_id += 1
            customers_created += 1
        
        # Create household with first member as primary
        primary_customer = household_customers[0]
        primary_member_id = primary_customer["person"]["customerId"]
        primary_member_name = f"{primary_customer['person']['firstName']} {primary_customer['person']['lastName']}".upper()
        
        household = generate_household(
            household_id=primary_member_id,  # householdId = primaryMemberId
            primary_member_id=primary_member_id,
            member_ids=household_member_ids,
            primary_member_name=primary_member_name
        )
        
        households.append(household)
    
    # Create output files
    customer_file = f"{output_prefix}_customers.json"
    household_file = f"{output_prefix}_households.json"
    
    customer_data = {"data": customers}
    household_data = {"households": households}
    
    # Write customer file
    with open(customer_file, 'w', encoding='utf-8') as f:
        json.dump(customer_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created {customer_file}")
    print(f"   - {len(customers)} customers")
    
    # Write household file
    with open(household_file, 'w', encoding='utf-8') as f:
        json.dump(household_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created {household_file}")
    print(f"   - {len(households)} households")
    
    # Statistics
    household_sizes = {}
    for household in households:
        size = len(household["memberIds"])
        household_sizes[size] = household_sizes.get(size, 0) + 1
    
    print(f"\n📊 Household size distribution:")
    for size in sorted(household_sizes.keys()):
        count = household_sizes[size]
        percentage = (count / len(households)) * 100
        print(f"   {size} member{'s' if size > 1 else ' '}: {count:4d} households ({percentage:5.1f}%)")
    
    print(f"\n🎯 Customer ID range: {start_id} - {current_id - 1}")
    print(f"✨ Test data generation complete!")

def main():
    parser = argparse.ArgumentParser(description="Generate test customer and household data")
    parser.add_argument("-n", "--num-customers", type=int, default=1000,
                       help="Number of customers to generate (default: 1000)")
    parser.add_argument("-s", "--start-id", type=int, default=60000000,
                       help="Starting customer ID (default: 60000000)")
    parser.add_argument("-o", "--output-prefix", type=str, default="generated",
                       help="Output file prefix (default: generated)")
    
    args = parser.parse_args()
    
    generate_test_data(
        num_customers=args.num_customers,
        start_id=args.start_id,
        output_prefix=args.output_prefix
    )

if __name__ == "__main__":
    main()
