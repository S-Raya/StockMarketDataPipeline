from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.microsoft.mssql.operators.mssql import MsSqlOperator
from airflow.utils.task_group import TaskGroup
import os
from dotenv import load_dotenv
load_dotenv()

PROJECT_DIR = "/opt/airflow/project"   # Project Path (Airflow Project Volume)
MSSQL_CONN_ID = "mssql_stockdb"
SYMBOL = os.getenv("SYMBOL")
EXTRACT_DELAY_SECONDS = 7

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

with DAG(
    dag_id="stock_market_pipeline5",
    description="Extract -> Load -> Transform pipeline untuk StockMarketDataPipeline (MSFT)",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval="15 22 * * 1-5", # UTC 
    catchup=False,
    max_active_runs=1,
    tags=["stock-market", "etl", "portfolio"],
) as dag:
    with TaskGroup("extract") as extract_group: # Extract
        extract_daily = BashOperator(
            task_id="extract_daily",
            bash_command=f"cd {PROJECT_DIR} && python src/extract.py --daily",
        )

        wait = BashOperator(
            task_id="wait",
            bash_command=f"sleep {EXTRACT_DELAY_SECONDS}",
        )

        extract_overview = BashOperator(
            task_id="extract_overview",
            bash_command=f"cd {PROJECT_DIR} && python src/extract.py --overview",
        )

    with TaskGroup("load_to_staging") as load_group: # Staging
        load_daily = BashOperator(
            task_id="load_daily",
            bash_command=f"cd {PROJECT_DIR} && python src/load_raw_to_stg.py --daily",
        )

        load_overview = BashOperator(
            task_id="load_overview",
            bash_command=f"cd {PROJECT_DIR} && python src/load_raw_to_stg.py --overview",
        )

    with TaskGroup("transform_and_load_to_warehouse") as transform_group: # Transform & Load
        transform_daily_price = MsSqlOperator(
            task_id="transform_daily_price",
            mssql_conn_id=MSSQL_CONN_ID,
            sql="EXEC TransformDailyPrice @Symbol = %(symbol)s;",
            parameters={"symbol": SYMBOL},
        )

        transform_overview = MsSqlOperator(
            task_id="transform_overview",
            mssql_conn_id=MSSQL_CONN_ID,
            sql="EXEC TransformOverview @Symbol = %(symbol)s;",
            parameters={"symbol": SYMBOL},
        )

    extract_daily >> load_daily >> transform_daily_price
    wait >> extract_overview >> load_overview >> transform_overview # Wait before requesting overview to avoid API rate limit issues