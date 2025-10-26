CREATE TABLE IF NOT EXISTS symbol_registry (
  symbol_canonique TEXT PRIMARY KEY,
  base TEXT NOT NULL,
  quote TEXT NOT NULL,
  aliases JSONB NOT NULL,
  enabled BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS candles_1m (
  symbol TEXT NOT NULL,
  window_start TIMESTAMPTZ NOT NULL,
  open NUMERIC NOT NULL,
  high NUMERIC NOT NULL,
  low NUMERIC NOT NULL,
  close NUMERIC NOT NULL,
  volume NUMERIC NOT NULL,
  sources_used TEXT[],
  quality_flags JSONB,
  PRIMARY KEY(symbol, window_start)
);

CREATE INDEX IF NOT EXISTS idx_candles_1m_symbol_ts ON candles_1m(symbol, window_start DESC);


CREATE TABLE IF NOT EXISTS candles_5m (LIKE candles_1m INCLUDING ALL);
ALTER TABLE candles_5m DROP CONSTRAINT candles_1m_pkey;
ALTER TABLE candles_5m ADD PRIMARY KEY(symbol, window_start);
SELECT create_hypertable('candles_5m', by_range('window_start'), if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS candles_1h (LIKE candles_1m INCLUDING ALL);
ALTER TABLE candles_1h DROP CONSTRAINT candles_1m_pkey;
ALTER TABLE candles_1h ADD PRIMARY KEY(symbol, window_start);
SELECT create_hypertable('candles_1h', by_range('window_start'), if_not_exists => TRUE);
