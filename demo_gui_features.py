"""
Demo script to showcase GUI features
This creates a simplified version to demonstrate the interface
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os

class DemoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bulk Customer Import Tool - DEMO")
        self.root.geometry("800x600")
        
        # Demo variables
        self.api_url = tk.StringVar(value="https://prod.cse.cloud4retail.co/customer-profile-service/...")
        self.auth_token = tk.StringVar(value="your_auth_token_here")
        self.gk_passport = tk.StringVar(value="your_gk_passport_here")
        self.batch_size = tk.IntVar(value=70)
        self.max_workers = tk.IntVar(value=3)
        
        self.create_demo_interface()
    
    def create_demo_interface(self):
        """Create demo interface"""
        
        # Title
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(title_frame, text="🚀 Bulk Customer Import Tool", 
                 font=("TkDefaultFont", 16, "bold")).pack()
        ttk.Label(title_frame, text="Multithreaded Customer Import with GUI", 
                 font=("TkDefaultFont", 10)).pack()
        
        # Main notebook
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configuration Tab
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="⚙️ Configuration")
        self.create_config_demo(config_frame)
        
        # Files Tab
        files_frame = ttk.Frame(notebook)
        notebook.add(files_frame, text="📁 Files")
        self.create_files_demo(files_frame)
        
        # Import Tab
        import_frame = ttk.Frame(notebook)
        notebook.add(import_frame, text="▶️ Import")
        self.create_import_demo(import_frame)
        
        # Results Tab
        results_frame = ttk.Frame(notebook)
        notebook.add(results_frame, text="📊 Results")
        self.create_results_demo(results_frame)
    
    def create_config_demo(self, parent):
        """Demo configuration tab"""
        
        # API Configuration
        api_group = ttk.LabelFrame(parent, text="🔐 API Configuration", padding=10)
        api_group.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(api_group, text="API URL:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(api_group, textvariable=self.api_url, width=60, state="readonly").grid(row=0, column=1, sticky=tk.EW, pady=2)
        
        ttk.Label(api_group, text="Auth Token:").grid(row=1, column=0, sticky=tk.W, pady=2)
        auth_entry = ttk.Entry(api_group, textvariable=self.auth_token, width=60, show="*")
        auth_entry.grid(row=1, column=1, sticky=tk.EW, pady=2)
        ttk.Button(api_group, text="Show", command=lambda: self.toggle_demo_password(auth_entry)).grid(row=1, column=2, padx=5)
        
        ttk.Label(api_group, text="GK-Passport:").grid(row=2, column=0, sticky=tk.W, pady=2)
        passport_entry = ttk.Entry(api_group, textvariable=self.gk_passport, width=60, show="*")
        passport_entry.grid(row=2, column=1, sticky=tk.EW, pady=2)
        ttk.Button(api_group, text="Show", command=lambda: self.toggle_demo_password(passport_entry)).grid(row=2, column=2, padx=5)
        
        api_group.columnconfigure(1, weight=1)
        
        # Import Settings
        settings_group = ttk.LabelFrame(parent, text="⚙️ Import Settings", padding=10)
        settings_group.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(settings_group, text="Batch Size:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(settings_group, from_=10, to=100, textvariable=self.batch_size, width=10).grid(row=0, column=1, sticky=tk.W, pady=2)
        ttk.Label(settings_group, text="customers per batch").grid(row=0, column=2, sticky=tk.W, pady=2)
        
        ttk.Label(settings_group, text="Worker Threads:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(settings_group, from_=1, to=10, textvariable=self.max_workers, width=10).grid(row=1, column=1, sticky=tk.W, pady=2)
        ttk.Label(settings_group, text="concurrent requests").grid(row=1, column=2, sticky=tk.W, pady=2)
        
        # Presets
        presets_group = ttk.LabelFrame(parent, text="🎯 Quick Presets", padding=10)
        presets_group.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(presets_group, text="Conservative (Safe)", command=self.demo_conservative).pack(side=tk.LEFT, padx=5)
        ttk.Button(presets_group, text="Balanced (Recommended)", command=self.demo_balanced).pack(side=tk.LEFT, padx=5)
        ttk.Button(presets_group, text="Aggressive (Fast)", command=self.demo_aggressive).pack(side=tk.LEFT, padx=5)
    
    def create_files_demo(self, parent):
        """Demo files tab"""
        
        # File selection buttons
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(buttons_frame, text="📁 Add Files", command=self.demo_add_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="📂 Add Directory", command=self.demo_add_directory).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="🚀 Load 700 Customer Files", command=self.demo_load_700).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="🗑️ Clear All", command=self.demo_clear).pack(side=tk.LEFT, padx=5)
        
        # File list demo
        list_group = ttk.LabelFrame(parent, text="📋 Selected Files", padding=10)
        list_group.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Demo file tree
        columns = ("File", "Customers", "Size", "Status")
        self.demo_tree = ttk.Treeview(list_group, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.demo_tree.heading(col, text=col)
            self.demo_tree.column(col, width=150)
        
        # Add demo data
        demo_files = [
            ("customers_70_batch_01.json", "70", "76,533 bytes", "✅ Valid"),
            ("customers_70_batch_02.json", "70", "76,504 bytes", "✅ Valid"),
            ("customers_70_batch_03.json", "70", "76,493 bytes", "✅ Valid"),
            ("customers_70_batch_04.json", "70", "76,595 bytes", "✅ Valid"),
            ("customers_70_batch_05.json", "70", "76,534 bytes", "✅ Valid"),
        ]
        
        for file_data in demo_files:
            self.demo_tree.insert("", tk.END, values=file_data)
        
        scrollbar = ttk.Scrollbar(list_group, orient=tk.VERTICAL, command=self.demo_tree.yview)
        self.demo_tree.configure(yscrollcommand=scrollbar.set)
        
        self.demo_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Summary
        ttk.Label(list_group, text="5 files selected, 350 customers, 382,659 bytes", 
                 font=("TkDefaultFont", 9, "bold")).pack(pady=5)
    
    def create_import_demo(self, parent):
        """Demo import tab"""
        
        # Control buttons
        control_group = ttk.LabelFrame(parent, text="🎮 Import Control", padding=10)
        control_group.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(control_group, text="▶️ Start Import", command=self.demo_start_import).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_group, text="⏹️ Stop Import", state=tk.DISABLED).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_group, text="✅ Validate Files", command=self.demo_validate).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_group, text="🔗 Test Connection", command=self.demo_test_connection).pack(side=tk.LEFT, padx=5)
        
        # Progress
        progress_group = ttk.LabelFrame(parent, text="📈 Progress", padding=10)
        progress_group.pack(fill=tk.X, padx=10, pady=5)
        
        self.demo_progress = ttk.Progressbar(progress_group, maximum=100, value=65)
        self.demo_progress.pack(fill=tk.X, pady=5)
        
        ttk.Label(progress_group, text="Processing batch 7 of 10... (65% complete)", 
                 font=("TkDefaultFont", 9)).pack()
        
        # Statistics
        stats_group = ttk.LabelFrame(parent, text="📊 Live Statistics", padding=10)
        stats_group.pack(fill=tk.X, padx=10, pady=5)
        
        stats_frame = ttk.Frame(stats_group)
        stats_frame.pack(fill=tk.X)
        
        # Demo statistics
        demo_stats = [
            ("Total Batches:", "10"),
            ("Completed:", "7"),
            ("Failed:", "0"),
            ("Success Rate:", "100%"),
            ("Duration:", "3m 45s"),
            ("Customers/min:", "156.2")
        ]
        
        for i, (label, value) in enumerate(demo_stats):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(stats_frame, text=label).grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            ttk.Label(stats_frame, text=value, font=("TkDefaultFont", 9, "bold")).grid(row=row, column=col+1, sticky=tk.W, padx=5, pady=2)
    
    def create_results_demo(self, parent):
        """Demo results tab"""
        
        # Log demo
        log_group = ttk.LabelFrame(parent, text="📝 Import Log", padding=10)
        log_group.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Demo log text
        log_text = tk.Text(log_group, height=15, width=80, state=tk.NORMAL)
        log_text.pack(fill=tk.BOTH, expand=True)
        
        demo_log = """[14:32:15] Starting import of 700 customers from 10 files
[14:32:15] Configuration: 70 batch size, 3 workers, 0.5s delay
[14:32:16] Processing customers_70_batch_01.json (70 customers)
[14:32:18] ✅ Batch 1/10 completed successfully (70 customers imported)
[14:32:18] Processing customers_70_batch_02.json (70 customers)
[14:32:20] ✅ Batch 2/10 completed successfully (70 customers imported)
[14:32:20] Processing customers_70_batch_03.json (70 customers)
[14:32:22] ✅ Batch 3/10 completed successfully (70 customers imported)
[14:32:22] Processing customers_70_batch_04.json (70 customers)
[14:32:24] ✅ Batch 4/10 completed successfully (70 customers imported)
[14:32:24] Processing customers_70_batch_05.json (70 customers)
[14:32:26] ✅ Batch 5/10 completed successfully (70 customers imported)
[14:32:26] Processing customers_70_batch_06.json (70 customers)
[14:32:28] ✅ Batch 6/10 completed successfully (70 customers imported)
[14:32:28] Processing customers_70_batch_07.json (70 customers)
[14:32:30] ✅ Batch 7/10 completed successfully (70 customers imported)
[14:32:30] Current progress: 490/700 customers (70% complete)
[14:32:30] Success rate: 100% | Average: 156.2 customers/minute"""
        
        log_text.insert(tk.END, demo_log)
        log_text.config(state=tk.DISABLED)
        
        # Log controls
        log_controls = ttk.Frame(log_group)
        log_controls.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(log_controls, text="🗑️ Clear Log", command=self.demo_clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_controls, text="💾 Save Log", command=self.demo_save_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_controls, text="📊 Export Results", command=self.demo_export).pack(side=tk.LEFT, padx=5)
    
    # Demo button handlers
    def toggle_demo_password(self, entry):
        if entry.cget("show") == "*":
            entry.config(show="")
        else:
            entry.config(show="*")
    
    def demo_conservative(self):
        self.batch_size.set(50)
        self.max_workers.set(2)
        messagebox.showinfo("Preset Applied", "Conservative settings applied:\n• 50 customers per batch\n• 2 worker threads\n• 1.0s delay between requests")
    
    def demo_balanced(self):
        self.batch_size.set(70)
        self.max_workers.set(3)
        messagebox.showinfo("Preset Applied", "Balanced settings applied:\n• 70 customers per batch\n• 3 worker threads\n• 0.5s delay between requests")
    
    def demo_aggressive(self):
        self.batch_size.set(100)
        self.max_workers.set(5)
        messagebox.showinfo("Preset Applied", "Aggressive settings applied:\n• 100 customers per batch\n• 5 worker threads\n• 0.2s delay between requests")
    
    def demo_add_files(self):
        messagebox.showinfo("Add Files", "This would open a file dialog to select individual JSON files.")
    
    def demo_add_directory(self):
        messagebox.showinfo("Add Directory", "This would open a directory dialog to select all JSON files from a folder.")
    
    def demo_load_700(self):
        messagebox.showinfo("Load 700 Files", "This would automatically load all 10 customer batch files (700 customers total).")
    
    def demo_clear(self):
        messagebox.showinfo("Clear Files", "This would clear all selected files from the import queue.")
    
    def demo_start_import(self):
        messagebox.showinfo("Start Import", "This would begin the actual import process with your configured settings.\n\nThe import runs in a separate thread so the GUI remains responsive.")
    
    def demo_validate(self):
        messagebox.showinfo("Validation Results", "File validation completed:\n\n✅ All 5 files are valid\n✅ Total customers: 350\n✅ All required fields present\n✅ Ready for import!")
    
    def demo_test_connection(self):
        messagebox.showinfo("Connection Test", "Connection test would verify:\n\n• API endpoint accessibility\n• Auth token validity\n• GK-Passport authentication\n• Network connectivity")
    
    def demo_clear_log(self):
        messagebox.showinfo("Clear Log", "This would clear the import log display.")
    
    def demo_save_log(self):
        messagebox.showinfo("Save Log", "This would save the import log to a text file.")
    
    def demo_export(self):
        messagebox.showinfo("Export Results", "This would export detailed import results to JSON or CSV format.")

def main():
    """Run the demo"""
    root = tk.Tk()
    
    # Try to set a nice theme
    try:
        style = ttk.Style()
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')
    except:
        pass
    
    app = DemoGUI(root)
    
    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    # Add demo info
    messagebox.showinfo(
        "Demo Mode", 
        "🎯 This is a DEMO of the Bulk Import GUI\n\n"
        "• All buttons show what they would do\n"
        "• No actual imports are performed\n"
        "• Explore all tabs to see features\n"
        "• Close this window to start the demo"
    )
    
    root.mainloop()

if __name__ == "__main__":
    main()