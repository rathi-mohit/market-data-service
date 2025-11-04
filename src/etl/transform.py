"""
Reads the raw Parquet file, transforms and validates the data,
and saves it as a new, clean Parquet file.

Usage:
  - 6-month load: python transform.py --days 180
  - Incremental:  python transform.py --days 10 
"""

import pandas as pd
import logging
import os
import argparse
from core.config import RAW_DATA_PATH, PROCESSED_DATA_PATH

# logging again, as wanted in 3.1
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("etl.log"), logging.StreamHandler()]
)

def transform(k_days=180):
    """
    Runs the full data transformation and validation process.
    """

    logging.info("Starting transformation process")
    try:
        df = pd.read_parquet(RAW_DATA_PATH)
        logging.info(f"Loaded {len(df)} raw records from {RAW_DATA_PATH}")

    except Exception as e:
        logging.error(f"Could not read raw data file: {e}")
        return None

    # Resetting Index and Renaming the Columns because otherwise
    # it was seen that the timestamp was not a column but index
    # Following the OHLCV format 
    df = df.reset_index()
    df = df.rename(columns={
        "index": "timestamp",
        "1. open": "open",
        "2. high": "high",
        "3. low": "low",
        "4. close": "close",
        "5. volume": "volume"
    })

    # Type Coercion
    # THis waas needed, so as to change timestamp to datetime and ohlcv to numeric
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Time-Based Filtering (Parameterized)
    # We keep only last k_days of data, which is passed as argument
    cutoff_date = pd.Timestamp.now() - pd.DateOffset(days=k_days)
    df = df[df['timestamp'] >= cutoff_date]
    logging.info(f"Filtered to {len(df)} records from the last {k_days} days.")

    # Column Selection
    final_columns = ["timestamp", "symbol", "open", "high", "low", "close", "volume"]
    df = df[final_columns].copy()

    # Validation: Missing Values
    # ANy missing values are forward/backward filled
    if df.isnull().sum().sum() > 0:
        logging.warning("Applying ffill/bfill on the NaN values.")
        df = df.sort_values(by=['symbol', 'timestamp'])
        df = df.ffill().bfill()

    # Validation: Outliers
    # ANy non-positive values in OHLCV are removed
    if (df[numeric_cols] <= 0).any().any():
        logging.warning("Removing non-positive values in OHLCV columns.")
        df = df[(df[['open', 'high', 'low', 'close']] > 0).all(axis=1)]

    # Final Type Conversion
    if 'volume' in df.columns:
        df['volume'] = df['volume'].astype(int)

    logging.info(f"Processed {len(df)} records and transformed.")
    return df

def save_processed_data(df):
    """
    Saves the processed data to a Parquet file.
    """

    try:
        os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok=True)
        df.to_parquet(PROCESSED_DATA_PATH)
        logging.info(f"Processed data saved to {PROCESSED_DATA_PATH}")
    except Exception as e:
        logging.error(f"Failed to save processed data: {e}")

if __name__ == "__main__":

    # Again, command line parser setup
    parser = argparse.ArgumentParser(description="Transform raw stock data.")
    parser.add_argument(
        "--days", 
        type = int, 
        default = 180, # As per the 6 month criteria in the assignment
        help= "Number of recent days of data to extract."
    )
    args = parser.parse_args()
    
    clean_df = transform(k_days = args.days)
    if clean_df is not None:
        save_processed_data(clean_df)
        logging.info("Transformed the data.")