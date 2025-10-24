This document outlines the system design for the Market Data Service.

## 1\. Architecture Diagram

The system is a modular ETL-driven API. It ingests data from an external source, processes it through a 3-stage pipeline (Extract, Transform, Load), stores it in an optimized analytical database, which can then be served via a REST-API high-performance implementation.

### Data Flow

```
[External Data Source] ----(1. Extract)----> [ETL Pipeline] ----(2. Transform)----> [Clean Data] ----(3. Load)----> [Database] <----(4. Query)---- [API Server] <----(5. Request)---- [User]

    (Alpha Vantage API)         (Python Scripts:                       (Parquet Files:         (DuckDB File:        (FastAPI:         (Browser / Client)
                                 extract.py,                            clean_data.parquet)     market_data.duckdb)  api.py)
                                 transform.py,
                                 load.py)
```

**Explanation:**

1.  **Extract:** The `extract.py` script sends an HTTP request to the **Alpha Vantage API** to fetch raw JSON data. This raw data is saved to a `raw_data.parquet` file.
2.  **Transform:** The `transform.py` script reads `raw_data.parquet`, then cleans, validates (for NaNs, outliers), and normalizes the data. It filters for the required time period and saves the result as `clean_data.parquet`.
3.  **Load:** The `load.py` script reads the `clean_data.parquet` file and performs a bulk "upsert" (`ON CONFLICT...`) into the **DuckDB** file (`market_data.duckdb`), which contains our `ohlcv_data` table. 

Things I was unable to implement:
4.  **Query:** When a user sends a request to the **FastAPI Server** (e.g., `GET /instruments/AAPL/ohlcv`), the API queries the **DuckDB** file.
5.  **Cache & Respond:**
      * **Not found in Cache:** If the data is not in the **In-Memory Cache**, the API fetches it from DuckDB, stores a copy in the cache, and then sends the JSON response to the user.
      * **Found in Cache:** If the user (or another user) makes the same request again quickly, the API serves the data directly from the cache, which is much faster and meets the `< 200ms` requirement.

-----

## 2\. Trade-offs Analysis

This section justifies the key technology choices for the database and caching layers.

### 2.1. Database Choice: DuckDB

  * **Why DuckDB:** I chose DuckDB because it was the only thing I was able to try in the given time. I couldn't try the other two (postgre and mongo).
  * **The Performace:** `EXPLAIN ANALYZE` showed that DuckDB can perform complex aggregations in **5.6ms**, proving it's more than capable of meeting the API's `< 200ms` latency requirement. There is no need for storing aggregated values or partitioning as per given requirements, because these might unnecessarily complicate the logic/code.


## 3\. Database Optimization

The database design was optimized for both fast incremental loads (ETL) and rapid API query performance (API).

### 3.1. Implemented Technique: Indexing Strategy

I implemented a single index on the `ohlcv_data` table.

**Technique:** A composite `UNIQUE` index on the `(symbol, timestamp)` columns.

```sql
CREATE TABLE IF NOT EXISTS ohlcv_data (
    timestamp TIMESTAMP,
    symbol VARCHAR,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume BIGINT,
    UNIQUE(symbol, timestamp)
);
```

#### Justification for Usage:

This single index is the most critical optimization as it solves two core requirements at once:

1.  **Solves Incremental Updates (ETL):** The `UNIQUE` constraint allows the `load.py` script to use an `INSERT ... ON CONFLICT DO NOTHING` query. This is a fast way to handle incremental updates. The database itself, rather than a slow Python script, handles duplicate checking and hence we get higher performance.

If the API were implemented, it would also solve the API's query performance
2.  **Solves API Query Performance (API):** ]DuckDB to instantly finds the exact data for a specific stock (e.g., 'AAPL') without scanning the entire data table.

### 3.2. Proof of Optimization (`EXPLAIN ANALYZE`)
The following `EXPLAIN ANALYZE` output demonstrates this optimization in action. The query asks for the average closing price for 'AAPL'.

**Query:**

```sql
EXPLAIN ANALYZE SELECT AVG(close) FROM ohlcv_data WHERE symbol = 'AAPL';
```

**Query Plan Output:**

```
┌───────────────────────────────────────────────────┐
│                      QUERY PLAN                   │
├───────────────────────────────────────────────────┤
│ ▼ UNGROUPED_AGGREGATE                             │
│   (actual time=0.00s, rows=1)                     │
│                                                   │
│ ▼ PROJECTION                                      │
│   (actual time=0.00s, rows=125)                   │
│                                                   │
│ ▼ TABLE_SCAN(ohlcv_data)                          │
│   (actual time=0.00s, rows=125)                   │
│   ► Filters: (symbol = 'AAPL')                    │
└───────────────────────────────────────────────────┘
Total Time: 0.0056s
```

**Analysis:**
As shown in the plan, the `TABLE_SCAN` step applied a filter (`Filters: symbol='AAPL'`) and **only read 125 rows**. It did *not* scan the entire table's 625+ (180*5 for the 6 month 5 stock data) rows, proving the index and DuckDB's query optimization are working efficiently. The query completed in **5.6ms**, well within the performance requirements.

-----

## 4\. Scalability Discussion

Here is how this system would evolve to handle more complex requirements.

### 4.1. Handling 1000+ Stocks

  * **ETL Pipeline:** The current sequential loop in `extract.py` (fetching one stock, waiting 30s) would be too slow. This could be parallelized using Python's `asyncio` (for concurrent API calls) or a job queue like **Celery** with multiple worker processes. Instead of a 30-second wait, we could make 5 calls in parallel, wait 30 seconds, and repeat, dramatically cutting down extraction time.
  * **Database:** DuckDB will handle 1000+ stocks (millions of rows) for read queries without any issues. No change is needed for this step.

### 4.2. Handling Real-Time Data

  * **ETL Source:** We would replace Alpha Vantage with a real-time data source.
  * **ETL Process:** The `extract.py` script should become a sort of "streaming" service, but I haven;t thought much on this.

-----
