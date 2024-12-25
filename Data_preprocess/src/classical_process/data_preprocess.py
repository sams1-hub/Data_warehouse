import pandas as pd
import os

# Step 1: Load CSV or Excel Data
def load_data(file_path):
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format. Use CSV or Excel files.")
        print(f"Data loaded successfully from {file_path}.")
        return df
    except Exception as e:
        print(f"An error occurred while loading the data: {e}")
        return None

# Step 2: Clean the Data
def clean_data(df):
    try:
        # Remove duplicates
        df = df.drop_duplicates()
        print("Duplicates removed.")

        # Handle missing values (example: filling with 'N/A')
        df = df.fillna('N/A')
        print("Missing values handled.")

        # Trim whitespace from string columns
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        print("Whitespace trimmed from string values.")

        return df
    except Exception as e:
        print(f"An error occurred while cleaning the data: {e}")
        return None

# Step 3: Validate Data Columns
def validate_columns(df, required_columns):
    try:
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        print("All required columns are present.")
    except Exception as e:
        print(f"An error occurred during column validation: {e}")

# Step 4: Save Preprocessed Data
def save_preprocessed_data(df, output_dir, file_name):
    try:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, file_name)
        df.to_csv(output_path, index=False)
        print(f"Preprocessed data saved to {output_path}.")
    except Exception as e:
        print(f"An error occurred while saving the preprocessed data: {e}")

if __name__ == "__main__":
    input_file = "data/raw/data.csv"  # Replace with your input file path
    output_dir = "data/preprocessed"
    output_file = "cleaned_data.csv"

    # Step 1: Load the data
    raw_data = load_data(input_file)

    if raw_data is not None:
        # Step 2: Clean the data
        cleaned_data = clean_data(raw_data)

        if cleaned_data is not None:
            # Step 3: Validate the data (add your required columns here)
            required_columns = ['column1', 'column2', 'column3']  # Replace with actual required columns
            validate_columns(cleaned_data, required_columns)

            # Step 4: Save the preprocessed data
            save_preprocessed_data(cleaned_data, output_dir, output_file)
