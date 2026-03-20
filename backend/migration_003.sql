-- Migration 003 — Table agents (authentification)

CREATE TABLE IF NOT EXISTS agents (
    agent_id    VARCHAR PRIMARY KEY,
    email       VARCHAR UNIQUE NOT NULL,
    full_name   VARCHAR NOT NULL,
    password_hash VARCHAR NOT NULL,
    role        VARCHAR NOT NULL DEFAULT 'operateur',  -- operateur, superviseur, admin
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login  TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agents_email ON agents(email);

-- Agent admin par défaut (mot de passe : "vigi2026" — à changer en production)
INSERT INTO agents (agent_id, email, full_name, password_hash, role)
VALUES (
    'ADMIN001',
    'admin@vigi-numerique.fr',
    'Administrateur',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMlJDs75EBGlyAtDNqXlPSMTQy',
    'admin'
) ON CONFLICT (agent_id) DO NOTHING;
