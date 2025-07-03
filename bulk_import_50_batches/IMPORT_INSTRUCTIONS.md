# 50 Batch Import Instructions

## Generated Data
- **Total Customers**: 5,000
- **Total Batches**: 50
- **Customers per Batch**: 100
- **Generated**: 2025-07-03 20:43:01

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
4. Select this directory: `bulk_import_50_batches`
5. Configure your API credentials
6. Click **"Start Import"**

### Option 2: Use Individual Files
Load specific batch files one by one:
   - customers_100_batch_01.json
   - customers_100_batch_02.json
   - customers_100_batch_03.json
   - customers_100_batch_04.json
   - customers_100_batch_05.json
   - ... and 45 more files

## Expected Import Time
- **Estimated Duration**: ~15-20 minutes
- **With 5 threads**: Parallel processing
- **With 1s delays**: Rate limiting protection

## Files in this Directory
- `generation_summary.json` - Detailed generation information
- `IMPORT_INSTRUCTIONS.md` - This file
- `customers_70_batch_XX.json` - Individual batch files (50 files)

All files are formatted correctly for immediate import!
