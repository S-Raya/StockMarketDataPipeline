import pyodbc 
import os
from dotenv import load_dotenv

load_dotenv()

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
try:
    with pyodbc.connect(conn_str, timeout=5) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
        if result:
            print("Connection Successful")
            
except pyodbc.Error as e:
    print("Connection failed")
    print(f"Error: {e}")
finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()