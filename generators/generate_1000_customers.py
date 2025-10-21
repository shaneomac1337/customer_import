#!/usr/bin/env python3
"""
Generate 1000 unique customers split into 20 batches of 50 customers each
Each customer will have a unique personalNumber and realistic Swedish data
"""

import json
import random
import os
from datetime import datetime, timedelta

# Swedish first names
FIRST_NAMES = [
    "Erik", "Lars", "Karl", "Anders", "Per", "Johan", "Nils", "Lennart", "Mikael", "Gunnar",
    "Anna", "Maria", "Margareta", "Elisabeth", "Eva", "Birgitta", "Kristina", "Barbro", "Ingrid", "Karin",
    "Stefan", "Peter", "Daniel", "Mattias", "Andreas", "Fredrik", "Christian", "Marcus", "David", "Thomas",
    "Susanne", "Monica", "Lena", "Marie", "Helena", "Annika", "Carina", "Inger", "Linda", "Agneta",
    "Magnus", "Patrik", "Jonas", "Alexander", "Henrik", "Gustav", "Oscar", "Emil", "Viktor", "Anton",
    "Cecilia", "Ulla", "Gunilla", "Marianne", "Anette", "Camilla", "Yvonne", "Madeleine", "Sara", "Emma",
    "Björn patrik", "Jan-Erik", "Lars-Erik", "Karl-Johan", "Per-Ove", "Nils-Erik", "Bo-Göran", "Sven-Erik",
    "Ann-Marie", "Eva-Lena", "Gun-Britt", "Inga-Lill", "May-Britt", "Britt-Marie", "Gun-Marie", "Eva-Britt"
]

# Swedish last names
LAST_NAMES = [
    "Andersson", "Johansson", "Karlsson", "Nilsson", "Eriksson", "Larsson", "Olsson", "Persson", "Svensson", "Gustafsson",
    "Pettersson", "Jonsson", "Jansson", "Hansson", "Bengtsson", "Jönsson", "Lindberg", "Jakobsson", "Magnusson", "Olofsson",
    "Lindström", "Lindqvist", "Lindgren", "Berg", "Axelsson", "Bergström", "Lundberg", "Lind", "Lundgren", "Mattsson",
    "Berglund", "Fredriksson", "Sandberg", "Henriksson", "Forsberg", "Sjöberg", "Wallin", "Engström", "Eklund", "Danielsson",
    "Håkansson", "Lundin", "Björk", "Bergman", "Wikström", "Isaksson", "Fransson", "Bergqvist", "Nyström", "Holmberg",
    "Arvidsson", "Löfgren", "Söderberg", "Nyberg", "Blomqvist", "Claesson", "Mårtensson", "Gunnarsson", "Hedberg", "Strand"
]

# Swedish cities
CITIES = [
    "Stockholm", "Göteborg", "Malmö", "Uppsala", "Västerås", "Örebro", "Linköping", "Helsingborg", "Jönköping", "Norrköping",
    "Lund", "Umeå", "Gävle", "Borås", "Södertälje", "Eskilstuna", "Halmstad", "Växjö", "Karlstad", "Sundsvall",
    "Trollhättan", "Östersund", "Borlänge", "Falun", "Skövde", "Karlskrona", "Kristianstad", "Kalmar", "Vänersborg", "Lidköping"
]

# Swedish street names
STREET_NAMES = [
    "Storgatan", "Kungsgatan", "Drottninggatan", "Järnvägsgatan", "Skolagatan", "Kyrkogatan", "Parkgatan", "Nygatan",
    "Västergatan", "Östergatan", "Södergatan", "Norrgatan", "Linnégatan", "Vasagatan", "Birger Jarlsgatan", "Sveavägen",
    "Hamngatan", "Biblioteksgatan", "Regeringsgatan", "Upplandsgatan", "Götgatan", "Hornsgatan", "Folkungagatan", "Ringvägen"
]

def generate_personal_number():
    """Generate a unique Swedish personal number (YYYYMMDD-XXXX format)"""
    # Generate birth date between 1940 and 2005
    start_date = datetime(1940, 1, 1)
    end_date = datetime(2005, 12, 31)
    
    # Random date between start and end
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    birth_date = start_date + timedelta(days=random_days)
    
    # Format as YYYYMMDD
    date_part = birth_date.strftime("%Y%m%d")
    
    # Generate 4-digit suffix (birth number + check digit)
    suffix = f"{random.randint(1000, 9999)}"
    
    return f"{date_part}-{suffix}"

def generate_address():
    """Generate a Swedish address"""
    street_name = random.choice(STREET_NAMES)
    street_number = random.randint(1, 200)
    city = random.choice(CITIES)
    postal_code = f"{random.randint(100, 999)} {random.randint(10, 99)}"
    
    return {
        "addressee": f"{street_name} {street_number}",
        "city": city,
        "postalCode": postal_code,
        "countryCode": "SE",
        "contactPurposeTypeCode": "HOME",
        "contactMethodTypeCode": "POSTAL_ADDRESS"
    }

def generate_customer(personal_number, customer_id):
    """Generate a single customer with Swedish data in correct API format"""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)

    # Generate birthday from personal number
    year = int(personal_number[:4])
    month = int(personal_number[4:6])
    day = int(personal_number[6:8])
    birthday = f"{year}-{month:02d}-{day:02d}"

    # Generate address
    address = generate_address()

    customer = {
        "changeType": "CREATE",
        "type": "PERSON",
        "person": {
            "customerId": customer_id,
            "status": "UNACTIVATED",
            "firstName": first_name.upper(),
            "lastName": last_name.upper(),
            "languageCode": "sv",
            "birthday": birthday,
            "statisticalUseAllowed": False,
            "marketingAllowedFlag": False,
            "declarationAvailable": True,
            "addresses": [
                {
                    "addressee": f"{first_name.upper()} {last_name.upper()}",
                    "street": address["addressee"].split()[0],  # Extract street name
                    "streetNumber": address["addressee"].split()[1] if len(address["addressee"].split()) > 1 else "1",
                    "city": address["city"],
                    "postalCode": address["postalCode"].replace(" ", ""),
                    "countryCode": "SE",
                    "contactPurposeTypeCode": "DEFAULT",
                    "contactMethodTypeCode": "HOME"
                }
            ],
            "customerCards": [
                {
                    "number": str(2000000 + int(customer_id)),
                    "type": "MAIN_CARD",
                    "scope": "GLOBAL"
                }
            ]
        }
    }

    # 30% chance to add a partner card
    if random.random() < 0.3:
        partner_card_number = str(2000000 + int(customer_id) + 500000)
        customer["person"]["customerCards"].append({
            "number": partner_card_number,
            "type": "PARTNER_CARD",
            "scope": "GLOBAL"
        })

    return customer

def main():
    """Generate 1000 unique customers in 20 batches of 50 each"""
    print("=" * 60)
    print("GENERATING 1000 UNIQUE CUSTOMERS")
    print("20 batches × 50 customers each")
    print("=" * 60)
    
    # Create output directory
    output_dir = "bulk_import_1000_customers"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")
    
    # Track used personal numbers to ensure uniqueness
    used_personal_numbers = set()
    total_customers_generated = 0
    customer_id_counter = 50000001000  # Start from a high number to avoid conflicts

    # Generate 20 batches
    for batch_num in range(1, 21):
        print(f"\nGenerating batch {batch_num:02d}/20...")

        batch_customers = []
        customers_in_batch = 0

        # Generate 50 unique customers for this batch
        while customers_in_batch < 50:
            personal_number = generate_personal_number()

            # Ensure uniqueness across all batches
            if personal_number not in used_personal_numbers:
                used_personal_numbers.add(personal_number)
                customer_id = str(customer_id_counter)
                customer = generate_customer(personal_number, customer_id)
                batch_customers.append(customer)
                customers_in_batch += 1
                customer_id_counter += 1

        # Wrap in correct API format
        batch_data = {
            "data": batch_customers
        }

        # Save batch to file
        filename = f"customers_50_batch_{batch_num:02d}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, indent=2, ensure_ascii=False)
        
        total_customers_generated += len(batch_customers)
        print(f"  [OK] Saved {len(batch_customers)} customers to {filename}")
    
    # Generate summary
    summary = {
        "generation_date": datetime.now().isoformat(),
        "total_customers": total_customers_generated,
        "total_batches": 20,
        "customers_per_batch": 50,
        "unique_personal_numbers": len(used_personal_numbers),
        "files_generated": [f"customers_50_batch_{i:02d}.json" for i in range(1, 21)]
    }
    
    summary_file = os.path.join(output_dir, "generation_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE!")
    print("=" * 60)
    print(f"[STATS] Total customers generated: {total_customers_generated}")
    print(f"[STATS] Total batches created: 20")
    print(f"[STATS] Customers per batch: 50")
    print(f"[STATS] Unique personal numbers: {len(used_personal_numbers)}")
    print(f"[STATS] Output directory: {output_dir}")
    print(f"[STATS] Summary file: {summary_file}")
    print("\n[SUCCESS] Ready for bulk import testing!")
    print("   Load these files in your Bulk Import GUI")

if __name__ == "__main__":
    main()
