CREATE TABLE IF NOT EXISTS etf_prices (
    "Date" TIMESTAMP,
    "Symbol" VARCHAR(10),
    "Open" DOUBLE PRECISION,
    "High" DOUBLE PRECISION,
    "Low" DOUBLE PRECISION,
    "Close" DOUBLE PRECISION,
    "Volume" BIGINT,
    "MA_50" DOUBLE PRECISION,
    "MA_200" DOUBLE PRECISION,
    
    -- Clé primaire composée (pour éviter les doublons Date/Symbole)
    PRIMARY KEY ("Date", "Symbol")
);