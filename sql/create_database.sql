IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'StockMarketDataDB')
    CREATE DATABASE StockMarketDataDB
GO