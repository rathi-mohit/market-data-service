Project Status

Part 1: Data Ingestion Pipeline: Complete.

Part 2: Database Design & Implementation: Complete.

Part 3: REST API Development: Not Implemented. (Due to time constraints).

Part 4: Systems Design Documentation: Complete. (See design/DESIGN.md).

Features

Modular ETL Pipeline: The ingestion process is separated into three distinct, runnable scripts:

extract.py: Fetches raw data from Alpha Vantage.

transform.py: Cleans, validates, and normalizes the data.

load.py: Bulk-loads the clean data into the database.

Incremental Updates: The load.py script uses an INSERT ... ON CONFLICT DO NOTHING strategy, making the pipeline idempotent and capable of handling daily incremental data loads without creating duplicates.

High-Performance Load: The load step uses DuckDB's in-memory register() function to perform a high-speed bulk insert, consistently exceeding the 1000 rec/s requirement (even upto 6-8k records per second).

Monitoring: All pipeline steps write to a timestamped etl.log file for monitoring and debugging.

Optimized Database: The market_data.duckdb file uses a UNIQUE(symbol, timestamp) index to ensure data integrity and enable high-speed queries, as documented in design/DESIGN.md.

1. Install Dependencies

Clone this repository to your local machine:

Install all required Python libraries using pip:

pip install -r requirements.txt


Create a .env file in the root directory and add your Alpha Vantage API key:

echo "AV_API_KEY=YOUR_API_KEY_HERE" > .env


2. Set Up the Database

No manual setup is required. The database (market_data.duckdb) and its schema are created automatically by the load.py script on its first run.

3. Run the ETL Pipeline

The pipeline is designed to be run in stages from your terminal.

Initial 6-Month Load (Run this first)

This will fetch the full history, transform the last 6 months, and load it into your new database.

# Step 1: Extract full data from the API
python extract.py --mode full

# Step 2: Transform and filter for the last 180 days (6 months)
python transform.py --days 180

# Step 3: Load the clean data into DuckDB
python load.py


You can monitor the progress in the etl.log file.

### Daily Incremental Update (Run this any time after)

This simulates a daily run. It fetches only the last k data points, processes them, and load.py will only insert the new day's data, skipping duplicates.

# Step 1: Extract only recent data (fast)
python extract.py --mode compact

# Step 2: Transform the recent k-DAYS DATA (e.g., last 10 days)
python transform.py --days 10

# Step 3: Load new data, skipping duplicates
python load.py


Since there are no API endpoints to test, you can verify the data and the pipeline's success by querying the DuckDB database directly.

Install the DuckDB Command Line Interface (CLI) from the duckdb website here:

Open the database file in the cli by using the .open FILENAME command:

Run SQL queries at the D prompt to verify the data:

-- Check the total number of records:
SELECT COUNT(*) FROM ohlcv_data;

-- See the 5 most recent entries for a single stock:
SELECT * FROM ohlcv_data
WHERE symbol = 'AAPL'
ORDER BY timestamp DESC
LIMIT 5;

-- List all instruments loaded into the database:
SELECT DISTINCT symbol FROM ohlcv_data;

-- Exit the CLI:
.exit

You can even run an EXPLAIN ANALYZE to test performance if necessary
A sample data is present in sample_data folder

This directly proves that the ETL pipeline (Part 1) and the database (Part 2) are working correctly.

Design Choices: My detailed design justifications are in the DESIGN.md file.