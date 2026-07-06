USE StockMarketDataDB;
GO

IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES 
               WHERE TABLE_SCHEMA = 'warehouse' 
               AND TABLE_NAME = 'whs_daily_price')
BEGIN
    CREATE TABLE warehouse.whs_daily_price (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    Symbol      NVARCHAR(20)     NOT NULL,
    TradeDate   DATE             NOT NULL,
    OpenPrice   DECIMAL(18,4)    NOT NULL,
    HighPrice   DECIMAL(18,4)    NOT NULL,
    LowPrice    DECIMAL(18,4)    NOT NULL,
    ClosePrice  DECIMAL(18,4)    NOT NULL,
    Volume      BIGINT           NOT NULL,

    PriceChange         DECIMAL(18,4) NULL,
    PriceChangePercent  DECIMAL(9,2)  NULL,
    DailyRange          DECIMAL(18,4) NOT NULL,
    IsBullish           BIT NOT NULL,
    MovingAvg7 DECIMAL(18,4) NULL,
    MovingAvg20 DECIMAL(18,4) NULL,
    MovingAvg50 DECIMAL(18,4) NULL,

    fetched_at  DATETIME2        NOT NULL,
    created_at  DATETIME2        NOT NULL DEFAULT GETDATE()
);
END
GO

IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES 
               WHERE TABLE_SCHEMA = 'warehouse' 
               AND TABLE_NAME = 'whs_overview')
BEGIN
    CREATE TABLE warehouse.whs_overview (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    Symbol                          NVARCHAR(50)    NOT NULL,
    Name                            NVARCHAR(255)    NOT NULL,
    Sector                          NVARCHAR(50)    NOT NULL,
    Industry                        NVARCHAR(50)    NOT NULL,
    Exchange                        NVARCHAR(50)    NOT NULL,
    Currency                        NVARCHAR(50)    NOT NULL,
    Country                         NVARCHAR(50)    NOT NULL,
    MarketCapitalization            BIGINT,
    PERatio                         DECIMAL(10,4),
    EPS                             DECIMAL(10,4),
    BookValue                       DECIMAL(10,4),
    ProfitMargin                    DECIMAL(10,6),
    RevenueTTM                      BIGINT,
    [52WeekHigh]                    DECIMAL(10,4),
    [52WeekLow]                     DECIMAL(10,4),
    Beta                            DECIMAL(10,4),
    is_current                      BIT             NOT NULL    DEFAULT 1,
    fetched_at                      DATETIME2        NOT NULL,
    created_at                      DATETIME2        NOT NULL    DEFAULT GETDATE()
);
END
GO