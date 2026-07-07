import json
from datetime import datetime
import pyodbc 
import os
from dotenv import load_dotenv
from utils import log_to_db
load_dotenv()
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--daily", help="load daily time series data", action="store_true")
parser.add_argument("--overview", help="load overview data", action="store_true")
args = parser.parse_args()

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

files = os.listdir("data/raw")

def get_latest_file(file_list):
    if not file_list:
        return None
    latest_file = max(file_list, key=lambda x: os.path.getmtime(os.path.join("data/raw", x)))
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


d1 = json.load(open(f"data/raw/{get_latest_file([f for f in files if 'data_TIME_SERIES_DAILY_' in f])}", "r", encoding="utf-8"))
d2 = json.load(open(f"data/raw/{get_latest_file([f for f in files if 'data_OVERVIEW_' in f])}", "r", encoding="utf-8"))
dt_object1 = construct_datetime_from_filedate(*split_date_from_daily_file(get_latest_file([f for f in files if 'data_TIME_SERIES_DAILY_' in f])))
dt_object2 = construct_datetime_from_filedate(*split_date_from_overview_file(get_latest_file([f for f in files if 'data_OVERVIEW_' in f])))

def load_daily_price_to_staging(data, dt_object):
    conn = None
    cursor = None
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        Symbol= data["Meta Data"]["2. Symbol"]
        for date, price in data["Time Series (Daily)"].items():
            Symbol= data["Meta Data"]["2. Symbol"]
            TradeDate= date
            OpenPrice= price["1. open"]
            HighPrice= price["2. high"]
            LowPrice= price["3. low"]
            ClosePrice= price["4. close"]
            Volume= price["5. volume"]
            fetched_at= dt_object
            cursor.execute("INSERT INTO staging.stg_daily_price (Symbol, TradeDate, OpenPrice, HighPrice, LowPrice, ClosePrice, Volume, fetched_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", Symbol, TradeDate, OpenPrice, HighPrice, LowPrice, ClosePrice, Volume, fetched_at)
        
        log_to_db("Load daily price to staging", Symbol, "Success", len(data["Time Series (Daily)"]), len(data["Time Series (Daily)"]), 0, None)

    except pyodbc.Error as e:
        log_to_db("Load daily price to staging", Symbol, "Failed", 0, 0, 0, str(e))
        print(f"Database error occurred: {e}")
        if conn:
            print("Rolling back transaction...")
            conn.rollback()
    except Exception as e:
        log_to_db("Load daily price to staging", Symbol, "Failed", 0, 0, 0, str(e))
        print(f"An unexpected error occurred: {e}")
        if conn:
            conn.rollback()
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
        cursor.execute(query,Value)
        log_to_db("Load overview to staging", data.get("Symbol", "N/A"), "Success", 1, 1, 0, None)

    except pyodbc.Error as e:
        log_to_db("Load overview to staging", data.get("Symbol", "N/A"), "Failed", 0, 0, 0, str(e))
        print(f"Database error occurred: {e}")
        if conn:
            print("Rolling back transaction...")
            conn.rollback()
    except Exception as e:
        log_to_db("Load overview to staging", data.get("Symbol", "N/A"), "Failed", 0, 0, 0, str(e))
        print(f"An unexpected error occurred: {e}")
        if conn:
            conn.rollback()
    else:
        conn.commit()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if (args.overview and args.daily) or (not args.overview and not args.daily):
    load_daily_price_to_staging(d1, dt_object1)
    load_overview_to_staging(d2, dt_object2)
elif args.daily:
    load_daily_price_to_staging(d1, dt_object1)
elif args.overview:
    load_overview_to_staging(d2, dt_object2)


