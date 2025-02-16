import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime
import queue
import warnings
import threading
from concurrent.futures import ThreadPoolExecutor

# Suppress warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all required components
from automated_workflow import WorkflowGUI
from DAG import WorkflowRunner
from workflow_manager import *
# Import all required components

from automated_workflow import WorkflowGUI
from DAG import WorkflowRunner
from ETL_process.etl import run_etl
from Extract_drive.src.drive_connection import (
    load_api_key,
    setup_drive_service,
    download_file,
    list_files_in_folder,
)
from Cloud_push.cloud_push import (
    connect_to_cassandra_cloud,
    create_keyspace as create_cloud_keyspace,
)
from Cloud_push.local_push import (
    connect_to_cassandra_local,
    create_keyspace as create_local_keyspace,
)
from Data_preprocess.src.data_simple_preprocess import DataPreprocessor

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


class UnifiedWorkflowGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Unified Data Processing Workflow")
        self.root.geometry("1200x800")
        
        # Initialize variables
        self.init_variables()
        
        # Initialize queues and threading components
        self.log_queue = queue.Queue()
        self.task_queue = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Create and initialize GUI components
        self.setup_gui()
        self.start_log_monitor()

    def init_variables(self):
        """Initialize all tkinter variables"""
        # File paths
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.api_key_path = tk.StringVar()
        self.folder_id = tk.StringVar()
        
        # Process configuration
        self.batch_size = tk.StringVar(value="1000")
        self.preprocess_type = tk.StringVar(value="simple")
        self.push_type = tk.StringVar(value="local")
        
        # Database settings
        self.keyspace = tk.StringVar(value="data_workflow")
        self.table = tk.StringVar(value="processed_data")
        
        # Progress tracking
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Ready")

    def setup_gui(self):
        """Create the main GUI structure"""
        # Create main container
        main_container = ttk.Frame(self.root)
        main_container.pack(expand=True, fill='both', padx=10, pady=5)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(expand=True, fill='both')
        
        # Create main frames
        self.extract_frame = ttk.Frame(self.notebook)
        self.preprocess_frame = ttk.Frame(self.notebook)
        self.etl_frame = ttk.Frame(self.notebook)
        self.push_frame = ttk.Frame(self.notebook)
        self.vis_frame = ttk.Frame(self.notebook)
        self.dag_frame = ttk.Frame(self.notebook)
        
        # Add frames to notebook
        self.notebook.add(self.extract_frame, text='Extract Data')
        self.notebook.add(self.preprocess_frame, text='Preprocess')
        self.notebook.add(self.etl_frame, text='ETL Process')
        self.notebook.add(self.push_frame, text='Push Data')
        self.notebook.add(self.vis_frame, text='Visualize')
        self.notebook.add(self.dag_frame, text='DAG Workflow')
        
        # Setup individual tabs
        self.setup_extract_tab()
        self.setup_preprocess_tab()
        self.setup_etl_tab()
        self.setup_push_tab()
        self.setup_visualization_tab()
        self.setup_dag_tab()
        
        # Setup common controls
        self.setup_common_controls(main_container)

    def setup_extract_tab(self):
        """Setup the data extraction tab"""
        # Google Drive credentials frame
        cred_frame = ttk.LabelFrame(self.extract_frame, text="Google Drive Configuration")
        cred_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(cred_frame, text="API Key File:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(cred_frame, textvariable=self.api_key_path).grid(row=0, column=1, sticky='ew')
        ttk.Button(cred_frame, text="Browse", command=self.browse_api_key).grid(row=0, column=2)
        
        # Folder selection
        folder_frame = ttk.LabelFrame(self.extract_frame, text="Folder Selection")
        folder_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(folder_frame, text="Folder ID:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(folder_frame, textvariable=self.folder_id).grid(row=0, column=1, sticky='ew')
        ttk.Button(folder_frame, text="List Files", command=self.list_drive_files).grid(row=0, column=2)
        
        # Files listbox
        self.files_listbox = tk.Listbox(self.extract_frame, selectmode='extended', height=10)
        self.files_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Action buttons
        button_frame = ttk.Frame(self.extract_frame)
        button_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(button_frame, text="Download Selected", command=self.download_selected_files).pack(side='left', padx=5)

    def setup_preprocess_tab(self):
        """Setup the preprocessing tab"""
        # Configuration frame
        config_frame = ttk.LabelFrame(self.preprocess_frame, text="Preprocessing Configuration")
        config_frame.pack(fill='x', padx=5, pady=5)
        
        # Preprocessing type selection
        ttk.Label(config_frame, text="Preprocessing Type:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Radiobutton(config_frame, text="Simple", variable=self.preprocess_type, 
                       value="simple").grid(row=0, column=1)
        ttk.Radiobutton(config_frame, text="Advanced", variable=self.preprocess_type,
                       value="advanced").grid(row=0, column=2)
        
        # File selection
        file_frame = ttk.LabelFrame(self.preprocess_frame, text="File Selection")
        file_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(file_frame, text="Input File:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(file_frame, textvariable=self.input_path).grid(row=0, column=1, sticky='ew')
        ttk.Button(file_frame, text="Browse", command=self.browse_input).grid(row=0, column=2)
        
        # Action buttons
        ttk.Button(self.preprocess_frame, text="Start Preprocessing",
                  command=self.start_preprocessing).pack(pady=10)

    def setup_etl_tab(self):
        """Setup the ETL tab"""
        # Configuration frame
        config_frame = ttk.LabelFrame(self.etl_frame, text="ETL Configuration")
        config_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(config_frame, text="Batch Size:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(config_frame, textvariable=self.batch_size).grid(row=0, column=1, sticky='ew')
        
        # File selection
        file_frame = ttk.LabelFrame(self.etl_frame, text="File Selection")
        file_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(file_frame, text="Input File:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(file_frame, textvariable=self.input_path).grid(row=0, column=1, sticky='ew')
        ttk.Button(file_frame, text="Browse", command=self.browse_input).grid(row=0, column=2)
        
        # Action buttons
        ttk.Button(self.etl_frame, text="Start ETL Process",
                  command=self.start_etl).pack(pady=10)

    def setup_push_tab(self):
        """Setup the data push tab"""
        # Push configuration
        config_frame = ttk.LabelFrame(self.push_frame, text="Push Configuration")
        config_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Radiobutton(config_frame, text="Local", variable=self.push_type,
                       value="local", command=self.update_push_params).grid(row=0, column=0)
        ttk.Radiobutton(config_frame, text="Cloud", variable=self.push_type,
                       value="cloud", command=self.update_push_params).grid(row=0, column=1)
        
        # Database parameters
        self.db_frame = ttk.LabelFrame(self.push_frame, text="Database Parameters")
        self.db_frame.pack(fill='x', padx=5, pady=5)
        
        # Initial setup of database parameters
        self.update_push_params()
        
        # Action buttons
        ttk.Button(self.push_frame, text="Start Data Push",
                  command=self.start_push).pack(pady=10)

    def setup_visualization_tab(self):
        """Setup the visualization tab"""
        # File selection
        file_frame = ttk.LabelFrame(self.vis_frame, text="Data Selection")
        file_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(file_frame, text="Data File:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(file_frame, textvariable=self.input_path).grid(row=0, column=1, sticky='ew')
        ttk.Button(file_frame, text="Browse", command=self.browse_input).grid(row=0, column=2)
        
        # Visualization options
        vis_frame = ttk.LabelFrame(self.vis_frame, text="Visualization Options")
        vis_frame.pack(fill='x', padx=5, pady=5)
        
        self.plot_type = tk.StringVar(value='histogram')
        ttk.Label(vis_frame, text="Plot Type:").grid(row=0, column=0, padx=5, pady=5)
        plot_types = ['histogram', 'bar', 'line', 'scatter', 'boxplot']
        ttk.OptionMenu(vis_frame, self.plot_type, *plot_types).grid(row=0, column=1)
        
        # Action buttons
        ttk.Button(self.vis_frame, text="Generate Visualization",
                  command=self.generate_visualization).pack(pady=10)

    def setup_dag_tab(self):
        """Setup the DAG workflow tab"""
        # Configuration frame
        config_frame = ttk.LabelFrame(self.dag_frame, text="DAG Configuration")
        config_frame.pack(fill='x', padx=5, pady=5)
        
        # Schedule settings
        schedule_frame = ttk.Frame(config_frame)
        schedule_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(schedule_frame, text="Schedule:").grid(row=0, column=0, padx=5, pady=5)
        self.schedule_type = tk.StringVar(value='daily')
        schedule_types = ['daily', 'weekly', 'monthly']
        ttk.OptionMenu(schedule_frame, self.schedule_type, *schedule_types).grid(row=0, column=1)
        
        # Time selection
        time_frame = ttk.Frame(config_frame)
        time_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(time_frame, text="Time:").grid(row=0, column=0, padx=5, pady=5)
        self.hour_var = tk.StringVar(value="00")
        self.minute_var = tk.StringVar(value="00")
        ttk.Spinbox(time_frame, from_=0, to=23, width=3, textvariable=self.hour_var).grid(row=0, column=1)
        ttk.Label(time_frame, text=":").grid(row=0, column=2)
        ttk.Spinbox(time_frame, from_=0, to=59, width=3, textvariable=self.minute_var).grid(row=0, column=3)
        
        # Action buttons
        button_frame = ttk.Frame(self.dag_frame)
        button_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(button_frame, text="Start DAG", command=self.start_dag).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Stop DAG", command=self.stop_dag).pack(side='left', padx=5)

    def setup_common_controls(self, container):
        """Create common control elements"""
        # Progress frame
        progress_frame = ttk.LabelFrame(container, text="Progress")
        progress_frame.pack(fill='x', pady=5)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(progress_frame, textvariable=self.status_var).pack(pady=2)
        
        # Log frame
        log_frame = ttk.LabelFrame(container, text="Logs")
        log_frame.pack(fill='both', expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5) 


    def browse_file(self, title, filetypes):
        """Generic file browser"""
        filename = filedialog.askopenfilename(
            title=title,
            filetypes=filetypes
        )
        if filename:
            self.bundle_entry.delete(0, tk.END)
            self.bundle_entry.insert(0, filename)
            self.log_message(f"Selected file: {filename}")

    def test_connection(self):
        """Test database connection"""
        try:
            if self.push_type.get() == "local":
                # Test local connection
                host = self.host_entry.get()
                port = self.port_entry.get()
                
                try:
                    session = connect_to_cassandra_local(
                        host=host,
                        port=int(port)
                    )
                    self.log_message(f"Attempting connection to local Cassandra at {host}:{port}")
                except Exception as e:
                    self.log_message(f"Local connection error: {str(e)}")
                    raise
            else:
                # Test cloud connection
                api_key = self.cloud_api_entry.get()
                bundle_path = self.bundle_entry.get()
                
                if not api_key or not bundle_path:
                    messagebox.showwarning("Warning", "Please provide API key and secure bundle")
                    return
                    
                try:
                    session = connect_to_cassandra_cloud(
                        api_key=api_key,
                        secure_bundle_path=bundle_path
                    )
                    self.log_message("Attempting connection to cloud Cassandra")
                except Exception as e:
                    self.log_message(f"Cloud connection error: {str(e)}")
                    raise
            
            if session:
                # Test keyspace creation
                keyspace = self.keyspace.get()
                try:
                    if self.push_type.get() == "local":
                        create_local_keyspace(session, keyspace)
                    else:
                        create_cloud_keyspace(session, keyspace)
                        
                    messagebox.showinfo("Success", "Connection test successful!")
                    self.log_message("Database connection test successful")
                except Exception as e:
                    self.log_message(f"Keyspace creation error: {str(e)}")
                    messagebox.showwarning("Warning", 
                        f"Connected to database but failed to create keyspace: {str(e)}")
            else:
                messagebox.showerror("Error", "Failed to establish connection")
                self.log_message("Failed to establish database connection")
                
        except Exception as e:
            error_msg = str(e)
            self.log_message(f"Connection test failed: {error_msg}")
            messagebox.showerror("Error", f"Connection test failed: {error_msg}")

    def update_push_params(self):
        """Update database parameters based on push type"""
        for widget in self.db_frame.winfo_children():
            widget.destroy()
            
        # Common parameters
        ttk.Label(self.db_frame, text="Keyspace:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(self.db_frame, textvariable=self.keyspace).grid(row=0, column=1, sticky='ew')
        
        ttk.Label(self.db_frame, text="Table:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(self.db_frame, textvariable=self.table).grid(row=1, column=1, sticky='ew')
        
        if self.push_type.get() == "local":
            # Local Cassandra parameters
            ttk.Label(self.db_frame, text="Host:").grid(row=2, column=0, padx=5, pady=5)
            self.host_entry = ttk.Entry(self.db_frame)
            self.host_entry.insert(0, "localhost")
            self.host_entry.grid(row=2, column=1, sticky='ew')
            
            ttk.Label(self.db_frame, text="Port:").grid(row=3, column=0, padx=5, pady=5)
            self.port_entry = ttk.Entry(self.db_frame)
            self.port_entry.insert(0, "9042")
            self.port_entry.grid(row=3, column=1, sticky='ew')
        else:
            # Cloud parameters
            ttk.Label(self.db_frame, text="API Key:").grid(row=2, column=0, padx=5, pady=5)
            self.cloud_api_entry = ttk.Entry(self.db_frame, show="*")  # Hide API key
            self.cloud_api_entry.grid(row=2, column=1, sticky='ew')
            
            ttk.Label(self.db_frame, text="Secure Bundle:").grid(row=3, column=0, padx=5, pady=5)
            self.bundle_entry = ttk.Entry(self.db_frame)
            self.bundle_entry.grid(row=3, column=1, sticky='ew')
            ttk.Button(self.db_frame, text="Browse", 
                      command=lambda: self.browse_file("Select Secure Connect Bundle",
                                                     [("ZIP files", "*.zip")])).grid(row=3, column=2)
        
        # Add test connection button
        ttk.Button(self.db_frame, text="Test Connection",
                  command=self.test_connection).grid(row=4, column=0, columnspan=2, pady=10)

    def start_log_monitor(self):
        """Start monitoring the log queue"""
        self.update_log_display()

    def update_log_display(self):
        """Update the log display from the queue"""
        while True:
            try:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
                self.log_text.see(tk.END)
                self.log_queue.task_done()
            except queue.Empty:
                break
        self.root.after(100, self.update_log_display)

    def log_message(self, message):
        """Add message to log queue"""
        self.log_queue.put(message)

    def update_progress(self, value, message=None):
        """Update progress bar and status message"""
        self.progress_var.set(value)
        if message:
            self.status_var.set(message)
        self.root.update_idletasks()

    # File Operations
    def browse_api_key(self):
        """Browse for API key file"""
        filename = filedialog.askopenfilename(
            title="Select API Key File",
            filetypes=[("Text files", "*.txt"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.api_key_path.set(filename)
            self.log_message(f"Selected API key file: {filename}")

    def browse_input(self):
        """Browse for input file"""
        filename = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx;*.xls"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.input_path.set(filename)
            self.log_message(f"Selected input file: {filename}")

    def browse_output(self):
        """Browse for output directory"""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_path.set(directory)
            self.log_message(f"Selected output directory: {directory}")

    # Google Drive Operations
    def list_drive_files(self):
        """List files from Google Drive folder"""
        try:
            if not self.api_key_path.get():
                messagebox.showwarning("Warning", "Please select API key file first")
                return
                
            if not self.folder_id.get():
                messagebox.showwarning("Warning", "Please enter folder ID")
                return
            
            self.update_progress(0, "Connecting to Google Drive...")
            
            api_key = load_api_key(self.api_key_path.get())
            drive_service = setup_drive_service(api_key)
            
            self.update_progress(30, "Listing files...")
            files = list_files_in_folder(drive_service, self.folder_id.get())
            
            self.files_listbox.delete(0, tk.END)
            for file in files:
                self.files_listbox.insert(tk.END, f"{file['name']} ({file['id']})")
            
            self.update_progress(100, "File listing complete")
            self.log_message(f"Found {len(files)} files in folder")
            
        except Exception as e:
            self.log_message(f"Error listing files: {str(e)}")
            messagebox.showerror("Error", str(e))
            self.update_progress(0, "Ready")

    def download_selected_files(self):
        """Download selected files from Google Drive"""
        selected_indices = self.files_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select files to download")
            return
        
        try:
            api_key = load_api_key(self.api_key_path.get())
            drive_service = setup_drive_service(api_key)
            
            total_files = len(selected_indices)
            for idx, index in enumerate(selected_indices):
                file_info = self.files_listbox.get(index)
                file_id = file_info.split('(')[-1].strip(')')
                file_name = file_info.split('(')[0].strip()
                
                progress = (idx / total_files) * 100
                self.update_progress(progress, f"Downloading {file_name}...")
                
                destination = os.path.join('data', 'raw', file_name)
                os.makedirs(os.path.dirname(destination), exist_ok=True)
                
                download_file(drive_service, file_id, destination)
                self.log_message(f"Downloaded: {destination}")
            
            self.update_progress(100, "Downloads complete")
            messagebox.showinfo("Success", "Files downloaded successfully")
            
        except Exception as e:
            self.log_message(f"Error downloading files: {str(e)}")
            messagebox.showerror("Error", str(e))
            self.update_progress(0, "Ready")

    # Data Processing Operations
    def start_preprocessing(self):
        """Start data preprocessing"""
        if not self.input_path.get():
            messagebox.showwarning("Warning", "Please select input file")
            return
            
        try:
            self.update_progress(0, "Initializing preprocessing...")
            
            config = {
                "input_dir": os.path.dirname(self.input_path.get()),
                "output_dir": os.path.join("data", "preprocessed"),
                "file_patterns": ["*.csv", "*.xlsx"],
                "type": self.preprocess_type.get()
            }
            
            preprocessor = DataPreprocessor(config)
            
            def process_callback(progress, message):
                self.update_progress(progress, message)
            
            # Start preprocessing in a separate thread
            self.executor.submit(self.run_preprocessing, preprocessor, [self.input_path.get()], process_callback)
            
        except Exception as e:
            self.log_message(f"Error in preprocessing: {str(e)}")
            messagebox.showerror("Error", str(e))
            self.update_progress(0, "Ready")

    def run_preprocessing(self, preprocessor, files, callback):
        """Run preprocessing in background"""
        try:
            preprocessor.start_processing(files)
            callback(100, "Preprocessing complete")
            self.log_message("Preprocessing completed successfully")
            messagebox.showinfo("Success", "Preprocessing completed successfully")
        except Exception as e:
            self.log_message(f"Preprocessing error: {str(e)}")
            messagebox.showerror("Error", str(e))
        finally:
            callback(0, "Ready")

    def start_etl(self):
        """Start ETL process"""
        if not self.input_path.get():
            messagebox.showwarning("Warning", "Please select input file")
            return
            
        try:
            self.update_progress(0, "Starting ETL process...")
            
            output_dir = os.path.join("data", "transformed")
            os.makedirs(output_dir, exist_ok=True)
            
            # Start ETL in a separate thread
            self.executor.submit(self.run_etl, self.input_path.get(), output_dir)
            
        except Exception as e:
            self.log_message(f"Error in ETL: {str(e)}")
            messagebox.showerror("Error", str(e))
            self.update_progress(0, "Ready")

    def run_etl(self, input_file, output_dir):
        """Run ETL in background"""
        try:
            self.update_progress(30, "Processing data...")
            run_etl(input_file, output_dir)
            
            self.update_progress(100, "ETL complete")
            self.log_message("ETL process completed successfully")
            messagebox.showinfo("Success", "ETL process completed successfully")
            
        except Exception as e:
            self.log_message(f"ETL error: {str(e)}")
            messagebox.showerror("Error", str(e))
        finally:
            self.update_progress(0, "Ready")

    # Database Operations
    def update_push_params(self):
        """Update database parameters based on push type"""
        for widget in self.db_frame.winfo_children():
            widget.destroy()
            
        # Common parameters
        ttk.Label(self.db_frame, text="Keyspace:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(self.db_frame, textvariable=self.keyspace).grid(row=0, column=1, sticky='ew')
        
        ttk.Label(self.db_frame, text="Table:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(self.db_frame, textvariable=self.table).grid(row=1, column=1, sticky='ew')
        
        if self.push_type.get() == "local":
            # Local Cassandra parameters
            ttk.Label(self.db_frame, text="Host:").grid(row=2, column=0, padx=5, pady=5)
            self.host_entry = ttk.Entry(self.db_frame)
            self.host_entry.insert(0, "localhost")
            self.host_entry.grid(row=2, column=1, sticky='ew')
            
            ttk.Label(self.db_frame, text="Port:").grid(row=3, column=0, padx=5, pady=5)
            self.port_entry = ttk.Entry(self.db_frame)
            self.port_entry.insert(0, "9042")
            self.port_entry.grid(row=3, column=1, sticky='ew')
        else:
            # Cloud parameters
            ttk.Label(self.db_frame, text="API Key:").grid(row=2, column=0, padx=5, pady=5)
            self.cloud_api_entry = ttk.Entry(self.db_frame)
            self.cloud_api_entry.grid(row=2, column=1, sticky='ew')
            
            ttk.Label(self.db_frame, text="Secure Bundle:").grid(row=3, column=0, padx=5, pady=5)
            self.bundle_entry = ttk.Entry(self.db_frame)
            self.bundle_entry.grid(row=3, column=1, sticky='ew')
            ttk.Button(self.db_frame, text="Browse", 
                      command=lambda: self.browse_file("Select Secure Connect Bundle",
                                                     [("ZIP files", "*.zip")])).grid(row=3, column=2)
        
        ttk.Button(self.db_frame, text="Test Connection",
                  command=self.test_connection).grid(row=4, column=0, columnspan=2, pady=10)

    def start_push(self):
        """Start data push to database"""
        if not self.input_path.get():
            messagebox.showwarning("Warning", "Please select input file")
            return
            
        try:
            self.update_progress(0, "Connecting to database...")
            
            # Start push in a separate thread
            self.executor.submit(self.run_push)
            
        except Exception as e:
            self.log_message(f"Error in data push: {str(e)}")
            messagebox.showerror("Error", str(e))
            self.update_progress(0, "Ready")

    def run_push(self):
        """Run database push in background"""
        try:
            if self.push_type.get() == "cloud":
                session = connect_to_cassandra_cloud()
                create_keyspace = create_cloud_keyspace
            else:
                session = connect_to_cassandra_local()
                create_keyspace = create_local_keyspace
            
            if session:
                self.update_progress(30, "Creating keyspace...")
                create_keyspace(session, self.keyspace.get())
                
                self.update_progress(60, "Pushing data...")
                # Add your data push logic here
                
                self.update_progress(100, "Data push complete")
                self.log_message("Data push completed successfully")
                messagebox.showinfo("Success", "Data push completed successfully")
            
        except Exception as e:
            self.log_message(f"Data push error: {str(e)}")
            messagebox.showerror("Error", str(e))
        finally:
            self.update_progress(0, "Ready")

    # DAG Operations
    def start_dag(self):
        """Start DAG workflow"""
        try:
            config = {
                'schedule_type': self.schedule_type.get(),
                'time': f"{self.hour_var.get()}:{self.minute_var.get()}"
            }
            
            runner = WorkflowRunner()
            self.executor.submit(self.run_dag, runner, config)
            
        except Exception as e:
            self.log_message(f"Error starting DAG: {str(e)}")
            messagebox.showerror("Error", str(e))


    def generate_visualization(self):
        """Generate visualization based on selected parameters"""
        if not self.input_path.get():
            messagebox.showwarning("Warning", "Please select a data file")
            return
            
        try:
            self.update_progress(0, "Loading data...")
            
            # Load data
            file_path = self.input_path.get()
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file format. Please provide a CSV or Excel file.")
            
            self.update_progress(30, "Analyzing data...")
            
            # Create figure window if it doesn't exist
            if not hasattr(self, 'fig_window'):
                self.fig_window = tk.Toplevel(self.root)
                self.fig_window.title("Data Visualization")
                self.fig_window.geometry("800x600")
                
                # Create frame for plot controls
                control_frame = ttk.Frame(self.fig_window)
                control_frame.pack(fill='x', padx=5, pady=5)
                
                # Column selection
                ttk.Label(control_frame, text="Select Column:").pack(side='left', padx=5)
                self.column_var = tk.StringVar()
                self.column_combo = ttk.Combobox(control_frame, textvariable=self.column_var)
                self.column_combo.pack(side='left', padx=5)
                
                # Update button
                ttk.Button(control_frame, text="Update Plot", 
                          command=lambda: self.update_plot(df)).pack(side='left', padx=5)
                
                # Create matplotlib figure and canvas
                self.fig = plt.figure(figsize=(8, 6))
                self.canvas = FigureCanvasTkAgg(self.fig, master=self.fig_window)
                self.canvas.get_tk_widget().pack(fill='both', expand=True)
                
                # Add navigation toolbar
                toolbar = NavigationToolbar2Tk(self.canvas, self.fig_window)
                toolbar.update()
                
            # Update column choices
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
            self.column_combo['values'] = list(numeric_cols)
            if len(numeric_cols) > 0:
                self.column_combo.set(numeric_cols[0])
            
            self.update_progress(60, "Generating plot...")
            
            # Generate initial plot
            self.update_plot(df)
            
            self.update_progress(100, "Visualization complete")
            
        except Exception as e:
            error_msg = str(e)
            self.log_message(f"Visualization error: {error_msg}")
            messagebox.showerror("Error", f"Failed to generate visualization: {error_msg}")
            self.update_progress(0, "Ready")

    def update_plot(self, df):
        """Update the plot with new settings"""
        try:
            # Clear previous plot
            self.fig.clear()
            
            # Get selected column and plot type
            column = self.column_var.get()
            plot_type = self.plot_type.get()
            
            # Create subplot
            ax = self.fig.add_subplot(111)
            
            # Generate plot based on type
            if plot_type == 'histogram':
                ax.hist(df[column].dropna(), bins=30, edgecolor='black')
                ax.set_title(f'Histogram of {column}')
                ax.set_xlabel(column)
                ax.set_ylabel('Frequency')
                
            elif plot_type == 'bar':
                value_counts = df[column].value_counts()
                ax.bar(range(len(value_counts)), value_counts.values)
                ax.set_xticks(range(len(value_counts)))
                ax.set_xticklabels(value_counts.index, rotation=45)
                ax.set_title(f'Bar Plot of {column}')
                ax.set_xlabel(column)
                ax.set_ylabel('Count')
                
            elif plot_type == 'boxplot':
                ax.boxplot(df[column].dropna())
                ax.set_title(f'Boxplot of {column}')
                ax.set_ylabel(column)
                
            elif plot_type == 'scatter':
                # For scatter plots, we need two columns
                numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
                if len(numeric_cols) >= 2:
                    x_col = numeric_cols[0]
                    y_col = numeric_cols[1]
                    ax.scatter(df[x_col], df[y_col])
                    ax.set_title(f'Scatter Plot: {x_col} vs {y_col}')
                    ax.set_xlabel(x_col)
                    ax.set_ylabel(y_col)
                else:
                    raise ValueError("Scatter plot requires at least two numeric columns")
                
            elif plot_type == 'line':
                if df[column].dtype.kind in 'biufc':  # Check if numeric
                    ax.plot(df.index, df[column])
                    ax.set_title(f'Line Plot of {column}')
                    ax.set_xlabel('Index')
                    ax.set_ylabel(column)
                else:
                    raise ValueError(f"Column {column} must be numeric for line plot")
            
            # Adjust layout and refresh canvas
            self.fig.tight_layout()
            self.canvas.draw()
            
            self.log_message(f"Updated {plot_type} plot for column: {column}")
            
        except Exception as e:
            error_msg = str(e)
            self.log_message(f"Plot update error: {error_msg}")
            messagebox.showerror("Error", f"Failed to update plot: {error_msg}")
            
    def setup_visualization_tab(self):
        """Setup the visualization tab"""
        # File selection
        file_frame = ttk.LabelFrame(self.vis_frame, text="Data Selection")
        file_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(file_frame, text="Data File:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(file_frame, textvariable=self.input_path).grid(row=0, column=1, sticky='ew')
        ttk.Button(file_frame, text="Browse", command=self.browse_input).grid(row=0, column=2)
        
        # Visualization options
        vis_frame = ttk.LabelFrame(self.vis_frame, text="Visualization Options")
        vis_frame.pack(fill='x', padx=5, pady=5)
        
        self.plot_type = tk.StringVar(value='histogram')
        ttk.Label(vis_frame, text="Plot Type:").grid(row=0, column=0, padx=5, pady=5)
        plot_types = ['histogram', 'bar', 'line', 'scatter', 'boxplot']
        ttk.OptionMenu(vis_frame, self.plot_type, *plot_types).grid(row=0, column=1)
        
        # Add additional options frame
        options_frame = ttk.LabelFrame(self.vis_frame, text="Additional Options")
        options_frame.pack(fill='x', padx=5, pady=5)
        
        # Statistics checkbox
        self.show_stats = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Show Statistics", 
                       variable=self.show_stats).pack(padx=5, pady=5)
        
        # Action buttons
        button_frame = ttk.Frame(self.vis_frame)
        button_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(button_frame, text="Generate Visualization",
                  command=self.generate_visualization).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Save Plot",
                  command=self.save_plot).pack(side='left', padx=5)
        
    def save_plot(self):
        """Save the current plot to a file"""
        if hasattr(self, 'fig'):
            try:
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".png",
                    filetypes=[("PNG files", "*.png"),
                              ("PDF files", "*.pdf"),
                              ("SVG files", "*.svg")]
                )
                if file_path:
                    self.fig.savefig(file_path, bbox_inches='tight', dpi=300)
                    self.log_message(f"Plot saved to: {file_path}")
                    messagebox.showinfo("Success", "Plot saved successfully!")
            except Exception as e:
                self.log_message(f"Error saving plot: {str(e)}")
                messagebox.showerror("Error", f"Failed to save plot: {str(e)}")
        else:
            messagebox.showwarning("Warning", "No plot to save. Generate a visualization first.")


            




    def run_dag(self, runner, config):
        """Run DAG workflow in background"""
        try:
            self.update_progress(0, "Starting DAG workflow...")
            runner.run_workflow(config)
            self.log_message("DAG workflow started successfully")
            self.update_progress(100, "DAG workflow running")
        except Exception as e:
            self.log_message(f"DAG error: {str(e)}")
            messagebox.showerror("Error", str(e))
            self.update_progress(0, "Ready")

    def stop_dag(self):
        """Stop DAG workflow"""
        try:
            # Add your DAG stopping logic here
            self.log_message("DAG workflow stopped")
            self.update_progress(0, "Ready")
        except Exception as e:
            self.log_message(f"Error stopping DAG: {str(e)}")
            messagebox.showerror("Error", str(e))

    def on_closing(self):
        """Handle application closing"""
        try:
            self.executor.shutdown(wait=False)
            self.root.destroy()
        except:
            pass

def main():
    root = tk.Tk()
    app = UnifiedWorkflowGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()