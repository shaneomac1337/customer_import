"""
Simple launcher for the Bulk Import GUI
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

def check_dependencies():
    """Check if required files exist"""
    required_files = [
        "bulk_import_multithreaded.py",
        "bulk_import_gui.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        root = tk.Tk()
        root.withdraw()  # Hide main window
        messagebox.showerror(
            "Missing Files", 
            f"Required files not found:\n" + "\n".join(missing_files) + 
            "\n\nPlease ensure all files are in the same directory."
        )
        return False
    
    return True

def main():
    """Launch the GUI application"""
    print("="*60)
    print("BULK CUSTOMER IMPORT GUI")
    print("="*60)
    print("Checking dependencies...")
    
    if not check_dependencies():
        print("ERROR: Dependency check failed!")
        input("Press Enter to exit...")
        return
    
    print("SUCCESS: All dependencies found!")
    print("LAUNCHING: Starting GUI...")
    
    try:
        # Import and run the GUI
        from bulk_import_gui import main as gui_main
        gui_main()
        
    except ImportError as e:
        print(f"ERROR: Import error: {e}")
        print("Make sure bulk_import_gui.py is in the same directory")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"ERROR: Error launching GUI: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()