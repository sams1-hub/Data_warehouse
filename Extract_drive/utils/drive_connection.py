import os
import csv
import requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
import pandas as pd

# Step 1: Setup Google Drive API Client
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'path/to/your/service-account-key.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build('drive', 'v3', credentials=credentials)

# Step 2: Create Directories for Download and Preprocessed Data
def create_directories():
    try:
        os.makedirs("data/download", exist_ok=True)
        os.makedirs("data/preprocessed", exist_ok=True)
        print("Directories created or already exist.")
    except Exception as e:
        print(f"An error occurred while creating directories: {e}")