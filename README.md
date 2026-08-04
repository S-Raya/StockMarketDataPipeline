# Stock Market Data Pipeline

## Overview

A batch ETL pipeline that extracts, transforms, and loads stock market data from the Alpha Vantage API into a structured SQL Server data warehouse. The pipeline currently tracks **MSFT (Microsoft)**, designed for single-symbol operation and extensible to multiple symbols.

Data collected includes daily price data (OHLCV) and company fundamental overview. This project was built as a portfolio piece demonstrating data engineering fundamentals, and is designed around a small research team use case — providing a consistent, validated, and queryable historical stock data store that eliminates the need for manual data collection from multiple sources.

The pipeline is orchestrated end-to-end with **Apache Airflow**, running on a fully containerized stack (SQL Server, Airflow metadata database, webserver, and scheduler).

## Architecture

The pipeline follows a layered ETL architecture across three database schemas: **staging** (raw data landing zone), **warehouse** (cleaned and transformed data), and **log** (pipeline monitoring). Each stage is orchestrated as a task in an Airflow DAG.

```
Extract (Alpha Vantage) → Save Raw JSON → Load to Staging → Transform (stored procedure) → Data Warehouse
                                                                      ↑
                                                        Orchestrated by Apache Airflow
```

For detailed diagrams, see:
- [`docs/dataFlow.md`](docs/dataFlow.md) — Pipeline flow diagram
- [`docs/erd.md`](docs/erd.md) — Entity Relationship Diagram

## Tech Stack

| Component | Technology |
|---|---|
| Database | Microsoft SQL Server 2022 (via Docker) |
| Orchestration | Apache Airflow 2.9.2 (via Docker) |
| Airflow Metadata DB | PostgreSQL 13 (via Docker) |
| Languages | Python 3, T-SQL |
| Python Libraries | See `requirements.txt` (pipeline) and `requirements-airflow.txt` (Airflow image) |
| Containerization | Docker Desktop |
| Data Source | Alpha Vantage API (free tier) |
| Version Control | Git / GitHub |

## Prerequisites

- Python 3.14.5+
- Docker Desktop
- Alpha Vantage API key — register and obtain a free API key at [https://www.alphavantage.co/documentation/](https://www.alphavantage.co/documentation/)
- Microsoft ODBC Driver 18 for SQL Server — installed automatically inside the Airflow container via `Dockerfile.airflow`; only required on your host machine if you plan to query SQL Server directly (e.g. via a local SQL client or extension). Download from [Microsoft's official site](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server) if needed.

## Setup & Installation

**1. Clone the repository**
```bash
git clone https://github.com/S-Raya/StockMarketDataPipeline.git
cd StockMarketDataPipeline
```

**2. Create and activate virtual environment** *(optional — only needed if you want to run pipeline scripts locally outside of Airflow, e.g. for development/debugging)*
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
```

**3. Install dependencies** *(optional, see note above)*
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

**5. Build and start the full stack** (SQL Server, Airflow metadata DB, webserver, scheduler)
```bash
docker compose build
docker compose up init-airflow        # one-time: initializes Airflow DB, admin user, and SQL Server connection
docker compose up -d sqlserver webserver scheduler
```

**6. Initialize the SQL Server database**

Run the SQL scripts in the following order using your preferred SQL client (e.g. VS Code MSSQL extension):
```
sql/create_database.sql
sql/create_schema.sql
sql/create_staging_table.sql
sql/create_warehouse_table.sql
sql/create_log_table.sql
sql/stored_procedures.sql
```

**7. Access the Airflow UI**

Open [http://localhost:8080](http://localhost:8080) and log in with the admin credentials created in step 5 (`airflow` / `password` by default — change this for anything beyond local development). The `mssql_stockdb` connection and `stock_market_pipeline` DAG should already be available.

## How to Run

**Automated (recommended):** The DAG `stock_market_pipeline` (defined in `airflow/dags/stock_pipeline_dag.py`) runs on a schedule (weekdays after US market close) and can also be triggered manually from the Airflow UI or CLI:
```bash
docker exec -it stockmarketdatapipeline-scheduler-1 airflow dags trigger stock_market_pipeline
```

**Manual (for local development/debugging):** All scripts must be run from the **root directory** of the project.

```bash
# Full pipeline (extract → load → transform)
python src/run_pipeline.py

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

## Orchestration (Apache Airflow)

The pipeline is orchestrated by a single DAG, `stock_market_pipeline`, structured in three task groups:

1. **extract** — pulls raw daily price and company overview data from Alpha Vantage
2. **load_to_staging** — loads the raw JSON into the `staging` schema
3. **transform** — calls the `TransformDailyPrice` and `TransformOverview` stored procedures to populate the `warehouse` schema

```
extract_daily     → load_daily     → transform_daily_price
extract_overview  → load_overview  → transform_overview
```

The Airflow stack runs as a custom image (`Dockerfile.airflow`, based on `apache/airflow:2.9.2`) with the Microsoft ODBC Driver 18 and `apache-airflow-providers-microsoft-mssql` installed, allowing Airflow to connect directly to the SQL Server warehouse to trigger transformations.

## Known Limitations

- **Raw price data (non-adjusted)**: The free tier of Alpha Vantage does not provide split/dividend-adjusted closing prices (`TIME_SERIES_DAILY_ADJUSTED` is a premium endpoint). As a result, metrics such as `PriceChange` and moving averages may be distorted on dates where a stock split occurred. Mitigation: verify data quality manually if anomalous price movements are detected.
- **100-day history limit**: The free tier only returns the latest 100 trading days (`outputsize=compact`). Moving average columns (`MovingAvg20`, `MovingAvg50`) will have fewer valid data points for shorter windows.
- **Single symbol**: The pipeline currently processes one symbol at a time, configured via the `SYMBOL` variable in `.env` and the DAG's `SYMBOL` constant.
- **Local-only orchestration**: Airflow runs via Docker Compose on a single machine; there is no remote/cloud deployment (e.g. managed Airflow, Kubernetes) yet.

## Future Improvements

- [ ] Add support for multiple symbols
- [ ] Expand warehouse metrics
- [ ] Add a data visualization layer
- [ ] Add Airflow SLAs / alerting (e.g. email or Slack on task failure)
- [ ] Deploy Airflow to a cloud environment instead of local Docker Compose