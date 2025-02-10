import os
import logging
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

from cryptography.fernet import Fernet
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from queue import Queue
from  automated_workflow import * 
# Add at the top of your script
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Import your existing components
#from src.drive_connection import (
   # load_api_key,
    #setup_drive_service,
    #create_directories,
    #download_file,
    #list_files_in_folder
#)
#from src.data_simple_preprocess import DataPreprocessor
#from src.etl import run_etl
#from src.cloud_push import *
#from src.local_push import *

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define encryption key for secure communication
encryption_key = Fernet.generate_key()
cipher_suite = Fernet(encryption_key)

# Monitoring wrapper for tasks
def monitor_task(task_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                logger.info(f"Task {task_name} started.")
                result = func(*args, **kwargs)
                logger.info(f"Task {task_name} completed successfully.")
                return result
            except Exception as e:
                logger.error(f"Task {task_name} failed with error: {e}")
                raise
        return wrapper
    return decorator

# Encryption function
def encrypt_data(file_path):
    with open(file_path, 'rb') as file:
        data = file.read()
    encrypted_data = cipher_suite.encrypt(data)
    encrypted_file_path = f"{file_path}.enc"
    with open(encrypted_file_path, 'wb') as file:
        file.write(encrypted_data)
    logger.info(f"Encrypted file saved to {encrypted_file_path}")
    return encrypted_file_path

# DAG Task Functions
@monitor_task("Download from Google Drive")
def download_from_drive(**context):
    """Download file from Google Drive"""
    api_key = load_api_key(context['dag_run'].conf.get('api_key_path'))
    drive_service = setup_drive_service(api_key)
    file_id = context['dag_run'].conf.get('file_id')
    destination = os.path.join('data', 'raw', 'downloaded_file.csv')
    download_file(drive_service, file_id, destination)
    return destination

@monitor_task("Preprocess Data")
def preprocess_data(**context):
    """Preprocess downloaded data"""
    ti = context['ti']
    file_path = ti.xcom_pull(task_ids='download_from_drive')
    config = {
        "input_dir": os.path.dirname(file_path),
        "output_dir": "data/preprocessed",
        "file_patterns": ["*.csv", "*.xlsx"]
    }
    preprocessor = DataPreprocessor(config)
    preprocessor.start_processing([file_path])
    return os.path.join("data/preprocessed", f"cleaned_{os.path.basename(file_path)}")

@monitor_task("ETL Process")
def run_etl_process(**context):
    """Run ETL process on preprocessed data"""
    ti = context['ti']
    input_file = ti.xcom_pull(task_ids='preprocess_data')
    output_dir = "data/transformed"
    run_etl(input_file, output_dir)
    return os.path.join(output_dir, "transformed_data.csv")

@monitor_task("Push to Database")
def push_to_database(**context):
    """Push processed data to database"""
    ti = context['ti']
    file_path = ti.xcom_pull(task_ids='run_etl_process')
    is_cloud = context['dag_run'].conf.get('use_cloud', False)
    
    if is_cloud:
        session = connect_to_cassandra_cloud()
        create_keyspace_func = create_cloud_keyspace
        create_table_func = create_cloud_table
        insert_data_func = insert_cloud_data
    else:
        session = connect_to_cassandra_local()
        create_keyspace_func = create_local_keyspace
        create_table_func = create_local_table
        insert_data_func = insert_local_data
    
    if session:
        keyspace = context['dag_run'].conf.get('keyspace', 'data_workflow')
        table = context['dag_run'].conf.get('table', 'processed_data')
        create_keyspace_func(session, keyspace)
        df = create_table_func(session, file_path, table)
        if df is not None:
            insert_data_func(session, df, table)

# Define the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'data_workflow',
    default_args=default_args,
    description='Automated Data Workflow with Monitoring and Logging',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False
) as dag:

    # Create DAG tasks
    create_dirs_task = PythonOperator(
        task_id='create_directories',
        python_callable=create_directories,
    )

    download_task = PythonOperator(
        task_id='download_from_drive',
        python_callable=download_from_drive,
    )

    preprocess_task = PythonOperator(
        task_id='preprocess_data',
        python_callable=preprocess_data,
    )

    etl_task = PythonOperator(
        task_id='run_etl_process',
        python_callable=run_etl_process,
    )

    push_task = PythonOperator(
        task_id='push_to_database',
        python_callable=push_to_database,
    )

    # Define task dependencies
    create_dirs_task >> download_task >> preprocess_task >> etl_task >> push_task

# Class for manual workflow execution
class WorkflowRunner:
    def __init__(self):
        self.logger = logger

    @monitor_task("Manual Workflow Execution")
    def run_workflow(self, config):
        """Execute workflow manually with given configuration"""
        try:
            # Create directories
            create_directories()
            self.logger.info("Directories created successfully")

            # Download file
            file_path = download_from_drive(dag_run=type('obj', (object,), {'conf': config}))
            self.logger.info(f"File downloaded to: {file_path}")

            # Preprocess data
            preprocessed_file = preprocess_data(
                ti=type('obj', (object,), {'xcom_pull': lambda task_ids: file_path}),
                dag_run=type('obj', (object,), {'conf': config})
            )
            self.logger.info(f"Preprocessing completed: {preprocessed_file}")

            # Run ETL
            transformed_file = run_etl_process(
                ti=type('obj', (object,), {'xcom_pull': lambda task_ids: preprocessed_file}),
                dag_run=type('obj', (object,), {'conf': config})
            )
            self.logger.info(f"ETL process completed: {transformed_file}")

            # Push to database
            push_to_database(
                ti=type('obj', (object,), {'xcom_pull': lambda task_ids: transformed_file}),
                dag_run=type('obj', (object,), {'conf': config})
            )
            self.logger.info("Data successfully pushed to database")

            return True

        except Exception as e:
            self.logger.error(f"Workflow failed: {str(e)}")
            raise

