###########################################################################

#  Utils functions pour les connexion avec cassandra en local ou depuis le cloud) 
# A utilisé dans le les differents étapes du data process

###########################################################################

from cassandra.cluster import Cluster
import pandas as pd

# Step 1: Connect to Cassandra (Local)
def connect_to_cassandra_local():
    try:
        cluster = Cluster(['127.0.0.1'])
        session = cluster.connect()
        print("Connected to Cassandra locally.")
        return session
    except Exception as e:
        print(f"An error occurred while connecting to Cassandra: {e}")
        return None

# Step 2: Create Keyspace if it does not exist
def create_keyspace(session, keyspace_name):
    try:
        session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {keyspace_name}
        WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}};
        """)
        session.set_keyspace(keyspace_name)
        print(f"Keyspace '{keyspace_name}' is ready.")
    except Exception as e:
        print(f"An error occurred while creating keyspace: {e}")

# Step 3: Create Tables Based on CSV
def create_table_for_csv(session, csv_path, table_name):
    try:
        df = pd.read_csv(csv_path)
        columns = [f"{col} text" for col in df.columns]
        columns_definition = ", ".join(columns)

        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id UUID PRIMARY KEY,
            {columns_definition}
        );
        """
        session.execute(create_table_query)
        print(f"Table '{table_name}' created or already exists.")
        return df
    except Exception as e:
        print(f"An error occurred while creating table: {e}")
        return None

# Step 4: Insert Data into the Table
def insert_data_to_table(session, df, table_name):
    try:
        for _, row in df.iterrows():
            columns = ", ".join(df.columns)
            placeholders = ", ".join(["%s"] * len(df.columns))

            insert_query = f"INSERT INTO {table_name} (id, {columns}) VALUES (uuid(), {placeholders});"
            session.execute(insert_query, tuple(row))
        print(f"Data inserted into table '{table_name}' successfully.")
    except Exception as e:
        print(f"An error occurred while inserting data: {e}")

if __name__ == "__main__":
    csv_path = "data/preprocessed/cleaned_data.csv"
    keyspace_name = "your_keyspace_name"
    table_name = "your_table_name"

    # Step 1: Connect to Cassandra locally
    session = connect_to_cassandra_local()

    if session:
        # Step 2: Create Keyspace
        create_keyspace(session, keyspace_name)

        # Step 3: Create Table and Load CSV
        df = create_table_for_csv(session, csv_path, table_name)

        # Step 4: Insert Data into the Table
        if df is not None:
            insert_data_to_table(session, df, table_name)
