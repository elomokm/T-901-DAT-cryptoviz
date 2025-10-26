-- =========================================================
-- CryptoViz - init.sql (TimescaleDB)
-- Tables + Hypertables + Continuous Aggregates
-- =========================================================

SET TIME ZONE 'UTC';

-- Extensions
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =======================
-- Table : news_events
-- =======================
CREATE TABLE IF NOT EXISTS news_events (
  id               BIGSERIAL      NOT NULL,
  url_hash         TEXT           NOT NULL,
  title            TEXT           NOT NULL,
  url              TEXT           NOT NULL,
  source           TEXT           NOT NULL,
  published_at     TIMESTAMPTZ    NOT NULL,   -- time column (hypertable)
  fetched_at       TIMESTAMPTZ    NOT NULL,
  tickers          TEXT[]         NOT NULL DEFAULT '{}',
  lang             TEXT,
  sentiment_score  REAL,
  inserted_at      TIMESTAMPTZ    NOT NULL DEFAULT now(),
  -- IMPORTANT : la PK inclut la colonne de partition
  CONSTRAINT news_events_pkey PRIMARY KEY (id, published_at),
  -- Unicité logique : inclure aussi la colonne temporelle
  CONSTRAINT uq_news_urlhash UNIQUE (url_hash, published_at)
);

-- Hypertable sur published_at
SELECT create_hypertable('news_events', 'published_at', if_not_exists => TRUE);

-- Index utiles (les uniques incluent la time col ; les non-uniques peuvent être libres)
CREATE INDEX IF NOT EXISTS idx_news_published_at
  ON news_events (published_at);
CREATE INDEX IF NOT EXISTS idx_news_source_published
  ON news_events (source, published_at);
-- Utile pour recherche par url_hash seule (non-unique, OK)
CREATE INDEX IF NOT EXISTS idx_news_url_hash_only
  ON news_events (url_hash);


-- =======================
-- Table : market_data
-- =======================
CREATE TABLE IF NOT EXISTS market_data (
  id                           BIGSERIAL       NOT NULL,
  asset_id                     TEXT            NOT NULL,   -- ex: 'bitcoin'
  symbol                       TEXT            NOT NULL,   -- ex: 'BTC'
  vs_currency                  TEXT            NOT NULL,   -- ex: 'usd'
  price                        DOUBLE PRECISION NOT NULL,
  price_change_percentage_24h  DOUBLE PRECISION,
  market_cap                   BIGINT,
  total_volume_24h             BIGINT,
  as_of                        TIMESTAMPTZ     NOT NULL,   -- time column (hypertable)
  fetched_at                   TIMESTAMPTZ     NOT NULL,
  source                       TEXT            NOT NULL DEFAULT 'coingecko',
  inserted_at                  TIMESTAMPTZ     NOT NULL DEFAULT now(),
  -- IMPORTANT : la PK inclut la colonne de partition
  CONSTRAINT market_data_pkey PRIMARY KEY (id, as_of),
  -- Ton unique métier inclut déjà la time col (OK)
  CONSTRAINT uq_market_unique UNIQUE (asset_id, vs_currency, as_of)
);

-- Hypertable sur as_of
SELECT create_hypertable('market_data', 'as_of', if_not_exists => TRUE);

-- Index utiles
CREATE INDEX IF NOT EXISTS idx_market_asof
  ON market_data (as_of);
CREATE INDEX IF NOT EXISTS idx_market_asset_asof
  ON market_data (asset_id, as_of);


-- =======================
-- Continuous Aggregates (CAGGs)
-- =======================

-- 1) Volume de news par heure
DROP MATERIALIZED VIEW IF EXISTS cagg_news_hour CASCADE;
CREATE MATERIALIZED VIEW cagg_news_hour
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 hour', published_at) AS ts_hour,
  count(*)::bigint AS news_count
FROM news_events
GROUP BY 1;

-- Politique de rafraîchissement (toutes les 5 min, fenêtre lookback 2 jours)
SELECT add_continuous_aggregate_policy('cagg_news_hour',
  start_offset => INTERVAL '2 days',
  end_offset   => INTERVAL '5 minutes',
  schedule_interval => INTERVAL '5 minutes');


-- 2) Prix moyen par minute et par actif
DROP MATERIALIZED VIEW IF EXISTS cagg_market_min CASCADE;
CREATE MATERIALIZED VIEW cagg_market_min
WITH (timescaledb.continuous) AS
SELECT
  asset_id,
  vs_currency,
  time_bucket('1 minute', as_of) AS ts_min,
  avg(price) AS price_avg
FROM market_data
GROUP BY asset_id, vs_currency, time_bucket('1 minute', as_of);

SELECT add_continuous_aggregate_policy('cagg_market_min',
  start_offset => INTERVAL '2 days',
  end_offset   => INTERVAL '2 minutes',
  schedule_interval => INTERVAL '1 minute');


-- =======================
-- Vues lisibles (option)
-- =======================

CREATE OR REPLACE VIEW v_news_volume_hour AS
SELECT * FROM cagg_news_hour ORDER BY ts_hour;

CREATE OR REPLACE VIEW v_market_price_min AS
SELECT * FROM cagg_market_min ORDER BY asset_id, ts_min;
