# workflow_manager.py
from automated_workflow import WorkflowGUI
from DAG import WorkflowRunner
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import queue
import warnings
import threading
#from concurrent.futures import ThreadPoolExecutor


# parent directory to Python path to enable imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Import components from your existing modules
from Data_preprocess.src.data_simple_preprocess import DataPreprocessor
from Extract_drive.src.drive_connection import (
    download_file,
)
from ETL_process.etl import run_etl
from Cloud_push.cloud_push import (
    connect_to_cassandra_cloud,
)
from Cloud_push.local_push import (
    connect_to_cassandra_local,
)

class UnifiedWorkflowManager:
    def __init__(self):
        self.manual_workflow = None
        self.automated_workflow = None
        self.logger = None
        
    def initialize_manual_workflow(self, parent):
        """Initialize manual workflow"""
        self.manual_workflow = WorkflowGUI(parent)
        return self.manual_workflow
        
    def initialize_automated_workflow(self):
        """Initialize automated workflow"""
        self.automated_workflow = WorkflowRunner()
        return self.automated_workflow
        
    def start_manual_process(self, process_type, **kwargs):
        """Start a manual process"""
        if self.manual_workflow:
            if process_type == 'extract':
                return self.manual_workflow.start_extraction(**kwargs)
            elif process_type == 'preprocess':
                return self.manual_workflow.start_preprocessing(**kwargs)
            elif process_type == 'etl':
                return self.manual_workflow.start_etl(**kwargs)
            elif process_type == 'push':
                return self.manual_workflow.start_push(**kwargs)
                
    def start_automated_workflow(self, config):
        """Start automated workflow"""
        if self.automated_workflow:
            return self.automated_workflow.run_workflow(config)
        
    def update_push_params(self):
        """Update database parameters based on push type"""
        # Clear existing parameters
        for widget in self.db_frame.winfo_children():
            widget.destroy()
            
        # Common parameters
        ttk.Label(self.db_frame, text="Keyspace:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(self.db_frame, textvariable=self.keyspace).grid(row=0, column=1, sticky='ew')
        
        ttk.Label(self.db_frame, text="Table:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(self.db_frame, textvariable=self.table).grid(row=1, column=1, sticky='ew')
        
        # Type-specific parameters
        if self.push_type.get() == "local":
            # Local Cassandra parameters
            ttk.Label(self.db_frame, text="Gossip:").grid(row=2, column=0, padx=5, pady=5)
            self.gossip_entry = ttk.Entry(self.db_frame)
            self.gossip_entry.grid(row=2, column=1, sticky='ew')
            
            ttk.Label(self.db_frame, text="Password:").grid(row=3, column=0, padx=5, pady=5)
            self.password_entry = ttk.Entry(self.db_frame, show="*")
            self.password_entry.grid(row=3, column=1, sticky='ew')
        else:
            # Cloud parameters
            ttk.Label(self.db_frame, text="API Key:").grid(row=2, column=0, padx=5, pady=5)
            self.cloud_api_entry = ttk.Entry(self.db_frame)
            self.cloud_api_entry.grid(row=2, column=1, sticky='ew')
            
            ttk.Label(self.db_frame, text="Token:").grid(row=3, column=0, padx=5, pady=5)
            self.token_entry = ttk.Entry(self.db_frame, show="*")
            self.token_entry.grid(row=3, column=1, sticky='ew')
        
        ttk.Button(self.db_frame, text="Test Connection",
                  command=self.test_connection).grid(row=4, column=0, columnspan=2, pady=10)

    def browse_api_key(self):
        """Browse for API key file"""
        filename = filedialog.askopenfilename(
            title="Select API Key File",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.api_key_path.set(filename)
            self.log_message(f"Selected API key file: {filename}")

    def test_connection(self):
        """Test database connection"""
        try:
            if self.push_type.get() == "local":
                # Test local connection
                session = connect_to_cassandra_local(
                    gossip=self.gossip_entry.get(),
                    password=self.password_entry.get()
                )
            else:
                # Test cloud connection
                session = connect_to_cassandra_cloud(
                    api_key=self.cloud_api_entry.get(),
                    token=self.token_entry.get()
                )
                
            if session:
                messagebox.showinfo("Success", "Connection test successful!")
                self.log_message("Database connection test successful")
            else:
                messagebox.showerror("Error", "Failed to establish connection")
                
        except Exception as e:
            messagebox.showerror("Error", f"Connection test failed: {str(e)}")
            self.log_message(f"Database connection test failed: {str(e)}")

    def start_extraction(self):
        """Start data extraction process"""
        selected_indices = self.files_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select files to extract")
            return
            
        try:
            self.progress_var.set(0)
            total_files = len(selected_indices)
            
            for idx, index in enumerate(selected_indices):
                file_info = self.files_listbox.get(index)
                file_id = file_info.split('(')[-1].strip(')')
                
                # Create output directory
                output_dir = os.path.join('data', 'raw')
                os.makedirs(output_dir, exist_ok=True)
                
                # Download file
                destination = os.path.join(output_dir, file_info.split('(')[0].strip())
                download_file(self.drive_service, file_id, destination)
                
                # Update progress
                progress = ((idx + 1) / total_files) * 100
                self.progress_var.set(progress)
                self.log_message(f"Extracted: {destination}")
                
            messagebox.showinfo("Success", "Extraction completed successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Extraction failed: {str(e)}")
            self.log_message(f"Extraction error: {str(e)}")
        finally:
            self.progress_var.set(0)

    def start_preprocessing(self):
        """Start preprocessing operation"""
        try:
            selected_indices = self.preprocess_files.curselection()
            if not selected_indices:
                messagebox.showwarning("Warning", "Please select files to preprocess")
                return
                
            # Create output directory with date
            output_dir = os.path.join('data', 'preprocessed', 
                                    datetime.now().strftime('%Y%m%d'))
            os.makedirs(output_dir, exist_ok=True)
            
            config = {
                "input_dir": os.path.dirname(self.preprocess_files.get(selected_indices[0])),
                "output_dir": output_dir,
                "file_patterns": ["*.csv", "*.xlsx"],
                "type": self.preprocess_type.get()
            }
            
            preprocessor = DataPreprocessor(config)
            files = [self.preprocess_files.get(idx) for idx in selected_indices]
            
            # Start preprocessing in a separate thread
            self.start_process_thread(preprocessor.start_processing, files)
            
        except Exception as e:
            messagebox.showerror("Error", f"Preprocessing failed: {str(e)}")
            self.log_message(f"Preprocessing error: {str(e)}")

    def start_process_thread(self, process_func, *args):
        """Start a process in a separate thread"""
        def run_process():
            try:
                process_func(*args)
                self.root.after(0, self.on_process_complete)
            except Exception as e:
                self.root.after(0, self.on_process_error, str(e))
                
        thread = threading.Thread(target=run_process)
        thread.daemon = True
        thread.start()

    def on_process_complete(self):
        """Handle process completion"""
        self.progress_var.set(100)
        messagebox.showinfo("Success", "Process completed successfully!")
        self.log_message("Process completed successfully")

    def on_process_error(self, error_message):
        """Handle process error"""
        messagebox.showerror("Error", f"Process failed: {error_message}")
        self.log_message(f"Process error: {error_message}")
        self.progress_var.set(0)