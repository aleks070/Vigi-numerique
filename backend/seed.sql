-- ============================================================
-- Vigi Numérique — Données de référence (lignes & stations)
-- ============================================================

-- ─── Lignes ──────────────────────────────────────────────────
INSERT INTO lines (line_id, line_name, mode, operator, is_active) VALUES
    ('STIF:Line::C01742:', 'RER A',  'rer',   'RATP',  TRUE),
    ('STIF:Line::C01743:', 'RER B',  'rer',   'RATP',  TRUE),
    ('STIF:Line::C01727:', 'RER C',  'rer',   'SNCF',  TRUE),
    ('STIF:Line::C01728:', 'RER D',  'rer',   'SNCF',  TRUE),
    ('STIF:Line::C01729:', 'RER E',  'rer',   'SNCF',  TRUE),
    ('STIF:Line::C01090:', 'Ligne 1', 'metro', 'RATP', TRUE),
    ('STIF:Line::C01091:', 'Ligne 2', 'metro', 'RATP', TRUE),
    ('STIF:Line::C01092:', 'Ligne 3', 'metro', 'RATP', TRUE),
    ('STIF:Line::C01093:', 'Ligne 4', 'metro', 'RATP', TRUE),
    ('STIF:Line::C01094:', 'Ligne 5', 'metro', 'RATP', TRUE),
    ('STIF:Line::C01095:', 'Ligne 6', 'metro', 'RATP', TRUE),
    ('STIF:Line::C01096:', 'Ligne 7', 'metro', 'RATP', TRUE),
    ('STIF:Line::C01097:', 'Ligne 8', 'metro', 'RATP', TRUE),
    ('STIF:Line::C01098:', 'Ligne 9', 'metro', 'RATP', TRUE),
    ('STIF:Line::C01099:', 'Ligne 10','metro', 'RATP', TRUE),
    ('STIF:Line::C01100:', 'Ligne 11','metro', 'RATP', TRUE),
    ('STIF:Line::C01101:', 'Ligne 12','metro', 'RATP', TRUE),
    ('STIF:Line::C01102:', 'Ligne 13','metro', 'RATP', TRUE),
    ('STIF:Line::C01103:', 'Ligne 14','metro', 'RATP', TRUE)
ON CONFLICT (line_id) DO NOTHING;

-- ─── Stations (arrêts majeurs RER A) ─────────────────────────
INSERT INTO stations (stop_id, stop_name, lat, lon, zone_id) VALUES
    ('STIF:StopPoint:Q:41027:', 'Saint-Germain-en-Laye',  48.8989, 2.0940,  '4'),
    ('STIF:StopPoint:Q:41030:', 'Le Vésinet-Le Pecq',     48.8953, 2.1189,  '3'),
    ('STIF:StopPoint:Q:41032:', 'Le Vésinet-Centre',      48.8914, 2.1364,  '3'),
    ('STIF:StopPoint:Q:41034:', 'Chatou-Croissy',         48.8875, 2.1578,  '3'),
    ('STIF:StopPoint:Q:41037:', 'Rueil-Malmaison',        48.8773, 2.1847,  '2'),
    ('STIF:StopPoint:Q:41040:', 'Nanterre-Université',    48.9033, 2.2097,  '2'),
    ('STIF:StopPoint:Q:41042:', 'Nanterre-Ville',         48.8936, 2.2056,  '2'),
    ('STIF:StopPoint:Q:41044:', 'Nanterre-Préfecture',    48.8966, 2.2122,  '2'),
    ('STIF:StopPoint:Q:41048:', 'La Défense',             48.8921, 2.2387,  '2'),
    ('STIF:StopPoint:Q:41050:', 'Charles de Gaulle-Étoile',48.8738, 2.2950, '1'),
    ('STIF:StopPoint:Q:41052:', 'Auber',                  48.8740, 2.3317,  '1'),
    ('STIF:StopPoint:Q:41054:', 'Châtelet-Les Halles',    48.8604, 2.3471,  '1'),
    ('STIF:StopPoint:Q:41056:', 'Gare de Lyon',           48.8448, 2.3736,  '1'),
    ('STIF:StopPoint:Q:41058:', 'Nation',                 48.8484, 2.3961,  '1'),
    ('STIF:StopPoint:Q:41060:', 'Vincennes',              48.8478, 2.4394,  '2'),
    ('STIF:StopPoint:Q:41062:', 'Saint-Mandé',            48.8453, 2.4194,  '2'),
    ('STIF:StopPoint:Q:41064:', 'Fontenay-sous-Bois',     48.8539, 2.4783,  '2'),
    ('STIF:StopPoint:Q:41066:', 'Nogent-sur-Marne',       48.8383, 2.4808,  '2'),
    ('STIF:StopPoint:Q:41068:', 'Le Perreux-Nogent',      48.8367, 2.5019,  '2'),
    ('STIF:StopPoint:Q:41070:', 'Neuilly-Plaisance',      48.8597, 2.5214,  '3'),
    ('STIF:StopPoint:Q:41072:', 'Bry-sur-Marne',          48.8400, 2.5253,  '3'),
    ('STIF:StopPoint:Q:41074:', 'Villiers-sur-Marne',     48.8328, 2.5456,  '3'),
    ('STIF:StopPoint:Q:41076:', 'Champigny',              48.8219, 2.5186,  '3'),
    ('STIF:StopPoint:Q:41078:', 'La Varenne-Chennevières',48.8042, 2.5086,  '3'),
    ('STIF:StopPoint:Q:41080:', 'Sucy-Bonneuil',          48.7714, 2.5253,  '3'),
    ('STIF:StopPoint:Q:41082:', 'Boissy-Saint-Léger',     48.7528, 2.5083,  '4')
ON CONFLICT (stop_id) DO NOTHING;
