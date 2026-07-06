USE StockMarketDataDB;
GO

IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES 
               WHERE TABLE_SCHEMA = 'staging' 
               AND TABLE_NAME = 'stg_daily_price')
BEGIN
    CREATE TABLE staging.stg_daily_price(
	id bigint IDENTITY(1,1) NOT NULL PRIMARY KEY,
	Symbol nvarchar(50) NULL,
	TradeDate nvarchar(20) NULL,
	OpenPrice nvarchar(50) NULL,
	HighPrice nvarchar(50) NULL,
	LowPrice nvarchar(50) NULL,
	ClosePrice nvarchar(50) NULL,
	Volume nvarchar(50) NULL,
	fetched_at datetime2 NOT NULL,
	created_at datetime2 NOT NULL DEFAULT GETDATE()
)
END
GO


IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES 
               WHERE TABLE_SCHEMA = 'staging' 
               AND TABLE_NAME = 'stg_overview')
BEGIN
    CREATE TABLE staging.stg_overview (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,

    Symbol NVARCHAR(50),
    AssetType NVARCHAR(100),
    Name NVARCHAR(255),
    Description NVARCHAR(MAX),

    CIK NVARCHAR(50),
    Exchange NVARCHAR(100),
    Currency NVARCHAR(20),
    Country NVARCHAR(100),
    Sector NVARCHAR(100),
    Industry NVARCHAR(255),

    Address NVARCHAR(500),
    OfficialSite NVARCHAR(255),

    FiscalYearEnd NVARCHAR(50),
    LatestQuarter NVARCHAR(50),

    MarketCapitalization NVARCHAR(50),
    EBITDA NVARCHAR(50),

    PERatio NVARCHAR(50),
    PEGRatio NVARCHAR(50),
    BookValue NVARCHAR(50),

    DividendPerShare NVARCHAR(50),
    DividendYield NVARCHAR(50),

    EPS NVARCHAR(50),
    RevenuePerShareTTM NVARCHAR(50),

    ProfitMargin NVARCHAR(50),
    OperatingMarginTTM NVARCHAR(50),
    ReturnOnAssetsTTM NVARCHAR(50),
    ReturnOnEquityTTM NVARCHAR(50),

    RevenueTTM NVARCHAR(50),
    GrossProfitTTM NVARCHAR(50),

    DilutedEPSTTM NVARCHAR(50),

    QuarterlyEarningsGrowthYOY NVARCHAR(50),
    QuarterlyRevenueGrowthYOY NVARCHAR(50),

    AnalystTargetPrice NVARCHAR(50),

    AnalystRatingStrongBuy NVARCHAR(50),
    AnalystRatingBuy NVARCHAR(50),
    AnalystRatingHold NVARCHAR(50),
    AnalystRatingSell NVARCHAR(50),
    AnalystRatingStrongSell NVARCHAR(50),

    TrailingPE NVARCHAR(50),
    ForwardPE NVARCHAR(50),

    PriceToSalesRatioTTM NVARCHAR(50),
    PriceToBookRatio NVARCHAR(50),

    EVToRevenue NVARCHAR(50),
    EVToEBITDA NVARCHAR(50),

    Beta NVARCHAR(50),

    [52WeekHigh] NVARCHAR(50),
    [52WeekLow] NVARCHAR(50),

    [50DayMovingAverage] NVARCHAR(50),
    [200DayMovingAverage] NVARCHAR(50),

    SharesOutstanding NVARCHAR(50),
    SharesFloat NVARCHAR(50),

    PercentInsiders NVARCHAR(50),
    PercentInstitutions NVARCHAR(50),

    DividendDate NVARCHAR(50),
    ExDividendDate NVARCHAR(50),

	fetched_at DATETIME2 NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE()
);
END
GO