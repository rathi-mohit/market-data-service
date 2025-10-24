"""
Extracts data from Alpha Vantage API and saves it as a raw Parquet file.
Usage:
  - Initial load: python extract.py --mode full
  - Incremental:  python extract.py --mode compact
"""

import requests
import pandas as pd
import time
import os
import logging
import argparse # (For command line argument parsing)
from src.core.config import AV_API_KEY, TICKERS, BASE_URL, RAW_DATA_PATH

# Logging, as wanted in 3.1
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("etl.log"), logging.StreamHandler()]
)

def fetch_data(output_mode="full"):
    """
    Fetches time series data for all tickers from Alpha Vantage.
    """

    all_stock_data = []
    # This will be a list of dataframes


    logging.info(f"Starting API extraction with mode {output_mode}")

    if not AV_API_KEY:
        logging.error("AV_API_KEY not found. Set it in your .env file.")
        return None

    for stock in TICKERS:
        logging.info(f"Fetching data for {stock}")

        # I define params here, based on alpha-vantage api documentation
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": stock,
            "outputsize": output_mode,
            "apikey": AV_API_KEY
        }
        
        try:
            r = requests.get(BASE_URL, params=params)
            r.raise_for_status() # HTTP Error check
            data = r.json()

            if "Error Message" in data:
                logging.error(f"API Error for {stock}: {data['Error Message']}")
                continue
            if "Note" in data:
                logging.warning(f"API Note for {stock}: {data['Note']}")
                logging.error("WE Hit rate limit. Abandoning.")
                break 

            time_series_data = data['Time Series (Daily)']
            df = pd.DataFrame.from_dict(time_series_data, orient='index')
            df['symbol'] = stock
            all_stock_data.append(df)
            
            logging.info(f"Success for {stock}. Fetched {len(df)} records.")
            logging.info("Waiting 30 seconds to avoid rate limits")
            time.sleep(30)

        # Handling errors 
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for {stock}: {e}")
        except KeyError:
            logging.error(f"Could not parse JSON for {stock}. Response: {data}")
        except Exception as e:
            logging.error(f"An unexpected error occurred for {stock}: {e}")
    
    if not all_stock_data:
        logging.error("No data was extracted. Exiting.")
        return None

    # We now concatenate all dataframes into one
    logging.info("Concatenating all data.")
    full_df = pd.concat(all_stock_data)
    return full_df


def save_raw_data(df):
    """
    Saves the raw DataFrame to a Parquet file.
    """

    try:
        os.makedirs(os.path.dirname(RAW_DATA_PATH), exist_ok=True)
        df.to_parquet(RAW_DATA_PATH)
        logging.info(f"Raw data saved to {RAW_DATA_PATH}")
    except Exception as e:
        logging.error(f"Failed to save raw data: {e}")


if __name__ == "__main__":

    #THe below is a command line parser setup
    parser = argparse.ArgumentParser(description="Extract data from Alpha Vantage.")
    parser.add_argument(
        "--mode", 
        type = str, 
        choices = ["full", "compact"], 
        default = "full", 
        help = "API output size: 'full' for full data, 'compact' for last k-days of data."
    )
    args = parser.parse_args()

    raw_df = fetch_data(output_mode=args.mode)
    if raw_df is not None:
        save_raw_data(raw_df)
        logging.info("Extraction complete.")
    else:

        logging.error("Extraction failed, data was empty.")