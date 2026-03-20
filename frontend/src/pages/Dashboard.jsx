import { useState, useEffect } from 'react'
import axios from 'axios'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// ─── Données mock en attendant le backend complet ─────────────
const MOCK_EVENTS = [
  {
    event_id: 1,
    line_id: 'STIF:Line::C01742:',
    line_name: 'RER A',
    event_type: 'derive_non_declaree',
    severity: 'fort',
    anomaly_score: 78,
    network_state: 'perturbe',
    status: 'ouvert',
    description: 'Retard moyen > 4 min sur 3 fenêtres successives — Châtelet-Les Halles',
    computed_at: new Date(Date.now() - 5 * 60000).toISOString(),
  },
  {
    event_id: 2,
    line_id: 'STIF:Line::C01742:',
    line_name: 'RER A',
    event_type: 'suppression_probable',
    severity: 'moyen',
    anomaly_score: 54,
    network_state: 'degrade',
    status: 'ouvert',
    description: 'Passage théorique absent — La Défense direction Boissy',
    computed_at: new Date(Date.now() - 12 * 60000).toISOString(),
  },
  {
    event_id: 3,
    line_id: 'STIF:Line::C01743:',
    line_name: 'RER B',
    event_type: 'irregularite',
    severity: 'faible',
    anomaly_score: 31,
    network_state: 'surveillance',
    status: 'en_cours',
    description: 'Irrégularité de fréquence — headway +40% au-dessus du théorique',
    computed_at: new Date(Date.now() - 23 * 60000).toISOString(),
  },
]

const MOCK_KPI = {
  active_events: 3,
  incidents_officiels: 3,
  lignes_surveillees: 19,
  score_global: 72,
  network_state: 'degrade',
}

// ─── Helpers ──────────────────────────────────────────────────
const STATE_LABELS = {
  nominal:       'Nominal',
  surveillance:  'Surveillance',
  degrade:       'Dégradé',
  perturbe:      'Perturbé',
  incident:      'Incident majeur',
}

const EVENT_TYPE_LABELS = {
  derive_non_declaree:  'Dérive non déclarée',
  suppression_probable: 'Suppression probable',
  irregularite:         'Irrégularité',
  retard:               'Retard',
  propagation:          'Propagation',
}

function timeAgo(iso) {
  const diff = Math.floor((Date.now() - new Date(iso)) / 60000)
  if (diff < 1) return 'à l\'instant'
  if (diff === 1) return 'il y a 1 min'
  return `il y a ${diff} min`
}

function lineShortName(lineId) {
  const map = {
    'STIF:Line::C01742:': 'RER A',
    'STIF:Line::C01743:': 'RER B',
    'STIF:Line::C01727:': 'RER C',
    'STIF:Line::C01728:': 'RER D',
    'STIF:Line::C01729:': 'RER E',
  }
  return map[lineId] || lineId
}

// ─── Composants ───────────────────────────────────────────────
function KpiCard({ label, value, sub, type }) {
  return (
    <div className={`kpi-card ${type}`}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
      {sub && <div className="kpi-sub">{sub}</div>}
    </div>
  )
}

function StateBadge({ state }) {
  return (
    <span className={`state-badge ${state}`}>
      {STATE_LABELS[state] || state}
    </span>
  )
}

function EventRow({ event, onClick }) {
  return (
    <tr onClick={() => onClick(event)}>
      <td>
        <span className="line-pill">{lineShortName(event.line_id)}</span>
      </td>
      <td>
        <span className={`severity-dot ${event.severity}`} />
        {EVENT_TYPE_LABELS[event.event_type] || event.event_type}
      </td>
      <td style={{ maxWidth: 300, color: 'var(--text-secondary)' }}>
        {event.description}
      </td>
      <td>
        <StateBadge state={event.network_state} />
      </td>
      <td style={{ fontFamily: 'DM Mono, monospace', fontSize: 12, color: 'var(--text-muted)' }}>
        {Math.round(event.anomaly_score)}
      </td>
      <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>
        {timeAgo(event.computed_at)}
      </td>
    </tr>
  )
}

// ─── Page principale ──────────────────────────────────────────
export default function Dashboard() {
  const [events, setEvents] = useState(MOCK_EVENTS)
  const [kpi, setKpi] = useState(MOCK_KPI)
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(false)

  // Tente de charger les vraies données, fallback sur mock
  useEffect(() => {
    const load = async () => {
      try {
        const [evRes, netRes] = await Promise.all([
          axios.get(`${API}/events`),
          axios.get(`${API}/network/status`),
        ])
        if (evRes.data?.length) setEvents(evRes.data)
        if (netRes.data) setKpi(prev => ({ ...prev, ...netRes.data }))
      } catch {
        // Backend pas encore connecté — mock actif
      }
    }
    load()
    const interval = setInterval(load, 60000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div>
      {/* ── KPIs ── */}
      <div className="kpi-grid">
        <KpiCard
          label="Événements actifs"
          value={kpi.active_events}
          sub="sur les dernières 24h"
          type="danger"
        />
        <KpiCard
          label="Incidents officiels"
          value={kpi.incidents_officiels}
          sub="déclarés par IDFM"
          type="warning"
        />
        <KpiCard
          label="Lignes surveillées"
          value={kpi.lignes_surveillees}
          sub="RER + Métro IDF"
          type="info"
        />
        <KpiCard
          label="Score réseau global"
          value={`${kpi.score_global}/100`}
          sub={<StateBadge state={kpi.network_state} />}
          type="nominal"
        />
      </div>

      {/* ── Événements ── */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Événements détectés</span>
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            Mise à jour toutes les 60s
          </span>
        </div>

        {events.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">✓</div>
            Aucun événement actif — réseau nominal
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
                <th>Détecté</th>
              </tr>
            </thead>
            <tbody>
              {events.map(ev => (
                <EventRow key={ev.event_id} event={ev} onClick={setSelected} />
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* ── Détail événement (panneau latéral simplifié) ── */}
      {selected && (
        <div style={{
          position: 'fixed', right: 0, top: 0, bottom: 0, width: 380,
          background: 'var(--surface)', borderLeft: '1px solid var(--border)',
          padding: 28, zIndex: 200, overflowY: 'auto',
          boxShadow: '-4px 0 20px rgba(0,0,0,0.08)',
          animation: 'fadeIn 0.2s ease'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
            <span className="card-title">Détail événement</span>
            <button
              onClick={() => setSelected(null)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 18, color: 'var(--text-muted)' }}
            >✕</button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <div className="kpi-label">Ligne</div>
              <span className="line-pill">{lineShortName(selected.line_id)}</span>
            </div>
            <div>
              <div className="kpi-label">Type d'événement</div>
              <div style={{ fontSize: 14, fontWeight: 500 }}>
                {EVENT_TYPE_LABELS[selected.event_type] || selected.event_type}
              </div>
            </div>
            <div>
              <div className="kpi-label">État réseau</div>
              <StateBadge state={selected.network_state} />
            </div>
            <div>
              <div className="kpi-label">Score d'anomalie</div>
              <div style={{ fontFamily: 'DM Mono, monospace', fontSize: 28, fontWeight: 300 }}>
                {Math.round(selected.anomaly_score)}<span style={{ fontSize: 14, color: 'var(--text-muted)' }}>/100</span>
              </div>
            </div>
            <div>
              <div className="kpi-label">Description</div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                {selected.description}
              </div>
            </div>
            <div>
              <div className="kpi-label">Détecté</div>
              <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                {new Date(selected.computed_at).toLocaleString('fr-FR')}
              </div>
            </div>

            {/* Zone de qualification */}
            <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16, marginTop: 8 }}>
              <div className="kpi-label" style={{ marginBottom: 10 }}>Qualification agent</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {['CONFIRME', 'FAUX_POSITIF', 'DEJA_CONNU', 'CLOS'].map(q => (
                  <button
                    key={q}
                    onClick={() => alert(`Qualification "${q}" envoyée (à connecter au backend)`)}
                    style={{
                      padding: '8px 14px',
                      border: '1px solid var(--border)',
                      borderRadius: 'var(--radius-sm)',
                      background: 'var(--surface-2)',
                      cursor: 'pointer',
                      fontSize: 12,
                      fontWeight: 500,
                      color: 'var(--text-secondary)',
                      textAlign: 'left',
                      transition: 'all 0.15s',
                    }}
                    onMouseOver={e => e.target.style.background = 'var(--blue-light)'}
                    onMouseOut={e => e.target.style.background = 'var(--surface-2)'}
                  >
                    {q.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}