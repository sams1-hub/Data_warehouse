import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from queue import Queue

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automated_workflow import WorkflowGUI
from DAG import WorkflowRunner

class UnifiedWorkflowGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Unified Data Processing Workflow")
        self.root.geometry("1000x800")
        
        self.log_queue = Queue()
        self.setup_gui()
        
    def setup_gui(self):
        # Create main notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=5)
        
        # Create frames for different modes
        self.manual_frame = ttk.Frame(self.notebook)
        self.automated_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.manual_frame, text='Manual Workflow')
        self.notebook.add(self.automated_frame, text='Automated Workflow (DAG)')
        
        # Setup Manual Workflow Tab
        self.setup_manual_tab()
        
        # Setup Automated Workflow Tab
        self.setup_automated_tab()
        
        # Setup common controls
        self.setup_common_controls()
        
    def setup_manual_tab(self):
        # Create a container frame for the manual workflow
        manual_container = ttk.Frame(self.manual_frame)
        manual_container.pack(fill='both', expand=True)
    
        # File Selection Frame
        file_frame = ttk.LabelFrame(manual_container, text="File Selection")
        file_frame.pack(fill='x', padx=5, pady=5)
    
        # Input file selection
        ttk.Label(file_frame, text="Input File:").grid(row=0, column=0, padx=5, pady=5)
        self.input_path = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.input_path).grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        ttk.Button(file_frame, text="Browse", command=self.browse_input).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(file_frame, text="Download from Drive", command=self.open_drive_window).grid(row=0, column=3, padx=5, pady=5)
    
        # Output directory selection
        ttk.Label(file_frame, text="Output Directory:").grid(row=1, column=0, padx=5, pady=5)
        self.output_path = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.output_path).grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        ttk.Button(file_frame, text="Browse", command=self.browse_output).grid(row=1, column=2, padx=5, pady=5)
    
        # Workflow container
        workflow_container = ttk.Frame(manual_container)
        workflow_container.pack(fill='both', expand=True)
    
         # Initialize manual workflow GUI
        self.manual_workflow = WorkflowGUI(workflow_container)
        
    def setup_automated_tab(self):
        # Configuration Frame
        config_frame = ttk.LabelFrame(self.automated_frame, text="DAG Configuration")
        config_frame.pack(fill='x', padx=5, pady=5)
        
        # API Key selection
        ttk.Label(config_frame, text="API Key File:").grid(row=0, column=0, padx=5, pady=5)
        self.api_key_path = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.api_key_path).grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        ttk.Button(config_frame, text="Browse", command=self.browse_api_key).grid(row=0, column=2, padx=5, pady=5)
        
        # Database configuration
        ttk.Label(config_frame, text="Keyspace:").grid(row=1, column=0, padx=5, pady=5)
        self.keyspace = tk.StringVar(value="data_workflow")
        ttk.Entry(config_frame, textvariable=self.keyspace).grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        
        ttk.Label(config_frame, text="Table:").grid(row=2, column=0, padx=5, pady=5)
        self.table = tk.StringVar(value="processed_data")
        ttk.Entry(config_frame, textvariable=self.table).grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        
        # Cloud/Local selection
        self.use_cloud = tk.BooleanVar(value=False)
        ttk.Checkbutton(config_frame, text="Use Cloud Storage", variable=self.use_cloud).grid(row=3, column=0, columnspan=2, pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(self.automated_frame)
        button_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(button_frame, text="Start DAG Workflow", command=self.start_dag_workflow).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Stop DAG Workflow", command=self.stop_dag_workflow).pack(side='left', padx=5)
        
    def setup_common_controls(self):
        # Progress Frame
        progress_frame = ttk.LabelFrame(self.root, text="Progress")
        progress_frame.pack(fill='x', padx=10, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill='x', padx=5, pady=5)
        
        # Log Frame
        log_frame = ttk.LabelFrame(self.root, text="Logs")
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=10)
        self.log_text.pack(fill='both', expand=True)
        
    def browse_input(self):
        filename = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if filename:
            self.input_path.set(filename)
            self.log_message(f"Selected input file: {filename}")
            
    def browse_output(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_path.set(directory)
            self.log_message(f"Selected output directory: {directory}")
            
    def browse_api_key(self):
        filename = filedialog.askopenfilename(
            title="Select API Key File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.api_key_path.set(filename)
            self.log_message(f"Selected API key file: {filename}")
            
    def open_drive_window(self):
        drive_window = tk.Toplevel(self.root)
        drive_window.title("Google Drive Download")
        drive_window.geometry("600x400")
        
        # Create a new instance of WorkflowGUI for drive operations
        drive_gui = WorkflowGUI(drive_window)
        
    def start_dag_workflow(self):
        config = {
            'api_key_path': self.api_key_path.get(),
            'use_cloud': self.use_cloud.get(),
            'keyspace': self.keyspace.get(),
            'table': self.table.get()
        }
        
        runner = WorkflowRunner()
        try:
            runner.run_workflow(config)
            self.log_message("DAG workflow started successfully")
        except Exception as e:
            self.log_message(f"Error starting DAG workflow: {str(e)}")
            messagebox.showerror("Error", str(e))
            
    def stop_dag_workflow(self):
        try:
            # Add DAG stopping logic here
            self.log_message("DAG workflow stopped")
        except Exception as e:
            self.log_message(f"Error stopping DAG workflow: {str(e)}")
            messagebox.showerror("Error", str(e))
            
    def log_message(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

def main():
    root = tk.Tk()
    app = UnifiedWorkflowGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()