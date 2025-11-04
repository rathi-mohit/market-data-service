import duckdb
import pandas as pd
import time
import datetime

# Database file and table name from your config.py
DB_FILE = 'market_data.duckdb'
TABLE_NAME = 'ohlcv_data'

# Sample data to insert
data_to_insert = pd.read_csv("clean_data.csv").values.tolist()

try:
    # Connect to the database
    con = duckdb.connect(database=DB_FILE, read_only=False)
    records = len(data_to_insert)
    
    # --- This is the simple SQL insert part ---
    
    # We create the SQL query template with placeholders (?)
    sql_query = f"""
        INSERT INTO {TABLE_NAME} (timestamp, symbol, open, high, low, close, volume) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (symbol, timestamp) DO NOTHING;
    """
    
    print("Starting row-by-row insert...")
    
    con.execute(f"""
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    timestamp TIMESTAMP,
                    symbol VARCHAR,
                    open DOUBLE,
                    high DOUBLE,
                    low DOUBLE,
                    close DOUBLE,
                    volume BIGINT,
                    UNIQUE(symbol, timestamp)
                );
            """)
    
    start_time = time.perf_counter()

    # Loop through each row of data and execute the query
    for row in data_to_insert:
        con.execute(sql_query, row)
    
    end_time = time.perf_counter()
        
    # In many SQL databases, you need to commit the transaction.
    # DuckDB often auto-commits, but this is good practice.
    con.commit()
    
    print(records / (end_time - start_time))
    print(f"Successfully inserted {len(data_to_insert)} rows (or skipped duplicates).")

except Exception as e:
    print(f"An error occurred: {e}")
    # In a real app, you might con.rollback() here
finally:
    # Always close the connection
    if 'con' in locals():
        con.close()