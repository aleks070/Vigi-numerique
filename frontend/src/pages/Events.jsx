import { useState, useEffect } from 'react'
import axios from 'axios'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// ─── Données mock ─────────────────────────────────────────────
const MOCK_EVENTS = [
  {
    event_id: 1,
    line_id: 'STIF:Line::C01742:',
    event_type: 'derive_non_declaree',
    severity: 'fort',
    anomaly_score: 78,
    network_state: 'perturbe',
    status: 'ouvert',
    description: 'Retard moyen > 4 min sur 3 fenêtres successives — Châtelet-Les Halles',
    justification: 'D=65 M=40 H=30 P=80 S=20',
    official_incident_flag: false,
    computed_at: new Date(Date.now() - 5 * 60000).toISOString(),
  },
  {
    event_id: 2,
    line_id: 'STIF:Line::C01742:',
    event_type: 'suppression_probable',
    severity: 'moyen',
    anomaly_score: 54,
    network_state: 'degrade',
    status: 'ouvert',
    description: 'Passage théorique absent — La Défense direction Boissy',
    justification: 'D=20 M=80 H=40 P=30 S=10',
    official_incident_flag: false,
    computed_at: new Date(Date.now() - 12 * 60000).toISOString(),
  },
  {
    event_id: 3,
    line_id: 'STIF:Line::C01743:',
    event_type: 'irregularite',
    severity: 'faible',
    anomaly_score: 31,
    network_state: 'sous_surveillance',
    status: 'en_cours',
    description: 'Irrégularité de fréquence — headway +40% au-dessus du théorique',
    justification: 'D=10 M=0 H=60 P=20 S=0',
    official_incident_flag: false,
    computed_at: new Date(Date.now() - 23 * 60000).toISOString(),
  },
  {
    event_id: 4,
    line_id: 'STIF:Line::C01742:',
    event_type: 'incident_officiel',
    severity: 'critique',
    anomaly_score: 85,
    network_state: 'perturbe',
    status: 'clos',
    description: 'Incident officiel RATP — interruption partielle RER A',
    justification: 'D=80 M=60 H=50 P=90 S=40',
    official_incident_flag: true,
    computed_at: new Date(Date.now() - 45 * 60000).toISOString(),
  },
]

// ─── Helpers ──────────────────────────────────────────────────
const LINE_NAMES = {
  'STIF:Line::C01742:': 'RER A',
  'STIF:Line::C01743:': 'RER B',
  'STIF:Line::C01727:': 'RER C',
  'STIF:Line::C01728:': 'RER D',
  'STIF:Line::C01729:': 'RER E',
}

const EVENT_TYPE_LABELS = {
  derive_non_declaree:  'Dérive non déclarée',
  suppression_probable: 'Suppression probable',
  irregularite:         'Irrégularité',
  retard:               'Retard',
  propagation:          'Propagation',
  incident_officiel:    'Incident officiel',
  anomalie_generique:   'Anomalie',
}

const STATE_LABELS = {
  nominal:          'Nominal',
  sous_surveillance: 'Surveillance',
  degrade:          'Dégradé',
  perturbe:         'Perturbé',
  incident_majeur:  'Incident majeur',
}

const QUALIFICATIONS = [
  { value: 'CONFIRME',        label: 'Confirmé',           color: '#EF4444' },
  { value: 'FAUX_POSITIF',    label: 'Faux positif',       color: '#10B981' },
  { value: 'DEJA_CONNU',      label: 'Déjà connu',         color: '#F59E0B' },
  { value: 'CLOS',            label: 'Clore',              color: '#6B7280' },
  { value: 'EN_COURS_ANALYSE',label: 'En cours d\'analyse', color: '#3B82F6' },
]

function timeAgo(iso) {
  const diff = Math.floor((Date.now() - new Date(iso)) / 60000)
  if (diff < 1) return 'à l\'instant'
  if (diff === 1) return 'il y a 1 min'
  if (diff < 60) return `il y a ${diff} min`
  return `il y a ${Math.floor(diff / 60)}h`
}

function lineShortName(lineId) {
  return LINE_NAMES[lineId] || lineId
}

// ─── Composants ───────────────────────────────────────────────
function StateBadge({ state }) {
  const colors = {
    nominal:           { bg: '#ECFDF5', text: '#10B981' },
    sous_surveillance: { bg: '#FFFBEB', text: '#F59E0B' },
    degrade:           { bg: '#FFF7ED', text: '#F97316' },
    perturbe:          { bg: '#FEF2F2', text: '#EF4444' },
    incident_majeur:   { bg: '#F5F3FF', text: '#7C3AED' },
  }
  const c = colors[state] || colors.nominal
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      padding: '2px 8px', borderRadius: 20,
      fontSize: 11, fontWeight: 600,
      background: c.bg, color: c.text,
    }}>
      {STATE_LABELS[state] || state}
    </span>
  )
}

function SeverityDot({ severity }) {
  const colors = { faible: '#10B981', moyen: '#F59E0B', fort: '#F97316', critique: '#EF4444' }
  return (
    <span style={{
      display: 'inline-block', width: 8, height: 8,
      borderRadius: '50%', marginRight: 6,
      background: colors[severity] || '#9CA3AF',
    }} />
  )
}

// ─── Page principale ──────────────────────────────────────────
export default function Events() {
  const [events, setEvents] = useState(MOCK_EVENTS)
  const [selected, setSelected] = useState(null)
  const [comment, setComment] = useState('')
  const [qualifyLoading, setQualifyLoading] = useState(false)
  const [qualifySuccess, setQualifySuccess] = useState('')

  // Filtres
  const [filterLine, setFilterLine] = useState('')
  const [filterSeverity, setFilterSeverity] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [search, setSearch] = useState('')

  // Charge les vrais événements
  useEffect(() => {
    const load = async () => {
      try {
        const params = {}
        if (filterLine) params.line_id = filterLine
        if (filterSeverity) params.severity = filterSeverity
        if (filterStatus) params.status = filterStatus
        const res = await axios.get(`${API}/events`, { params })
        if (res.data?.length) setEvents(res.data)
      } catch {
        // fallback mock
      }
    }
    load()
    const interval = setInterval(load, 60000)
    return () => clearInterval(interval)
  }, [filterLine, filterSeverity, filterStatus])

  // Filtrage côté client (search)
  const filtered = events.filter(ev => {
    if (search) {
      const q = search.toLowerCase()
      const desc = (ev.description || '').toLowerCase()
      const line = lineShortName(ev.line_id).toLowerCase()
      if (!desc.includes(q) && !line.includes(q)) return false
    }
    return true
  })

  // Qualification
  const handleQualify = async (qualification) => {
    if (!selected) return
    setQualifyLoading(true)
    setQualifySuccess('')
    try {
      await axios.post(`${API}/events/${selected.event_id}/qualify`, {
        agent_id: 'ADMIN001',
        qualification,
        comment: comment || null,
      })
      setQualifySuccess(`Qualification "${qualification}" enregistrée`)
      setComment('')
      // Rafraîchit la liste
      if (qualification === 'CLOS') {
        setEvents(prev => prev.map(e =>
          e.event_id === selected.event_id ? { ...e, status: 'clos' } : e
        ))
        setSelected(prev => ({ ...prev, status: 'clos' }))
      }
    } catch {
      setQualifySuccess('Erreur lors de la qualification')
    } finally {
      setQualifyLoading(false)
    }
  }

  const uniqueLines = [...new Set(events.map(e => e.line_id))]

  return (
    <div style={{ display: 'flex', gap: 16, height: 'calc(100vh - 108px)' }}>

      {/* ── Liste + filtres ── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 16, minWidth: 0 }}>

        {/* Filtres */}
        <div className="card">
          <div style={{ padding: '12px 16px', display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>

            {/* Recherche */}
            <input
              type="text"
              placeholder="Rechercher..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{
                padding: '6px 10px', border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)', fontSize: 13,
                color: 'var(--text-primary)', background: 'var(--surface)',
                width: 180, outline: 'none',
              }}
            />

            {/* Filtre ligne */}
            <select
              value={filterLine}
              onChange={e => setFilterLine(e.target.value)}
              style={{
                padding: '6px 10px', border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)', fontSize: 13,
                color: 'var(--text-primary)', background: 'var(--surface)',
                outline: 'none', cursor: 'pointer',
              }}
            >
              <option value="">Toutes les lignes</option>
              {uniqueLines.map(l => (
                <option key={l} value={l}>{lineShortName(l)}</option>
              ))}
            </select>

            {/* Filtre gravité */}
            <select
              value={filterSeverity}
              onChange={e => setFilterSeverity(e.target.value)}
              style={{
                padding: '6px 10px', border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)', fontSize: 13,
                color: 'var(--text-primary)', background: 'var(--surface)',
                outline: 'none', cursor: 'pointer',
              }}
            >
              <option value="">Toutes gravités</option>
              <option value="faible">Faible</option>
              <option value="moyen">Moyen</option>
              <option value="fort">Fort</option>
              <option value="critique">Critique</option>
            </select>

            {/* Filtre statut */}
            <select
              value={filterStatus}
              onChange={e => setFilterStatus(e.target.value)}
              style={{
                padding: '6px 10px', border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)', fontSize: 13,
                color: 'var(--text-primary)', background: 'var(--surface)',
                outline: 'none', cursor: 'pointer',
              }}
            >
              <option value="">Tous statuts</option>
              <option value="ouvert">Ouvert</option>
              <option value="en_cours">En cours</option>
              <option value="clos">Clos</option>
            </select>

            <span style={{ fontSize: 12, color: 'var(--text-muted)', marginLeft: 'auto' }}>
              {filtered.length} événement(s)
            </span>
          </div>
        </div>

        {/* Table */}
        <div className="card" style={{ flex: 1, overflow: 'auto' }}>
          {filtered.length === 0 ? (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
              Aucun événement correspondant aux filtres
            </div>
          ) : (
            <table className="events-table">
              <thead>
                <tr>
                  <th>Ligne</th>
                  <th>Type</th>
                  <th>Description</th>
                  <th>État</th>
                  <th>Score</th>
                  <th>Statut</th>
                  <th>Détecté</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(ev => (
                  <tr
                    key={ev.event_id}
                    onClick={() => { setSelected(ev); setQualifySuccess('') }}
                    style={{ background: selected?.event_id === ev.event_id ? 'var(--blue-light)' : undefined }}
                  >
                    <td>
                      <span className="line-pill">{lineShortName(ev.line_id)}</span>
                    </td>
                    <td>
                      <SeverityDot severity={ev.severity} />
                      {EVENT_TYPE_LABELS[ev.event_type] || ev.event_type}
                    </td>
                    <td style={{ maxWidth: 280, color: 'var(--text-secondary)', fontSize: 12 }}>
                      {ev.description}
                    </td>
                    <td><StateBadge state={ev.network_state} /></td>
                    <td style={{ fontFamily: 'DM Mono, monospace', fontSize: 12 }}>
                      {Math.round(ev.anomaly_score)}
                    </td>
                    <td>
                      <span style={{
                        fontSize: 11, fontWeight: 500,
                        color: ev.status === 'ouvert' ? '#EF4444' : ev.status === 'en_cours' ? '#F59E0B' : '#6B7280',
                      }}>
                        {ev.status === 'ouvert' ? '● Ouvert' : ev.status === 'en_cours' ? '● En cours' : '○ Clos'}
                      </span>
                    </td>
                    <td style={{ fontSize: 12, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                      {timeAgo(ev.computed_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* ── Panneau détail + qualification ── */}
      <div style={{
        width: 300, background: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius)', padding: 16,
        display: 'flex', flexDirection: 'column', gap: 14,
        overflowY: 'auto', flexShrink: 0,
      }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
          Détail & Qualification
        </div>

        {!selected ? (
          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            Sélectionnez un événement dans la liste.
          </div>
        ) : (
          <>
            {/* Infos */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div>
                <div className="kpi-label">Ligne</div>
                <span className="line-pill">{lineShortName(selected.line_id)}</span>
              </div>
              <div>
                <div className="kpi-label">Type</div>
                <div style={{ fontSize: 13, fontWeight: 500 }}>
                  {EVENT_TYPE_LABELS[selected.event_type] || selected.event_type}
                </div>
              </div>
              <div>
                <div className="kpi-label">État réseau</div>
                <StateBadge state={selected.network_state} />
              </div>
              <div>
                <div className="kpi-label">Score d'anomalie</div>
                <div style={{ fontFamily: 'DM Mono, monospace', fontSize: 26, fontWeight: 300 }}>
                  {Math.round(selected.anomaly_score)}
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>/100</span>
                </div>
              </div>
              {selected.official_incident_flag && (
                <div style={{
                  background: '#FEF2F2', border: '1px solid #EF4444',
                  borderRadius: 'var(--radius-sm)', padding: '6px 10px',
                  fontSize: 12, color: '#EF4444', fontWeight: 500,
                }}>
                  ⚠ Incident officiel associé
                </div>
              )}
              <div>
                <div className="kpi-label">Description</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  {selected.description}
                </div>
              </div>
              <div>
                <div className="kpi-label">Détecté</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  {new Date(selected.computed_at).toLocaleString('fr-FR')}
                </div>
              </div>
            </div>

            {/* Qualification */}
            <div style={{ borderTop: '1px solid var(--border)', paddingTop: 14 }}>
              <div className="kpi-label" style={{ marginBottom: 10 }}>Qualification agent</div>

              <textarea
                value={comment}
                onChange={e => setComment(e.target.value)}
                placeholder="Commentaire optionnel..."
                rows={2}
                style={{
                  width: '100%', padding: '7px 10px',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 12, color: 'var(--text-primary)',
                  background: 'var(--surface)', resize: 'none',
                  fontFamily: 'DM Sans, sans-serif',
                  outline: 'none', marginBottom: 8,
                  boxSizing: 'border-box',
                }}
              />

              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {QUALIFICATIONS.map(q => (
                  <button
                    key={q.value}
                    onClick={() => handleQualify(q.value)}
                    disabled={qualifyLoading || selected.status === 'clos'}
                    style={{
                      padding: '7px 12px',
                      border: `1px solid ${q.color}20`,
                      borderRadius: 'var(--radius-sm)',
                      background: `${q.color}10`,
                      cursor: qualifyLoading || selected.status === 'clos' ? 'not-allowed' : 'pointer',
                      fontSize: 12, fontWeight: 500,
                      color: q.color,
                      textAlign: 'left',
                      fontFamily: 'DM Sans, sans-serif',
                      transition: 'all 0.15s',
                      opacity: selected.status === 'clos' ? 0.5 : 1,
                    }}
                  >
                    {q.label}
                  </button>
                ))}
              </div>

              {qualifySuccess && (
                <div style={{
                  marginTop: 10, padding: '7px 10px',
                  background: 'var(--nominal-bg)', color: 'var(--nominal)',
                  borderRadius: 'var(--radius-sm)', fontSize: 12, fontWeight: 500,
                }}>
                  {qualifySuccess}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}