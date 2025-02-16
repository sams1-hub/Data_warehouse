import os
import sys
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from queue import Queue, Empty  # Import Empty exception directly


# parent directory to Python path to enable imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import components from your existing modules
from Data_preprocess.src.data_simple_preprocess import DataPreprocessor
from Extract_drive.src.drive_connection import (
    load_api_key,
    setup_drive_service,
    create_directories,
    download_file,
    list_files_in_folder
)

from ETL_process.etl import run_etl
from Cloud_push.cloud_push import (
    connect_to_cassandra_cloud,
    create_keyspace as create_cloud_keyspace,
    create_table_for_csv as create_cloud_table,
    insert_data_to_table as insert_cloud_data
)
from Cloud_push.local_push import (
    connect_to_cassandra_local,
    create_keyspace as create_local_keyspace,
    create_table_for_csv as create_local_table,
    insert_data_to_table as insert_local_data
)

class WorkflowGUI:
    def __init__(self, parent):
        self.parent = parent
        # Get the root window
        self.root = self.get_root(parent)
        
        # Check if parent is root window or frame
        if isinstance(parent, tk.Tk):
            self.parent.title("Data Processing Workflow")
            self.parent.geometry("900x700")
        
        self.log_queue = Queue()
        self.setup_gui()
        self.start_log_monitor()
        
        # Initialize workflow components
        self.data_preprocessor = None
        self.drive_service = None
    
    def get_root(self, widget):
        """Get the root window from any widget"""
        root = widget
        while not isinstance(root, tk.Tk):
            root = root.master
        return root
        
    def setup_gui(self):
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=5)
        
        # Create tabs
        self.extract_frame = ttk.Frame(self.notebook)
        self.preprocess_frame = ttk.Frame(self.notebook)
        self.etl_frame = ttk.Frame(self.notebook)
        self.push_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.extract_frame, text='Extract Data')
        self.notebook.add(self.preprocess_frame, text='Preprocess')
        self.notebook.add(self.etl_frame, text='ETL Process')
        self.notebook.add(self.push_frame, text='Push Data')
        
        self.setup_extract_tab()
        self.setup_preprocess_tab()
        self.setup_etl_tab()
        self.setup_push_tab()
        
        # Setup logging area
        self.log_frame = ttk.LabelFrame(self.parent, text="Logs")
        self.log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(self.log_frame, height=10)
        self.log_text.pack(fill='both', expand=True)
    
    def update_log_display(self):
        while True:
            try:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')}: {message}\n")
                self.log_text.see(tk.END)
                self.log_queue.task_done()
            except Queue.Empty:
                break
            # Schedule the next update
        self.root.after(100, self.update_log_display)
    
    def start_log_monitor(self):
        self.root.after(100, self.update_log_display)
        
    def setup_extract_tab(self):
        # Google Drive credentials frame
        cred_frame = ttk.LabelFrame(self.extract_frame, text="Google Drive Configuration")
        cred_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(cred_frame, text="API Key File:").grid(row=0, column=0, padx=5, pady=5)
        self.api_key_path = tk.StringVar()
        ttk.Entry(cred_frame, textvariable=self.api_key_path).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(cred_frame, text="Browse", command=self.browse_api_key).grid(row=0, column=2, padx=5, pady=5)
        
        # Folder selection frame
        folder_frame = ttk.LabelFrame(self.extract_frame, text="Folder Selection")
        folder_frame.pack(fill='x', padx=5, pady=5)
        
        self.folder_id = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.folder_id).pack(fill='x', padx=5, pady=5)
        ttk.Button(folder_frame, text="List Files", command=self.list_drive_files).pack(pady=5)
        
        # Files listbox
        self.files_listbox = tk.Listbox(self.extract_frame, height=10)
        self.files_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        
    def setup_preprocess_tab(self):
        config_frame = ttk.LabelFrame(self.preprocess_frame, text="Preprocessing Configuration")
        config_frame.pack(fill='x', padx=5, pady=5)
        
        self.preprocess_type = tk.StringVar(value="simple")
        ttk.Radiobutton(config_frame, text="Simple", variable=self.preprocess_type, 
                       value="simple").grid(row=0, column=0, padx=5, pady=5)
        ttk.Radiobutton(config_frame, text="Advanced", variable=self.preprocess_type,
                       value="advanced").grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(self.preprocess_frame, text="Start Preprocessing",
                  command=self.start_preprocessing).pack(pady=10)
        
    def setup_etl_tab(self):
        config_frame = ttk.LabelFrame(self.etl_frame, text="ETL Configuration")
        config_frame.pack(fill='x', padx=5, pady=5)
        
        self.batch_size = tk.StringVar(value="1000")
        ttk.Label(config_frame, text="Batch Size:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(config_frame, textvariable=self.batch_size).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(self.etl_frame, text="Start ETL Process",
                  command=self.start_etl).pack(pady=10)
        
    def setup_push_tab(self):
        config_frame = ttk.LabelFrame(self.push_frame, text="Push Configuration")
        config_frame.pack(fill='x', padx=5, pady=5)
        
        self.push_type = tk.StringVar(value="local")
        ttk.Radiobutton(config_frame, text="Local", variable=self.push_type,
                       value="local").grid(row=0, column=0, padx=5, pady=5)
        ttk.Radiobutton(config_frame, text="Cloud", variable=self.push_type,
                       value="cloud").grid(row=0, column=1, padx=5, pady=5)
        
        # Database configuration
        db_frame = ttk.LabelFrame(self.push_frame, text="Database Configuration")
        db_frame.pack(fill='x', padx=5, pady=5)
        
        self.keyspace_name = tk.StringVar(value="data_workflow")
        self.table_name = tk.StringVar(value="processed_data")
        
        ttk.Label(db_frame, text="Keyspace:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(db_frame, textvariable=self.keyspace_name).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(db_frame, text="Table:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(db_frame, textvariable=self.table_name).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Button(self.push_frame, text="Start Data Push",
                  command=self.start_push).pack(pady=10)
    
    def log_message(self, message):
        self.log_queue.put(message)
    
    def update_log_display(self):
        while True:
            try:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')}: {message}\n")
                self.log_text.see(tk.END)
                self.log_queue.task_done()
            except Queue.Empty:
                break
        self.root.after(100, self.update_log_display)
    
    def start_log_monitor(self):
        self.root.after(100, self.update_log_display)
    
    def browse_api_key(self):
        filename = filedialog.askopenfilename(
            title="Select API Key File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.api_key_path.set(filename)
            self.log_message(f"Selected API key file: {filename}")
    
    def list_drive_files(self):
        try:
            api_key = load_api_key(self.api_key_path.get())
            self.drive_service = setup_drive_service(api_key)
            files = list_files_in_folder(self.drive_service, self.folder_id.get())
            
            self.files_listbox.delete(0, tk.END)
            for file in files:
                self.files_listbox.insert(tk.END, f"{file['name']} ({file['id']})")
            
            self.log_message(f"Found {len(files)} files in folder")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.log_message(f"Error listing files: {str(e)}")
    
    def start_preprocessing(self):
        try:
            config = {
                "input_dir": "data/raw",
                "output_dir": "data/preprocessed",
                "file_patterns": ["*.csv", "*.xlsx"]
            }
            
            self.data_preprocessor = DataPreprocessor(config)
            selected_indices = self.files_listbox.curselection()
            if not selected_indices:
                messagebox.showwarning("Warning", "Please select files to process")
                return
            
            files = [self.files_listbox.get(idx) for idx in selected_indices]
            self.data_preprocessor.start_processing(files)
            self.log_message("Preprocessing started")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.log_message(f"Preprocessing error: {str(e)}")
    
    def start_etl(self):
        try:
            batch_size = int(self.batch_size.get())
            run_etl("data/preprocessed/processed_data.csv", "data/transformed")
            self.log_message("ETL process completed")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.log_message(f"ETL error: {str(e)}")
    
    def start_push(self):
        try:
            if self.push_type.get() == "cloud":
                session = connect_to_cassandra_cloud()
                create_keyspace = create_cloud_keyspace
                create_table = create_cloud_table
                insert_data = insert_cloud_data
            else:
                session = connect_to_cassandra_local()
                create_keyspace = create_local_keyspace
                create_table = create_local_table
                insert_data = insert_local_data
            
            if session:
                create_keyspace(session, self.keyspace_name.get())
                df = create_table(session, "data/transformed/final_data.csv",
                                self.table_name.get())
                if df is not None:
                    insert_data(session, df, self.table_name.get())
                    self.log_message("Data push completed successfully")
                    
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.log_message(f"Data push error: {str(e)}")

