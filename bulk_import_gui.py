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
import time

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
        self.file_loading_queue = queue.Queue()
        self.current_importer = None

        # Cache for customer counts to avoid re-reading files
        self.customer_count_cache = {}
        
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

        # Failed Customers Tab
        failed_customers_frame = ttk.Frame(notebook)
        notebook.add(failed_customers_frame, text="Failed Customers")
        self.create_failed_customers_tab(failed_customers_frame)
    
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

        self.pause_button = ttk.Button(control_group, text="Pause Import", command=self.pause_import, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)

        self.resume_button = ttk.Button(control_group, text="Resume Import", command=self.resume_import, state=tk.DISABLED)
        self.resume_button.pack(side=tk.LEFT, padx=5)

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
            # First, quickly count JSON files
            json_files = [f for f in os.listdir(directory) if f.endswith('.json')]

            if not json_files:
                messagebox.showinfo("No Files", "No JSON files found in the selected directory.")
                return

            # Show confirmation for large directories
            if len(json_files) > 1000:
                result = messagebox.askyesno(
                    "Large Directory",
                    f"Found {len(json_files):,} JSON files in the directory.\n\n"
                    f"Loading this many files may take several minutes.\n"
                    f"Do you want to continue?",
                    icon='warning'
                )
                if not result:
                    return

            # Add files to selection (fast operation)
            added_count = 0
            for file in json_files:
                full_path = os.path.join(directory, file)
                if full_path not in self.selected_files:
                    self.selected_files.append(full_path)
                    added_count += 1

            # Show progress dialog for file processing
            if len(self.selected_files) > 500:
                self.show_file_loading_progress()
            else:
                self.update_file_list()

            self.log_message(f"Added {added_count} files from {directory} ({len(json_files)} total found)")
    

    def clear_files(self):
        """Clear all selected files"""
        self.selected_files.clear()
        self.update_file_list()
        self.log_message("Cleared all selected files")

    def show_file_loading_progress(self):
        """Show progress dialog for file loading"""
        # Create progress dialog
        self.progress_dialog = tk.Toplevel(self.root)
        self.progress_dialog.title("Loading Files")
        self.progress_dialog.geometry("400x150")
        self.progress_dialog.resizable(False, False)
        self.progress_dialog.transient(self.root)
        self.progress_dialog.grab_set()

        # Center the dialog
        self.progress_dialog.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))

        # Progress dialog content
        ttk.Label(self.progress_dialog, text="Loading and analyzing files...", font=('Arial', 10)).pack(pady=10)

        self.file_progress_var = tk.DoubleVar()
        self.file_progress_bar = ttk.Progressbar(
            self.progress_dialog,
            variable=self.file_progress_var,
            maximum=100,
            length=350
        )
        self.file_progress_bar.pack(pady=10)

        self.file_progress_label = ttk.Label(self.progress_dialog, text="Preparing...")
        self.file_progress_label.pack(pady=5)

        # Cancel button
        cancel_frame = ttk.Frame(self.progress_dialog)
        cancel_frame.pack(pady=10)

        self.cancel_loading = False
        ttk.Button(cancel_frame, text="Cancel", command=self.cancel_file_loading).pack()

        # Start background processing
        self.file_loading_thread = threading.Thread(target=self.process_files_background, daemon=True)
        self.file_loading_thread.start()

        # Start checking for updates
        self.check_file_loading_progress()

    def cancel_file_loading(self):
        """Cancel file loading process"""
        self.cancel_loading = True
        self.progress_dialog.destroy()
        self.log_message("File loading cancelled by user")

    def process_files_background(self):
        """Process files in background thread"""
        try:
            total_files = len(self.selected_files)
            processed = 0

            # Create file info cache
            file_info_cache = []

            for file_path in self.selected_files:
                if self.cancel_loading:
                    return

                try:
                    # Get file info
                    file_size = os.path.getsize(file_path)

                    # Try to count customers (this is the slow part)
                    customer_count = 0
                    status = "Valid"

                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        customer_count = len(data.get('data', []))
                    except Exception as e:
                        status = f"Error: {str(e)[:30]}..."

                    file_info_cache.append({
                        'path': file_path,
                        'name': os.path.basename(file_path),
                        'size': file_size,
                        'customers': customer_count,
                        'status': status
                    })

                except Exception as e:
                    file_info_cache.append({
                        'path': file_path,
                        'name': os.path.basename(file_path),
                        'size': 0,
                        'customers': 0,
                        'status': f"Error: {str(e)[:30]}..."
                    })

                processed += 1

                # Update progress (put in queue for main thread)
                progress_percent = (processed / total_files) * 100
                self.file_loading_queue.put(('progress', progress_percent, processed, total_files))

                # Small delay to keep GUI responsive
                time.sleep(0.001)

            # Send completion signal
            if not self.cancel_loading:
                self.file_loading_queue.put(('complete', file_info_cache))

        except Exception as e:
            self.file_loading_queue.put(('error', str(e)))

    def check_file_loading_progress(self):
        """Check for file loading progress updates"""
        try:
            while True:
                message_type, *data = self.file_loading_queue.get_nowait()

                if message_type == 'progress':
                    progress_percent, processed, total = data
                    self.file_progress_var.set(progress_percent)
                    self.file_progress_label.config(text=f"Processing file {processed:,} of {total:,}...")

                elif message_type == 'complete':
                    file_info_cache = data[0]
                    self.file_progress_var.set(100)
                    self.file_progress_label.config(text="Updating display...")

                    # Update the file list with cached data
                    self.update_file_list_with_cache(file_info_cache)

                    # Close progress dialog
                    self.progress_dialog.destroy()
                    self.log_message(f"Successfully loaded {len(file_info_cache):,} files")
                    return

                elif message_type == 'error':
                    error_msg = data[0]
                    self.progress_dialog.destroy()
                    messagebox.showerror("Loading Error", f"Error loading files: {error_msg}")
                    self.log_message(f"Error loading files: {error_msg}")
                    return

        except queue.Empty:
            pass

        # Schedule next check if dialog still exists
        if hasattr(self, 'progress_dialog') and self.progress_dialog.winfo_exists():
            self.root.after(100, self.check_file_loading_progress)

    def update_file_list_with_cache(self, file_info_cache):
        """Update file list using pre-processed cache data"""
        # Clear existing items
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        total_customers = 0
        total_size = 0

        # Clear and rebuild customer count cache
        self.customer_count_cache = {}

        for file_info in file_info_cache:
            # Add to tree
            self.file_tree.insert("", tk.END, values=(
                file_info['name'],
                file_info['customers'],
                f"{file_info['size']:,} bytes",
                file_info['status']
            ))

            # Cache customer count for fast access later
            self.customer_count_cache[file_info['path']] = file_info['customers']

            if file_info['status'] == "Valid":
                total_customers += file_info['customers']
            total_size += file_info['size']

        # Update summary
        self.files_summary.config(text=f"{len(self.selected_files)} files selected, {total_customers:,} customers, {total_size:,} bytes")
    
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
                    # Cache the customer count
                    self.customer_count_cache[file_path] = customer_count
                except Exception as e:
                    status = f"Error: {str(e)[:30]}..."
                    # Cache zero for error files
                    self.customer_count_cache[file_path] = 0
                
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
        self.pause_button.config(state=tk.NORMAL)
        self.resume_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        self.import_thread = threading.Thread(target=self.run_import, daemon=True)
        self.import_thread.start()
        
        self.log_message(f"Started import of {total_customers:,} customers from {len(self.selected_files)} files")
    
    def pause_import(self):
        """Pause the import process"""
        if self.import_running and self.current_importer:
            self.current_importer.pause_import()
            self.pause_button.config(state=tk.DISABLED)
            self.resume_button.config(state=tk.NORMAL)
            self.log_message("⏸️ Import paused - current batches will complete, then pause")
            messagebox.showinfo("Pause Import", "Import paused. Click Resume to continue.")

    def resume_import(self):
        """Resume the paused import process"""
        if self.import_running and self.current_importer:
            self.current_importer.resume_import()
            self.pause_button.config(state=tk.NORMAL)
            self.resume_button.config(state=tk.DISABLED)
            self.log_message("▶️ Import resumed")
            messagebox.showinfo("Resume Import", "Import resumed.")

    def stop_import(self):
        """Stop the import process"""
        if self.import_running and self.current_importer:
            self.current_importer.stop_import()
            self.log_message("🛑 Stopping import... (current batches will complete)")
            messagebox.showinfo("Stop Import", "Import stop requested. Current batches will complete, then stop.\nRemaining work will be saved for resume.")
    
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
                    # Auto-refresh failed customers tab if enabled
                    if hasattr(self, 'auto_refresh_failed') and self.auto_refresh_failed.get():
                        self.refresh_failed_customers()
                elif message_type == "retry_files_created":
                    self.handle_retry_files_created(data)
                
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.check_progress_queue)
    
    def handle_import_complete(self, result):
        """Handle import completion"""
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.resume_button.config(state=tk.DISABLED)
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

        # Final refresh of failed customers tab
        if hasattr(self, 'failed_customers_tree'):
            self.refresh_failed_customers()
    
    def handle_import_error(self, error_msg):
        """Handle import error"""
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.resume_button.config(state=tk.DISABLED)
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
            self.update_file_list()

            # Load all JSON files from retry directory (except summary files)
            retry_files = []
            for filename in os.listdir(retry_dir):
                if filename.startswith('retry_batch_') and filename.endswith('.json'):
                    filepath = os.path.join(retry_dir, filename)
                    retry_files.append(filepath)

            # Add retry files to selection
            self.selected_files.extend(sorted(retry_files))
            self.update_file_list()

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
        """Count customers in a file - uses cache if available"""
        # Check cache first (fast!)
        if file_path in self.customer_count_cache:
            return self.customer_count_cache[file_path]

        # Fallback to reading file (slow, but safe)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            count = len(data.get('data', []))
            # Cache the result for next time
            self.customer_count_cache[file_path] = count
            return count
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

    def create_failed_customers_tab(self, parent):
        """Create failed customers tab"""

        # Main frame
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title and summary frame
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text="Failed Customers", font=('Arial', 12, 'bold')).pack(side=tk.LEFT)

        # Total count label
        self.failed_count_label = ttk.Label(header_frame, text="Total: 0", font=('Arial', 10, 'bold'), foreground='red')
        self.failed_count_label.pack(side=tk.RIGHT)

        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(button_frame, text="Refresh", command=self.refresh_failed_customers).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Export Failed Customers", command=self.export_failed_customers).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Clear Failed Customers", command=self.clear_failed_customers).pack(side=tk.LEFT)

        # Auto-refresh checkbox
        self.auto_refresh_failed = tk.BooleanVar(value=True)
        ttk.Checkbutton(button_frame, text="Auto-refresh during import", variable=self.auto_refresh_failed).pack(side=tk.RIGHT)

        # Failed customers table
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Create Treeview for failed customers
        columns = ("Customer ID", "Username", "Error", "Timestamp", "Batch Info")
        self.failed_customers_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

        # Configure column headings and widths
        self.failed_customers_tree.heading("Customer ID", text="Customer ID")
        self.failed_customers_tree.heading("Username", text="Username")
        self.failed_customers_tree.heading("Error", text="Error")
        self.failed_customers_tree.heading("Timestamp", text="Timestamp")
        self.failed_customers_tree.heading("Batch Info", text="Batch Info")

        self.failed_customers_tree.column("Customer ID", width=120, minwidth=100)
        self.failed_customers_tree.column("Username", width=150, minwidth=120)
        self.failed_customers_tree.column("Error", width=300, minwidth=200)
        self.failed_customers_tree.column("Timestamp", width=150, minwidth=120)
        self.failed_customers_tree.column("Batch Info", width=200, minwidth=150)

        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.failed_customers_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.failed_customers_tree.xview)
        self.failed_customers_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Pack table and scrollbars
        self.failed_customers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Add initial message
        self.failed_customers_tree.insert("", tk.END, values=("No failed customers yet", "", "", "", ""))

        # Bind double-click to show details
        self.failed_customers_tree.bind("<Double-1>", self.show_failed_customer_details)

    def refresh_failed_customers(self):
        """Refresh the failed customers display"""
        try:
            # Clear existing items
            for item in self.failed_customers_tree.get_children():
                self.failed_customers_tree.delete(item)

            # Get failed customers from current importer
            failed_customers = []
            if self.current_importer:
                try:
                    failed_info = self.current_importer.get_failed_customers_summary()
                    if failed_info['total_failed'] > 0:
                        # Get the actual failed customers list
                        with self.current_importer.failed_customers_lock:
                            failed_customers = self.current_importer.failed_customers.copy()
                except Exception as e:
                    self.log_message(f"Error getting failed customers from importer: {e}")

            # Also try to load from failed customers file
            if not failed_customers:
                # Look for both timestamped and non-timestamped failed customers files
                failed_customers_files = []
                failed_customers_dir = "failed_customers"

                if os.path.exists(failed_customers_dir):
                    try:
                        # Find all failed customers JSON files
                        for filename in os.listdir(failed_customers_dir):
                            if filename.startswith('failed_customers') and filename.endswith('.json'):
                                filepath = os.path.join(failed_customers_dir, filename)
                                if os.path.isfile(filepath):
                                    failed_customers_files.append(filepath)

                        # Sort by modification time (most recent first)
                        failed_customers_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

                        # Try to load from the most recent file
                        if failed_customers_files:
                            failed_customers_file = failed_customers_files[0]
                            self.log_message(f"Loading failed customers from: {failed_customers_file}")
                            with open(failed_customers_file, 'r', encoding='utf-8') as f:
                                failed_customers = json.load(f)

                    except Exception as e:
                        self.log_message(f"Error loading failed customers file: {e}")

            # Update count label
            total_failed = len(failed_customers)
            self.failed_count_label.config(text=f"Total: {total_failed}")

            if total_failed == 0:
                self.failed_customers_tree.insert("", tk.END, values=("No failed customers", "", "", "", ""))
            else:
                # Add failed customers to tree
                for customer in failed_customers:
                    customer_id = customer.get('customerId', 'Unknown')
                    username = customer.get('username', 'Unknown')
                    error = customer.get('error', 'Unknown error')
                    timestamp = customer.get('timestamp', 'Unknown')
                    batch_info = customer.get('batchInfo', 'Unknown')

                    # Truncate long error messages for display
                    if len(error) > 50:
                        error = error[:47] + "..."

                    # Format timestamp for display
                    if timestamp != 'Unknown':
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            pass  # Keep original timestamp if parsing fails

                    self.failed_customers_tree.insert("", tk.END, values=(
                        customer_id, username, error, timestamp, batch_info
                    ))

            self.log_message(f"Refreshed failed customers display: {total_failed} failed customers")

        except Exception as e:
            self.log_message(f"Error refreshing failed customers: {e}")
            messagebox.showerror("Error", f"Failed to refresh failed customers: {e}")

    def export_failed_customers(self):
        """Export failed customers to file"""
        try:
            # Get failed customers data
            failed_customers = []
            if self.current_importer:
                try:
                    with self.current_importer.failed_customers_lock:
                        failed_customers = self.current_importer.failed_customers.copy()
                except Exception as e:
                    self.log_message(f"Error getting failed customers from importer: {e}")

            # Also try to load from file if no current importer data
            if not failed_customers:
                failed_customers_file = "failed_customers/failed_customers.json"
                if os.path.exists(failed_customers_file):
                    try:
                        with open(failed_customers_file, 'r', encoding='utf-8') as f:
                            failed_customers = json.load(f)
                    except Exception as e:
                        self.log_message(f"Error loading failed customers file: {e}")

            if not failed_customers:
                messagebox.showinfo("No Data", "No failed customers to export")
                return

            # Ask user for export file location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")],
                title="Export Failed Customers"
            )

            if file_path:
                if file_path.endswith('.csv'):
                    # Export as CSV
                    import csv
                    with open(file_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Customer ID', 'Username', 'Error', 'Timestamp', 'Batch Info'])
                        for customer in failed_customers:
                            writer.writerow([
                                customer.get('customerId', 'Unknown'),
                                customer.get('username', 'Unknown'),
                                customer.get('error', 'Unknown error'),
                                customer.get('timestamp', 'Unknown'),
                                customer.get('batchInfo', 'Unknown')
                            ])
                else:
                    # Export as JSON
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(failed_customers, f, indent=2, ensure_ascii=False)

                messagebox.showinfo("Success", f"Failed customers exported to {file_path}")
                self.log_message(f"Exported {len(failed_customers)} failed customers to {file_path}")

        except Exception as e:
            self.log_message(f"Error exporting failed customers: {e}")
            messagebox.showerror("Error", f"Failed to export failed customers: {e}")

    def clear_failed_customers(self):
        """Clear failed customers data"""
        result = messagebox.askyesno(
            "Clear Failed Customers",
            "Are you sure you want to clear all failed customers data?\n\nThis will:\n- Clear the display\n- Clear data from current importer\n- NOT delete saved files"
        )

        if result:
            try:
                # Clear from current importer
                if self.current_importer:
                    with self.current_importer.failed_customers_lock:
                        self.current_importer.failed_customers.clear()

                # Clear the display
                for item in self.failed_customers_tree.get_children():
                    self.failed_customers_tree.delete(item)

                self.failed_customers_tree.insert("", tk.END, values=("No failed customers", "", "", "", ""))
                self.failed_count_label.config(text="Total: 0")

                self.log_message("Cleared failed customers data")
                messagebox.showinfo("Success", "Failed customers data cleared")

            except Exception as e:
                self.log_message(f"Error clearing failed customers: {e}")
                messagebox.showerror("Error", f"Failed to clear failed customers: {e}")

    def show_failed_customer_details(self, event):
        """Show detailed information about a failed customer"""
        selection = self.failed_customers_tree.selection()
        if not selection:
            return

        item = self.failed_customers_tree.item(selection[0])
        values = item['values']

        if len(values) < 5 or values[0] == "No failed customers":
            return

        customer_id = values[0]

        # Find the full customer data
        failed_customer = None
        if self.current_importer:
            try:
                with self.current_importer.failed_customers_lock:
                    for customer in self.current_importer.failed_customers:
                        if customer.get('customerId') == customer_id:
                            failed_customer = customer
                            break
            except Exception as e:
                self.log_message(f"Error getting customer details: {e}")

        if not failed_customer:
            messagebox.showinfo("No Details", f"No detailed information available for customer {customer_id}")
            return

        # Create details window
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Failed Customer Details - {customer_id}")
        details_window.geometry("600x500")
        details_window.transient(self.root)
        details_window.grab_set()

        # Create scrolled text widget for details
        details_text = scrolledtext.ScrolledText(details_window, wrap=tk.WORD, font=('Consolas', 10))
        details_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Format and display customer details
        details = f"FAILED CUSTOMER DETAILS\n"
        details += "=" * 50 + "\n\n"
        details += f"Customer ID: {failed_customer.get('customerId', 'Unknown')}\n"
        details += f"Username: {failed_customer.get('username', 'Unknown')}\n"
        details += f"Result: {failed_customer.get('result', 'Unknown')}\n"
        details += f"Error: {failed_customer.get('error', 'Unknown error')}\n"
        details += f"Timestamp: {failed_customer.get('timestamp', 'Unknown')}\n"
        details += f"Batch Info: {failed_customer.get('batchInfo', 'Unknown')}\n\n"

        if failed_customer.get('originalData'):
            details += "ORIGINAL CUSTOMER DATA:\n"
            details += "-" * 30 + "\n"
            details += json.dumps(failed_customer['originalData'], indent=2, ensure_ascii=False)

        details_text.insert(tk.END, details)
        details_text.config(state=tk.DISABLED)

        # Add close button
        ttk.Button(details_window, text="Close", command=details_window.destroy).pack(pady=10)

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