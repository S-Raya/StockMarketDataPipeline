import pyodbc 
import os
from dotenv import load_dotenv
from utils import log_to_db
load_dotenv()

from extract import fetch_data
from load_raw_to_stg import get_data_and_timestamp, load_daily_price_to_staging, load_overview_to_staging

# import argparse

# parser = argparse.ArgumentParser()
# parser.add_argument("--daily", help="load daily time series data", action="store_true")
# parser.add_argument("--overview", help="load overview data", action="store_true")
# args = parser.parse_args()

api_key = os.getenv("API_KEY")
symbol = os.getenv("SYMBOL")
url = os.getenv("API_URL")
function1 = os.getenv("FUNCTION1")
function2 = os.getenv("FUNCTION2")
server=os.getenv("SERVER")
database=os.getenv("DATABASE")
uid=os.getenv("MSSQL_SA_USERNAME")
pwd=os.getenv("MSSQL_SA_PASSWORD")
conn_str = (
r'DRIVER={ODBC Driver 18 for SQL Server};'
f'SERVER={server};'
f'DATABASE={database};'
f'UID={uid};'
f'PWD={pwd};'
r'TrustServerCertificate=yes;'
)

def run_extract():
    param1 = {
        "function": function1,
        "symbol": symbol,
        "apikey": api_key
    }
    param2 = {
        "function": function2,
        "symbol": symbol,
        "apikey": api_key
    }
    fetch_data(url, param1)
    fetch_data(url, param2)

def run_load():
    data_daily, dt_object_daily, data_overview, dt_object_overview = get_data_and_timestamp()
    load_daily_price_to_staging(data_daily, dt_object_daily)
    load_overview_to_staging(data_overview, dt_object_overview)

def run_transform():
    conn = None
    cursor = None
    try:
        conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()
        cursor.execute("EXEC TransformDailyPrice ?", symbol)
        cursor.execute("EXEC TransformOverview ?", symbol)
    except pyodbc.Error as e:
        log_to_db("Run Transform", symbol, "Failed", 0, 0, 0, str(e))
        print(f"Database error occurred: {e}")
        if conn:
            print("Rolling back transaction...")
            conn.rollback()
    except Exception as e:
        log_to_db("Run Transform", symbol, "Failed", 0, 0, 0, str(e))
        print(f"An unexpected error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    run_extract()
    run_load()
    run_transform()