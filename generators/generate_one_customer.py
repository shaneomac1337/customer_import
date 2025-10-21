#!/usr/bin/env python3
"""
Generate just one customer with firstname and lastname using the test data
"""

import random

# Swedish first names (from tests/generate_1000_customers.py)
FIRST_NAMES = [
    "Erik", "Lars", "Karl", "Anders", "Per", "Johan", "Nils", "Lennart", "Mikael", "Gunnar",
    "Anna", "Maria", "Margareta", "Elisabeth", "Eva", "Birgitta", "Kristina", "Barbro", "Ingrid", "Karin",
    "Stefan", "Peter", "Daniel", "Mattias", "Andreas", "Fredrik", "Christian", "Marcus", "David", "Thomas",
    "Susanne", "Monica", "Lena", "Marie", "Helena", "Annika", "Carina", "Inger", "Linda", "Agneta",
    "Magnus", "Patrik", "Jonas", "Alexander", "Henrik", "Gustav", "Oscar", "Emil", "Viktor", "Anton",
    "Cecilia", "Ulla", "Gunilla", "Marianne", "Anette", "Camilla", "Yvonne", "Madeleine", "Sara", "Emma",
    "Björn", "Jan-Erik", "Lars-Erik", "Karl-Johan", "Per-Ove", "Nils-Erik", "Bo-Göran", "Sven-Erik",
    "Ann-Marie", "Eva-Lena", "Gun-Britt", "Inga-Lill", "May-Britt", "Britt-Marie", "Gun-Marie", "Eva-Britt"
]

# Swedish last names (from tests/generate_1000_customers.py)
LAST_NAMES = [
    "Andersson", "Johansson", "Karlsson", "Nilsson", "Eriksson", "Larsson", "Olsson", "Persson", "Svensson", "Gustafsson",
    "Pettersson", "Jonsson", "Jansson", "Hansson", "Bengtsson", "Jönsson", "Lindberg", "Jakobsson", "Magnusson", "Olofsson",
    "Lindström", "Lindqvist", "Lindgren", "Berg", "Axelsson", "Bergström", "Lundberg", "Lind", "Lundgren", "Mattsson",
    "Berglund", "Fredriksson", "Sandberg", "Henriksson", "Forsberg", "Sjöberg", "Wallin", "Engström", "Eklund", "Danielsson",
    "Håkansson", "Lundin", "Björk", "Bergman", "Wikström", "Isaksson", "Fransson", "Bergqvist", "Nyström", "Holmberg",
    "Arvidsson", "Löfgren", "Söderberg", "Nyberg", "Blomqvist", "Claesson", "Mårtensson", "Gunnarsson", "Hedberg", "Strand"
]

def generate_one_customer_batch():
    """Generate one customer batch in proper import format without addresses and customer cards"""

    # Randomly select names
    firstname = random.choice(FIRST_NAMES)
    lastname = random.choice(LAST_NAMES)

    # Generate a random birthday (between 1940 and 2005)
    import datetime
    start_year = 1940
    end_year = 2005
    year = random.randint(start_year, end_year)
    month = random.randint(1, 12)
    day = random.randint(1, 28)  # Use 28 to avoid month-specific day issues
    birthday = f"{year:04d}-{month:02d}-{day:02d}"

    # Create proper import batch format (same as your retry batches but without addresses and customerCards)
    batch = {
        "data": [
            {
                "changeType": "CREATE",
                "type": "PERSON",
                "person": {
                    "customerId": "50000000001",
                    "status": "UNACTIVATED",
                    "firstName": firstname,
                    "lastName": lastname,
                    "languageCode": "sv",
                    "birthday": birthday,
                    "statisticalUseAllowed": False,
                    "marketingAllowedFlag": random.choice([True, False]),
                    "declarationAvailable": True
                }
            }
        ]
    }

    return batch

if __name__ == "__main__":
    import json

    batch = generate_one_customer_batch()

    # Save to file
    filename = "single_customer_batch.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(batch, f, indent=2, ensure_ascii=False)

    print(f"✅ Generated single customer batch file: {filename}")
    print(f"📋 Customer: {batch['data'][0]['person']['firstName']} {batch['data'][0]['person']['lastName']}")
    print(f"🆔 Customer ID: {batch['data'][0]['person']['customerId']}")

    # Also display the content
    print(f"\n📄 File content:")
    print(json.dumps(batch, indent=2, ensure_ascii=False))
