from cassandra.cluster import Cluster
import pandas as pd
from sqlalchemy import create_engine

def extract_from_cassandra(table_name, keyspace, host='127.0.0.1'):
    """Extract data from a Cassandra table."""
    cluster = Cluster([host])
    session = cluster.connect()
    session.set_keyspace(keyspace)
    query = f"SELECT * FROM {table_name};"
    rows = session.execute(query)
    columns = rows.column_names
    data = [row._asdict() for row in rows]
    df = pd.DataFrame(data, columns=columns)
    print(f"Extracted data from Cassandra table {table_name}.")
    return df

def transform_to_sql_format(df, sql_schema=None):
    """Transform data for SQL compatibility."""
    # Example: Ensure column names match SQL conventions
    df.columns = [col.replace(" ", "_").lower() for col in df.columns]
    if sql_schema:
        # Reorder or rename columns as per SQL schema
        df = df[sql_schema]
    print("Data transformed for SQL.")
    return df

def load_to_sql(df, table_name, sql_db_url, if_exists='replace'):
    """Load data into a SQL database."""
    engine = create_engine(sql_db_url)
    df.to_sql(table_name, engine, if_exists=if_exists, index=False)
    print(f"Data loaded into SQL table {table_name}.")
