import pyodbc
import os
from dotenv import load_dotenv
load_dotenv()

def log_to_db(processName, symbol, status, nProcessed, nInserted=0, nSkipped=0, errorMessage=None):
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

    conn = None
    cursor = None
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        query = """
            INSERT INTO log.etl_log (ProcessName, Symbol, Status, nProcessed, nInserted, nSkipped, ErrorMessage)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (processName, symbol, status, nProcessed, nInserted, nSkipped, errorMessage))
        conn.commit()
    except pyodbc.Error as e:
        print("Error logging to database:", e)
        if conn:
            print("Rolling back transaction...")
            conn.rollback()
    except Exception as e:
        print("Unexpected error:", e)
        if conn:
            print("Rolling back transaction...")
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
