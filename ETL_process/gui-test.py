import tkinter as tk
from tkinter import filedialog, messagebox
import os
from etl import run_etl

class ETLApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ETL Process")
        
        # Configure grid weights
        self.root.grid_columnconfigure(1, weight=1)
        
        self.input_label = tk.Label(root, text="Input File:")
        self.input_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")
        
        self.input_entry = tk.Entry(root, width=50)
        self.input_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        self.browse_button = tk.Button(root, text="Browse", command=self.browse_file)
        self.browse_button.grid(row=0, column=2, padx=10, pady=10)
        
        self.output_label = tk.Label(root, text="Output Folder:")
        self.output_label.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        
        self.output_entry = tk.Entry(root, width=50)
        self.output_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        self.browse_output_button = tk.Button(root, text="Browse", command=self.browse_output_folder)
        self.browse_output_button.grid(row=1, column=2, padx=10, pady=10)
        
        self.run_button = tk.Button(root, text="Run ETL", command=self.run_etl)
        self.run_button.grid(row=2, column=1, padx=10, pady=10)
        
        # Add status label
        self.status_label = tk.Label(root, text="", wraplength=400)
        self.status_label.grid(row=3, column=0, columnspan=3, padx=10, pady=10)
    
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=[
                ("All Supported Files", "*.csv;*.xlsx;*.xls;*.json;*.parquet;*.feather;*.pkl;*.hdf;*.txt;*.dat"),
                ("CSV Files", "*.csv"),
                ("Excel Files", "*.xlsx;*.xls"),
                ("JSON Files", "*.json"),
                ("Parquet Files", "*.parquet"),
                ("Feather Files", "*.feather"),
                ("Pickle Files", "*.pkl"),
                ("HDF Files", "*.hdf"),
                ("Text Files", "*.txt;*.dat"),
                ("All Files", "*.*")
            ]
        )
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, file_path)
    
    def browse_output_folder(self):
        folder_path = filedialog.askdirectory(title="Select Output Folder")
        self.output_entry.delete(0, tk.END)
        self.output_entry.insert(0, folder_path)
    
    def update_status(self, message, is_error=False):
        self.status_label.config(text=message, fg="red" if is_error else "black")
        self.root.update()
    
    def run_etl(self):
        input_file = self.input_entry.get()
        output_folder = self.output_entry.get()
        
        if not input_file or not output_folder:
            self.update_status("Please specify input file and output folder.", is_error=True)
            return
        
        try:
            self.update_status("Processing...")
            self.run_button.config(state=tk.DISABLED)
            
            run_etl(input_file, output_folder)
            
            self.update_status("ETL process completed successfully.")
            messagebox.showinfo("Success", "ETL process completed successfully.")
            
        except Exception as e:
            error_message = str(e)
            self.update_status(f"Error: {error_message}", is_error=True)
            messagebox.showerror("Error", error_message)
            
        finally:
            self.run_button.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = ETLApp(root)
    root.mainloop()