# JSON Splitter Format Support

## Overview
Both `split_large_json.py` and `split_json_simple.py` now support multiple input formats and automatically convert them to import-compatible formats.

## Supported Input Formats

### Customer Files
The splitters accept **3 different customer formats**:

1. **Standard Format** (already compatible):
```json
{
  "data": [
    { "changeType": "CREATE", ... }
  ]
}
```

2. **GK Engage Export Format** (needs conversion):
```json
{
  "importId": "...",
  "customers": [
    { "changeType": "CREATE", ... }
  ]
}
```

3. **Array Format**:
```json
[
  { "changeType": "CREATE", ... }
]
```

### Household Files
The splitters accept **household format**:

```json
{
  "households": [
    { "changeType": "CREATE", "householdId": "...", ... }
  ]
}
```

## Automatic Conversion

### Customers
- Input key `"customers"` → Output key `"data"`
- Input key `"data"` → Output key `"data"` (no change)
- Array format → Output key `"data"`

### Households
- Input key `"households"` → Output key `"households"` (no change)

## Detection Priority

The splitters check for keys in this order:
1. Array format (`[...]`)
2. `"households"`
3. `"customers"` 
4. `"data"`
5. Generic fallback (checks common keys)

## Output Files

### Customers
- Filename: `customer_00001.json`, `customer_00002.json`, etc.
- Format: `{"data": [...]}`

### Households
- Filename: `household_00001.json`, `household_00002.json`, etc.
- Format: `{"households": [...]}`

## Usage

Both splitters work identically:

```powershell
# For large files (split_large_json.py)
python utils/split_large_json.py "CustomerImportData/Output_GKengagePROD_Customer_251105.json"

# For simpler splitting (split_json_simple.py)
python utils/split_json_simple.py "CustomerImportData/Output_GKengagePROD_Customer_251105.json" 100

# For households
python utils/split_large_json.py "CustomerImportData/Output_GKengagePROD_Household_251105.json"
```

## Summary File

Each split operation creates a `split_summary.json` with:
- `import_type`: "customers" or "households"
- `input_key`: The key found in source file
- `output_key`: The key used in output files
- `total_items`: Count of items processed
- File list and statistics

## Import Compatibility

All output files are **100% compatible** with the bulk import tool:
- Customer files use `"data"` key (as expected by import system)
- Household files use `"households"` key (as expected by import system)
- Files can be directly loaded into the GUI or CLI import tool

## Example Conversion

**Input** (`Output_GKengagePROD_Customer_251105.json`):
```json
{
  "importId": "ceb3678b-7b21-4727-8e63-4ddc7423d68f",
  "customers": [
    { "changeType": "CREATE", "type": "PERSON", ... }
  ]
}
```

**Output** (`customer_00001.json`):
```json
{
  "data": [
    { "changeType": "CREATE", "type": "PERSON", ... }
  ]
}
```

The `"customers"` key is automatically converted to `"data"` and the `"importId"` field is stripped out.

## Notes

- Both splitters handle large files (2.6 GB+ tested)
- Memory usage optimized for large datasets
- UTF-8 encoding preserved for international characters
- Progress updates during splitting
- Error handling for invalid formats
