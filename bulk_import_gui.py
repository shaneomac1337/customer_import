"""
Bulk Customer Import GUI Application
A user-friendly interface for importing customers with multithreaded processing
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import json
import os
from datetime import datetime
import queue
import sys

# Import our bulk importer
from bulk_import_multithreaded import BulkCustomerImporter

class BulkImportGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bulk Customer Import Tool")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Variables
        self.api_url = tk.StringVar(value="https://prod.cse.cloud4retail.co/customer-profile-service/tenants/001/services/rest/customers-import/v1/customers")
        self.auth_token = tk.StringVar()
        self.gk_passport = tk.StringVar(value="1.1:CiMg46zV+88yKOOMxZPwMjIDMDAxOg5idXNpbmVzc1VuaXRJZBIKCAISBnVzZXJJZBoSCAIaCGNsaWVudElkIgR3c0lkIhoaGGI6Y3VzdC5jdXN0b21lci5pbXBvcnRlcg==")
        self.batch_size = tk.IntVar(value=70)
        self.max_workers = tk.IntVar(value=3)
        self.delay_between_requests = tk.DoubleVar(value=0.5)
        self.max_retries = tk.IntVar(value=3)

        # New authentication variables
        self.use_auto_auth = tk.BooleanVar(value=False)
        self.username = tk.StringVar(value="coop_sweden")
        self.password = tk.StringVar(value="coopsverige123")
        
        # File management
        self.selected_files = []
        self.import_running = False
        self.import_thread = None
        
        # Progress tracking
        self.progress_queue = queue.Queue()
        self.current_importer = None
        
        self.create_widgets()
        self.check_progress_queue()
    
    def create_widgets(self):
        """Create all GUI widgets"""
        
        # Main notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configuration Tab
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="Configuration")
        self.create_config_tab(config_frame)
        
        # Files Tab
        files_frame = ttk.Frame(notebook)
        notebook.add(files_frame, text="Files")
        self.create_files_tab(files_frame)
        
        # Import Tab
        import_frame = ttk.Frame(notebook)
        notebook.add(import_frame, text="Import")
        self.create_import_tab(import_frame)
        
        # Results Tab
        results_frame = ttk.Frame(notebook)
        notebook.add(results_frame, text="Results")
        self.create_results_tab(results_frame)

        # API Responses Tab
        api_responses_frame = ttk.Frame(notebook)
        notebook.add(api_responses_frame, text="API Responses")
        self.create_api_responses_tab(api_responses_frame)
    
    def create_config_tab(self, parent):
        """Create configuration tab"""
        
        # API Configuration
        api_group = ttk.LabelFrame(parent, text="API Configuration", padding=10)
        api_group.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(api_group, text="API URL:").grid(row=0, column=0, sticky=tk.W, pady=2)
        api_entry = ttk.Entry(api_group, textvariable=self.api_url, width=80)
        api_entry.grid(row=0, column=1, columnspan=2, sticky=tk.EW, pady=2)
        
        # Authentication mode selection
        auth_mode_frame = ttk.Frame(api_group)
        auth_mode_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(auth_mode_frame, text="Authentication Mode:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(auth_mode_frame, text="Manual Token", variable=self.use_auto_auth,
                       value=False, command=self.toggle_auth_mode).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(auth_mode_frame, text="Automatic (Username/Password)", variable=self.use_auto_auth,
                       value=True, command=self.toggle_auth_mode).pack(side=tk.LEFT)

        # Manual authentication fields
        self.manual_auth_frame = ttk.Frame(api_group)
        self.manual_auth_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(self.manual_auth_frame, text="Auth Token:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.auth_entry = ttk.Entry(self.manual_auth_frame, textvariable=self.auth_token, width=60, show="*")
        self.auth_entry.grid(row=0, column=1, sticky=tk.EW, pady=2, padx=(10, 5))
        ttk.Button(self.manual_auth_frame, text="Show", command=lambda: self.toggle_password(self.auth_entry)).grid(row=0, column=2, padx=5)

        ttk.Label(self.manual_auth_frame, text="GK-Passport:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.passport_entry = ttk.Entry(self.manual_auth_frame, textvariable=self.gk_passport, width=60, show="*", state="readonly")
        self.passport_entry.grid(row=1, column=1, sticky=tk.EW, pady=2, padx=(10, 5))
        ttk.Label(self.manual_auth_frame, text="(Hardcoded)", foreground="gray").grid(row=1, column=2, padx=5)

        # Automatic authentication fields
        self.auto_auth_frame = ttk.Frame(api_group)
        self.auto_auth_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(self.auto_auth_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(self.auto_auth_frame, textvariable=self.username, width=30).grid(row=0, column=1, sticky=tk.W, pady=2, padx=(10, 0))

        ttk.Label(self.auto_auth_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.password_entry = ttk.Entry(self.auto_auth_frame, textvariable=self.password, width=30, show="*")
        self.password_entry.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(10, 5))
        ttk.Button(self.auto_auth_frame, text="Show", command=lambda: self.toggle_password(self.password_entry)).grid(row=1, column=2, padx=5)

        ttk.Label(self.auto_auth_frame, text="GK-Passport:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.auto_passport_entry = ttk.Entry(self.auto_auth_frame, textvariable=self.gk_passport, width=60, show="*", state="readonly")
        self.auto_passport_entry.grid(row=2, column=1, sticky=tk.EW, pady=2, padx=(10, 5))
        ttk.Label(self.auto_auth_frame, text="(Hardcoded)", foreground="gray").grid(row=2, column=2, padx=5)

        # Configure column weights for proper resizing
        self.manual_auth_frame.columnconfigure(1, weight=1)
        self.auto_auth_frame.columnconfigure(1, weight=1)

        # Test authentication button
        ttk.Button(api_group, text="Test Authentication", command=self.test_connection).grid(row=4, column=1, sticky=tk.E, pady=(10, 0))

        # Initially set up the auth mode
        self.toggle_auth_mode()
        
        api_group.columnconfigure(1, weight=1)
        
        # Import Settings
        settings_group = ttk.LabelFrame(parent, text="Import Settings", padding=10)
        settings_group.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(settings_group, text="Batch Size:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(settings_group, from_=10, to=100, textvariable=self.batch_size, width=10).grid(row=0, column=1, sticky=tk.W, pady=2)
        ttk.Label(settings_group, text="(customers per batch)").grid(row=0, column=2, sticky=tk.W, pady=2)
        
        ttk.Label(settings_group, text="Worker Threads:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(settings_group, from_=1, to=10, textvariable=self.max_workers, width=10).grid(row=1, column=1, sticky=tk.W, pady=2)
        ttk.Label(settings_group, text="(concurrent requests)").grid(row=1, column=2, sticky=tk.W, pady=2)
        
        ttk.Label(settings_group, text="Request Delay:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(settings_group, from_=0.1, to=5.0, increment=0.1, textvariable=self.delay_between_requests, width=10).grid(row=2, column=1, sticky=tk.W, pady=2)
        ttk.Label(settings_group, text="(seconds between requests)").grid(row=2, column=2, sticky=tk.W, pady=2)
        
        ttk.Label(settings_group, text="Max Retries:").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(settings_group, from_=1, to=10, textvariable=self.max_retries, width=10).grid(row=3, column=1, sticky=tk.W, pady=2)
        ttk.Label(settings_group, text="(retry attempts for failed batches)").grid(row=3, column=2, sticky=tk.W, pady=2)
        
        # Preset buttons
        presets_group = ttk.LabelFrame(parent, text="Presets", padding=10)
        presets_group.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(presets_group, text="Conservative (Safe)", command=self.set_conservative_preset).pack(side=tk.LEFT, padx=5)
        ttk.Button(presets_group, text="Balanced (Recommended)", command=self.set_balanced_preset).pack(side=tk.LEFT, padx=5)
        ttk.Button(presets_group, text="Aggressive (Fast)", command=self.set_aggressive_preset).pack(side=tk.LEFT, padx=5)
    
    def create_files_tab(self, parent):
        """Create files management tab"""
        
        # File selection
        selection_group = ttk.LabelFrame(parent, text="File Selection", padding=10)
        selection_group.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Buttons frame
        buttons_frame = ttk.Frame(selection_group)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(buttons_frame, text="Add Files", command=self.add_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Add Directory", command=self.add_directory).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Clear All", command=self.clear_files).pack(side=tk.LEFT, padx=5)
        
        # File list
        list_frame = ttk.Frame(selection_group)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for file list
        columns = ("File", "Customers", "Size", "Status")
        self.file_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.file_tree.heading(col, text=col)
            self.file_tree.column(col, width=150)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.file_tree.grid(row=0, column=0, sticky=tk.NSEW)
        v_scrollbar.grid(row=0, column=1, sticky=tk.NS)
        h_scrollbar.grid(row=1, column=0, sticky=tk.EW)
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Summary
        self.files_summary = ttk.Label(selection_group, text="No files selected")
        self.files_summary.pack(pady=5)
    
    def create_import_tab(self, parent):
        """Create import control tab"""
        
        # Control buttons
        control_group = ttk.LabelFrame(parent, text="Import Control", padding=10)
        control_group.pack(fill=tk.X, padx=10, pady=5)
        
        self.start_button = ttk.Button(control_group, text="Start Import", command=self.start_import, style="Accent.TButton")
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(control_group, text="Stop Import", command=self.stop_import, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_group, text="Validate Files", command=self.validate_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_group, text="Test Connection", command=self.test_connection).pack(side=tk.LEFT, padx=5)
        
        # Progress
        progress_group = ttk.LabelFrame(parent, text="Progress", padding=10)
        progress_group.pack(fill=tk.X, padx=10, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_group, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.progress_label = ttk.Label(progress_group, text="Ready to import")
        self.progress_label.pack()
        
        # Statistics
        stats_group = ttk.LabelFrame(parent, text="Statistics", padding=10)
        stats_group.pack(fill=tk.X, padx=10, pady=5)
        
        stats_frame = ttk.Frame(stats_group)
        stats_frame.pack(fill=tk.X)
        
        # Create statistics labels
        self.stats_labels = {}
        stats_items = [
            ("Total Batches:", "total_batches"),
            ("Completed:", "completed_batches"),
            ("Failed:", "failed_batches"),
            ("Success Rate:", "success_rate"),
            ("Duration:", "duration"),
            ("Customers/min:", "rate")
        ]
        
        for i, (label, key) in enumerate(stats_items):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(stats_frame, text=label).grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            self.stats_labels[key] = ttk.Label(stats_frame, text="0", font=("TkDefaultFont", 9, "bold"))
            self.stats_labels[key].grid(row=row, column=col+1, sticky=tk.W, padx=5, pady=2)
    
    def create_results_tab(self, parent):
        """Create results and logging tab"""
        
        # Log output
        log_group = ttk.LabelFrame(parent, text="Import Log", padding=10)
        log_group.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_group, height=20, width=80)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Log controls
        log_controls = ttk.Frame(log_group)
        log_controls.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(log_controls, text="Clear Log", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_controls, text="Save Log", command=self.save_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_controls, text="Export Results", command=self.export_results).pack(side=tk.LEFT, padx=5)
    
    def toggle_password(self, entry_widget):
        """Toggle password visibility"""
        if entry_widget.cget("show") == "*":
            entry_widget.config(show="")
        else:
            entry_widget.config(show="*")

    def toggle_auth_mode(self):
        """Toggle between manual and automatic authentication modes"""
        if self.use_auto_auth.get():
            # Show automatic auth, hide manual auth
            self.manual_auth_frame.grid_remove()
            self.auto_auth_frame.grid()
        else:
            # Show manual auth, hide automatic auth
            self.auto_auth_frame.grid_remove()
            self.manual_auth_frame.grid()
    
    def set_conservative_preset(self):
        """Set conservative import settings"""
        self.batch_size.set(50)
        self.max_workers.set(2)
        self.delay_between_requests.set(1.0)
        self.max_retries.set(5)
        self.log_message("Applied Conservative preset: 50 batch size, 2 workers, 1.0s delay")
    
    def set_balanced_preset(self):
        """Set balanced import settings"""
        self.batch_size.set(70)
        self.max_workers.set(3)
        self.delay_between_requests.set(0.5)
        self.max_retries.set(3)
        self.log_message("Applied Balanced preset: 70 batch size, 3 workers, 0.5s delay")
    
    def set_aggressive_preset(self):
        """Set aggressive import settings"""
        self.batch_size.set(100)
        self.max_workers.set(5)
        self.delay_between_requests.set(0.2)
        self.max_retries.set(2)
        self.log_message("Applied Aggressive preset: 100 batch size, 5 workers, 0.2s delay")
    
    def add_files(self):
        """Add individual files"""
        files = filedialog.askopenfilenames(
            title="Select Customer JSON Files",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        for file in files:
            if file not in self.selected_files:
                self.selected_files.append(file)
        
        self.update_file_list()
    
    def add_directory(self):
        """Add all JSON files from a directory"""
        directory = filedialog.askdirectory(title="Select Directory with Customer Files")
        
        if directory:
            json_files = [f for f in os.listdir(directory) if f.endswith('.json')]
            
            for file in json_files:
                full_path = os.path.join(directory, file)
                if full_path not in self.selected_files:
                    self.selected_files.append(full_path)
            
            self.update_file_list()
            self.log_message(f"Added {len(json_files)} files from {directory}")
    

    def clear_files(self):
        """Clear all selected files"""
        self.selected_files.clear()
        self.update_file_list()
        self.log_message("Cleared all selected files")
    
    def update_file_list(self):
        """Update the file list display"""
        # Clear existing items
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        total_customers = 0
        total_size = 0
        
        for file_path in self.selected_files:
            try:
                # Get file info
                file_size = os.path.getsize(file_path)
                total_size += file_size
                
                # Try to count customers
                customer_count = 0
                status = "Valid"
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    customer_count = len(data.get('data', []))
                    total_customers += customer_count
                except Exception as e:
                    status = f"Error: {str(e)[:30]}..."
                
                # Add to tree
                self.file_tree.insert("", tk.END, values=(
                    os.path.basename(file_path),
                    customer_count,
                    f"{file_size:,} bytes",
                    status
                ))
                
            except Exception as e:
                self.file_tree.insert("", tk.END, values=(
                    os.path.basename(file_path),
                    "?",
                    "?",
                    f"Error: {str(e)[:30]}..."
                ))
        
        # Update summary
        self.files_summary.config(text=f"{len(self.selected_files)} files selected, {total_customers:,} customers, {total_size:,} bytes")
    
    def validate_files(self):
        """Validate all selected files"""
        if not self.selected_files:
            messagebox.showwarning("Warning", "No files selected!")
            return
        
        self.log_message("Validating files...")
        
        valid_files = 0
        total_customers = 0
        errors = []
        
        for file_path in self.selected_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                customers = data.get('data', [])
                if not customers:
                    errors.append(f"{os.path.basename(file_path)}: No customer data found")
                    continue
                
                # Basic validation
                for i, customer in enumerate(customers[:3]):  # Check first 3 customers
                    if not customer.get('person', {}).get('customerId'):
                        errors.append(f"{os.path.basename(file_path)}: Customer {i+1} missing customerId")
                        break
                
                valid_files += 1
                total_customers += len(customers)
                
            except Exception as e:
                errors.append(f"{os.path.basename(file_path)}: {str(e)}")
        
        # Show results
        if errors:
            error_msg = "\n".join(errors[:10])  # Show first 10 errors
            if len(errors) > 10:
                error_msg += f"\n... and {len(errors) - 10} more errors"
            messagebox.showerror("Validation Errors", error_msg)
        else:
            messagebox.showinfo("Validation Success", f"All {valid_files} files are valid!\nTotal customers: {total_customers:,}")
        
        self.log_message(f"Validation complete: {valid_files}/{len(self.selected_files)} files valid, {len(errors)} errors")
    
    def test_connection(self):
        """Test API connection"""
        self.log_message("🔍 Testing authentication...")

        try:
            # Create a temporary importer to test authentication
            if self.use_auto_auth.get():
                # Test automatic authentication
                if not self.username.get() or not self.password.get():
                    messagebox.showerror("Error", "Please enter Username and Password!")
                    return

                importer = BulkCustomerImporter(
                    api_url=self.api_url.get(),
                    gk_passport=self.gk_passport.get(),
                    username=self.username.get(),
                    password=self.password.get(),
                    use_auto_auth=True
                )
            else:
                # Test manual authentication
                if not self.auth_token.get():
                    messagebox.showerror("Error", "Please enter Auth Token!")
                    return

                importer = BulkCustomerImporter(
                    api_url=self.api_url.get(),
                    auth_token=self.auth_token.get(),
                    gk_passport=self.gk_passport.get(),
                    use_auto_auth=False
                )

            # Test authentication
            result = importer.test_authentication()

            if result['success']:
                self.log_message(f"✅ Authentication successful!")
                if 'token_preview' in result:
                    self.log_message(f"   Token: {result['token_preview']}")
                if 'expires_at' in result and result['expires_at']:
                    self.log_message(f"   Expires: {result['expires_at']}")

                messagebox.showinfo("Authentication Test",
                                  f"✅ Authentication successful!\n\n"
                                  f"Mode: {'Automatic' if self.use_auto_auth.get() else 'Manual'}\n"
                                  f"Token: {result.get('token_preview', 'N/A')}\n"
                                  f"Message: {result.get('message', 'OK')}")
            else:
                self.log_message(f"❌ Authentication failed: {result.get('error', 'Unknown error')}")
                messagebox.showerror("Authentication Test",
                                   f"❌ Authentication failed!\n\n"
                                   f"Error: {result.get('error', 'Unknown error')}\n"
                                   f"Message: {result.get('message', 'Authentication failed')}")

        except Exception as e:
            self.log_message(f"❌ Authentication test error: {e}")
            messagebox.showerror("Authentication Test", f"Test failed with error:\n{e}")
    
    def start_import(self):
        """Start the import process"""
        # Validation
        if not self.selected_files:
            messagebox.showerror("Error", "No files selected!")
            return
        
        # Validate authentication based on mode
        if self.use_auto_auth.get():
            if not self.username.get() or not self.password.get():
                messagebox.showerror("Error", "Please enter Username and Password!")
                return
        else:
            if not self.auth_token.get():
                messagebox.showerror("Error", "Please enter Auth Token!")
                return
        
        if self.import_running:
            messagebox.showwarning("Warning", "Import is already running!")
            return
        
        # Confirm start
        total_customers = sum(self.count_customers_in_file(f) for f in self.selected_files)
        
        result = messagebox.askyesno(
            "Confirm Import",
            f"Start import of {total_customers:,} customers from {len(self.selected_files)} files?\n\n"
            f"Settings:\n"
            f"- Batch size: {self.batch_size.get()}\n"
            f"- Worker threads: {self.max_workers.get()}\n"
            f"- Request delay: {self.delay_between_requests.get()}s\n"
            f"- Max retries: {self.max_retries.get()}"
        )
        
        if not result:
            return
        
        # Start import in separate thread
        self.import_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        self.import_thread = threading.Thread(target=self.run_import, daemon=True)
        self.import_thread.start()
        
        self.log_message(f"Started import of {total_customers:,} customers from {len(self.selected_files)} files")
    
    def stop_import(self):
        """Stop the import process"""
        if self.import_running:
            self.import_running = False
            self.log_message("Stopping import... (may take a moment)")
            
            # Note: The actual stopping mechanism would need to be implemented in the importer
            messagebox.showinfo("Stop Import", "Import stop requested. Current batches will complete.")
    
    def run_import(self):
        """Run the import process (in separate thread)"""
        try:
            # Create importer with progress callback based on authentication mode
            # Generate unique failed customers filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            failed_customers_file = f"failed_customers_{timestamp}.json"

            if self.use_auto_auth.get():
                importer = BulkCustomerImporter(
                    api_url=self.api_url.get(),
                    gk_passport=self.gk_passport.get(),
                    batch_size=self.batch_size.get(),
                    max_workers=self.max_workers.get(),
                    delay_between_requests=self.delay_between_requests.get(),
                    max_retries=self.max_retries.get(),
                    progress_callback=self.handle_api_response,
                    username=self.username.get(),
                    password=self.password.get(),
                    use_auto_auth=True,
                    failed_customers_file=failed_customers_file
                )
            else:
                importer = BulkCustomerImporter(
                    api_url=self.api_url.get(),
                    auth_token=self.auth_token.get(),
                    gk_passport=self.gk_passport.get(),
                    batch_size=self.batch_size.get(),
                    max_workers=self.max_workers.get(),
                    delay_between_requests=self.delay_between_requests.get(),
                    max_retries=self.max_retries.get(),
                    progress_callback=self.handle_api_response,
                    use_auto_auth=False,
                    failed_customers_file=failed_customers_file
                )
            
            self.current_importer = importer
            
            # Run import
            result = importer.import_customers(self.selected_files)
            
            # Update UI with results
            self.progress_queue.put(("complete", result))
            
        except Exception as e:
            self.progress_queue.put(("error", str(e)))
        finally:
            self.import_running = False
            self.current_importer = None
    
    def check_progress_queue(self):
        """Check for progress updates from import thread"""
        try:
            while True:
                message_type, data = self.progress_queue.get_nowait()
                
                if message_type == "complete":
                    self.handle_import_complete(data)
                elif message_type == "error":
                    self.handle_import_error(data)
                elif message_type == "progress":
                    self.handle_progress_update(data)
                elif message_type == "api_response":
                    self.log_api_response(data)
                elif message_type == "retry_files_created":
                    self.handle_retry_files_created(data)
                
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.check_progress_queue)
    
    def handle_import_complete(self, result):
        """Handle import completion"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        if result:
            success_rate = result.get('success_rate', '0%')
            duration = result.get('duration_seconds', 0)
            
            self.progress_var.set(100)
            self.progress_label.config(text=f"Import completed! Success rate: {success_rate}")
            
            # Update statistics
            self.stats_labels['total_batches'].config(text=str(result.get('total_batches', 0)))
            self.stats_labels['completed_batches'].config(text=str(result.get('successful_batches', 0)))
            self.stats_labels['failed_batches'].config(text=str(result.get('failed_batches', 0)))
            self.stats_labels['success_rate'].config(text=success_rate)
            self.stats_labels['duration'].config(text=f"{duration:.1f}s")
            
            if duration > 0:
                rate = (result.get('successful_customers', 0) * 60) / duration
                self.stats_labels['rate'].config(text=f"{rate:.1f}")
            
            self.log_message(f"Import completed! {result.get('successful_customers', 0)} customers imported successfully")

            # Get failed customers summary if available
            failed_summary = ""
            if self.current_importer:
                try:
                    failed_info = self.current_importer.get_failed_customers_summary()
                    if failed_info['total_failed'] > 0:
                        failed_summary = f"\n\n❌ Failed Customers Details:\n"
                        failed_summary += f"Total failed: {failed_info['total_failed']}\n"
                        failed_summary += f"Failed customers file: {failed_info['failed_customers_file']}\n"

                        # Show error types
                        if 'error_types' in failed_info:
                            failed_summary += "\nError breakdown:\n"
                            for error, count in failed_info['error_types'].items():
                                failed_summary += f"  • {error}: {count}\n"
                except Exception as e:
                    failed_summary = f"\n\nNote: Could not retrieve failed customer details: {e}"

            # Show completion dialog
            messagebox.showinfo(
                "Import Complete",
                f"Import completed!\n\n"
                f"Total customers: {result.get('total_customers', 0):,}\n"
                f"Successful: {result.get('successful_customers', 0):,}\n"
                f"Failed: {result.get('failed_customers', 0):,}\n"
                f"Success rate: {success_rate}\n"
                f"Duration: {duration:.1f} seconds"
                f"{failed_summary}"
            )
        else:
            self.log_message("Import completed with no results")
    
    def handle_import_error(self, error_msg):
        """Handle import error"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_label.config(text="Import failed")
        
        self.log_message(f"Import failed: {error_msg}")
        messagebox.showerror("Import Error", f"Import failed:\n{error_msg}")
    
    def handle_progress_update(self, progress_data):
        """Handle progress updates"""
        # This would be called if we implement progress callbacks in the importer
        pass

    def handle_api_response(self, response_data):
        """Handle API response from importer (called from worker thread)"""
        # Put the response data in the queue to be processed by the main thread
        self.progress_queue.put(("api_response", response_data))

    def handle_retry_files_created(self, retry_data):
        """Handle retry files creation notification"""
        retry_dir = retry_data.get('retry_directory', '')
        failed_batches = retry_data.get('failed_batches_count', 0)
        failed_customers = retry_data.get('failed_customers_count', 0)
        retry_files = retry_data.get('retry_files', [])

        # Log the retry files creation
        self.log_message(f"🔄 RETRY FILES CREATED:")
        self.log_message(f"   Directory: {retry_dir}")
        self.log_message(f"   Failed batches: {failed_batches}")
        self.log_message(f"   Failed customers: {failed_customers}")
        self.log_message(f"   Retry files: {len(retry_files)}")

        # Show popup notification
        retry_message = f"""Failed batches detected! Retry files have been created:

📁 Directory: {retry_dir}
📊 Failed batches: {failed_batches}
👥 Failed customers: {failed_customers}
📄 Retry files: {len(retry_files)}

The retry files are formatted correctly for immediate re-import.
You can load them using "Add Directory" in the Files tab.

Check the RETRY_INSTRUCTIONS.md file in the retry directory for detailed instructions."""

        messagebox.showinfo("Retry Files Created", retry_message)

        # Optionally, ask if user wants to load retry files immediately
        if messagebox.askyesno("Load Retry Files?",
                              f"Would you like to load the retry files from {retry_dir} now?\n\n"
                              "This will clear your current file selection and load only the failed batches for retry."):
            self.load_retry_directory(retry_dir)

    def load_retry_directory(self, retry_dir):
        """Load retry files from the specified directory"""
        try:
            # Clear current selection
            self.selected_files = []
            self.update_files_display()

            # Load all JSON files from retry directory (except summary files)
            retry_files = []
            for filename in os.listdir(retry_dir):
                if filename.startswith('retry_batch_') and filename.endswith('.json'):
                    filepath = os.path.join(retry_dir, filename)
                    retry_files.append(filepath)

            # Add retry files to selection
            self.selected_files.extend(sorted(retry_files))
            self.update_files_display()

            self.log_message(f"✅ Loaded {len(retry_files)} retry files from {retry_dir}")

            # Switch to Files tab to show the loaded files
            # Find the notebook widget and select the Files tab
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.Notebook):
                    widget.select(1)  # Files tab is typically index 1
                    break

        except Exception as e:
            self.log_message(f"❌ Error loading retry files: {e}")
            messagebox.showerror("Error", f"Failed to load retry files:\n{e}")
    
    def count_customers_in_file(self, file_path):
        """Count customers in a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return len(data.get('data', []))
        except:
            return 0
    
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.delete(1.0, tk.END)
    
    def save_log(self):
        """Save log to file"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Log File"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("Success", f"Log saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save log: {e}")
    
    def export_results(self):
        """Export import results"""
        # This would export detailed results if available
        messagebox.showinfo("Export Results", "Results export not implemented yet")

    def create_api_responses_tab(self, parent):
        """Create API responses tab"""

        # Main frame with scrollbar
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title
        ttk.Label(main_frame, text="Real-time API Responses", font=('Arial', 12, 'bold')).pack(pady=(0, 10))

        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(button_frame, text="Clear Responses", command=self.clear_api_responses).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Save Responses", command=self.save_api_responses).pack(side=tk.LEFT)

        # Auto-scroll checkbox
        self.auto_scroll_api = tk.BooleanVar(value=True)
        ttk.Checkbutton(button_frame, text="Auto-scroll", variable=self.auto_scroll_api).pack(side=tk.RIGHT)

        # API responses text area with scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.api_responses_text = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=('Consolas', 9),
            bg='#f8f9fa',
            fg='#212529'
        )
        self.api_responses_text.pack(fill=tk.BOTH, expand=True)

        # Add initial message
        self.api_responses_text.insert(tk.END, "API responses will appear here during import...\n\n")
        self.api_responses_text.config(state=tk.DISABLED)

    def clear_api_responses(self):
        """Clear API responses"""
        self.api_responses_text.config(state=tk.NORMAL)
        self.api_responses_text.delete(1.0, tk.END)
        self.api_responses_text.insert(tk.END, "API responses cleared.\n\n")
        self.api_responses_text.config(state=tk.DISABLED)

    def save_api_responses(self):
        """Save API responses to file"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("JSON files", "*.json"), ("All files", "*.*")],
                title="Save API Responses"
            )

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.api_responses_text.get(1.0, tk.END))
                messagebox.showinfo("Success", f"API responses saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save API responses: {e}")

    def log_api_response(self, response_data):
        """Log API response to the API responses tab"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.api_responses_text.config(state=tk.NORMAL)

        if response_data['type'] == 'batch_success':
            failed_count = response_data.get('failed_customers_count', 0)
            status_icon = "⚠️" if failed_count > 0 else "✅"

            self.api_responses_text.insert(tk.END, f"[{timestamp}] {status_icon} SUCCESS - Batch {response_data['batch_id']}\n")
            self.api_responses_text.insert(tk.END, f"Status Code: {response_data['status_code']}\n")
            self.api_responses_text.insert(tk.END, f"Customers: {response_data['customers_count']}\n")
            
            # Show response file location instead of full data
            response_file = response_data.get('response_file', 'not_saved')
            self.api_responses_text.insert(tk.END, f"Response File: {response_file}\n")
            
            # Show response summary instead of full data
            response_summary = response_data.get('response_summary', {})
            if response_summary:
                if 'total_customers' in response_summary:
                    self.api_responses_text.insert(tk.END, f"API Processed: {response_summary['total_customers']} customers\n")
                if 'success_count' in response_summary:
                    self.api_responses_text.insert(tk.END, f"API Success: {response_summary['success_count']}\n")
                if 'failure_count' in response_summary:
                    self.api_responses_text.insert(tk.END, f"API Failures: {response_summary['failure_count']}\n")

            if failed_count > 0:
                self.api_responses_text.insert(tk.END, f"❌ Failed Customers: {failed_count}\n")
                failed_customers = response_data.get('failed_customers', [])
                if failed_customers:
                    self.api_responses_text.insert(tk.END, f"Failed Customer Details (first 3):\n")
                    for i, customer in enumerate(failed_customers[:3], 1):
                        self.api_responses_text.insert(tk.END, f"  {i}. ID: {customer.get('customerId', 'Unknown')}\n")
                        self.api_responses_text.insert(tk.END, f"     Username: {customer.get('username', 'Unknown')}\n")
                        self.api_responses_text.insert(tk.END, f"     Error: {customer.get('error', 'Unknown error')}\n")

                        # Show enhanced batch information if available
                        if 'batch_number' in customer:
                            self.api_responses_text.insert(tk.END, f"     Batch: {customer.get('batch_number', 'Unknown')} of {customer.get('total_batches', 'Unknown')}\n")
                        if 'batch_size' in customer:
                            self.api_responses_text.insert(tk.END, f"     Batch Size: {customer.get('batch_size', 'Unknown')} customers\n")
                        if 'source_file' in customer and customer.get('source_file') != 'unknown':
                            self.api_responses_text.insert(tk.END, f"     Source File: {customer.get('source_file', 'Unknown')}\n")

            # Show lightweight headers instead of full headers
            headers = response_data.get('response_headers', {})
            if headers:
                self.api_responses_text.insert(tk.END, f"Headers: Content-Type: {headers.get('content-type', 'unknown')}, ")
                self.api_responses_text.insert(tk.END, f"Size: {headers.get('content-length', 'unknown')}\n")
            
            self.api_responses_text.insert(tk.END, "-" * 80 + "\n\n")

        elif response_data['type'] == 'batch_error':
            self.api_responses_text.insert(tk.END, f"[{timestamp}] ❌ ERROR - Batch {response_data['batch_id']}\n")
            self.api_responses_text.insert(tk.END, f"Status Code: {response_data['status_code']}\n")
            self.api_responses_text.insert(tk.END, f"Customers: {response_data['customers_count']}\n")
            self.api_responses_text.insert(tk.END, f"Attempt: {response_data['attempt']}/{response_data['max_retries']}\n")
            
            # Show response file and error summary instead of full error data
            response_file = response_data.get('response_file', 'not_saved')
            self.api_responses_text.insert(tk.END, f"Response File: {response_file}\n")
            
            error_summary = response_data.get('error_summary', 'Unknown error')
            self.api_responses_text.insert(tk.END, f"Error Summary: {error_summary}\n")
            
            # Show lightweight headers
            headers = response_data.get('response_headers', {})
            if headers:
                self.api_responses_text.insert(tk.END, f"Content-Type: {headers.get('content-type', 'unknown')}\n")
            
            self.api_responses_text.insert(tk.END, "-" * 80 + "\n\n")

        if self.auto_scroll_api.get():
            self.api_responses_text.see(tk.END)

        self.api_responses_text.config(state=tk.DISABLED)

def main():
    """Main function to run the GUI"""
    root = tk.Tk()
    
    # Set theme (if available)
    try:
        root.tk.call("source", "azure.tcl")
        root.tk.call("set_theme", "light")
    except:
        pass  # Theme not available, use default
    
    app = BulkImportGUI(root)
    
    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()