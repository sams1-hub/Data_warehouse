from ..utils.drive_connection import *

# Step 3: Function to Download Files from Google Drive
def download_file_from_drive(file_id, destination):
    try:
        request = drive_service.files().get_media(fileId=file_id)
        with open(destination, 'wb') as file:
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download progress: {int(status.progress() * 100)}%")
        print(f"File downloaded successfully to {destination}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Step 4: Function to Clean CSV Data
def clean_csv_data(input_path, output_path):
    try:
        # Read the CSV into a DataFrame
        df = pd.read_csv(input_path)

        # Example Cleaning Steps
        #df.dropna(inplace=True)  # Drop rows with missing values
       # df.columns = df.columns.str.strip()  # Strip whitespace from headers

        # Save the cleaned DataFrame back to a CSV
        df.to_csv(output_path, index=False)
        print(f"Cleaned data saved to {output_path}")
    except Exception as e:
        print(f"An error occurred during cleaning: {e}")

# Step 5: Logging and Security Enhancements
def log_action(action, status, details=""):
    log_file = "data_pipeline.log"
    with open(log_file, "a") as log:
        log.write(f"{action} | {status} | {details}\n")
    print(f"Logged action: {action}")

