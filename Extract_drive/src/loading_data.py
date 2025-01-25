from drive_connection import *
import pandas as pd

def clean_csv_data(input_path, output_path):
    """Clean and process CSV data"""
    try:
        df = pd.read_csv(input_path)
        # Example Cleaning Steps
        df.dropna(how='all', inplace=True)  # Drop completely empty rows
        df.columns = df.columns.str.strip()  # Clean column names
        
        df.to_csv(output_path, index=False)
        print(f"Cleaned data saved to {output_path}")
        return True
    except Exception as e:
        print(f"An error occurred during cleaning: {e}")
        raise

def log_action(action, status, details=""):
    """Log actions to file"""
    try:
        log_file = "data_pipeline.log"
        with open(log_file, "a") as log:
            log.write(f"{action} | {status} | {details}\n")
        print(f"Logged action: {action}")
    except Exception as e:
        print(f"Logging error: {e}")