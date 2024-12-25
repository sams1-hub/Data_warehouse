from ..Extract_drive.src.loading_data import *
from ..Data_preprocess.src.classical_process.data_preprocess import *
from DAG import *
from ..Cloud_push.cloud_push import *
from ..Cloud_push.local_push import *



# Step 6: Automating the Workflow
if __name__ == "__main__":
    # Create necessary directories
    create_directories()

    # File IDs and Local Paths
    google_drive_file_id = "your-google-drive-file-id"
    raw_csv_path = "data/download/raw_data.csv"
    cleaned_csv_path = "data/preprocessed/cleaned_data.csv"

    # Step 1: Download the file
    try:
        log_action("Downloading file", "Started")
        download_file_from_drive(google_drive_file_id, raw_csv_path)
        log_action("Downloading file", "Completed")
    except Exception as e:
        log_action("Downloading file", "Failed", str(e))

    # Step 2: Clean the file
    try:
        log_action("Cleaning data", "Started")
        clean_csv_data(raw_csv_path, cleaned_csv_path)
        log_action("Cleaning data", "Completed")
    except Exception as e:
        log_action("Cleaning data", "Failed", str(e))

    # Step 3: Preprocess the data
    try:
        log_action("Preprocessing data", "Started")
        preprocess_data(cleaned_csv_path)
        log_action("Preprocessing data", "Completed")
    except Exception as e:
        log_action("Preprocessing data", "Failed", str(e))

    # Step 4: Encrypt the cleaned data
    try:
        log_action("Encrypting data", "Started")
        encrypted_file_path = encrypt_file(cleaned_csv_path)
        log_action("Encrypting data", "Completed")
    except Exception as e:
        log_action("Encrypting data", "Failed", str(e))

    # Step 5: Insert data into Cassandra (local)
    try:
        log_action("Inserting data into Cassandra (local)", "Started")
        insert_data_to_cassandra_local(cleaned_csv_path)
        log_action("Inserting data into Cassandra (local)", "Completed")
    except Exception as e:
        log_action("Inserting data into Cassandra (local)", "Failed", str(e))

    # Step 6: Insert data into Cassandra (cloud)
    try:
        log_action("Inserting data into Cassandra (cloud)", "Started")
        insert_data_to_cassandra_cloud(encrypted_file_path)
        log_action("Inserting data into Cassandra (cloud)", "Completed")
    except Exception as e:
        log_action("Inserting data into Cassandra (cloud)", "Failed", str(e))

    # Step 7: Extract text information
    try:
        log_action("Extracting text information", "Started")
        extract_text_information(raw_csv_path)
        log_action("Extracting text information", "Completed")
    except Exception as e:
        log_action("Extracting text information", "Failed", str(e))
