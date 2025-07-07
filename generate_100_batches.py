#!/usr/bin/env python3
"""
Generate 10,000 unique customers split into 100 batches of 100 customers each
Each customer will have a unique personalNumber and realistic Swedish data
Optimized for large-scale bulk import testing with 100 batches
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
    "Björn", "Jan-Erik", "Lars-Erik", "Karl-Johan", "Per-Ove", "Nils-Erik", "Bo-Göran", "Sven-Erik",
    "Ann-Marie", "Eva-Lena", "Gun-Britt", "Inga-Lill", "May-Britt", "Britt-Marie", "Gun-Marie", "Eva-Britt",
    "Åke", "Rune", "Göran", "Bengt", "Ulf", "Rolf", "Kjell", "Christer", "Mats", "Leif",
    "Astrid", "Gudrun", "Maj", "Elsa", "Rut", "Sigrid", "Ingegerd", "Solveig", "Dagmar", "Märta",
    "Stig", "Bertil", "Ragnar", "Folke", "Ivar", "Torsten", "Helge", "Arvid", "Sixten", "Nils",
    "Ingeborg", "Greta", "Hulda", "Edith", "Vera", "Alma", "Signe", "Tekla", "Hilda", "Olga"
]

# Swedish last names
LAST_NAMES = [
    "Andersson", "Johansson", "Karlsson", "Nilsson", "Eriksson", "Larsson", "Olsson", "Persson", "Svensson", "Gustafsson",
    "Pettersson", "Jonsson", "Jansson", "Hansson", "Bengtsson", "Jönsson", "Lindberg", "Jakobsson", "Magnusson", "Olofsson",
    "Lindström", "Lindqvist", "Lindgren", "Berg", "Axelsson", "Bergström", "Lundberg", "Lind", "Lundgren", "Mattsson",
    "Berglund", "Fredriksson", "Sandberg", "Henriksson", "Forsberg", "Sjöberg", "Wallin", "Engström", "Eklund", "Danielsson",
    "Håkansson", "Lundin", "Björk", "Bergman", "Wikström", "Isaksson", "Fransson", "Bergqvist", "Nyström", "Holmberg",
    "Arvidsson", "Löfgren", "Söderberg", "Nyberg", "Blomqvist", "Claesson", "Mårtensson", "Gunnarsson", "Hedberg", "Strand",
    "Sundberg", "Holm", "Sandström", "Linder", "Norberg", "Falk", "Blom", "Dahl", "Borg", "Sjögren",
    "Åberg", "Wiklund", "Rosén", "Öberg", "Martinsson", "Abrahamsson", "Öhman", "Månsson", "Holmqvist", "Jonasson",
    "Nordin", "Hedström", "Lindahl", "Åkesson", "Persson", "Carlsson", "Samuelsson", "Höglund", "Ström", "Hermansson"
]

# Swedish cities
CITIES = [
    "Stockholm", "Göteborg", "Malmö", "Uppsala", "Västerås", "Örebro", "Linköping", "Helsingborg", "Jönköping", "Norrköping",
    "Lund", "Umeå", "Gävle", "Borås", "Södertälje", "Eskilstuna", "Halmstad", "Växjö", "Karlstad", "Sundsvall",
    "Trollhättan", "Östersund", "Borlänge", "Falun", "Skövde", "Karlskrona", "Kristianstad", "Kalmar", "Vänersborg", "Lidköping",
    "Sandviken", "Sollentuna", "Varberg", "Trelleborg", "Landskrona", "Ängelholm", "Falkenberg", "Katrineholm", "Nyköping", "Mariestad",
    "Motala", "Kiruna", "Skellefteå", "Piteå", "Luleå", "Härnösand", "Örnsköldsvik", "Bollnäs", "Hudiksvall", "Söderhamn",
    "Värnamo", "Alvesta", "Ljungby", "Markaryd", "Älmhult", "Osby", "Höör", "Eslöv", "Kävlinge", "Staffanstorp"
]

# Swedish street names
STREET_NAMES = [
    "Storgatan", "Kungsgatan", "Drottninggatan", "Järnvägsgatan", "Skolagatan", "Kyrkogatan", "Parkgatan", "Nygatan",
    "Västergatan", "Östergatan", "Södergatan", "Norrgatan", "Linnégatan", "Vasagatan", "Birger Jarlsgatan", "Sveavägen",
    "Hamngatan", "Biblioteksgatan", "Regeringsgatan", "Upplandsgatan", "Götgatan", "Hornsgatan", "Folkungagatan", "Ringvägen",
    "Malmgatan", "Brogatan", "Stensgatan", "Bergsgatan", "Änggatan", "Skogsgatan", "Åkergatan", "Lundagatan",
    "Klostergatan", "Torggatan", "Bryggaregatan", "Fiskaregatan", "Handelsgatan", "Industrigatatan", "Fabriksgatan", "Hantverkargatan",
    "Prästgatan", "Rådhusgatan", "Tullgatan", "Slottsgatan", "Kyrkbrinken", "Åsgatan", "Björkgatan", "Ekgatan",
    "Lönnvägen", "Kastanjevägen", "Lindvägen", "Almvägen", "Hasselvägen", "Rönnvägen", "Aspvägen", "Granvägen"
]

def generate_personal_number():
    """Generate a unique Swedish personal number (YYYYMMDD-XXXX format)"""
    # Generate birth date between 1930 and 2005
    start_date = datetime(1930, 1, 1)
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
    street_number = random.randint(1, 300)
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
            "marketingAllowedFlag": True,  # Set to True as per your requirements
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
                    "number": str(4000000 + int(customer_id)),
                    "type": "MAIN_CARD",
                    "scope": "GLOBAL"
                }
            ]
        }
    }

    # 35% chance to add a partner card
    if random.random() < 0.35:
        partner_card_number = str(4000000 + int(customer_id) + 500000)
        customer["person"]["customerCards"].append({
            "number": partner_card_number,
            "type": "PARTNER_CARD",
            "scope": "GLOBAL"
        })

    return customer

def main():
    """Generate 10,000 unique customers in 100 batches of 100 each"""
    print("=" * 60)
    print("GENERATING 10,000 UNIQUE CUSTOMERS")
    print("100 batches × 100 customers each")
    print("=" * 60)
    
    # Create output directory
    output_dir = "bulk_import_100_batches"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")
    
    # Track used personal numbers to ensure uniqueness
    used_personal_numbers = set()
    total_customers_generated = 0
    customer_id_counter = 70000001000  # Start from a high number to avoid conflicts

    # Generate 100 batches
    for batch_num in range(1, 101):
        print(f"\nGenerating batch {batch_num:03d}/100...")

        batch_customers = []
        customers_in_batch = 0

        # Generate 100 unique customers for this batch
        while customers_in_batch < 100:
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
        filename = f"customers_100_batch_{batch_num:03d}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, indent=2, ensure_ascii=False)
        
        total_customers_generated += len(batch_customers)
        print(f"  [OK] Saved {len(batch_customers)} customers to {filename}")
        
        # Progress indicator for every 10 batches
        if batch_num % 10 == 0:
            print(f"  📊 Progress: {batch_num}/100 batches complete ({total_customers_generated:,} customers)")
    
    # Generate summary
    summary = {
        "generation_date": datetime.now().isoformat(),
        "total_customers": total_customers_generated,
        "total_batches": 100,
        "customers_per_batch": 100,
        "unique_personal_numbers": len(used_personal_numbers),
        "files_generated": [f"customers_100_batch_{i:03d}.json" for i in range(1, 101)],
        "recommended_import_settings": {
            "batch_size": 100,
            "max_workers": 5,
            "delay_between_requests": 1.0,
            "max_retries": 3
        },
        "estimated_import_time": {
            "conservative": "30-40 minutes",
            "balanced": "20-30 minutes",
            "aggressive": "15-20 minutes"
        }
    }
    
    summary_file = os.path.join(output_dir, "generation_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    # Create import instructions
    instructions_file = os.path.join(output_dir, "IMPORT_INSTRUCTIONS.md")
    instructions_content = f"""# 100 Batch Import Instructions

## Generated Data
- **Total Customers**: {total_customers_generated:,}
- **Total Batches**: 100
- **Customers per Batch**: 100
- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Import Settings (Recommended)
- **Batch Size**: 100 customers
- **Max Workers**: 5 threads
- **Delay Between Requests**: 1.0 seconds
- **Max Retries**: 3 attempts

## How to Import

### Option 1: Use Bulk Import GUI
1. Launch the Bulk Import GUI
2. Go to **Files** tab
3. Click **"Add Directory"**
4. Select this directory: `{output_dir}`
5. Configure your API credentials
6. Click **"Start Import"**

### Option 2: Use Individual Files
Load specific batch files one by one:
{chr(10).join(f'   - {filename}' for filename in summary["files_generated"][:10])}
   - ... and 90 more files

## Expected Import Time
- **Conservative**: 30-40 minutes
- **Balanced**: 20-30 minutes
- **Aggressive**: 15-20 minutes

## Performance Recommendations
- **Start with Conservative settings** for first run
- **Monitor success rates** and adjust accordingly
- **Use automatic authentication** for uninterrupted processing
- **Enable retry functionality** for failed batches

## Files in this Directory
- `generation_summary.json` - Detailed generation information
- `IMPORT_INSTRUCTIONS.md` - This file
- `customers_100_batch_XXX.json` - Individual batch files (100 files)

All files are formatted correctly for immediate import!

## Large Scale Import Tips
1. **Test with smaller subset first** (e.g., first 10 batches)
2. **Use automatic authentication** to avoid token expiry
3. **Monitor system resources** during import
4. **Consider running during off-peak hours**
5. **Have retry strategy ready** for any failures

## Troubleshooting
- **Rate limiting**: Increase delays if you see 429 errors
- **Memory usage**: Monitor system resources during import
- **Network issues**: Use retry functionality for recovery
- **Authentication**: Use automatic mode for long imports

Good luck with your 10,000 customer import! 🚀
"""

    with open(instructions_file, 'w', encoding='utf-8') as f:
        f.write(instructions_content)
    
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE!")
    print("=" * 60)
    print(f"[STATS] Total customers generated: {total_customers_generated:,}")
    print(f"[STATS] Total batches created: 100")
    print(f"[STATS] Customers per batch: 100")
    print(f"[STATS] Unique personal numbers: {len(used_personal_numbers):,}")
    print(f"[STATS] Output directory: {output_dir}")
    print(f"[STATS] Summary file: {summary_file}")
    print(f"[STATS] Instructions file: {instructions_file}")
    print(f"[STATS] Customer ID range: 70000001000 - {customer_id_counter-1}")
    print("\n[SUCCESS] Ready for large-scale bulk import testing!")
    print("   Load these files in your Bulk Import GUI")
    print(f"   Estimated import time: 20-40 minutes")
    print(f"   Recommended: Start with Conservative settings")
    print(f"   Use automatic authentication for uninterrupted processing")

if __name__ == "__main__":
    main()
