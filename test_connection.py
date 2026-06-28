import pyodbc 
import os
from dotenv import load_dotenv
import pandas as pd

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

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

df = pd.read_sql_query('SELECT * FROM staging.stg_daily_price', conn)

print(df.head())

cursor.close()
conn.close()