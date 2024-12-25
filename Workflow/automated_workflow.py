from ..Extract_drive.src.loading_data import *
from ..Data_preprocess.src.classical_process.data_preprocess import *
from DAG import *
from ..Cloud_push.cloud_push import *
from ..Cloud_push.local_push import *

import logging
from datetime import datetime

# Set up centralized logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Monitoring function
def log_action(task_name, status, error_message=None):
    if error_message:
        logger.error(f"Task: {task_name} - Status: {status} - Error: {error_message}")
    else:
        logger.info(f"Task: {task_name} - Status: {status}")

# Wrapper for task monitoring
def monitor_task(task_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                log_action(task_name, "Started")
                result = func(*args, **kwargs)
                log_action(task_name, "Completed")
                return result
            except Exception as e:
                log_action(task_name, "Failed", str(e))
                raise
        return wrapper
    return decorator

# Main Workflow
@monitor_task("Creating directories")
def create_directories_task():
    create_directories()

@monitor_task("Downloading file from Google Drive")
def download_file_task(file_id, destination):
    download_file_from_drive(file_id, destination)

@monitor_task("Cleaning data")
def clean_data_task(source, destination):
    clean_csv_data(source, destination)

@monitor_task("Preprocessing data")
def preprocess_data_task(file_path):
    preprocess_data(file_path)

@monitor_task("Encrypting data")
def encrypt_data_task(file_path):
    return encrypt_file(file_path)

@monitor_task("Inserting data into Cassandra (local)")
def insert_local_cassandra_task(file_path):
    insert_data_to_cassandra_local(file_path)

@monitor_task("Inserting data into Cassandra (cloud)")
def insert_cloud_cassandra_task(file_path):
    insert_data_to_cassandra_cloud(file_path)

@monitor_task("Extracting text information")
def extract_text_info_task(file_path):
    extract_text_information(file_path)

if __name__ == "__main__":
    # File paths and IDs
    google_drive_file_id = "your-google-drive-file-id"
    raw_csv_path = "data/download/raw_data.csv"
    cleaned_csv_path = "data/preprocessed/cleaned_data.csv"

    try:
        # Step 1: Create necessary directories
        create_directories_task()

        # Step 2: Download the file
        download_file_task(google_drive_file_id, raw_csv_path)

        # Step 3: Clean the file
        clean_data_task(raw_csv_path, cleaned_csv_path)

        # Step 4: Preprocess the data
        preprocess_data_task(cleaned_csv_path)

        # Step 5: Encrypt the cleaned data
        encrypted_file_path = encrypt_data_task(cleaned_csv_path)

        # Step 6: Insert data into Cassandra (local)
        insert_local_cassandra_task(cleaned_csv_path)

        # Step 7: Insert data into Cassandra (cloud)
        insert_cloud_cassandra_task(encrypted_file_path)

        # Step 8: Extract text information
        extract_text_info_task(raw_csv_path)

    except Exception as workflow_exception:
        logger.critical(f"Workflow execution failed: {workflow_exception}")
