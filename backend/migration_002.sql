-- Migration 002 — enrichissement table stations
-- Ajoute les colonnes produites par le pipeline de ton collègue

ALTER TABLE stations ADD COLUMN IF NOT EXISTS quay_id      VARCHAR;
ALTER TABLE stations ADD COLUMN IF NOT EXISTS quay_code    VARCHAR;
ALTER TABLE stations ADD COLUMN IF NOT EXISTS nature       VARCHAR;
ALTER TABLE stations ADD COLUMN IF NOT EXISTS city         VARCHAR;
ALTER TABLE stations ADD COLUMN IF NOT EXISTS postal_code  VARCHAR;
ALTER TABLE stations ADD COLUMN IF NOT EXISTS tariff_zone  VARCHAR;
ALTER TABLE stations ADD COLUMN IF NOT EXISTS raw_data     JSONB;
ALTER TABLE stations ADD COLUMN IF NOT EXISTS created_at   TIMESTAMP NOT NULL DEFAULT NOW();
ALTER TABLE stations ADD COLUMN IF NOT EXISTS updated_at   TIMESTAMP NOT NULL DEFAULT NOW();

-- Index utiles pour le moteur de détection
CREATE INDEX IF NOT EXISTS idx_stations_quay_id  ON stations(quay_id);
CREATE INDEX IF NOT EXISTS idx_stations_zone_id  ON stations(zone_id);
CREATE INDEX IF NOT EXISTS idx_stations_nature   ON stations(nature);
CREATE INDEX IF NOT EXISTS idx_stations_geom     ON stations USING GIST(geom);