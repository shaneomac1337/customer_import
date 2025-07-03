@echo off
echo ============================================================
echo BULK CUSTOMER IMPORT - 1000 CUSTOMERS LOADER
echo ============================================================
echo.
echo This will launch the Bulk Import GUI and automatically
echo load all 20 batch files (1000 customers total)
echo.
echo Files to be loaded:
echo - bulk_import_1000_customers/customers_50_batch_01.json (50 customers)
echo - bulk_import_1000_customers/customers_50_batch_02.json (50 customers)
echo - ... (through batch 20)
echo.
echo Total: 1000 unique customers in 20 batches of 50 each
echo.
pause
echo.
echo Launching GUI...
python bulk_import_gui.py
pause
