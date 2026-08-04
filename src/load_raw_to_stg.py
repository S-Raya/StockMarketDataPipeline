import json
from datetime import datetime
import pyodbc
import os
import time
from dotenv import load_dotenv
from utils import log_to_db
import argparse

load_dotenv()
server = os.getenv("SERVER")
database = os.getenv("DATABASE")
uid = os.getenv("MSSQL_SA_USERNAME")
pwd = os.getenv("MSSQL_SA_PASSWORD")

conn_str = (
    r'DRIVER={ODBC Driver 18 for SQL Server};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'UID={uid};'
    f'PWD={pwd};'
    r'TrustServerCertificate=yes;'
    r'Timeout=30;'
)


def get_latest_file(file_list):
    if not file_list:
        return None
    latest_file = max(file_list)
    return latest_file


def split_date_from_daily_file(filename):
    dateSplit = filename.split('_')
    yy = dateSplit[4].strip()
    mo = dateSplit[5].strip()
    dd = dateSplit[6].strip()
    hh = dateSplit[7].strip()
    mm = dateSplit[8].replace('.json', '').strip()
    return yy, mo, dd, hh, mm


def split_date_from_overview_file(filename):
    dateSplit = filename.split('_')
    yy = dateSplit[2].strip()
    mo = dateSplit[3].strip()
    dd = dateSplit[4].strip()
    hh = dateSplit[5].strip()
    mm = dateSplit[6].replace('.json', '').strip()
    return yy, mo, dd, hh, mm


def construct_datetime_from_filedate(yy, mo, dd, hh, mm):
    date_string = f"{yy}-{mo}-{dd} {hh}:{mm}:00"
    format = "%Y-%m-%d %H:%M:%S"
    dt_object = datetime.strptime(date_string, format)
    return dt_object


def get_data_and_timestamp():
    files = os.listdir("data/raw")

    latest_daily_file = get_latest_file([f for f in files if 'data_TIME_SERIES_DAILY_' in f])
    latest_overview_file = get_latest_file([f for f in files if 'data_OVERVIEW_' in f])

    if latest_daily_file is None:
        raise FileNotFoundError("No 'data_TIME_SERIES_DAILY_*' file found in data/raw")
    if latest_overview_file is None:
        raise FileNotFoundError("No 'data_OVERVIEW_*' file found in data/raw")

    data_daily = json.load(open(f"data/raw/{latest_daily_file}", "r", encoding="utf-8"))
    data_overview = json.load(open(f"data/raw/{latest_overview_file}", "r", encoding="utf-8"))
    dt_object_daily = construct_datetime_from_filedate(*split_date_from_daily_file(latest_daily_file))
    dt_object_overview = construct_datetime_from_filedate(*split_date_from_overview_file(latest_overview_file))

    return data_daily, dt_object_daily, data_overview, dt_object_overview


def _safe_log_to_db(*args, **kwargs):
    # Wrapper so that a log_to_db failure doesn't hide the original exception.
    try:
        log_to_db(*args, **kwargs)
    except Exception as log_err:
        print(f"Failed to write log to DB: {log_err}")


def load_daily_price_to_staging(data, dt_object):
    conn = None
    cursor = None
    Symbol = data["Meta Data"]["2. Symbol"]

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        for date, price in data["Time Series (Daily)"].items():
            TradeDate = date
            OpenPrice = price["1. open"]
            HighPrice = price["2. high"]
            LowPrice = price["3. low"]
            ClosePrice = price["4. close"]
            Volume = price["5. volume"]
            fetched_at = dt_object
            cursor.execute(
                "INSERT INTO staging.stg_daily_price "
                "(Symbol, TradeDate, OpenPrice, HighPrice, LowPrice, ClosePrice, Volume, fetched_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                Symbol, TradeDate, OpenPrice, HighPrice, LowPrice, ClosePrice, Volume, fetched_at
            )
        _safe_log_to_db(
            "Load daily price to staging", Symbol, "Success",
            len(data["Time Series (Daily)"]), len(data["Time Series (Daily)"]), 0, None
        )

    except pyodbc.Error as e:
        print(f"Database error occurred: {e}")
        _safe_log_to_db("Load daily price to staging", Symbol, "Failed", 0, 0, 0, str(e))
        if conn:
            print("Rolling back transaction...")
            conn.rollback()
        raise  # re-raise so Airflow marks this task as failed instead of succeeded

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        _safe_log_to_db("Load daily price to staging", Symbol, "Failed", 0, 0, 0, str(e))
        if conn:
            conn.rollback()
        raise  # re-raise so the task actually fails in Airflow

    else:
        conn.commit()

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def load_overview_to_staging(data, dt_object):
    conn = None
    cursor = None
    Symbol = data.get("Symbol", "N/A")

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        Keys = data.keys()
        Value = list(data.values())
        Value.append(dt_object)
        collumn = []
        for i in Keys:
            if i[0].isdigit():
                collumn.append(f"[{i}]")
            else:
                collumn.append(i)

        collumn.append("fetched_at")
        collumns = ", ".join(collumn)
        q = ["?"] * (len(Keys) + 1)
        qm = ", ".join(q)
        query = f"INSERT INTO staging.stg_overview ({collumns}) VALUES ({qm})"
        cursor.execute(query, Value)

        _safe_log_to_db("Load overview to staging", Symbol, "Success", 1, 1, 0, None)

    except pyodbc.Error as e:
        print(f"Database error occurred: {e}")
        _safe_log_to_db("Load overview to staging", Symbol, "Failed", 0, 0, 0, str(e))
        if conn:
            print("Rolling back transaction...")
            conn.rollback()
        raise  # re-raise so Airflow marks this task as failed

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        _safe_log_to_db("Load overview to staging", Symbol, "Failed", 0, 0, 0, str(e))
        if conn:
            conn.rollback()
        raise  # re-raise so the task actually fails in Airflow

    else:
        conn.commit()

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--daily", help="load daily time series data", action="store_true")
    parser.add_argument("--overview", help="load overview data", action="store_true")
    args = parser.parse_args()

    data_daily, dt_object_daily, data_overview, dt_object_overview = get_data_and_timestamp()

    if (args.overview and args.daily) or (not args.overview and not args.daily):
        load_daily_price_to_staging(data_daily, dt_object_daily)
        time.sleep(5)
        load_overview_to_staging(data_overview, dt_object_overview)
    elif args.daily:
        load_daily_price_to_staging(data_daily, dt_object_daily)
    elif args.overview:
        load_overview_to_staging(data_overview, dt_object_overview)