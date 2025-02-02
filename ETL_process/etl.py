import pandas as pd
import os
from concurrent.futures import ThreadPoolExecutor
import dask.dataframe as dd
import dask
import pathlib

def extract_data(file_path, output_folder):
    """Extract data from various file formats."""
    file_extension = pathlib.Path(file_path).suffix.lower()
    
    # Dictionary mapping file extensions to reading functions
    readers = {
        '.csv': lambda x: pd.read_csv(x),
        '.xlsx': lambda x: pd.read_excel(x),
        '.xls': lambda x: pd.read_excel(x),
        '.json': lambda x: pd.read_json(x),
        '.parquet': lambda x: pd.read_parquet(x),
        '.feather': lambda x: pd.read_feather(x),
        '.pkl': lambda x: pd.read_pickle(x),
        '.hdf': lambda x: pd.read_hdf(x),
        '.sql': lambda x: pd.read_sql(x),
        '.txt': lambda x: pd.read_csv(x, sep=None, engine='python'),  # Auto-detect separator
        '.dat': lambda x: pd.read_csv(x, sep=None, engine='python'),  # Auto-detect separator
    }
    
    try:
        if file_extension in readers:
            df = readers[file_extension](file_path)
        else:
            # Try to read as CSV with auto-detection of separator
            df = pd.read_csv(file_path, sep=None, engine='python')
            
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        print(f"Successfully extracted data from: {file_path}")
        return df
    
    except Exception as e:
        raise ValueError(f"Error reading file {file_path}: {str(e)}")

def transform_data_large(file_path, output_folder):
    """Transform large datasets using Dask for parallel processing."""
    file_extension = pathlib.Path(file_path).suffix.lower()
    
    try:
        if file_extension == '.csv':
            ddf = dd.read_csv(file_path)
        elif file_extension == '.parquet':
            ddf = dd.read_parquet(file_path)
        else:
            # For other formats, first read with pandas then convert to dask
            df = extract_data(file_path, output_folder)
            ddf = dd.from_pandas(df, npartitions=4)

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        def save_column(col):
            """Save a single column to a separate file using Dask."""
            column_data = ddf[[col]]
            output_path = os.path.join(output_folder, f"{col}.csv")
            column_data.to_csv(output_path, index=False, single_file=True)
            print(f"Saved column {col} to {output_path}")

        dask.compute([save_column(col) for col in ddf.columns])
        print("Data transformation and saving completed for large dataset.")
        
    except Exception as e:
        raise ValueError(f"Error processing large dataset: {str(e)}")

def transform_data(df, output_folder):
    """Transform data by splitting into separate files per column."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    def save_column(col):
        """Save a single column to a separate file."""
        column_data = df[[col]]
        output_path = os.path.join(output_folder, f"{col}.csv")
        column_data.to_csv(output_path, index=False)
        print(f"Saved column {col} to {output_path}")

    with ThreadPoolExecutor() as executor:
        executor.map(save_column, df.columns)

    print("Data transformation and saving completed.")

def run_etl(input_file, output_folder):
    """Runs the ETL process based on file size."""
    try:
        file_size = os.path.getsize(input_file) / (1024 * 1024)  # Size in MB
        if file_size > 100:
            print("Large dataset detected. Using Dask for parallel processing.")
            transform_data_large(input_file, output_folder)
        else:
            print("Small dataset detected. Using Pandas with multi-threading.")
            df = extract_data(input_file, output_folder)
            transform_data(df, output_folder)
    except Exception as e:
        raise ValueError(f"ETL process failed: {str(e)}")