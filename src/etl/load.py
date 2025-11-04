"""
Reads the processed Parquet file and loads it into a DuckDB database.
Handles incremental updates via 'ON CONFLICT'.
"""

import duckdb
import pandas as pd
import logging
import time
from core.config import PROCESSED_DATA_PATH, DB_FILE, TABLE_NAME

# Again, logging as wanted in 3.1
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("etl.log"), logging.StreamHandler()]
)

def load_to_duckdb():
    """
    Loads the processed DataFrame into the DuckDB database.
    """

    logging.info(f"Starting load process for {DB_FILE}")
    
    try:
        df_to_load = pd.read_parquet(PROCESSED_DATA_PATH)

        record_count = len(df_to_load)
        if record_count == 0:
            logging.info("No data to load. Exiting.")
            return
        logging.info(f"Loaded {record_count} processed records from {PROCESSED_DATA_PATH}")

    except Exception as e:
        logging.error(f"Could not read processed data file: {e}")
        return

    start_time = time.perf_counter()
    
    try:
        con = duckdb.connect(database=DB_FILE, read_only=False)
        
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
        
        # Register the DataFrame as a virtual table (this is a memory-based performance optimization)
        con.register('df_to_load', df_to_load)
        
        # Insert data, ignoring conflicts on (symbol, timestamp)
        # THis ensures incremental loading, avoiding duplicates and hence 
        # one can load any k-days at any point, without worrying about duplicates
        insert_sql = f"""
            INSERT INTO {TABLE_NAME}
            SELECT * FROM df_to_load
            ON CONFLICT (symbol, timestamp) DO NOTHING;
        """
        con.execute(insert_sql)
        
        con.close()
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        recs_per_sec = record_count / duration
        
        logging.info("Load complete in %.2f seconds.", duration)
        logging.info("Performance: %.2f records/sec.", recs_per_sec)

    except Exception as e:
        logging.error(f"Error during DuckDB load: {e}")

if __name__ == "__main__":
    load_to_duckdb()
    logging.info("Loaded the data into DuckDB successfully.")