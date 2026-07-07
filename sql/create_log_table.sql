USE StockMarketDataDB;
GO

IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES 
               WHERE TABLE_SCHEMA = 'log' 
               AND TABLE_NAME = 'etl_log')
BEGIN
    CREATE TABLE log.etl_log(
	id BIGINT IDENTITY(1,1) PRIMARY KEY,
    ProcessName NVARCHAR(50) NOT NULL,
    Symbol NVARCHAR(10) NULL,
    Status NVARCHAR(10) NOT NULL,
    nProcessed INT NULL,
    nInserted INT NULL,
    nSkipped INT NULL,
    DateTime DATETIME2 NOT NULL DEFAULT GETDATE(),
    ErrorMessage NVARCHAR(MAX) NULL
)
END
GO