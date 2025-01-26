import pandas as pd
import numpy as np
import os
import logging
from tkinter import Tk, filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from typing import List, Dict

# Define base directories
BASE_DIR = "../../data/"
pre_process_dir = os.path.join(BASE_DIR, "pre_process")

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataPreprocessor:
    def __init__(self, config: Dict):
        self.config = config
        self._validate_config()
        self.executor = None
        self.futures = []
        self.running = False

    def _validate_config(self):
        """Validate configuration parameters"""
        required_keys = ['input_dir', 'output_dir', 'file_patterns']
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required config key: {key}")

    def start_processing(self, files: List[str]):
        """Initialize and start thread pool"""
        self.running = True
        self.executor = ThreadPoolExecutor(max_workers=min(os.cpu_count() or 1, 4))
        self.futures = [self.executor.submit(self._process_single_file, f) for f in files]

    def stop_processing(self):
        """Gracefully shutdown processing"""
        if self.executor:
            self.running = False
            for future in self.futures:
                if not future.done():
                    future.cancel()
            self.executor.shutdown(wait=False)
            logger.info("Processing threads terminated")

    def _process_single_file(self, file_path: str) -> bool:
        """Process a single file efficiently"""
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
                df = self._clean_data(df, file_path)
                self._save_data(df, file_path)
                return True
            elif file_path.endswith(('.xls', '.xlsx')):
                with pd.ExcelFile(file_path) as excel:
                    for sheet_name in excel.sheet_names:
                        df = pd.read_excel(excel, sheet_name=sheet_name)
                        df = self._clean_data(df, file_path, sheet_name)
                        self._save_data(df, file_path, sheet_name)
                return True
            else:
                raise ValueError(f"Unsupported file format: {file_path}")
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return False

    def _clean_data(self, df: pd.DataFrame, file_path: str, sheet_name: str = None) -> pd.DataFrame:
        """Efficient data cleaning operations"""
        logger.info(f"Processing file: {file_path} (Sheet: {sheet_name})")

        # Standardize column names
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        logger.info(f"Standardized column names: {df.columns.tolist()}")

        # Convert to optimal dtypes
        df = df.convert_dtypes()
        logger.info(f"Converted data types:\n{df.dtypes}")

        # Handle date_of_birth conversion
        if 'date_of_birth' in df.columns:
            df['date_of_birth'] = pd.to_datetime(df['date_of_birth'], errors='coerce')
            logger.info("Converted 'date_of_birth' to datetime")

        # Handle missing values and invalid entries
        df = self._handle_missing_values(df, file_path, sheet_name)

        # Remove duplicates
        initial_rows = len(df)
        df = df.drop_duplicates(ignore_index=True)
        logger.info(f"Removed {initial_rows - len(df)} duplicate rows")

        # Clean string columns
        str_cols = df.select_dtypes(include='string').columns
        for col in str_cols:
            df[col] = df[col].str.strip().str.normalize('NFKC')
        logger.info(f"Cleaned string columns: {str_cols.tolist()}")

        return df

    def _handle_missing_values(self, df: pd.DataFrame, file_path: str, sheet_name: str = None) -> pd.DataFrame:
        """Smart missing value handling with zero value checks"""
        logger.info(f"Handling missing/zero values for: {file_path} (Sheet: {sheet_name})")

        # Replace zero values in class column
        if 'class' in df.columns:
            df['class'] = df['class'].replace({0: 'NULL', '0': 'NULL'})
            logger.info("Replaced 0/'0' values in 'class' with NULL")

        # Handle invalid/zero dates
        date_cols = df.select_dtypes(include=['datetime', 'datetime64']).columns
        for col in date_cols:
            invalid_dates = (df[col] == pd.Timestamp(0)) | df[col].isna()
            df.loc[invalid_dates, col] = pd.NaT
            logger.info(f"Replaced invalid dates in '{col}' with NULL")

        # Log missing values after zero replacement
        missing_values = df.isnull().sum()
        logger.info(f"Missing values after zero replacement:\n{missing_values}")

        # Fill numeric columns with median
        num_cols = df.select_dtypes(include=np.number).columns
        for col in num_cols:
            if df[col].isnull().any():
                median = df[col].median()
                df[col] = df[col].fillna(median)
                logger.info(f"Filled numeric '{col}' with median: {median}")

        # Fill categorical columns with mode
        cat_cols = df.select_dtypes(include='category').columns
        for col in cat_cols:
            if df[col].isnull().any():
                mode = df[col].mode()[0]
                df[col] = df[col].fillna(mode)
                logger.info(f"Filled categorical '{col}' with mode: {mode}")

        # Fill remaining columns with NULL
        other_cols = set(df.columns) - set(num_cols) - set(cat_cols)
        for col in other_cols:
            if df[col].isnull().any():
                df[col] = df[col].fillna('NULL')
                logger.info(f"Filled '{col}' with NULL")

        return df

    def _save_data(self, df: pd.DataFrame, original_path: str, sheet_name: str = None):
        """Save processed data with NULL replacements"""
        # Ensure output directory exists
        os.makedirs(self.config['output_dir'], exist_ok=True)

        # Generate filename
        filename = os.path.basename(original_path)
        if sheet_name:
            output_path = os.path.join(self.config['output_dir'], f"cleaned_{filename}_{sheet_name}.csv")
        else:
            output_path = os.path.join(self.config['output_dir'], f"cleaned_{filename}")

        # Convert NaT to NULL before saving
        df = df.replace({pd.NaT: 'NULL'})
        df.to_csv(output_path, index=False)
        logger.info(f"Saved processed data to {output_path}")

def select_files() -> List[str]:
    """File selection dialog"""
    root = Tk()
    root.withdraw()
    files = filedialog.askopenfilenames(
        title='Select Files',
        #filetypes=[("Data Files", "*.csv;*.xls;*.xlsx")]
    )
    root.destroy()
    return list(files)

def main():
    """Main workflow"""
    os.makedirs(pre_process_dir, exist_ok=True)

    config = {
        "input_dir": os.path.join(BASE_DIR, "raw"),
        "output_dir": pre_process_dir,
        "file_patterns": ["*.csv", "*.xlsx"],
        "required_columns": [],
        "validation_rules": []
    }
    
    processor = DataPreprocessor(config)
    
    try:
        if files := select_files():
            processor.start_processing(files)
            
            success_count = 0
            with tqdm(total=len(files), desc="Processing Files") as pbar:
                for future in as_completed(processor.futures):
                    if not processor.running:
                        break
                    try:
                        if future.result():
                            success_count += 1
                    except Exception as e:
                        logger.error(f"Error: {e}")
                    finally:
                        pbar.update(1)
            
            messagebox.showinfo(
                "Complete",
                f"Processed {success_count}/{len(files)} files\n"
                f"Output saved in: {pre_process_dir}"
            )
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        messagebox.showwarning("Interrupted", "Processing cancelled")
    finally:
        processor.stop_processing()

if __name__ == "__main__":
    main()