from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import os

from ..Cloud_push.cloud_push import *
from ..Cloud_push.local_push import *

from ..Extract_drive.src.loading_data import *

from ..Data_preprocess.src.classical_process.data_preprocess import *
from ..Data_preprocess.src.text_minning.minning import *






# Define encryption key for secure communication
encryption_key = Fernet.generate_key()
cipher_suite = Fernet(encryption_key)

# Define default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Encryption function
def encrypt_data(file_path):
    with open(file_path, 'rb') as file:
        data = file.read()
    encrypted_data = cipher_suite.encrypt(data)
    encrypted_file_path = f"{file_path}.enc"
    with open(encrypted_file_path, 'wb') as file:
        file.write(encrypted_data)
    print(f"Encrypted file saved to {encrypted_file_path}")
    return encrypted_file_path

# Task Functions
def download_from_drive(**kwargs):
    # Use the pre-written Google Drive API script here
    from drive_download_script import download_data
    file_path = download_data()
    return file_path

def preprocess_data(**kwargs):
    from data_preprocessing import preprocess
    ti = kwargs['ti']
    file_path = ti.xcom_pull(task_ids='download_from_drive')
    preprocessed_file = preprocess(file_path)
    return preprocessed_file

def insert_data_to_cassandra(**kwargs):
    from cassandra_local_import import import_to_cassandra
    ti = kwargs['ti']
    preprocessed_file = ti.xcom_pull(task_ids='preprocess_data')
    import_to_cassandra(preprocessed_file)

def extract_text_info(**kwargs):
    from text_winning_script import process_text
    ti = kwargs['ti']
    file_path = ti.xcom_pull(task_ids='download_from_drive')
    extracted_info = process_text(file_path)
    return extracted_info

# Define the DAG
with DAG(
    'data_workflow',
    default_args=default_args,
    description='Automated Data Workflow with Airflow',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False
) as dag:

    create_directories_task = PythonOperator(
        task_id='create_directories',
        python_callable=create_directories
    )

    download_task = PythonOperator(
        task_id='download_from_drive',
        python_callable=download_from_drive
    )

    preprocess_task = PythonOperator(
        task_id='preprocess_data',
        python_callable=preprocess_data
    )

    insert_cassandra_task = PythonOperator(
        task_id='insert_data_to_cassandra',
        python_callable=insert_data_to_cassandra
    )

    extract_text_task = PythonOperator(
        task_id='extract_text_info',
        python_callable=extract_text_info
    )

    # Task Dependencies
    create_directories_task >> download_task >> preprocess_task >> [insert_cassandra_task, extract_text_task]
