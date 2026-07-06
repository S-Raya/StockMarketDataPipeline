USE StockMarketDataDB;
GO

-- TransformOverview
CREATE OR ALTER PROCEDURE TransformOverview
    @Symbol NVARCHAR(10)
AS
BEGIN TRY
    SET NOCOUNT ON

    IF NOT EXISTS (SELECT 1 FROM staging.stg_overview WHERE Symbol = @Symbol)
    BEGIN
        RAISERROR ('No data found in staging for symbol: %s', 16, 1, @Symbol)
        RETURN
    END

    BEGIN TRANSACTION
    
        UPDATE warehouse.whs_overview
        SET
            is_current = 0
        WHERE Symbol = @Symbol AND is_current = 1

        INSERT INTO warehouse.whs_overview (Symbol, Name, Sector, Industry, Exchange, Currency, Country, MarketCapitalization, PERatio, EPS, BookValue, ProfitMargin, RevenueTTM, [52WeekHigh], [52WeekLow], Beta, is_current, fetched_at)
        SELECT TOP 1 
            Symbol, 
            Name, 
            Sector, 
            Industry, 
            Exchange, 
            Currency, 
            Country, 
            TRY_CAST(MarketCapitalization AS BIGINT), 
            TRY_CAST(PERatio AS DECIMAL(10,4)), 
            TRY_CAST(EPS AS DECIMAL(10,4)),
            TRY_CAST(BookValue AS DECIMAL(10,4)), 
            TRY_CAST(ProfitMargin AS DECIMAL(10,6)), 
            TRY_CAST(RevenueTTM AS BIGINT), 
            TRY_CAST([52WeekHigh] AS DECIMAL(10,4)), 
            TRY_CAST([52WeekLow] AS DECIMAL(10,4)), 
            TRY_CAST(Beta AS DECIMAL(10,4)), 
            1 AS is_current,
            fetched_at
        FROM staging.stg_overview 
        WHERE Symbol = @Symbol 
        ORDER BY fetched_at DESC
    COMMIT TRANSACTION    
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION

    DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE()
    RAISERROR(@ErrorMessage, 16, 1)
END CATCH;  
GO

-- TransformDailyPrice
CREATE OR ALTER PROCEDURE TransformDailyPrice
    @Symbol NVARCHAR(10)
AS
BEGIN TRY
    SET NOCOUNT ON

    IF NOT EXISTS (SELECT 1 FROM staging.stg_daily_price WHERE Symbol = @Symbol)
    BEGIN
        RAISERROR ('No data found in staging for symbol: %s', 16, 1, @Symbol)
        RETURN
    END

    BEGIN TRANSACTION
        -- Insert into the warehouse table from staging table
        INSERT INTO warehouse.whs_daily_price (Symbol, TradeDate, OpenPrice, HighPrice, LowPrice, ClosePrice, Volume, PriceChange, PriceChangePercent, DailyRange, IsBullish, MovingAvg7, MovingAvg20, MovingAvg50, fetched_at)
        SELECT 
            Symbol,
            TRY_CAST(TradeDate AS DATE),
            TRY_CAST(OpenPrice AS DECIMAL(18,4)),
            TRY_CAST(HighPrice AS DECIMAL(18,4)),
            TRY_CAST(LowPrice AS DECIMAL(18,4)),
            TRY_CAST(ClosePrice AS DECIMAL(18,4)),
            TRY_CAST(Volume AS BIGINT),
            NULL AS PriceChange,
            NULL AS PriceChangePercent,
            TRY_CAST(HighPrice AS DECIMAL(18,4)) - TRY_CAST(LowPrice AS DECIMAL(18,4)) AS DailyRange,
            CASE WHEN TRY_CAST(ClosePrice AS DECIMAL(18,4)) > TRY_CAST(OpenPrice AS DECIMAL(18,4)) THEN 1 ELSE 0 END AS IsBullish,
            NULL AS MovingAvg7,
            NULL AS MovingAvg20,
            NULL AS MovingAvg50,
            fetched_at
        FROM staging.stg_daily_price
        WHERE TRY_CAST(TradeDate AS DATE) NOT IN (SELECT TradeDate FROM warehouse.whs_daily_price WHERE Symbol = @Symbol) AND Symbol = @Symbol

        -- update the PriceChange, PriceChangePercent, and Moving Averages
        UPDATE w
        SET
            PriceChange = ClosePrice - PrevClose,
            PriceChangePercent = CASE WHEN PrevClose = 0 THEN NULL ELSE ((ClosePrice - PrevClose) / PrevClose) * 100 END,
            MovingAvg7 = MA7,
            MovingAvg20 = MA20,
            MovingAvg50 = MA50
        FROM warehouse.whs_daily_price w
        INNER JOIN (
            SELECT
                id,
                LAG(ClosePrice, 1) OVER (PARTITION BY Symbol ORDER BY TradeDate) AS PrevClose,
                AVG(ClosePrice) OVER (PARTITION BY Symbol ORDER BY TradeDate ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS MA7,
                AVG(ClosePrice) OVER (PARTITION BY Symbol ORDER BY TradeDate ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS MA20,
                AVG(ClosePrice) OVER (PARTITION BY Symbol ORDER BY TradeDate ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS MA50
            FROM warehouse.whs_daily_price
            WHERE Symbol = @Symbol
        ) calc ON w.id = calc.id
        WHERE w.Symbol = @Symbol
    COMMIT TRANSACTION
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION

    DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE()
    RAISERROR(@ErrorMessage, 16, 1)
END CATCH;  
GO