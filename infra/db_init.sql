-- Extensions
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Table articles
DROP TABLE IF EXISTS news_articles CASCADE;
CREATE TABLE news_articles (
    id        UUID DEFAULT gen_random_uuid(),
    ts        TIMESTAMPTZ NOT NULL,
    source    TEXT NOT NULL,
    url       TEXT NOT NULL,
    url_hash  TEXT GENERATED ALWAYS AS (encode(digest(url, 'sha256'), 'hex')) STORED,
    title     TEXT,
    summary   TEXT,
    content   TEXT,
    lang      TEXT,
    symbols   TEXT[] DEFAULT '{}',
    sentiment REAL,
    raw       JSONB,
    PRIMARY KEY (id, ts)  -- clé composite, inclut ts
);

-- Hypertable sur ts
SELECT create_hypertable('news_articles', 'ts', if_not_exists => TRUE, migrate_data => TRUE);

-- Contraintes d'unicité
CREATE UNIQUE INDEX IF NOT EXISTS news_articles_url_uniq ON news_articles(url);

-- Index temps + symboles
CREATE INDEX IF NOT EXISTS ix_news_articles_ts ON news_articles(ts DESC);
CREATE INDEX IF NOT EXISTS ix_news_articles_symbols ON news_articles USING GIN(symbols);

-- Continuous aggregate : volume par minute et source
DROP MATERIALIZED VIEW IF EXISTS mv_news_volume_1m CASCADE;
CREATE MATERIALIZED VIEW mv_news_volume_1m
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 minute', ts) AS bucket,
       source,
       COUNT(*)::BIGINT AS volume
FROM news_articles
GROUP BY bucket, source;

-- Politique de refresh (1 min)
SELECT add_continuous_aggregate_policy('mv_news_volume_1m',
    start_offset => INTERVAL '7 days',
    end_offset   => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute');

-- Retention : 180 jours
SELECT add_retention_policy('news_articles', INTERVAL '180 days', if_not_exists => TRUE);
