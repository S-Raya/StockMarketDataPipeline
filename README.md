# Stock Market Data Pipeline

## Overview

A batch ETL pipeline that extracts, transforms, and loads stock market data from the Alpha Vantage API into a structured SQL Server data warehouse. The pipeline currently tracks **MSFT (Microsoft)**, designed for single-symbol operation and extensible to multiple symbols.

Data collected includes daily price data (OHLCV) and company fundamental overview. This project was built as a portfolio piece demonstrating data engineering fundamentals, and is designed around a small research team use case — providing a consistent, validated, and queryable historical stock data store that eliminates the need for manual data collection from multiple sources.

## Architecture

The pipeline follows a layered ETL architecture across three database schemas: **staging** (raw data landing zone), **warehouse** (cleaned and transformed data), and **log** (pipeline monitoring).

```
Extract → Save Raw JSON → Load to Staging → Transform → Data Warehouse
```

For detailed diagrams, see:
- [`docs/dataFlow.md`](docs/dataFlow.md) — Pipeline flow diagram
- [`docs/erd.md`](docs/erd.md) — Entity Relationship Diagram

## Tech Stack

| Component | Technology |
|---|---|
| Database | Microsoft SQL Server 2022 (via Docker) |
| Languages | Python 3, T-SQL |
| Python Libraries | See `requirements.txt` |
| Containerization | Docker Desktop 4.34.2 |
| Data Source | Alpha Vantage API (free tier) |
| Version Control | Git / GitHub |

## Prerequisites

- Python 3.14.5+
- Docker Desktop 4.34.2+
- Alpha Vantage API key — register and obtain a free API key at [https://www.alphavantage.co/documentation/](https://www.alphavantage.co/documentation/)
- Microsoft ODBC Driver 18 for SQL Server — download from [Microsoft's official site](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

## Setup & Installation

**1. Clone the repository**
```bash
git clone https://github.com/S-Raya/StockMarketDataPipeline.git
cd StockMarketDataPipeline
```

**2. Create and activate virtual environment**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

Create a `.env` file in the root directory with the following variables:
```
API_KEY=your_alpha_vantage_api_key
SYMBOL=MSFT
API_URL=https://www.alphavantage.co/query
FUNCTION1=TIME_SERIES_DAILY
FUNCTION2=OVERVIEW
SERVER=localhost
DATABASE=StockMarketDataDB
MSSQL_SA_USERNAME=sa
MSSQL_SA_PASSWORD=your_password
```

**5. Start SQL Server container**
```bash
docker-compose up -d
```

**6. Initialize the database**

Run the SQL scripts in the following order using your preferred SQL client (e.g. VS Code SQL Server extension):
```
sql/create_database.sql
sql/create_schema.sql
sql/create_staging_table.sql
sql/create_warehouse_table.sql
sql/create_log_table.sql
sql/stored_procedures.sql
```

## How to Run

All scripts must be run from the **root directory** of the project.

**Run the full pipeline (extract → load → transform):**
```bash
python src/run_pipeline.py
```

**Run individual steps:**
```bash
# Extract only
python src/extract.py --daily
python src/extract.py --overview
python src/extract.py  # both

# Load to staging only
python src/load_raw_to_stg.py --daily
python src/load_raw_to_stg.py --overview
python src/load_raw_to_stg.py  # both

# Monitor pipeline runs
SELECT * FROM log.etl_log ORDER BY DateTime DESC
```

## Database Schema

The database consists of three schemas:

- **staging** — raw data from the API, stored as-is with minimal transformation (`stg_daily_price`, `stg_overview`)
- **warehouse** — cleaned and transformed data with derived metrics (`whs_daily_price`, `whs_overview`)
- **log** — pipeline execution history for monitoring and troubleshooting (`etl_log`)

See [`docs/erd.md`](docs/erd.md) for the full Entity Relationship Diagram.

## Known Limitations

- **Raw price data (non-adjusted)**: The free tier of Alpha Vantage does not provide split/dividend-adjusted closing prices (`TIME_SERIES_DAILY_ADJUSTED` is a premium endpoint). As a result, metrics such as `PriceChange` and moving averages may be distorted on dates where a stock split occurred. Mitigation: verify data quality manually if anomalous price movements are detected.
- **100-day history limit**: The free tier only returns the latest 100 trading days (`outputsize=compact`). Moving average columns (`MovingAvg20`, `MovingAvg50`) will have fewer valid data points for shorter windows.
- **Single symbol**: The pipeline currently processes one symbol at a time, configured via the `SYMBOL` variable in `.env`.
- **Manual scheduling**: The pipeline must be triggered manually. Automated scheduling (e.g. Apache Airflow) is not yet implemented.

## Future Improvements

- [ ] Add support for multiple symbols
- [ ] Integrate Apache Airflow for automated scheduling
- [ ] Expand warehouse metrics
- [ ] Add a data visualization layer