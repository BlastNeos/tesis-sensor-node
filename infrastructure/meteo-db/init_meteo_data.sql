-- ============================================================
-- init_meteo_data.sql — DB: meteo_data
--
-- Persistencia de datos ambientales y meteorológicos.
-- Adaptado del DER compartido al contrato ambiental vigente:
--
--   source   = naturaleza del dato: real | mock
--   producer = productor concreto: bme280 | open_meteo | ohmc | ...
--
-- Este contrato se documentará como ADR compartido en
-- starlink-station-stack.
--
-- Idempotente siempre que TimescaleDB soporte IF NOT EXISTS /
-- if_not_exists para la operación correspondiente.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ── Tabla base de métricas ambientales ───────────────────────
CREATE TABLE IF NOT EXISTS env_metrics (
    time                TIMESTAMPTZ  NOT NULL,
    node_id             VARCHAR(64)  NOT NULL,
    source              VARCHAR(16)  NOT NULL,
    producer            VARCHAR(64)  NOT NULL,

    temperature_c       FLOAT8,
    humidity_pct        FLOAT8,
    pressure_hpa        FLOAT8,
    precipitation_mm    FLOAT8,
    wind_speed_kmh      FLOAT8,
    wind_direction_deg  INTEGER,
    cloud_cover_pct     FLOAT8,

    sensor_id           INTEGER,
    schema_version      VARCHAR(16)  NOT NULL DEFAULT '1.0',

    PRIMARY KEY (time, node_id, source, producer),

    CONSTRAINT chk_env_source
        CHECK (source IN ('real', 'mock')),

    CONSTRAINT chk_env_temperature
        CHECK (
            temperature_c IS NULL
            OR (temperature_c > -50 AND temperature_c < 80)
        ),

    CONSTRAINT chk_env_humidity
        CHECK (
            humidity_pct IS NULL
            OR (humidity_pct >= 0 AND humidity_pct <= 100)
        ),

    CONSTRAINT chk_env_pressure
        CHECK (
            pressure_hpa IS NULL
            OR (pressure_hpa > 800 AND pressure_hpa < 1100)
        ),

    CONSTRAINT chk_env_precipitation
        CHECK (
            precipitation_mm IS NULL
            OR precipitation_mm >= 0
        ),

    CONSTRAINT chk_env_wind_speed
        CHECK (
            wind_speed_kmh IS NULL
            OR wind_speed_kmh >= 0
        ),

    CONSTRAINT chk_env_wind_direction
        CHECK (
            wind_direction_deg IS NULL
            OR (wind_direction_deg >= 0 AND wind_direction_deg < 360)
        ),

    CONSTRAINT chk_env_cloud_cover
        CHECK (
            cloud_cover_pct IS NULL
            OR (cloud_cover_pct >= 0 AND cloud_cover_pct <= 100)
        )
);

SELECT create_hypertable(
    'env_metrics',
    'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ── Índices secundarios ──────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_env_node_producer_time
    ON env_metrics (node_id, producer, time DESC);

CREATE INDEX IF NOT EXISTS idx_env_precipitation
    ON env_metrics (time DESC)
    WHERE precipitation_mm > 0;

-- ── Compresión + retención ───────────────────────────────────

ALTER TABLE env_metrics SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'node_id, source, producer',
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy(
    'env_metrics',
    INTERVAL '7 days',
    if_not_exists => TRUE
);

SELECT add_retention_policy(
    'env_metrics',
    INTERVAL '12 months',
    if_not_exists => TRUE
);

-- ── Continuous Aggregate horario ─────────────────────────────

CREATE MATERIALIZED VIEW IF NOT EXISTS env_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    node_id,
    source,
    producer,

    AVG(temperature_c)      AS avg_temperature_c,
    MAX(temperature_c)      AS max_temperature_c,
    MIN(temperature_c)      AS min_temperature_c,

    AVG(humidity_pct)       AS avg_humidity_pct,
    AVG(pressure_hpa)       AS avg_pressure_hpa,

    SUM(precipitation_mm)   AS total_precipitation_mm,

    AVG(wind_speed_kmh)     AS avg_wind_speed_kmh,

    COUNT(*)                AS sample_count

FROM env_metrics
GROUP BY bucket, node_id, source, producer
WITH NO DATA;

SELECT add_continuous_aggregate_policy(
    'env_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);
