-- ============================================================
-- Vigi Numérique — Schéma PostgreSQL opérationnel
-- ============================================================

CREATE EXTENSION IF NOT EXISTS postgis;

-- ─── 1. Lignes ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lines (
    line_id     VARCHAR PRIMARY KEY,
    line_name   VARCHAR NOT NULL,
    mode        VARCHAR NOT NULL,   -- metro, rer, train, bus, tram
    operator    VARCHAR NOT NULL,   -- SNCF, RATP, ...
    is_active   BOOLEAN NOT NULL DEFAULT TRUE
);

-- ─── 2. Stations / Arrêts ────────────────────────────────────
CREATE TABLE IF NOT EXISTS stations (
    stop_id     VARCHAR PRIMARY KEY,
    stop_name   VARCHAR NOT NULL,
    lat         FLOAT,
    lon         FLOAT,
    zone_id     VARCHAR,
    geom        GEOMETRY(Point, 4326)
);

-- ─── 3. Passages théoriques ──────────────────────────────────
CREATE TABLE IF NOT EXISTS scheduled_passages (
    scheduled_id    BIGSERIAL PRIMARY KEY,
    line_id         VARCHAR NOT NULL REFERENCES lines(line_id),
    stop_id         VARCHAR NOT NULL REFERENCES stations(stop_id),
    direction       VARCHAR,
    trip_id         VARCHAR,
    scheduled_time  TIMESTAMP NOT NULL,
    service_date    DATE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_scheduled_line_time
    ON scheduled_passages(line_id, scheduled_time);

CREATE INDEX IF NOT EXISTS idx_scheduled_stop_time
    ON scheduled_passages(stop_id, scheduled_time);

-- ─── 4. Passages observés (temps réel) ───────────────────────
CREATE TABLE IF NOT EXISTS observed_passages (
    observed_id     BIGSERIAL PRIMARY KEY,
    line_id         VARCHAR NOT NULL REFERENCES lines(line_id),
    stop_id         VARCHAR NOT NULL REFERENCES stations(stop_id),
    direction       VARCHAR,
    observed_time   TIMESTAMP NOT NULL,
    collected_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    source_ref      VARCHAR,
    status          VARCHAR,
    raw_payload     JSONB
);

CREATE INDEX IF NOT EXISTS idx_observed_line_time
    ON observed_passages(line_id, observed_time);

CREATE INDEX IF NOT EXISTS idx_observed_stop_time
    ON observed_passages(stop_id, observed_time);

-- ─── 5. Incidents officiels ───────────────────────────────────
CREATE TABLE IF NOT EXISTS official_incidents (
    incident_id     VARCHAR PRIMARY KEY,
    line_id         VARCHAR REFERENCES lines(line_id),
    stop_id         VARCHAR REFERENCES stations(stop_id),
    severity        VARCHAR,        -- low, medium, high, critical
    start_time      TIMESTAMP NOT NULL,
    end_time        TIMESTAMP,
    label           VARCHAR,
    description     TEXT,
    source_payload  JSONB
);

CREATE INDEX IF NOT EXISTS idx_incidents_line
    ON official_incidents(line_id, start_time);

-- ─── 6. Métriques réseau calculées ───────────────────────────
CREATE TABLE IF NOT EXISTS network_metrics (
    metric_id           BIGSERIAL PRIMARY KEY,
    computed_at         TIMESTAMP NOT NULL DEFAULT NOW(),
    line_id             VARCHAR NOT NULL REFERENCES lines(line_id),
    stop_id             VARCHAR REFERENCES stations(stop_id),
    window_size_min     INT NOT NULL DEFAULT 5,
    mean_delay          FLOAT,
    abs_mean_delay      FLOAT,
    punctuality_score   FLOAT,
    regularity_score    FLOAT,
    missing_passages    INT DEFAULT 0,
    headway_gap         FLOAT,
    anomaly_score       FLOAT,
    network_state       VARCHAR     -- nominal, sous_surveillance, degrade, perturbe, incident_majeur
);

CREATE INDEX IF NOT EXISTS idx_metrics_line_time
    ON network_metrics(line_id, computed_at);

-- ─── 7. Événements détectés ───────────────────────────────────
CREATE TABLE IF NOT EXISTS events (
    event_id                BIGSERIAL PRIMARY KEY,
    computed_at             TIMESTAMP NOT NULL DEFAULT NOW(),
    line_id                 VARCHAR NOT NULL REFERENCES lines(line_id),
    stop_id                 VARCHAR REFERENCES stations(stop_id),
    event_type              VARCHAR NOT NULL,   -- retard, suppression_probable, irregularite, propagation, derive_non_declaree
    severity                VARCHAR NOT NULL,   -- faible, moyen, fort, critique
    anomaly_score           FLOAT,
    network_state           VARCHAR,
    status                  VARCHAR NOT NULL DEFAULT 'ouvert',  -- ouvert, clos, en_cours
    official_incident_flag  BOOLEAN DEFAULT FALSE,
    description             TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_line_time
    ON events(line_id, computed_at);

CREATE INDEX IF NOT EXISTS idx_events_status
    ON events(status);

-- ─── 8. Qualifications agents ────────────────────────────────
CREATE TABLE IF NOT EXISTS event_qualifications (
    qualification_id    BIGSERIAL PRIMARY KEY,
    event_id            BIGINT NOT NULL REFERENCES events(event_id),
    agent_id            VARCHAR NOT NULL,
    qualification       VARCHAR NOT NULL,   -- CONFIRME, FAUX_POSITIF, DEJA_CONNU, CLOS, EN_COURS_ANALYSE
    comment             TEXT,
    qualified_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_qualif_event
    ON event_qualifications(event_id);