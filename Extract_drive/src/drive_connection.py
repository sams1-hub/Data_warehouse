import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pandas as pd

# Define the base directory outside the current folder
BASE_DIR = "../data"  # "../" moves one level up from the current folder

def load_api_key(api_key_file):
    """Load API key from file"""
    try:
        with open(api_key_file, "r") as file:
            api_key = file.read().strip()
            print("API Key loaded successfully.")
            return api_key
    except FileNotFoundError:
        print(f"Error: API key file '{api_key_file}' not found.")
        raise

def setup_drive_service(api_key):
    """Setup Google Drive API client"""
    return build('drive', 'v3', developerKey=api_key)

def create_directories():
    """Create necessary directories"""
    try:
        os.makedirs(os.path.join(BASE_DIR, "download"), exist_ok=True)
        os.makedirs(os.path.join(BASE_DIR, "preprocessed"), exist_ok=True)
        print(f"Folders created at: {os.path.abspath(BASE_DIR)}")
        print("Directories created or already exist.")
    except Exception as e:
        print(f"An error occurred while creating directories: {e}")
        raise

def extract_folder_id(folder_input):
    """Extract folder ID from Google Drive URL or return the ID if already clean"""
    if 'folders/' in folder_input:
        folder_id = folder_input.split('folders/')[1]
        return folder_id.split('?')[0]
    return folder_input

def load_folder_config(config_file="drive_folders.txt"):
    """Load folder configurations from a text file"""
    folders = {}
    try:
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and ',' in line:
                    name, url = line.split(',', 1)
                    folders[name.strip()] = url.strip()
        return folders
    except Exception as e:
        print(f"Error loading folder config: {e}")
        return {}

def list_files_in_folder(drive_service, folder_input):
    """List all files in a Google Drive folder"""
    try:
        # Extract folder ID
        folder_id = extract_folder_id(folder_input)
        print(f"Using folder ID: {folder_id}")
        
        # Query to list files
        query = f"'{folder_id}' in parents and trashed=false"
        results = drive_service.files().list(
            q=query,
            spaces='drive',
            fields="files(id, name, mimeType, size)",
            pageSize=1000
        ).execute()
        
        files = results.get('files', [])
        
        if not files:
            print("No files found in the folder.")
            return []
            
        print("\nFiles found:")
        print("-" * 50)
        for idx, file in enumerate(files, 1):
            size = int(file.get('size', 0)) // 1024 if file.get('size') else 0
            print(f"{idx}. {file['name']} ({size}KB)")
        print("-" * 50)
        
        return files
        
    except Exception as e:
        print(f"Error listing files: {str(e)}")
        raise

def download_file(drive_service, file_id, destination_path, progress_callback=None):
    """Download file from Google Drive with optional progress callback"""
    try:
        request = drive_service.files().get_media(fileId=file_id)
        with open(destination_path, "wb") as file:
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                progress = int(status.progress() * 100)
                print(f"Download {progress}% complete.")
                if progress_callback:
                    progress_callback(progress)
        print(f"File downloaded successfully to {destination_path}.")
        return True
    except Exception as e:
        print(f"An error occurred while downloading the file: {e}")
        raise

def process_file(file_path, processed_file_path=None):
    """Process downloaded file (CSV format)"""
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
            print(f"CSV data loaded successfully: \n{df.head()}")
            df.columns = df.columns.str.lower()

            # If processed_file_path is not provided, save in the same directory
            if processed_file_path is None:
                processed_file_path = os.path.join(
                    os.path.dirname(file_path),
                    "preprocessed",
                    os.path.basename(file_path)
                )
                os.makedirs(os.path.dirname(processed_file_path), exist_ok=True)

            # Save the processed file
            df.to_csv(processed_file_path, index=False)
            print(f"Preprocessed data saved to {processed_file_path}.")
            return processed_file_path
        else:
            print(f"No processing applied. Unsupported file type: {file_path}")
            return None
    except Exception as e:
        print(f"An error occurred while processing the file: {e}")
        raise
