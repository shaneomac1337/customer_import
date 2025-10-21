# Customer Data Generators

This folder contains scripts for generating test customer data.

## Scripts

### Quick Generators
- **generate_one_customer.py** - Generate a single customer for quick testing

### Batch Generators
- **generate_1000_customers.py** - Generate 1,000 customers in 20 batches (50 each)
- **generate_50_batches.py** - Generate 5,000 customers in 50 batches (100 each)
- **generate_100_batches.py** - Generate 10,000 customers in 100 batches (100 each)

## Usage

### Generate Single Customer
```powershell
python generators/generate_one_customer.py
```
Creates: `single_customer_batch.json` in test_data/

### Generate 1,000 Customers
```powershell
python generators/generate_1000_customers.py
```
Creates: `bulk_import_1000_customers/` directory with 20 files

### Generate 5,000 Customers
```powershell
python generators/generate_50_batches.py
```
Creates: `bulk_import_50_batches/` directory with 50 files

## Output

All generators create:
- Customers with realistic Swedish names
- Proper addresses and postal codes
- Customer cards (main + optional partner)
- Unique customer IDs
- Valid date ranges (1940-2005)

Output directories are created automatically in the `output/` folder.
