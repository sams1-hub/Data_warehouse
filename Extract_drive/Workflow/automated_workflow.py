from ..src.loading import *

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
