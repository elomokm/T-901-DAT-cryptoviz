-- ==========================
-- 0) Préambule & extensions
-- ==========================
CREATE SCHEMA IF NOT EXISTS cryptoviz;

-- Extensions utiles (optionnelles mais recommandées)
CREATE EXTENSION IF NOT EXISTS pgcrypto;     -- pour digest() si besoin
CREATE EXTENSION IF NOT EXISTS pg_trgm;      -- recherche full-text approximative sur titre
-- TimescaleDB si disponible (sinon tout marche en "vanilla")
DO $$
BEGIN
  PERFORM 1 FROM pg_extension WHERE extname = 'timescaledb';
  IF NOT FOUND THEN
    RAISE NOTICE 'TimescaleDB non détecté, mode PostgreSQL standard.';
  ELSE
    RAISE NOTICE 'TimescaleDB détecté, hypertables et continuous aggregates activables.';
  END IF;
END$$;

-- ==========================
-- 1) Types & tables de référence
-- ==========================

-- Type de source d'info pour news
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'source_kind') THEN
    CREATE TYPE cryptoviz.source_kind AS ENUM ('rss', 'api', 'social', 'manual');
  END IF;
END$$;

-- Référentiel des symboles (tickers)
CREATE TABLE IF NOT EXISTS cryptoviz.symbols (
  symbol        TEXT PRIMARY KEY,                  -- ex. 'BTC', 'ETH'
  name          TEXT NOT NULL,                     -- ex. 'Bitcoin'
  coingecko_id  TEXT,                              -- id source prix (pour ingestion)
  cmc_id        TEXT,                              -- optionnel: CoinMarketCap id
  is_active     BOOLEAN NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Référentiel des sources (news)
CREATE TABLE IF NOT EXISTS cryptoviz.sources (
  source_id     BIGSERIAL PRIMARY KEY,
  name          TEXT NOT NULL,                     -- ex. 'CoinDesk'
  kind          cryptoviz.source_kind NOT NULL,    -- rss/api/social/manual
  base_url      TEXT,                              -- ex. 'https://www.coindesk.com'
  is_active     BOOLEAN NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (name, kind)
);

-- ==========================
-- 2) News & tagging des symboles
-- ==========================

-- Événements "news"
CREATE TABLE IF NOT EXISTS cryptoviz.news_events (
  news_id         BIGSERIAL PRIMARY KEY,
  source_id       BIGINT NOT NULL REFERENCES cryptoviz.sources(source_id) ON DELETE RESTRICT,
  external_id     TEXT,                           -- id fourni par l'API/RSS si dispo
  title           TEXT NOT NULL,
  url             TEXT NOT NULL,
  url_hash        TEXT GENERATED ALWAYS AS (md5(url)) STORED, -- idempotence
  summary         TEXT,                           -- résumé nettoyé
  language        TEXT,                           -- ex. 'en', 'fr'
  published_at    TIMESTAMPTZ NOT NULL,           -- date de publication de la source
  collected_at    TIMESTAMPTZ NOT NULL DEFAULT now(), -- date de collecte
  sentiment_score NUMERIC(6,3),                   -- [-1.000, 1.000] (lexicon/ML)
  tags            JSONB,                          -- mots-clés, catégories
  raw_payload     JSONB,                          -- dump brut utile pour debug
  -- Idempotence forte: (source_id, external_id) si external_id dispo
  -- Sinon fallback sur url_hash + published_at
  UNIQUE (source_id, external_id),
  UNIQUE (url_hash, published_at)
);

-- Association many-to-many: news ↔ symbol
CREATE TABLE IF NOT EXISTS cryptoviz.news_event_symbols (
  news_id     BIGINT NOT NULL REFERENCES cryptoviz.news_events(news_id) ON DELETE CASCADE,
  symbol      TEXT   NOT NULL REFERENCES cryptoviz.symbols(symbol) ON DELETE RESTRICT,
  relevance   NUMERIC(5,2),                       -- optionnel: score d'association 0-1
  PRIMARY KEY (news_id, symbol)
);

-- Index utiles pour recherche
CREATE INDEX IF NOT EXISTS news_events_published_idx
  ON cryptoviz.news_events (published_at DESC);

CREATE INDEX IF NOT EXISTS news_events_title_trgm_idx
  ON cryptoviz.news_events USING GIN (title gin_trgm_ops);

CREATE INDEX IF NOT EXISTS news_events_tags_gin_idx
  ON cryptoviz.news_events USING GIN (tags);

-- ==========================
-- 3) Market data (OHLCV + market cap)
-- ==========================

-- Table de ticks (granularité libre: 1m, 5m, 1h, 1d selon l’ingestion)
-- Clé naturelle: (symbol, ts)
CREATE TABLE IF NOT EXISTS cryptoviz.market_ticks (
  symbol       TEXT NOT NULL REFERENCES cryptoviz.symbols(symbol) ON DELETE RESTRICT,
  ts           TIMESTAMPTZ NOT NULL,
  open         NUMERIC(18,8) NOT NULL,
  high         NUMERIC(18,8) NOT NULL,
  low          NUMERIC(18,8) NOT NULL,
  close        NUMERIC(18,8) NOT NULL,
  volume       NUMERIC(28,8),            -- volume en unités (coin)
  market_cap   NUMERIC(28,8),            -- market cap en $
  source       TEXT,                     -- ex. 'coingecko'
  collected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (symbol, ts)
);

CREATE INDEX IF NOT EXISTS market_ticks_ts_idx
  ON cryptoviz.market_ticks (ts DESC);

-- ==========================
-- 4) Hypertables & Continuous Aggregates (si TimescaleDB)
-- ==========================
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
    -- Hypertable: partitionnement par temps (ts) + dimension "space" (symbol)
    PERFORM create_hypertable('cryptoviz.market_ticks', 'ts', 'symbol', 2, if_not_exists => TRUE);

    -- Exemple de continuous aggregate journalier (OHLC + volume & market cap)
    -- Vue matérialisée s’actualisant sur nouvelles données
    CREATE MATERIALIZED VIEW IF NOT EXISTS cryptoviz.cagg_market_daily
    WITH (timescaledb.continuous) AS
    SELECT
      symbol,
      time_bucket('1 day', ts) AS bucket,
      first(open, ts)          AS open,
      max(high)                AS high,
      min(low)                 AS low,
      last(close, ts)          AS close,
      sum(volume)              AS volume,
      last(market_cap, ts)     AS market_cap
    FROM cryptoviz.market_ticks
    GROUP BY symbol, bucket
    WITH NO DATA;

    -- Politique de rafraîchissement automatique (derniers 7 jours, toutes les 15 min)
    SELECT add_continuous_aggregate_policy(
      'cryptoviz.cagg_market_daily',
      start_offset => INTERVAL '7 days',
      end_offset   => INTERVAL '1 hour',
      schedule_interval => INTERVAL '15 minutes'
    );

    -- Politique de rétention sur les ticks bruts (ex: conserver 180 jours)
    SELECT add_retention_policy('cryptoviz.market_ticks', INTERVAL '180 days');

  END IF;
END$$;

-- ==========================
-- 5) Vues pratiques (fonctionnent sans TimescaleDB)
-- ==========================

-- Vue quotidienne "vanilla" (fallback si pas de TimescaleDB)
-- (Si TimescaleDB présent, préfère cryptoviz.cagg_market_daily)
CREATE OR REPLACE VIEW cryptoviz.market_daily AS
SELECT
  symbol,
  date_trunc('day', ts) AS bucket,
  first_value(open)  OVER w AS open,
  max(high)          OVER w AS high,
  min(low)           OVER w AS low,
  last_value(close)  OVER w AS close,
  SUM(volume)        OVER w AS volume,
  last_value(market_cap) OVER w AS market_cap
FROM cryptoviz.market_ticks
WINDOW w AS (PARTITION BY symbol, date_trunc('day', ts)
             ORDER BY ts
             ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING);

-- ==========================
-- 6) Contrainte d’idempotence côté news (fallback)
-- ==========================
-- Si external_id non fourni par la source, on s’appuie sur (url_hash, published_at)
-- déjà couvert par UNIQUE, mais on peut ajouter un index partiel utile:
CREATE INDEX IF NOT EXISTS news_events_urlhash_idx
  ON cryptoviz.news_events (url_hash)
  WHERE external_id IS NULL;

-- ==========================
-- 7) Helpers: vues & fonctions de confort
-- ==========================

-- Vue: top movers sur 24h (delta close)
CREATE OR REPLACE VIEW cryptoviz.top_movers_24h AS
WITH last_close AS (
  SELECT DISTINCT ON (symbol)
    symbol, close AS close_now, ts
  FROM cryptoviz.market_ticks
  ORDER BY symbol, ts DESC
),
close_24h AS (
  SELECT mt.symbol, mt.close AS close_24h
  FROM cryptoviz.market_ticks mt
  JOIN last_close lc
    ON lc.symbol = mt.symbol
   AND mt.ts <= lc.ts - INTERVAL '24 hours'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY mt.symbol ORDER BY mt.ts DESC) = 1
)
SELECT
  lc.symbol,
  lc.close_now,
  c24.close_24h,
  CASE WHEN c24.close_24h IS NULL OR c24.close_24h = 0
       THEN NULL
       ELSE (lc.close_now - c24.close_24h) / c24.close_24h * 100.0
  END AS pct_change_24h
FROM last_close lc
LEFT JOIN close_24h c24 ON c24.symbol = lc.symbol
ORDER BY pct_change_24h DESC NULLS LAST;

-- Vue: jointure news + symboles + sentiment
CREATE OR REPLACE VIEW cryptoviz.news_with_symbols AS
SELECT
  n.news_id,
  n.published_at,
  n.title,
  n.url,
  n.sentiment_score,
  s.symbol,
  src.name AS source_name,
  src.kind AS source_kind
FROM cryptoviz.news_events n
JOIN cryptoviz.news_event_symbols ns USING (news_id)
JOIN cryptoviz.symbols s ON s.symbol = ns.symbol
JOIN cryptoviz.sources src ON src.source_id = n.source_id;
