-- Migration — ajout colonne justification à la table events
ALTER TABLE events ADD COLUMN IF NOT EXISTS justification TEXT;
