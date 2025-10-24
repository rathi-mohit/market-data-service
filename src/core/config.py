"""
Stores all necessary configurations for our pipeline.
"""

import os
from dotenv import load_dotenv


# API
BASE_URL = 'https://www.alphavantage.co/query'

# API KEY from .env (ALPHA VANTAGE)
load_dotenv()
AV_API_KEY = os.getenv("AV_API_KEY")

# Stocks to fetch
STOCKS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]


# Data storing paths
DATA_DIR = "data"
RAW_DATA_PATH = os.path.join(DATA_DIR, "raw", "raw_data.parquet")
PROCESSED_DATA_PATH = os.path.join(DATA_DIR, "processed", "clean_data.parquet")

# DuckDB
DB_FILE = 'market_data.duckdb'
TABLE_NAME = 'ohlcv_data'